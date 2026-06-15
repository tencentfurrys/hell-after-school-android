# 64-bit (arm64-v8a) PGMMV engine build — WORKING RECIPE (2026-06-13)

Goal: build a true arm64-v8a `libMyGame.so` (the PGMMV/cocos2d-x 3.17.1 engine) from
source, for FOBS 64-bit (and HAS). Milestone 1 (engine compiles+links) = DONE.
Verified output: `libs/arm64-v8a/libMyGame.so`, ELF64 / AArch64, ~33MB.

## Sources (all in /work/temp, do NOT persist across fresh workspaces)
- Engine port repo: `sonicsonica701-cloud/hell-after-school-android` (gh acct sonicsonica701-cloud).
  Cloned to `/work/temp/has-port` (branch `v72-rt-shader-fix`). Has Classes (patched) +
  cocos2d/cocos (patched) but STRIPPED: no cocos2d/external, no extensions/tools/etc.
- Upstream PGMMV `GGGweb-adm/PGMMV` cloned sparse to `/work/temp/pgmmv-up` — provides the
  missing `Player/cocos2d/external` (full source + committed prebuilt .a for armeabi-v7a AND
  arm64-v8a) plus sibling dirs (extensions, tools, cmake, build, etc.).
- (Optional) `cocos2d-x-3rd-party-libs-bin` tag v3-deps-153 zip — only needed if upstream
  external lacked prebuilts; it didn't (PGMMV committed them). 141MB.

## Toolchain setup (fresh each session)
- NDK r17c: `curl -L -o ndk-r17c.zip https://dl.google.com/android/repository/android-ndk-r17c-linux-x86_64.zip; unzip` -> `/work/temp/android-ndk-r17c`.
- **libtinfo fix:** NDK r17c clang needs `libtinfo.so.5` (only .6 present). 
  `mkdir -p /work/temp/libcompat; ln -sf /usr/lib/x86_64-linux-gnu/libtinfo.so.6 /work/temp/libcompat/libtinfo.so.5`
  then export `LD_LIBRARY_PATH=/work/temp/libcompat` for the build. (`file` util also missing
  -> harmless "file: command not found" warning from ndk-build line 148.)
- JDK17 already at `/work/temp/toolchain/jdk-17.0.13+11` (for later APK packaging).

## Assemble the buildable tree (one-time)
1. `cp -r pgmmv-up/Player/cocos2d/external has-port/Player/cocos2d/external`
2. Copy missing cocos2d sibling dirs from pgmmv-up into has-port (NOT cocos, NOT external):
   build, cmake, docs, extensions, licenses, tools + top files (CMakeLists.txt, download-deps.py, setup.py, etc.).

## Source patches needed for arm64 (NOT in the stripped repo; external came from upstream)
1. `Player/cocos2d/external/json/document.h` — add primitive-value rvalue-name AddMember
   overload (inside `#if RAPIDJSON_HAS_CXX11_RVALUE_REFS`, after the GenericValue&& overloads):
   ```cpp
   template <typename T>
   RAPIDJSON_DISABLEIF_RETURN((internal::OrExpr<internal::IsPointer<T>, internal::IsGenericValue<T> >), (GenericValue&))
   AddMember(GenericValue&& name, T value, Allocator& allocator) { return AddMember(name, value, allocator); }
   ```
   (Code calls `obj.AddMember(rapidjson::Value("k",alloc), intValue, alloc)` — rvalue name + primitive value; stock had no match.)
2. `Player/Classes/Lib/Scene.cpp` — 3x `return (int)p1 < (int)p2;` -> `(intptr_t)p1 < (intptr_t)p2;`
   (pointer->int truncation; 64-bit only. There may be more pointer->int casts elsewhere; fix as they surface.)
3. `Player/cocos2d/external/unzip/unzip.cpp` — add `#include "platform/CCPlatformConfig.h"`
   before `#include <stdio.h>`. (File didn't include it, so `CC_TARGET_PLATFORM`/`CC_PLATFORM_NX`
   were both undefined -> `0==0` true -> empty NX branch taken -> orphaned `else if` "expected expression". 28 NX guards.)

