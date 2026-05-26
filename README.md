# Hell After School — Android Port (Checkpoint)

PGMMV / Cocos2d-x 3.17.1 Windows-built game ported to Android (armeabi-v7a, Android 8.0+ / minSdk 26 target).
Based on the upstream open-source [PGMMV](https://github.com/GGGweb-adm/PGMMV) runtime + the game's original assets.

> **Status at this checkpoint:** APK builds and signs cleanly, native lib loads, JNI binds, the cocos2d-x engine boots, `AppDelegate::applicationDidFinishLaunching()` runs. Crash isolated to `ProjectLoadingManager::postProcessPreloadTex()` — null pointer during particle texture preload — null-guarded + logged in build 59.

## Build environment

- **NDK:** r17c
- **SDK build-tools:** 30.0.3, platform: android-30
- **JDK:** 17 (used for `aapt2`, `apksigner`, `d8`, `keytool`)
- **Target ABI:** `armeabi-v7a` (Samsung Galaxy J3 Orbit, 32-bit ARMv7, Android 8.0)
- **C++ runtime:** `c++_static` (NDK r17c)

## What was modified

### Engine / runtime patches
- `Player/cocos2d/cocos/audio/AudioEngine.{cpp,h}` — gated AGTK-specific 6-arg `play2d` behind `defined(USE_AGTK) && !defined(__ANDROID__)`; Android uses upstream 3-arg signature.
- `Player/cocos2d/cocos/platform/android/CCApplication-android.cpp` — added `getCurrentLanguageShortName()`.
- `Player/cocos2d/cocos/platform/android/CCFileUtils-android.cpp` & `FileUtils-runtime.cpp` — `USE_AGTK` stubs for `memFopen/memFclose/getApplicationPath/getDirContents`.
- Hundreds of small patches across the PGMMV codebase (Win32 wrapping, `Vec2`/`Color4F` qualified ctors, rapidjson AddMember template overload, `cpCollisionHandlerDoNothing` redefinition guard in `js_bindings_chipmunk_manual.cpp`, `stricmp→strcasecmp`, `__declspec`/`ARRAYSIZE` shims, etc.).
- ImGUI stubs (debug overlay disabled on Android).
- `cocos2d/external/giflib`: added `S_IREAD`/`S_IWRITE` compat shim.

### Game code patches
- `Player/Classes/Manager/ProjectLoadingManager.cpp::postProcessPreloadTex()` — early-return with null-guarded step-by-step logging on Android. Particle preload disabled to avoid the crash; particles still init lazily at scene load.
- `Player/Classes/Lib/Macros.h` — added stdlib pulls + GUID stub + `ARRAYSIZE` compat.
- `Player/Classes/External/SSPlayer/Loader/Common.cpp` — `UTF8toSjis` Android branch.

### Android-specific additions
- `Player/proj.android-studio/app/AndroidManifest.xml` — `com.sthdk.hellafterschool`, storage perms, `requestLegacyExternalStorage=true`.
- `Player/proj.android-studio/app/src/org/cocos2dx/cpp/AppActivity.java` — instrumented with try/catch around `onLoadNativeLibraries` and `onCreate`, writes `boot.log` / `crash.log` to `getExternalFilesDir(null)`.
- `Player/proj.android-studio/app/jni/CrashHandler/CrashHandler.cpp` — `sigaction` + `_Unwind_Backtrace` + `dladdr` crash dumper, installs at `.so` dlopen time via `__attribute__((constructor(101)))`. Writes to `/sdcard/Android/data/com.sthdk.hellafterschool/files/` (no permission required on Android 4.4+).
- `Player/proj.android-studio/app/jni/Android.mk` — 93 Player source files, `cc_static` + `ccjs_static` + `ext_spidermonkey` + `ext_websockets` modules.
- `Player/proj.android-studio/app/jni/Application.mk` — `APP_ABI armeabi-v7a arm64-v8a`, `APP_PLATFORM android-26`, `-DUSE_AGTK -DAGTK_RUNTIME -DAGTK_RELEASE -DUSE_RUNTIME`.
- `Player/proj.android-studio/app/jni/android-stubs/` — VLC + AGTK plugin stubs (vibration, shared-memory, audio pitch/pan, DllPluginManager).

## Build commands

```bash
# Native lib (libMyGame.so)
cd Player/proj.android-studio/app
$NDK_HOME/ndk-build NDK_DEBUG=0 APP_ABI=armeabi-v7a -j4

# APK packaging is done outside Gradle — see apk-build/ for the manual pipeline:
# aapt2 compile → aapt2 link → javac → d8 → python zipfile pack → zipalign → apksigner
```

## Known stubbed on Android (vs Win32 build)

- ImGUI debug overlay
- AGTK audio extensions (pitch/pan, loop-info)
- Shared-memory IPC
- Vibration
- `postProcessPreloadTex()` particle preload (build 59 — pending proper fix)
- Touch input (intentionally — keys will be remapped post-launch)

## Next steps

1. Verify build 59 boots past `applicationDidFinishLaunching`
2. Re-enable `postProcessPreloadTex` with proper Android `Image::initWithImageFileLateSetup` path
3. Wire on-screen touch gamepad (user has key mappings ready)
4. arm64-v8a + x86 ABIs

## Tags

`PGMMV` `Cocos2d-x` `Android` `JNI` `SpiderMonkey`
