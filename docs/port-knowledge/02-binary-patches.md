# Binary patches applied to `libMyGame.so`

All patches are against the **armeabi-v7a** `libMyGame.so` that ships inside
Coolkids' working `hell-after-school-v71.apk` (Hot Dog King's build).

- Source APK SHA-256: see Slack — was on the MediaFire link
  `https://www.mediafire.com/file/5o3fagmj2e28i19/hell-after-school-v71.apk`.
- The `.so` is ~29 MB stripped, thumb-mode ARMv7-A.

We patch at the byte level because the v71 binary contains undocumented
changes Hot Dog King made *outside* this GitHub repo (the most consequential
being the `GameManager::getAppName()` fallback strings — without them a
clean rebuild from this repo crashes on first frame inside
`JavascriptManager::addObject`). Patching the working binary is therefore
safer than rebuilding.

> **All offsets below are 4-byte hex offsets into `libMyGame.so` taken from
> the `.text` section, thumb mode.** They are recomputed each time we add a
> patch via the standard ARM EABI demangling of the function names below
> against the v71 symbol table. If you ship a new base APK, recompute.

## Cumulative patch list (v72b → v72L)

| # | Patch | Function | Origin / rationale | Bytes | Introduced in |
|---|---|---|---|---|---|
| 1 | RT-shader kill | `agtk::RenderTextureCtrl::isUseShader()` | Real fix for the black-world bug — see [01](01-world-not-rendering-fix.md). | 4 | v72b |
| 2 | Skip layer RT alloc | `agtk::SceneLayer::createRenderTexture()` | After patch #1 the per-layer RTs are never sampled. Skipping their allocation saves ~60 MB (12 layers × 1366×768 × 4 bytes RGBA + depth) of VmPeak headroom. | 2 | v72c |
| 3 | Scene::setShader null-cbz nop | `agtk::Scene::setShader(...)` at func+0x108 | Tutorial's first-frame `execActionSceneEffect` calls `Scene::setShader`. After patch #2 the controller is null. The original code has a `cbz r0, .create_new_shader` that would call `RenderTextureCtrl::addShader(null + 0x1f)` → SIGSEGV. Nopping the cbz makes the null case fall through into `SceneLayer::setShader`, which is null-safe. | 2 | v72d |
| 4 | TouchGamepad draw → setVisible(false) | `agtk::TouchGamepad::drawGamepad()` | Hide the persistent label nodes (`L`, `R`, `SE`, `ST`, `X`, `Y`, `A`, `B`) the old built-in pad added once in `attachToScene`. Letting init run and only neutering the draw avoids the v72g uninit-field collision crash. Tail-call to `setVisible(false)` on first frame hides the entire node tree thereafter. | 8 | v72i |
| 5 | TouchGamepad draw buttons nop | `agtk::TouchGamepad::drawButtons()` | Defensive — second draw entry point that could still re-show shapes. Replaced with `bx lr`. | 2 | v72h (retained) |
| 6 | TouchGamepad touch capture off | `agtk::TouchGamepad::onTouchBegan(Touch*, Event*)` | Return `false` so the old pad doesn't steal touches from our new Java overlay. | 4 | v72h |
| 7 | TouchGamepad touch moved nop | `agtk::TouchGamepad::onTouchMoved(Touch*, Event*)` | Defensive — `bx lr`. | 2 | v72h |
| 8 | TouchGamepad touch ended nop | `agtk::TouchGamepad::onTouchEnded(Touch*, Event*)` | Defensive — `bx lr`. | 2 | v72h |

## Reverted / dead patches (don't reapply)

| # | Patch | Why we reverted |
|---|---|---|
| R1 | `TouchGamepad::attachToScene` prologue NOPed (v72g only) | Prevented internal state init → ObjectCollision::updateWall read uninitialized field as a pointer → SIGSEGV at 0x41600004. Replaced in v72h by patches #4–#8 which let init run. **Do not reapply.** |
| R2 | `largeHeap="true"` + `extractNativeLibs="true"` in `AndroidManifest.xml` (v72i only) | Pushed VmPeak from 1.75 GB → 2.3 GB — made memory pressure *worse* on 1.5 GB devices. Reverted in v72j. |

## Active patches in detail

### Patch #1 — `RenderTextureCtrl::isUseShader` always returns false

- **Function**: `_ZN4agtk17RenderTextureCtrl12isUseShaderEv`
- **Original prologue** (typical):
  ```
  push  {r4, lr}        ; 10 b5
  mov   r4, r0          ; 04 46
  bl    getShaderList   ; ?? ??
  ```
- **Patched** (overwrite first 4 bytes of the function entry):
  ```
  movs  r0, #0          ; 00 20
  bx    lr              ; 70 47
  ```