## Build command (milestone 1)
```bash
cd /work/temp/has-port/Player/proj.android-studio/app
LD_LIBRARY_PATH=/work/temp/libcompat \
NDK_MODULE_PATH=/work/temp/android-ndk-r17c/sources \
/work/temp/android-ndk-r17c/ndk-build NDK_DEBUG=0 APP_ABI=arm64-v8a -j4 V=0
```
- ~720 files, several minutes. Output -> `app/libs/arm64-v8a/libMyGame.so`.
- Application.mk already has `APP_ABI := armeabi-v7a arm64-v8a`, `APP_PLATFORM android-26`,
  `-DUSE_AGTK -DAGTK_RUNTIME -DAGTK_RELEASE -DUSE_RUNTIME`, c++_static.
- Backup saved: `/work/temp/libMyGame_arm64_m1.so`.

## STEP 2 (DONE) — FOBS data slots into the engine, no aapt2 rebuild needed
- KEY FACT: FOBS's OWN engine lib is ALSO named `libMyGame.so` (both swd_v2 and clean 1.00) — same
  name my engine builds. So my arm64 lib drops in with the exact same name; no JNI/lib-name mismatch.
- Engine loads game from `Resources/data/project.json` (AppDelegate addSearchPath("Resources") ->
  ProjectLoadingManager::load("data/project.json")). On Android the input/key MAPPING comes from
  project.json itself (`gm->getProjectData()->getInputMapping()`); the `playerResources/defaultSettings.json`
  path is NX-ONLY. FOBS needs NO extra settings file.
- ASSETS ARE PLAINTEXT: `FileUtilsRuntime::getContents()` only decrypts if `s_key` set; s_key is empty
  by default -> falls through to stock `FileUtilsAndroid::getContents` = plaintext, NO decryption.
  So use FOBS's DECRYPTED apk (`forestblueskin_swd_v2.apk`) assets. Match confirmed.
- `menushim` (32-bit gamepad overlay lib) load in `MenuShim.smali` is wrapped in try/catchall ->
  fails gracefully (logs "loadLibrary FAILED", returns) -> a missing 64-bit menushim does NOT crash boot.

## STEP 3 (DONE) — Package arm64 APK via ZIP-SURGERY (fast path, no aapt2/d8/javac!)
Because FOBS apk already has the right manifest/dex/resources/java that loads `libMyGame.so`, just
swap the lib in the existing apk. Script: `/work/temp/repack_arm64.py`:
1. Copy `forestblueskin_swd_v2.apk` entries preserving per-entry `compress_type`.
2. DROP `lib/armeabi-v7a/libMyGame.so` + `lib/armeabi-v7a/libmenushim.so`.
3. ADD `lib/arm64-v8a/libMyGame.so` STORED (my engine). -> arm64-only apk = Android installs 64-bit.
4. Sign (zipalign + v1/v2/v3) with uber-apk-signer:
   ```bash
   JH=/work/temp/toolchain/jdk-17.0.13+11
   $JH/bin/java -jar /work/temp/uber-apk-signer.jar --apks fobs_arm64_unsigned.apk \
     --ks /work/temp/fobs.keystore --ksAlias fobs --ksPass fobsmod --ksKeyPass fobsmod \
     --out signed_arm64 --allowResign --skipZipAlign
   ```
   - Keystore: `/work/temp/fobs.keystore`, alias `fobs`, pass `fobsmod`, CN=FOBSMod.
   - `--skipZipAlign` REQUIRED: uber's built-in zipalign binary fails in this sandbox ("could not align").
     OK because swd_v2 manifest doesn't set extractNativeLibs=false (legacy default = libs extracted
     at install -> strict alignment not required to run).
- Output v1: `/work/temp/FOBS_arm64_v1-test.apk` (~195 MiB, arm64 ELF64 lib, 1632 assets, zip OK).
- Delivered via gofile (links expire -> re-up). filebin rejects .apk -> upload as .apk.zip.

