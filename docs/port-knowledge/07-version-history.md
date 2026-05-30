# Version history

Chronological log of every Hell After School Android build, what it
contained, and what we learned from it. Times are approximate Slack
timestamps.

## v71 — Hot Dog King's baseline

Source: `hell-after-school-v71.apk` (MediaFire link from Coolkids,
2026-05-28).

What works:
- Boots, audio, title screen, loading screen.
- Direct-visit render path on non-scrolling scenes (Title, Loading).
- v71's `libMyGame.so` includes undocumented fallbacks for
  `GameManager::getAppName()` and similar that are NOT in this GitHub
  repo's source — meaning a clean rebuild without porting those
  fixes will crash on first frame.

What's broken:
- Black world in every scrolling scene (Tutorial, school, world map).
- Built-in on-screen pad has only L/R/SE/ST/X/Y/A/B — no Shift, Ctrl,
  or Space, so reload/DNA/dash are unreachable.

This is our "compile target" for all binary patches.

## v72 (`v72-rt-shader-fix` branch on this repo) — source-level fix

Commit `eb043b2`. Patches `Player/Classes/Lib/RenderTexture.cpp` to
short-circuit `RenderTextureCtrl::isUseShader()` for `kTypeSceneLayer`
on Android. Not shipped as APK because the v72 fresh build hit
runtime crashes from Hot Dog King's missing patches.

## v72b — first usable APK

Approach pivoted: instead of rebuilding from source, **binary-patched
v71's `libMyGame.so`** (4-byte poke at
`agtk::RenderTextureCtrl::isUseShader` → always return false).

Status: title and loading worked. Crashed on Tutorial load before world
appeared.

SHA-256: `acd96b9436c14d197a885b37aa5e4c13e0a9256c9995553f35b2e504c2aef1b1`

## v72c — adds SceneLayer RT skip

Added binary patch #2 (`SceneLayer::createRenderTexture` → no-op) to
save ~60 MB on Tutorial scene.

Crashed mid-Tutorial-init in `RenderTextureCtrl::addShader+0x1f`
(SIGSEGV @ null) — turns out `Scene::setShader` was unconditionally
calling `addShader` on a now-null controller.

SHA-256: `d2037b4e00278184d2648b96c5d1fe15af3008d3849e8b20225bada6672d733c`

## v72d — `Scene::setShader` null-cbz nop

Added binary patch #3 (nop the `cbz r0` at `Scene::setShader+0x108`)
so the null-controller case routes through `SceneLayer::setShader`'s
null-safe path.

**🎉 World finally rendered.** Coolkids confirmed Tutorial loads with
visible world, character moves, HUD draws.

SHA-256: `0aa3141499ad03b24b48135572fc16d38728da557893aa6754080eaa7f0d9eb0`

## v72e — first Java gamepad overlay

Replaced built-in `TouchGamepad` with Xbox-style Java overlay (see
[03](03-gamepad-overlay.md)). Initial layout had RELOAD on the right
shoulder + AIM drag zone.

## v72f — RELOAD/DNA combos + aim-drag zone

Per Coolkids' feedback:
- Removed AIM button.
- Added RELOAD = Shift+X combo.
- Added DNA = Ctrl+X combo.
- Right side of screen = aim-drag zone (hold = aim, drag = aim
  up/down, tap = shoot).

SHA-256: `051c056f5564fd1984506338aa5f4baa7a327d6e2e3dc4b5c5047d6e6d2a20a0`

## v72g — drop old pad + spaced buttons + dedicated SHOOT buttons

Per Coolkids' annotated screenshot:
- 🔴 NOPed `TouchGamepad::attachToScene` to kill the old pad. (BAD MOVE.)
- 🟠 Spaced D-pad + face buttons from 1.05r → 1.55r.
- 🟡 Removed aim-drag zone. Added SHOOT ↑ (Shift+Up+Z) and SHOOT ↓
  (Shift+Down+Z) buttons.

SHA-256: `bb4cf3b805d3a2781bd8c7b702aca154c2e8f9d503973992f5b709b70e2f1400`

**Crashed in `ObjectCollision::updateWall`** at fault addr 0x41600004
— turns out nopping `attachToScene` left the singleton's internal state
uninitialized, and another agtk subsystem deref'd a 14.0f float as a
pointer.

## v72h — safer "kill the old pad" approach

Reverted `attachToScene` to original. Instead neutered:
- `drawGamepad` → `bx lr`
- `drawButtons` → `bx lr`
- `onTouchBegan` → return false
- `onTouchMoved` → `bx lr`
- `onTouchEnded` → `bx lr`

SHA-256: `0f0c66b4948f7d1ec6c43e5491701d44b385b6e083ce0392d997997963f5e90c`

Wall-collision crash gone. But old labels (`L`/`R`/etc.) still drew
because they're persistent `cocos2d::Label` children added once in
`attachToScene`, not per-frame draws.