- **Effect**: the function returns 0 (false) before doing anything. Both
  `SceneLayer::updateRenderer` and `GameManager::visitScene` then take the
  direct-visit branch for *every* controller, not just `kTypeSceneLayer`.
  This is broader than the source patch but equivalent in this game's data
  (no controller in HAS has shader-list entries that we've observed).
- **Cumulative byte cost**: 4 bytes.

### Patch #2 — `SceneLayer::createRenderTexture` is a no-op

- **Function**: `_ZN4agtk10SceneLayer19createRenderTextureEv`
- **Patched prologue** (2 bytes):
  ```
  bx    lr              ; 70 47
  ```
- **Effect**: the layer's `m_pRenderTextureCtrl` member stays `nullptr`.
  Safe because:
  - Patch #1 makes `isUseShader()` always-false → the controller is never
    referenced for sampling.
  - `removeRenderTexture` and `setBlendAdditive...Sprite` both null-check
    the pointer (`cbz r0, .skip` in their disassembly), so a null
    controller doesn't crash them.
  - `Scene::setShader` originally did *not* null-check it — that's what
    patch #3 fixes.
- **Memory saved**: ~60 MB per Tutorial-style scene (12 layers × 1366×768
  × (4-byte RGBA + 4-byte depth/stencil)).
- **Cumulative byte cost**: 2 bytes.

### Patch #3 — `Scene::setShader` null branch nop

- **Function**: `_ZN4agtk5Scene9setShaderE...` (overloaded — the one taking
  `(Shader::ShaderKind, float)` or similar; signature inferred from
  v72c crash backtrace: `Scene::setShader+0x153 → RenderTextureCtrl::addShader+0x1f`).
- **Target instruction**: `cbz r0, +next_branch` at function offset `+0x108`.
- **Patched**:
  ```
  nop                   ; 00 bf
  ```
  (2-byte thumb NOP, replacing the 2-byte `cbz`)
- **Effect**: the "controller is null → go create a new shader" branch is
  removed. Control falls through into the alternative path, which calls
  `SceneLayer::setShader` — that path *does* null-check the controller and
  is therefore safe.
- **Verified by**: v72c repro crashed at `RenderTextureCtrl::addShader+0x1f`
  with fault addr `0x0`; v72d with this patch boots into Tutorial cleanly.
- **Cumulative byte cost**: 2 bytes.

### Patch #4 — `TouchGamepad::drawGamepad` → `setVisible(false)` tail call

- **Function**: `_ZN4agtk12TouchGamepad12drawGamepadEv`
- **Patched prologue** (8 bytes, thumb):
  ```
  movs  r1, #0          ; 00 21
  bl    TouchGamepad::setVisible(bool)   ; ?? ?? ?? ??  (call within same .text)
  bx    lr              ; 70 47
  ```
  (The `bl` operand is a PC-relative offset to
  `_ZN4agtk12TouchGamepad10setVisibleEb`. Recompute on each base APK.)
- **Effect**: the first time the engine calls `drawGamepad` (which it does
  every frame), the entire `TouchGamepad` node tree is set invisible.
  cocos2d's visit pass honors `setVisible(false)` for the whole subtree, so
  the label nodes (`L`, `R`, etc.) added during `attachToScene` stop drawing
  immediately and stay hidden for the lifetime of the scene.
- **Why not just nop the func like in v72h?** Because the labels are
  persistent `cocos2d::Label` children, not per-frame draws. Nopping
  `drawGamepad` kills only the shape circles. `setVisible(false)` cascades.
- **Cumulative byte cost**: 8 bytes (was 2 bytes pre-v72i, increased).

### Patches #5–#8 — TouchGamepad draw/touch handlers neutered

All four are 2-byte `bx lr` (return) patches except `onTouchBegan` which is
4 bytes (zero `r0` + return):

| Function | Patched bytes | Reason |
|---|---|---|
| `_ZN4agtk12TouchGamepad11drawButtonsEv` | `70 47` | Belt-and-braces — no buttons drawn even if engine bypasses `drawGamepad`. |
| `_ZN4agtk12TouchGamepad12onTouchBeganEPN7cocos2d5TouchEPNS1_5EventE` | `00 20 70 47` | Returns `false` so the old pad's touch listener doesn't capture taps meant for our Java overlay. |
| `_ZN4agtk12TouchGamepad12onTouchMovedEPN7cocos2d5TouchEPNS1_5EventE` | `70 47` | No-op. |
| `_ZN4agtk12TouchGamepad12onTouchEndedEPN7cocos2d5TouchEPNS1_5EventE` | `70 47` | No-op. |

Cumulative byte cost: 10 bytes.

## Total patched footprint

**26 bytes** modified in `libMyGame.so` (armeabi-v7a) across 8 functions.
Everything else byte-identical to v71. PC, Mac, iOS builds untouched.

## How to apply

A reproducible patch can be expressed as a Python script that takes
`libMyGame.so` (input) and writes a patched copy. The required pieces are:

1. Locate the dynamic symbol table (`.dynsym`) and find each mangled name in
   the table above. Each entry's `st_value` is the function's offset from
   the file base (subtract any base load address — typically 0 for stripped
   `.so` since they're position-independent).
2. For each function, mask the low bit of `st_value` (thumb flag) and write
   the patched bytes at that offset.
3. For patch #4, compute the BL operand: it's the 24-bit thumb-BL encoding
   `(target_offset - source_offset - 4) >> 1`, split across two
   half-words.

`pyelftools` makes step 1 trivial:

```python
from elftools.elf.elffile import ELFFile

def find_symbol(elf_path, name):
    with open(elf_path, "rb") as f:
        elf = ELFFile(f)
        for sec in elf.iter_sections():
            if sec.name == ".dynsym":
                for sym in sec.iter_symbols():
                    if sym.name == name:
                        return sym["st_value"] & ~1  # strip thumb flag
    return None
```

A complete reference implementation lives in
`apk-build/patch_libmygame.py` (TODO: commit alongside this doc — for now
this section *is* the spec).

## How to ship after patching

See [05-build-pipeline.md](05-build-pipeline.md) — the swap-into-v71-APK +
zipalign + apksigner v1+v2+v3 workflow takes ~2 minutes per build.
