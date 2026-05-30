# The "world not rendering" bug — root cause and fix

## Symptom

On the Hot Dog King Android port of Hell After School (`v71`, build 59), every
scrolling scene (Tutorial, the school, anywhere the camera is not at world
origin) renders as a **solid black screen with the HUD overlay drawn correctly
on top**. The character and world are alive — input, collisions, AI, audio all
behave normally — they're just *not visible*.

The Loading scene and the Title scene work perfectly. Both happen to use
`camera.position = (0, 0)`.

## Wrong theory (mine — recorded so we don't waste time on it again)

> "Layer render targets are being allocated at the world's full width
> (~9562 × 768) which exceeds the emulator's `GL_MAX_TEXTURE_SIZE`. GL
> silently rejects the FBO attachment, so every layer sample returns black."

This theory **was wrong** but it consumed an evening. The reason it looked
plausible: MuMu reports `vulkan version is 0` (GLES-only), and PGMMV does have
RT sizing logic that uses the full world width in some code paths.

The reason it's wrong: the in-game dumper Coolkids enabled in v71 prints the
actual RT size at allocation time. **Every single scene-layer RT is created at
1366 × 768. Always.** No texture-size violation anywhere.

## Real root cause

The dumper output, side-by-side, was the smoking gun:

**Loading scene (works):**
```
visitScene: camera pos=(0,0)
layer 4 direct visit visible=1 children=6 pos=(0,0) size=(1366,768)
layer 3 direct visit visible=1 children=6 pos=(0,0) size=(1366,768)
```

**Tutorial scene (black):**
```
visitScene: camera pos=(8196,0)
bg via RT sprite  visible=1 pos=(8196,0) size=(1366,768)
layer 12 via RT shader visible=1 pos=(8196,0)
layer 11 via RT shader visible=1 pos=(8196,0)
... (all 12 layers via RT shader)
```

Two completely different render paths:

| Scene | Path | Status |
|---|---|---|
| Loading / Title | **direct visit** — `sceneLayer->visit(renderer, viewMatrix, true)` from `GameManager::visitScene` | ✅ works |
| Tutorial (and every scrolling scene) | **RT shader** — each layer is pre-rendered into a 1366×768 `RenderTexture` via `RenderTextureCtrl::update(...)`, then the RT *sprite* is drawn at world position `camera.position` | ❌ produces a black RT |

So the issue is specifically in the *RT capture step*. The capture produces an
empty RT, then the sprite that displays the RT is correctly positioned at
`(8196, 0)` where the camera is looking, but the sprite has nothing in it. The
HUD draws on top via the main camera (no RT) and so it survives.

### Why the RT capture comes up empty

PGMMV's cocos2d-x layer 0 calls into `RenderTexture::onBegin` with
`setKeepMatrix(true)` to "capture in the current world transform". Inside that
path on this NDK r17c + armeabi-v7a + Mali/x86-bridge stack, the matrix that
ends up bound to the FBO does **not** stay coherent with the per-layer view
matrix that `SceneLayer::updateRenderer` then passes to its children's
`visit(parentTransform=…)`. The end result is that world-coord children at
~`(8196..9562, 0..768)` get transformed into NDC coordinates that fall outside
`[-1, 1]` and clip to the RT's clear color (black) — even though the RT is
otherwise allocated, bound, and presented correctly.

In other words: the layer RTs **were drawn into the wrong slice of the world**
on every frame. Loading/Title got away with it because `camera.position == 0`
so "wrong slice" happened to coincide with "right slice".

This is repeatable across emulators (MuMu, MEMU, the unnamed third one
Coolkids tried) and on physical hardware (Galaxy J3 Orbit). It is *not* an
emulator quirk and it is *not* a GLES feature-bit issue.

## The fix

Bypass the broken capture path entirely **for scene layers, on Android only**.
Background, TopMost, menus, HUD overlays and object-level shaders all keep the
RT path (they don't hit the bug because their camera offset is 0 in their own
coordinate space, or they're tiny enough that capture-misalignment doesn't
matter visually).

The intervention point is `agtk::RenderTextureCtrl::isUseShader()`. Both
`SceneLayer::updateRenderer` and `GameManager::visitScene` consult it to
decide between the RT-shader path and the direct-visit path. If we return
`false` for scene-layer controllers on Android, both fall back to direct
visit, which Loading/Title prove works.

### Source-level patch

File: `Player/Classes/Lib/RenderTexture.cpp`, function `bool
RenderTextureCtrl::isUseShader()`.

Branch in this repo: `v72-rt-shader-fix`.

