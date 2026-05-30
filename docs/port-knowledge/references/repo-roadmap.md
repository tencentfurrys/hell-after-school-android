# Repo roadmap — porting v72L knowledge back to source

The v71→v72L work happened almost entirely as binary patches and a
new Java overlay. To make this repo (`sonicsonica701-cloud/hell-after-school-android`)
the single source of truth, the following pieces need to land in
proper code.

## Already in repo

- ✅ `Player/Classes/Lib/RenderTexture.cpp` — RT-shader-kill fix (branch
  `v72-rt-shader-fix`, commit `eb043b2`).
- ✅ `Player/...` — cocos2d-x 3.17.1 + PGMMV runtime source tree from
  Hot Dog King's build 59 checkpoint.
- ✅ `docs/port-knowledge/` — this knowledge base.
- ✅ `apk-build/patch_libmygame.py` — reference binary patcher.

## Needs to be added (priority order)

### 1. Hot Dog King's missing source patches

Without these the source build (Path A in
[05-build-pipeline.md](../05-build-pipeline.md)) crashes on first
frame inside `JavascriptManager::addObject`. Specifically:

- `GameManager::getAppName()` and friends need Android fallbacks
  returning `"HellAfterSchool"` / `"1.0"` instead of null. The exact
  patch lives only in v71's binary. Best path: disassemble v71's
  `getAppName`, transcribe the fallback strings + branch into the
  source's `GameManager.cpp`, commit.

### 2. The other binary patches as source patches

For each patch in [02-binary-patches.md](../02-binary-patches.md):

| # | Source target | Edit |
|---|---|---|
| 1 | `RenderTexture.cpp::isUseShader` | ✅ already on `v72-rt-shader-fix`. Merge to main. |
| 2 | `SceneLayer.cpp::createRenderTexture` | Wrap body in `#ifdef __ANDROID__ return; #endif`. |
| 3 | `Scene.cpp::setShader(...)` | Add explicit null-check on the controller before `addShader` call. |
| 4–8 | `TouchGamepad.cpp` | Either guard the whole class with `#ifdef HELL_AFTER_SCHOOL_USE_JAVA_OVERLAY` or stub out `drawGamepad/drawButtons/onTouch*` on Android. |

### 3. Java overlay

Add to `Player/proj.android-studio/app/src/`:

- `org/cocos2dx/cpp/AppActivity.java` — replace with our version that
  adds the overlay to the FrameLayout and provides the
  `Cocos2dxGLSurfaceView.queueEvent`-wrapped `injectKey`.
- `com/cooolkidds/hellafterschool/GamepadOverlay.java` — full overlay
  class.
- `res/drawable-xxhdpi/pad_*.png` — button bitmaps.

Currently these only live inside the shipped v72X APKs. Need to pull
them out and commit.

### 4. arm64-v8a fixes

Three `(int)p1` casts in `Player/Classes/.../Scene.cpp` need
`(intptr_t)` to compile clean on arm64. Easy commit, would let us
ship a 64-bit APK that bypasses the 3 GB VM ceiling.

### 5. rapidjson upgrade

`Player/cocos2d/external/rapidjson` is too old. Replace with rapidjson
1.1.0+ (or pull from PGMMV's own SDK). See
[05-build-pipeline.md](../05-build-pipeline.md) for the symptom.

## Suggested branch strategy

- `main` — Hot Dog King's build 59 checkpoint (current).
- `v72-rt-shader-fix` — single-patch fix (current, ready to merge).
- `v72-full-source` — main + all patches above + Java overlay,
  reproducing v72L from a clean build. This is the target everyone
  should be aiming at — it would make the GitHub repo deployable as
  is, and we could retire the binary-patch workflow.
- `docs/port-knowledge-backup` — this branch (the documentation).

## Where to put assets

Shipping the Hell After School `assets/` (140 MB of PGMMV data) in
GitHub is awkward but possible:

- Option A: Git LFS. Set `assets/*.png assets/data/* filter=lfs` in
  `.gitattributes`. Public LFS bandwidth is paid.
- Option B: Keep `assets/` out of GitHub, document the v71-APK
  extraction step in build instructions:
  ```sh
  unzip hell-after-school-v71.apk assets/* -d Player/Resources/
  ```
- Option C (recommended): keep `assets/` out of GitHub. The CI/release
  job pulls them from a private S3 bucket on build. PGMMV `assets/`
  are content — they don't belong in source control for the same reason
  game art usually doesn't.

## CI / release ideas

- A GitHub Action that runs Path B (binary-patch v71 + new dex/manifest +
  resign) on every push to a release branch. Output: a `.apk` artifact.
  Would let us ship v72M, v72N etc. without a human running ndk-build.
- A separate Action for Path A (full ndk-build) that runs nightly,
  exercises the source tree, and surfaces regressions before they
  affect the binary-patch workflow.

## Owner / contact

Coolkids (`U0B6HBM5A78` in Slack) is the project owner. All design
decisions (overlay layout, keymap, fix priorities) flow through them.