## v72i — `drawGamepad → setVisible(false)` + manifest experiments

- Replaced `drawGamepad` nop with tail-call to `setVisible(false)` so
  the entire TouchGamepad node tree gets hidden on first frame. **Fixed
  the ghost labels.**
- 🔴 Added `largeHeap="true"` + `extractNativeLibs="true"` to the
  manifest hoping to help memory. **Made it worse** — VmPeak went
  1.75 GB → 2.3 GB. Reverted in v72j.

SHA-256: `91c9ba7ccfd4a69e28442fdb2588b97c51c61b0a025a63d08518bb942538f725`

Symptoms: V-menu freeze, save freeze, load freeze — all looking like
the same family of bugs. Native crashes during gameplay (`Bullet::init`
heap corruption, `EventDispatcher` SIGSEGV) — those latter ones turned
out to be the thread-safety race fixed in v72j.

## v72j — GL-thread-safe key inject + manifest revert

The big realization: my `nativeInjectCocos2dKey` was being called from
the Android UI thread, racing the GL thread's listener walk in
`EventDispatcher::dispatchEvent`. Fixed by wrapping every call in
`Cocos2dxGLSurfaceView.queueEvent(Runnable)`. See
[03-gamepad-overlay.md](03-gamepad-overlay.md) for code.

Also reverted `largeHeap` + `extractNativeLibs`.

SHA-256: `f47a5b2f820c615428c14b2ce524e0ea0606fe414ff1a8c6838f3ce5f7f92913`

Result: `updateDirtyFlagForSceneGraph` SIGSEGV gone for good. V-menu
freeze persisted, confirming it's a *separate* bug from the race.

## v72k — diagnostic build (overlay-only logging)

Added `JAVA GP touch DOWN`, `JAVA GP inject queued`, `JAVA GP inject
fired` lines. Did not yet catch physical-keyboard V presses.

SHA-256: `3d62440ace2a036ca031af9b77338d5839d73fc5ac625b0333f48ae69144ba7e`

User reported the same V-menu freeze. Log analysis:
- Render thread alive through Tutorial → 110 sec gameplay → V pressed →
  render thread silent.
- Zero `JAVA GP touch` lines, suggesting V was pressed via PC keyboard
  not the on-screen button.
- VmPeak 1.96 GB but RSS only 720 MB — no OOM imminent.
- "OOM kill imminent" log lines were misleading — level=80 just means
  app was backgrounded.

## v72L — diagnostic build (full input + lifecycle logging)

Adds:
- `INPUT KEY act=... code=...` for every hardware key (catches physical
  V on PC keyboard or phone hardware keys)
- `INPUT TOUCH act=... x=... y=...` for every touch
- `FOCUS hasFocus=...` for window focus
- `LIFE onPause` / `LIFE onResume`

SHA-256: `19e6ff37d305aabb2dd92851477cd3baca327f4fa1098acf859cf477bbecf4e8`

User's first v72L log was incomplete (he wiped the log file before
recording, so only the tail of the session was captured). Confirmed:
- v72L is installed (`LIFE onPause` + `FOCUS` lines appeared)
- Freeze IS the GL thread stalling, not memory (VmPeak steady at 1.75 GB,
  RSS ~720 MB)
- `onTrimMemory level=80` only fires *after* the freeze when the user
  backgrounds the app

Awaiting a clean v72L log (force-stop → delete `hell_runtime.log` →
fresh launch → repro → send).

## v72M — TBD (not yet built)

Two candidate scopes; user has approved doing both in parallel:

- **v72M (fix)**: target the actual broken function in the V-menu
  transition. Will be designed once v72L log identifies it. Expected:
  small null-check patches around the menu/save/load family of
  postprocess calls.
- **v72M-bypass**: re-implement V menu + inventory entry in the Java
  overlay, calling save/load via direct Java→native bindings, bypassing
  the broken native menu scene. ~half day of work.

## Summary table

| Build | Date | RT-shader fix | Layer-RT skip | setShader nop | Old-pad hidden | Java overlay | queueEvent | Diag logging |
|---|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| v71 | Hot Dog King | ❌ | ❌ | ❌ | n/a | ❌ | ❌ | ❌ |
| v72b | 05-28 | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| v72c | 05-28 | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| v72d | 05-28 | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| v72e | 05-28 | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| v72f | 05-28 | ✅ | ✅ | ✅ | ❌ | ✅ aim-drag | ❌ | ❌ |
| v72g | 05-28 | ✅ | ✅ | ✅ | ❌ broke | ✅ SHOOT | ❌ | ❌ |
| v72h | 05-29 | ✅ | ✅ | ✅ | partial | ✅ | ❌ | ❌ |
| v72i | 05-29 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| v72j | 05-29 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| v72k | 05-29 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | partial |
| v72L | 05-30 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