```cpp
bool RenderTextureCtrl::isUseShader()
{
#ifdef __ANDROID__
    // Hell After School Android port — v72 RT-shader compositing fix.
    //
    // On Android the per-scene-layer RT capture path
    // (RenderTextureCtrl::update(delta, viewMatrix, maskList, objList,
    //  tileMapList, ignoreVisibleObject)) produces a fully-black RT for
    // scenes where the camera has scrolled (camera.position != (0,0)).
    // Patch: for kTypeSceneLayer specifically, return false so that
    //   1) SceneLayer::updateRenderer skips the broken RT capture path,
    //   2) GameManager::visitScene draws the layer via the working
    //      "direct visit" path (sceneLayer->visit(renderer, vm, true)),
    // which the Loading/Title scenes already prove works.
    //
    // Trade-off: disables per-layer shader filters (color tint / blur)
    // and overlap-mask effects on scene layers. Background, TopMost,
    // menus, HUD overlays and object-level shaders are untouched.
    if (getType() == kTypeSceneLayer) {
        return false;
    }
#endif
    if (getShaderList()->count()) {
        return true;
    }
    // ... rest of original implementation unchanged
}
```

Commit that introduced it: `eb043b2` ("Player/Classes/Lib/RenderTexture.cpp:
short-circuit isUseShader for kTypeSceneLayer on Android").

PR: `https://github.com/sonicsonica701-cloud/hell-after-school-android/pull/new/v72-rt-shader-fix`.

### Binary-equivalent patch

For shipping a patched APK without a full rebuild (which has been the actual
delivery path because Hot Dog King's `libMyGame.so` contains undocumented
quirks not in this GitHub repo — see [05-build-pipeline.md](05-build-pipeline.md)),
we do the same intervention as a 4-byte poke in the shipped v71 `.so`:

- Find `agtk::RenderTextureCtrl::isUseShader(void)` (mangled
  `_ZN4agtk17RenderTextureCtrl12isUseShaderEv`).
- Rewrite the function prologue to:
  ```
  movs r0, #0      ; 00 20
  bx   lr          ; 70 47
  ```
  (Total 4 bytes, thumb-mode, armeabi-v7a.)

This is the source patch's `if (kTypeSceneLayer) return false;` collapsed to
"always return false" — safe in practice because non-`kTypeSceneLayer`
controllers don't have shader lists set in this game's data (the dumper
confirms), so the original method's `getShaderList()->count() != 0` branch
never fired for them. Byte-precise offsets in [02-binary-patches.md](02-binary-patches.md).

## What this fix breaks

- Per-scene-layer shader effects on Android: color tints, blur, depth fog,
  any custom shader you assign to a layer in PGMMV editor. None of Hell After
  School's verified scenes appear to use these on layers — they apply shaders
  to objects (the dumper logs `object N shader=…` lines, those still work).
- Overlap-mask effects between layers (e.g. fog of war revealing as the
  player walks). Same applies — not used in HAS as far as we've seen.
- Windows / Mac / iOS builds are untouched (`#ifdef __ANDROID__` guard).

If a future scene *does* use a per-layer shader and renders wrong, the fix
is to extend the guard to only short-circuit when there are no
`m_shaderList` entries on that controller, instead of unconditional return on
`kTypeSceneLayer`.

## What this fix did NOT break that we worried about

- **HUD** — drawn on the main camera, not through a layer RT. Always worked.
- **Menus and pause overlays** — drawn through `TopMost`, not a scene layer.
  Note: V-menu freeze is a *separate* bug, see
  [06-open-bugs-and-next-steps.md](06-open-bugs-and-next-steps.md).
- **Audio / input / save** — pure C++, no GL touched.
- **Title / Loading scenes** — were already on direct-visit, this patch
  doesn't change their path.

## How to verify the fix on a fresh build

1. Apply the patch (source or binary).
2. Launch the game in an emulator with at least 2 GB RAM (MEMU works well;
   the Galaxy J3 Orbit is below the game's footprint so it's a poor test
   bench — see [04-memory-and-oom.md](04-memory-and-oom.md)).
3. Title → New Game → wait for Tutorial scene to load.
4. **Expected**: world tiles visible, player visible, HUD on top.
5. **Confirm in log**: `hell_runtime.log` should now show
   `layer N direct visit` lines for the tutorial layers (not
   `via RT shader`).

Once that's green, the rest of the work is the input/menu/save freezes,
which are not this bug.

## Lessons

- **Trust the dumper, not your priors.** I spent hours on the texture-size
  theory based on a single `vulkan version is 0` log line. The in-game
  dumper Coolkids built into v71 spelled the bug out in one minute.
- **Two render paths in a single engine, picked by a "use shader?" flag, is
  always a place where bugs hide.** Both paths existed and worked
  independently — but only one was being tested at `camera.position=0`.
- **Binary-patching a working `.so` beats rebuilding from a partially
  documented source tree.** Took 2 minutes vs ~6 hours. See
  [05-build-pipeline.md](05-build-pipeline.md) for the swap-into-existing-APK
  workflow.