### ⚠️ v1 FAILED TO INSTALL — "App not installed" even on a REAL arm64-v8a device (Samsung Remote Test Lab, 2026-06-14)
NOT a 32/64 issue (it was a genuine arm64 device). aapt + apksigner both parse v1 fine (minSdk/targetSdk
23, native-code arm64-v8a, sig v1+v2+v3 valid), BUT Android's INSTALLER parser is STRICTER than aapt —
the hand-built zip-surgery archive + `--skipZipAlign` produced an archive the device rejected. FIX = rebuild
with REAL Android build-tools (uber's zipalign is broken in-sandbox; download build-tools instead):
```bash
# get build-tools (gives aapt, apksigner, zipalign):
curl -sL -o bt.zip https://dl.google.com/android/repository/build-tools_r34-linux.zip && unzip -q bt.zip -d btx
export JAVA_HOME=/work/temp/toolchain/jdk-17.0.13+11   # NOTE: java is under toolchain/, NOT /work/temp/jdk-*
export PATH=$JAVA_HOME/bin:/work/temp/btx/android-14:$PATH
zipalign -p 4 -f FOBS_arm64_v1-test.apk aligned.apk          # rewrites/normalizes zip + page-aligns .so
apksigner sign --ks fobs.keystore --ks-key-alias fobs --ks-pass pass:fobsmod --key-pass pass:fobsmod \
  --v1-signing-enabled true --v2-signing-enabled true --v3-signing-enabled true --out FOBS_arm64_v2.apk aligned.apk
zipalign -c -p 4 FOBS_arm64_v2.apk            # verify alignment preserved after signing
apksigner verify --min-sdk-version 23 FOBS_arm64_v2.apk   # verify v1+v2+v3
```
- Output **`/work/temp/FOBS_arm64_v2.apk`** (204,936,988 bytes, md5 dbc229d25b0467cf302e8ab5d16a4c2f).
  Delivered 2026-06-14 via Slack file + gofile. Always give size+md5 so user can confirm download isn't
  truncated (a partial download also shows "App not installed").
- TESTING: user has no 64-bit phone; he tests 64-bit builds in **Samsung Remote Test Lab** (real arm64
  Galaxy device, free). If v2 still fails, get the exact `INSTALL_FAILED_*` line from RTL's Logcat panel.
- LESSON: for ANY APK delivery, build/sign with real build-tools (zipalign -p 4 + apksigner), not hand zip
  + uber --skipZipAlign — the latter can install on some devices but be rejected by stricter installers.

### ⭐ UNIVERSAL (fat) APK — the pragmatic fix that installs on BOTH 32-bit and 64-bit (2026-06-14)
The arm64-ONLY apk can NEVER install on his 32-bit J3 phone ("App not installed" = INSTALL_FAILED_NO_MATCHING_ABIS,
not a bug). He kept trying to install arm64 builds on his own phone. Solution = ONE universal apk containing
both ABIs: starts from the WORKING 32-bit `forestblueskin_swd_v2.apk` (has lib/armeabi-v7a/libMyGame.so +
libmenushim.so + controls) and ADDS lib/arm64-v8a/libMyGame.so. On a 32-bit phone Android uses the v7a libs
(= full working game w/ controls); on a 64-bit device it uses arm64 (= WIP engine, no controls yet).
Build (`/work/temp/build_universal.py`): copy all swd_v2 entries (drop META-INF/*.SF/.RSA/.MF), add
lib/arm64-v8a/libMyGame.so STORED, then `zipalign -p 4` + `apksigner sign` (v1+v2+v3). Verify
`aapt dump badging` shows `native-code: 'arm64-v8a' 'armeabi-v7a'`.
Output **`/work/temp/FOBS_universal.apk`** (231,163,826 bytes, md5 640979522e05019c91f8201abd47cf6e).
NOTE: swd_v2 (32-bit) already installs on his phone AND most 64-bit devices (64-bit Android runs 32-bit apps),
so if his only goal is to PLAY, plain swd_v2 is enough — arm64 is only needed for 64-bit-ONLY devices.

### ⭐ REAL test device = Galaxy S26 Ultra (Android 16, 64-bit) in Samsung RTL — install blocked by OLD targetSdk (2026-06-14)
He tests in **Samsung Remote Test Lab** on a **Galaxy S26 Ultra** (real 64-bit flagship, very new Android).
BOTH the arm64-only AND the universal APK got "App not installed" there — even though the arm64 ABI matches.
That is NOT corruption/ABI (apksigner verifies, aapt parses): it's a **policy block** — the app's
`targetSdkVersion=23` is too old for the device's new Android (→ `INSTALL_FAILED_DEPRECATED_SDK_VERSION`).
FIX = raise targetSdkVersion. Did it WITHOUT apktool/recompile via a precise **binary AXML patch** of
AndroidManifest.xml (`/work/temp/patch_targetsdk.py`): parse chunks, find RESOURCE_MAP (0x0180) → map attr
name index to resource id; in each START_ELEMENT (0x0102) attribute (20 bytes: ns4,name4,raw4,typed{size2,res0,
dtype1,data4}; attrs start at chunkbody+8+attributeStart — note the +8), patch the 4-byte data of the attr whose
resid==0x01010270 (targetSdkVersion) from 23→30. Same byte length → no string-pool/offset changes → safe.
Then `zipalign -p 4` + `apksigner sign`. KEEP target ≤30: target **31+** (Android 12) requires explicit
`android:exported` on every component with an intent-filter or install fails MANIFEST_MALFORMED; target **29+**
enforces scoped storage (may affect game saves later — install first, fix saves later).
Output **`/work/temp/FOBS_universal_v2.apk`** (231,163,826 bytes, md5 c59519d30d76bef5d545acd494b6c533,
targetSdk 30, both ABIs). AXML attr-offset gotcha: attributes start at (start-of-attrExt = chunk+16) +
attributeStart, i.e. chunk+8 +8 +attributeStart — easy to be off by 8.
LESSON: when a clean, valid-signed APK install-fails on a NEW device but passes aapt/apksigner, suspect a
policy block (targetSdk too low, or 31+ exported, or signature scheme) — ask the user for the exact
`INSTALL_FAILED_*` line (RTL has a **Logs** panel) instead of guessing.

### ⭐ S26 BOOT TEST of FOBS_universal_v2 (targetSdk 30) — INSTALLS + engine LOADS, then crashes (2026-06-14)
He installed it on the S26 Ultra: it INSTALLED ✅ and his app instrumentation logs (boot.log/hell_runtime.log/
input.log) showed:
`onLoadNativeLibraries → System.loadLibrary(MyGame) → after loadLibrary: SUCCESS` → the **arm64 libMyGame.so
LOADS and runs** — so there is NO 16KB-page-size wall, NO fundamental 64-bit block. App reached onResume and
sized the GL surface (1440×720), THEN crashed. Smoking gun line: **`MenuShim init FAILED`**. libmenushim.so
(the porter's custom on-screen-controls bridge that provides nativeInjectCocos2dKey etc.) exists ONLY for
armeabi-v7a — there is NO arm64 build of it. Hypothesis: gamepad/controller code calls a native method the
missing arm64 libmenushim should provide → `UnsatisfiedLinkError` → crash just after onResume. (Awaiting his
red FATAL/UnsatisfiedLinkError logcat line to confirm.)
- The engine repo `hell-after-school-android` is the cocos2d-x/PGMMV **Player** (CMake/Android.mk under
  Player/cocos2d/...). It does **NOT contain menushim source** — menushim is a separate porter shim, source not
  in that repo. So an arm64 libmenushim can't be cross-compiled from there without finding its source.
- NEXT options to get FOBS booting on 64-bit: (a) find/obtain libmenushim source and build arm64 with NDK r17c,
  or (b) stub/skip the MenuShim + gamepad-overlay init path (apktool smali edit) so the engine boots first
  (controls disabled), then add controls later. Boot-first (b) is the faster proof the arm64 engine renders.

### ⭐⭐ REBUILT arm64 libmenushim.so from scratch (chose path a) — FOBS_universal_v3 (2026-06-14)
The crash was simply that `lib/arm64-v8a/libmenushim.so` DIDN'T EXIST, so Java `System.loadLibrary("menushim")`
in `org.cocos2dx.cpp.MenuShim.init()` threw UnsatisfiedLinkError → "MenuShim init FAILED". Fix = build an
arm64 libmenushim.so. Full method (see `references/menushim/menushim.cpp` for the reconstructed source):
1. The 32-bit `libmenushim.so` is tiny (10.7KB) and imports ONLY libc/liblog/libdl (NO static engine symbols) —
   it finds engine functions at runtime via `dlopen("libMyGame.so", RTLD_NOLOAD) + dlsym`. So it's fully
   self-contained and re-buildable for arm64. Recover its design from `strings` (the mangled C++ symbol names
   it dlsyms + the log-format strings reveal every arg) and `arm-linux-androideabi-objdump -d -C` (NDK r17c) of
   `ensureInit()`.
2. Get EXACT JNI signatures from the app dex, not guesses: `btx/android-14/dexdump -d classes.dex` then find
   class `Lorg/cocos2dx/cpp/MenuShim;` methods marked `NATIVE`. For FOBS they were:
   `nativeInit ()I`, `nativeInjectKey (IZ)Z`, `nativePrecedeTriggered/Released (IIII)Z`,
   `nativeSetCommonVariable (ID)I`, `nativeGetCommonVariable (I)D`, `nativeSetDiagPath (Ljava/lang/String;)V`.
3. The shim dlsyms 11 engine C++ symbols: TouchGamepad::getInstance/injectKeyPress/injectKeyRelease (KeyCode=int),
   InputManager::getInstance/setPrecedeInputTriggered/Released(int,int,EnumTriggerType,int)/setPrecedeInputJudgeData,
   GameManager::getInstance/getPlayData, agtk::data::PlayData::getCommonVariableData(int),
   PlayVariableData::setValue(double). Verify which exist in the arm64 engine with
   `aarch64-linux-android-readelf -W --dyn-syms arm64lib/libMyGame.so | grep <mangled>`. ⚠️ For FOBS the THREE
   **TouchGamepad** symbols are ABSENT from the arm64 engine (0 string hits) — that class is the porter's custom
   on-screen-controls injector, only compiled into the 32-bit engine. So `nativeInjectKey` (movement keys) is a
   guarded no-op on arm64; the InputManager/GameManager paths (menu/interact/common-vars) DO resolve. FULL
   movement controls on arm64 require rebuilding the engine WITH TouchGamepad (bigger job).
4. Write menushim.cpp: cache the dlsym'd pointers, NULL-GUARD every engine call (so missing TouchGamepad never
   crashes), return success from nativeInit if InputManager/GameManager resolved (don't hard-fail on TouchGamepad).
5. Build for arm64 with an NDK r17c standalone toolchain:
   `python3 $NDK/build/tools/make_standalone_toolchain.py --arch arm64 --api 21 --install-dir ta64 --force`.
   GOTCHA: r17c clang needs `libtinfo.so.5` (missing on modern hosts) → `ln -sf <libtinfo.so.6> shims_lib/
   libtinfo.so.5` and run with `LD_LIBRARY_PATH=shims_lib`. Compile:
   `aarch64-linux-android-clang++ -fPIC -O2 -fvisibility=hidden -shared -static-libstdc++
   -Wl,-soname,libmenushim.so -o libmenushim.so menushim.cpp -llog -ldl`. ⚠️ Use **-static-libstdc++** or it
   adds a NEEDED `libc++_shared.so` that isn't in the APK → load fails. Confirm NEEDED == liblog/libdl/libm/libc
   only (matches the original) via `readelf -d`.
6. Insert into the APK as `lib/arm64-v8a/libmenushim.so` STORED/uncompressed (the app sets
   `extractNativeLibs=false`; all .so are Stored). Keep v7a's original libmenushim.so. Then `zipalign -p 4`
   (page-aligns the stored .so) + `apksigner sign` (v1+v2+v3). Output **FOBS_universal_v3.apk** (231,180,284 B,
   md5 64a3714ff90443c8617899ff80f2c7d8). Delivered gofile.io/d/l0Z08V. Awaiting his boot result.
LESSON: "MenuShim init FAILED" on arm64 = missing arm64 .so, not bad code. A tiny dlsym-based JNI shim can be
fully reconstructed from strings+objdump+dexdump and rebuilt for the new ABI without its original source.

### v3 result + v4 EMBEDDED NATIVE CRASH HANDLER (2026-06-14)
v3 (with rebuilt arm64 libmenushim.so) booted FURTHER: app logs showed `MenuShim init OK`, `gamepad overlay
added`, `virtual game controller registered`, reached `onResume` and sized GL surface 1440x720 — then crashed
DEEPER inside the engine's GL/scene startup (a libMyGame.so crash, not the shim). Problem: can't read the fatal
logcat line (Samsung RTL "Logs" panel auto-scrolls). SOLUTION = bake a SIGSEGV/SIGABRT/SIGBUS/SIGILL/SIGFPE
handler INTO libmenushim.so (it loads early via System.loadLibrary before GL). On crash it uses
`_Unwind_Backtrace` + `dladdr` to resolve each PC to `library+offset (symbol+off)` and writes to
`<diagDir>/native_crash.txt` (same folder the app writes its boot.log/input.log to — user can zip it) AND logs
each frame at ANDROID_LOG_FATAL, then restores SIG_DFL and re-raises for a normal tombstone. Install in
JNI_OnLoad + nativeInit + nativeSetDiagPath (derive crash path from the diag path the app passes). Use
sigaltstack + SA_ONSTACK so stack-overflow SIGSEGV is still caught. Build needs no extra NEEDED libs (unwinder
links statically; size ~123KB vs 11KB). This bypasses the un-catchable-logcat problem on RTL/locked devices —
the `library+offset` in native_crash.txt maps directly back to a symbol in arm64 libMyGame.so
(`readelf --dyn-syms` + addr2line). FOBS_universal_v4.apk md5 c4b0fea11518978e769285de2f5890c4, gofile lnrN6R.
GENERAL TECHNIQUE: when you ship any custom early-loading .so to a device whose logcat you can't read, embed
this crash handler to self-capture native backtraces to app-accessible storage.

## REMAINING (TODO)
4. BOOT test. CI route (GitHub Actions android-emulator-runner on repo hell-after-school-android,
   release `boot-apk` holds the APK, workflow `boot-test`) is SET UP and triggers via creating a fresh
   published release — BUT 2026-06-13 first run the cloud emulator (api33/google_apis/x86_64) failed to
   boot (600s timeout, never installed FOBS) → no game log. CI emulator also has no real GPU = non-definitive
   for this heavy game. So the DEFINITIVE boot test is the user clean-installing FOBS_arm64_v1-test.apk on
   his Galaxy J3 and reporting what happens (menu / instant crash / black screen). Awaiting his phone report.
   Unknowns: HAS-port engine is WIP
   (postProcessPreloadTex particle crash null-guarded @build59; v72 fixed black-world RT-shader).
   FOBS content may hit its own issues. Iterate per crash location user reports.
5. Controls: reuse FOBS Java GamepadOverlay + confirmed mappings (X=attack/KEY_A, C=dash/Shift,
   V=Ctrl+Q menu, arrows, W/S/D, jump). NO menushim (closed/32-bit) — inject keys via the engine's
   own cocos2d keyboard path (CCEventListenerKeyboard) with a small JNI bridge built into the apk's
   dex (smali) or engine source. (FOBS dex already decompiled at /work/temp/v100_smali.)
