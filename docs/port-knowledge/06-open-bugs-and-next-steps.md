# Open bugs, current state, and next steps

State as of 2026-05-30 (after v72L diagnostic build shipped).

## ✅ Fixed and verified

| Bug | Fixed in | Evidence |
|---|---|---|
| Black world in Tutorial / scrolling scenes | v72b (RT-shader patch #1) | v72d+ logs show `layer N direct visit` instead of `via RT shader`, player visible on screen. |
| Tutorial crash on first frame (`Scene::setShader` → null `RenderTextureCtrl::addShader+0x1f`) | v72d (patch #3) | v72d boots into Tutorial without SIGSEGV. |
| Wall-collision crash (SIGSEGV 0x41600004 in `ObjectCollision::updateWall`) introduced by my own v72g `TouchGamepad::attachToScene` nop | v72h (reverted to `drawGamepad → setVisible(false)` instead) | v72h+ logs don't contain the collision backtrace anymore. |
| V-menu race-condition crash (`updateDirtyFlagForSceneGraph` SIGSEGV) | v72j (`queueEvent` wrap) | v72k+ MEMU logs no longer contain the dispatcher backtrace. **Note**: V-menu is still broken — see "open" section — but it's now a *different* bug. |

## ⚠️ Open — confirmed bugs

### 1. V-key menu does not open (and "freezes" input)

**Repro**: launch game → New Game → in Tutorial → press V (either
on-screen V button or physical V key on PC/emulator).

**Symptom**: menu doesn't appear, character + world stay drawn, no
input registers thereafter, no SIGSEGV.

**What we know from v72k–v72L logs**:
- GL render thread is alive throughout — `visitScene:` frame counter
  keeps ticking *across* the freeze window all the way until the user
  backgrounds the app. (Updated after first clean v72L log — see
  [`08-v72L-log-1-analysis.md`](08-v72L-log-1-analysis.md). The
  earlier "render thread stops within 1 frame after V" reading was
  based on v72k data and didn't survive v72L's wider coverage.)
- What is paused is the *update* path — scheduler / action manager /
  physics step — i.e. `Director::pause()` semantics. The visible
  result is character locked mid-animation while the renderer keeps
  drawing the same paused state.
- v72L's input/touch coverage is solid: 1470 INPUT TOUCH events, 0
  INPUT KEY events (touchscreen-only session), every `JAVA GP inject
  queued` matched by `JAVA GP inject fired` within ~20 ms.

**Updated hypothesis (post v72L log #1)**: V-menu open calls
`Director::pause()` (or AGTK equivalent — `GameScene::pauseGame` /
`Scene::pauseAll`) which suspends scheduler + action manager + physics
*without* suspending the GL surface visitor. Then the menu push either
(a) silently nulls before `Scene::onEnter`, (b) enters but renders
invisible because of a postprocess-RT issue, or (c) pushes a
zero-sized node tree. All three look identical to the player: paused
world, overlay still drawn, no menu, no input progress, no exception.
The prior "RT-shader leftover" theory was about the rendering side —
the actual freeze is on the *update* side.

**Next move**: build v72M with the instrumentation in
[`09-v72M-spec.md`](09-v72M-spec.md) (Director pause/resume trace,
scene push/pop trace, V-button overlay trace, `onTrimMemory` reword,
+ a bypass-prep shim). Behaviour-neutral, so shippable immediately.
One repro of the freeze with v72M will disambiguate (a) / (b) / (c)
and dictate the v72N fix.

### 2. Bed save freezes the game

Same shape as V-menu: input dies, render appears to stop.

**Hypothesis**: same root as #1. Save UI probably uses the menu/dialog
scene which triggers the same broken postprocess path.

**Next move**: piggyback on the v72L log session — after grabbing the
V-menu freeze log, do a *second* run, walk to bed, press X to save,
let it freeze, send a second log. Compare the two for divergence
points.

### 3. Load save on title freezes

Same shape. Almost certainly the same dialog-scene postprocess issue.
Worth verifying once #1 and #2 are root-caused.

### 4. Cutscene blackscreen on Tutorial-room exit

After completing tutorial, the cutscene that should play between
Tutorial → world map renders as black. World becomes interactive after
"skipping" the cutscene.

**Hypothesis**: cutscenes likely use a fade-via-postprocess-RT that's
in the family of paths patch #1 disabled. Possibly fixable by extending
the patch — or treatable cosmetically by ensuring inputs always advance
through the cutscene (which they already do).

**Priority**: low. Cutscene is content, not gameplay. Address after #1.

### 5. Game-Over "press any key to continue" not responding

**Hypothesis**: the Game-Over screen polls keyboard events via a path
that, when our `nativeInjectCocos2dKey` runs on the GL thread now, may
arrive in a state where the key handler isn't subscribed yet. Race
between scene transition and our queued event.

**Priority**: low until repro is cleaner. Bundle with the next diag log.

### 6. MuMu Player — `System.loadLibrary("MyGame")` hangs

Splash icon hangs forever; no native code runs.

**Status**: this is a MuMu translator issue, not our code — v72j has
the exact same `.so` as v72k and v71 loaded fine on MuMu earlier (per
v71 thread). Possibly fixable by:
- Letting it sit 5+ minutes on first launch (JIT translation lag).
- Reinstalling MuMu fresh.
- Using MEMU or LDPlayer instead.

**Priority**: low — the user has MEMU and physical hardware as
alternatives.

## 🔬 Diagnostic builds

- **v72L** (in user's hands): functionally same as v72j; adds full
  input-path logging (`INPUT TOUCH`, `INPUT KEY`, `FOCUS`,
  `LIFE onPause/onResume`, `JAVA GP touch/inject queued/fired`).
- **v72M** (next, fully spec'd in
  [`09-v72M-spec.md`](09-v72M-spec.md)): on top of v72L, adds
  `DIRECTOR pause/resume`, `DIRECTOR pushScene/popScene`,
  `SCENE onEnter/onExit`, `V_BTN tap`, rewords the misleading
  `CRITICAL OOM` line, and adds the bypass-prep shim. All behaviour-
  neutral. Ship the moment it builds.
- **v72N** (depends on what v72M's first repro shows):
  - if `V_BTN tap` never fires → `bringToFront()` on overlay,
  - if pause + push fire but `SCENE onEnter` doesn't → null-check
    the menu scene's init path,
  - if all three fire and the menu just renders invisible → extend
    the `isUseShader` guard or skip RT capture on the top-most layer.
- **v72M-bypass** (parallel alternative): re-implement V menu in
  Java overlay, invoke inventory + save + load via direct Lua/JS
  bindings, bypass the native menu scene entirely. Bigger lift
  (~half day) but isolates from the shader pipeline. Coolkids has
  explicitly approved this path as a parallel shot to the v72M fix.
  v72M's track-B prep makes this a one-function swap in
  `GamepadOverlay.java::onVButtonTap()`.

## 💸 Memory/asset downscale (deferred, not currently planned)

VmPeak at 1.75 GB is fine on every test target except the Galaxy J3
Orbit (1.5 GB physical). If we want the J3 Orbit as a first-class
target, work would be (in order):

1. `pngcrush -rem allb` every PNG to strip iCCP profiles (~10 MB win,
   zero risk).
2. `pngquant --quality=70-90 --strip` every PNG (~200 MB win, low risk
   — spot-check sprite positioning afterwards).
3. Drop unused asset preloads by parsing `assets/data/project.json` and
   conditionally skipping non-Tutorial scene assets at boot (~100 MB
   win, higher risk — could cause mid-scene hitches).

**Do not do this until** the V-menu / save / load family of bugs are
fixed. We don't want to chase a memory-shaped bug that's actually a
code bug. The MEMU emulator (3+ GB RAM) has enough headroom that all
freezes there are real code bugs, and that's the right test bench.

## Communication TODOs

- Coolkids is generally onto the v72L log capture now. The clearest
  instruction for them is: **"force-stop the game, delete
  `hell_runtime.log`, then launch fresh, repro the freeze, send the
  log"** — paraphrased as needed. The v72k log had no INPUT lines
  because the user wiped the log mid-session, which we should warn
  against again.
- The Slack thread is at `general` channel, thread_ts `1780031254.132759`
  and continuing in `1780104899.326779` (this knowledge-dump message).
- Coolkids tends to want both fixes (diagnostic + hot-wire bypass) in
  parallel. That's reasonable; v72L is shipped, v72M-bypass is what
  he's asking for next.

## Lessons accumulated through v72L

- **One change per binary patch.** Patch #2 (skip RT alloc) caused
  patch #3 (`Scene::setShader` null-cbz nop) to become necessary. If
  we had shipped only #1 and verified, then shipped #2, the cascading
  cause-effect would have been obvious in one log instead of two.
- **`onTrimMemory` in `hell_runtime.log` is not a crash indicator on
  its own.** It fires at level=80 every time the app is backgrounded.
  Always cross-check with `LIFE onPause` and the last `signal:` line.
- **Manifest knobs (`largeHeap`, `extractNativeLibs`) are not free.**
  They moved VmPeak in the wrong direction on this codebase. Default
  values are correct.
- **MEMU is currently our most reliable test target.** Galaxy J3 Orbit
  is below the memory budget and MuMu has the loadLibrary hang. MEMU
  works and has enough RAM that bugs there are real.
- **`hell_runtime.log` is the source of truth, not the logcat ring
  buffer.** The runtime log is persistent and complete; logcat scrolls
  off in ~64 KB. Always ask for `hell_runtime.log` first.
