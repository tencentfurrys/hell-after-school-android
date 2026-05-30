# Hell After School — Android Port Knowledge Base

This folder is a persistent, source-controlled brain dump of everything we
(Viktor + Coolkids) learned while porting **Hell After School** (PGMMV /
cocos2d-x 3.17.1 build) to Android. It is the answer to "if I lose Slack
tomorrow, what would I need to keep working on this port?"

Contents:

| File | What it covers |
|---|---|
| [`01-world-not-rendering-fix.md`](01-world-not-rendering-fix.md) | **THE bug**: black world in Tutorial / any scrolling scene. Root cause, why my first theory was wrong, the real `RenderTextureCtrl::isUseShader` patch, the source-level diff, the binary equivalent, and the test that proves it works. |
| [`02-binary-patches.md`](02-binary-patches.md) | Every byte-level patch applied to `libMyGame.so` from v72b through v72L. Function name, offset, original bytes, new bytes, rationale, side-effects. Cumulative table at the bottom. |
| [`03-gamepad-overlay.md`](03-gamepad-overlay.md) | The Java/Dex `GamepadOverlay` we built from scratch. Button layout, keymap (from `Tutorial_Keybind.txt`), multi-touch model, combo presses (RELOAD = Shift+X, DNA = Ctrl+X, SHOOT↑/↓), and the GL-thread-safety wrap (`queueEvent`) that killed the v-menu race-condition crash. |
| [`04-memory-and-oom.md`](04-memory-and-oom.md) | VmPeak ≈ 1.75 GB on 32-bit, the Galaxy J3 Orbit's 1.5 GB RAM ceiling, what `onTrimMemory level=80` actually means, why `largeHeap=true` + `extractNativeLibs=true` made things worse, and the asset-downscale roadmap if we ever need it. |
| [`05-build-pipeline.md`](05-build-pipeline.md) | NDK r17c + build-tools 30.0.3 + JDK 17 toolchain. `ndk-build` knobs. rapidjson / cocos2d-x v3-deps-153 / PGMMV extension gotchas. The "swap `.so` into an existing APK and resign" shortcut that's saved hours. |
| [`06-open-bugs-and-next-steps.md`](06-open-bugs-and-next-steps.md) | Current known issues (V-menu still freezes, bed save freezes, load freezes, cutscene blackscreen, gameover key, MuMu's `loadLibrary` hang). What we *think* each one is. What log to grab next. Candidate fixes ranked by risk. |
| [`07-version-history.md`](07-version-history.md) | What changed in every release: v71 → v72 → v72b → v72c → v72d → v72e → v72f → v72g → v72h → v72i → v72j → v72k → v72L. SHA-256, download links, install gotchas, what to test. |
| [`08-v72L-log-1-analysis.md`](08-v72L-log-1-analysis.md) | First v72L capture from Coolkids analysed. Updates the V-menu hypothesis: render thread doesn't stop after V — *update* thread does. Render-alive + update-paused. |
| [`09-v72M-spec.md`](09-v72M-spec.md) | The v72M build spec: Director pause/resume trace, scene push/pop trace, V button overlay trace, `onTrimMemory` line reword, and a bypass-prep shim. All behaviour-neutral — shippable to Coolkids immediately. |
| [`references/`](references/) | Raw artifacts: the v72 RenderTexture source diff, the patched dumper output excerpt that broke the bug open, key MEMU/Galaxy log signatures, the in-game key map. |

## TL;DR for someone picking this up cold

1. The original Hot Dog King port of HAS to Android shipped with a **black world** in every scrolling scene. The bug is *not* texture-size — every scene-layer render target is created cleanly at 1366×768. The bug is that on Android the `RenderTextureCtrl::update(...)` per-layer RT capture path produces an empty RT for any scene whose camera position is not `(0,0)`.

2. The **fix** is to make `RenderTextureCtrl::isUseShader()` return `false` on Android when the controller belongs to a `kTypeSceneLayer`. That short-circuits both `SceneLayer::updateRenderer` and `GameManager::visitScene` into the *direct-visit* render path that Loading and Title already prove works. See [`01-world-not-rendering-fix.md`](01-world-not-rendering-fix.md).

3. The fix exists in **two equivalent forms** in this repo:
   - **Source patch** (`Player/Classes/Lib/RenderTexture.cpp`, branch `v72-rt-shader-fix`) — for clean rebuilds.
   - **Binary patch** (4 bytes inside `libMyGame.so::agtk::RenderTextureCtrl::isUseShader`) — for swap-into-existing-APK shipping.

4. There's an entire follow-up tail of binary patches on top: kill `SceneLayer::createRenderTexture` to save the 60 MB of unused layer RTs, nop the `Scene::setShader` cbz so shader=null routes through the null-safe path, hide the legacy `TouchGamepad`, wrap every key inject in `queueEvent` for GL-thread safety. See [`02-binary-patches.md`](02-binary-patches.md).

5. The remaining bugs (V-menu freeze, bed save freeze, load freeze, cutscene blackscreen) all almost certainly share a root cause: code that **expected** the per-scene-layer RT pipeline to exist and is now hitting null/empty paths. The next move is the v72L diag log followed by a targeted patch. See [`06-open-bugs-and-next-steps.md`](06-open-bugs-and-next-steps.md).

## Conventions used in this doc

- All offsets are armeabi-v7a thumb-mode, computed from the `libMyGame.so` shipped inside v71's APK (the one Coolkids uploaded to MediaFire on 2026‑05‑28). SHA-256 of that `.so` is recorded at the top of `02-binary-patches.md`.
- "v71" = the working Hot Dog King build (`hell-after-school-v71.apk`) — boots, has the black-world bug.
- "v72*" = our patched builds.
- Source paths use the layout of this repo: `Player/Classes/...`, `Player/proj.android-studio/...`, `apk-build/...`.

Last updated: 2026-05-30 (after v72L diag build + first log analysis + v72M spec).
