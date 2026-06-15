# FOBS arm64 Port — HANDOFF / SAVE POINT

> Goal: make **Forest of the Blue Skin** (port of *Hell After School*, package
> `com.sthdk.forestblueskin`, a PGMMV / cocos2d-x game) run on a **64-bit
> Android 16** device (Samsung Galaxy S26 Ultra, arm64-v8a) **with on-screen
> controls**. The original mod only shipped a 32-bit (armeabi-v7a) build that
> works on the owner's old phone (Galaxy J3 Orbit, Android 9, armv7). New
> flagship/Play devices are 64-bit-only and reject/!run the 32-bit build.
>
> This folder is a complete checkpoint so another engineer/AI can continue
> instantly. Read this whole file first.

---

## 0. TL;DR — current status (2026-06-15)

| Milestone | State |
|---|---|
| APK installs on 64-bit Android 16 | ✅ SOLVED (targetSdk policy fix) |
| arm64 engine `libMyGame.so` loads (no 16KB-page wall) | ✅ confirmed (`loadLibrary SUCCESS`) |
| `MenuShim` JNI bridge loads on arm64 | ✅ SOLVED (rebuilt `libmenushim.so` for arm64) |
| Game boots past bridge into engine | ✅ reaches `onResume` + GL surface 1440×720 |
| Game renders / stays up | ❌ **crashes deeper inside engine GL/scene startup** |
| On-screen MOVEMENT controls on arm64 | ❌ blocked — `TouchGamepad` class absent from arm64 engine (needs engine rebuild) |

**Current build:** `FOBS_universal_v4.apk` (see Release assets) — universal
(arm64-v8a + armeabi-v7a), targetSdk 30, contains the rebuilt arm64
`libmenushim.so` **with an embedded native crash handler**.

**Immediate next action (was in flight):** owner runs v4 on the S26, lets it
crash, and zips the app's diag folder. v4's crash handler writes
**`native_crash.txt`** there (alongside `boot.log`/`input.log`). That file's
`library+offset` lines map directly to a symbol in the arm64 `libMyGame.so`
→ tells us the real engine crash to fix. **We are waiting on that file.**

---

## 1. The two devices (DO NOT CONFLATE — owner gets upset)
- **Owner's own phone:** Samsung Galaxy J3 Orbit, Android 9, **32-bit armv7**,
  2GB RAM. The 32-bit build (`forestblueskin_swd_v2.apk`) WORKS here, controls
  and all.
- **Test device:** Samsung **Remote Test Lab** (tester.samsung.com) running a
  **Galaxy S26 Ultra, Android 16, 64-bit**. Free cloud flagship. Tell-tale:
  browser chrome with URL bar, HQ/LQ slider, and a **Logs** button.
  ⚠️ The RTL **Logs** panel **auto-scrolls**, so the owner **cannot copy the
  fatal logcat line**. This is why v4 self-captures the crash to a file.

---

## 2. What was wrong and how each was fixed

### 2a. "App not installed" on the S26 — POLICY BLOCK, not corruption
A clean, valid-signed arm64 APK still failed to install on Android 16 with
`INSTALL_FAILED_DEPRECATED_SDK_VERSION`: the manifest had
`targetSdkVersion=23`, too old for Android 16 to accept.
**Fix:** binary-patch the (compiled) `AndroidManifest.xml` AXML to bump
targetSdk **23 → 30**. We kept it at **30** deliberately:
- `targetSdk >= 31` would force every `<activity>` to declare
  `android:exported` (more edits, more risk).
- `targetSdk >= 29` triggers scoped storage (the app already handles ext
  storage with `maxSdkVersion=29` perms, so 30 is fine).
- **30 is the safe sweet spot.** `minSdkVersion` stays 23.

Scripts: `scripts/dump_axml.py` (inspect AXML), `scripts/patch_targetsdk.py`
(find attr resid `0x01010270`, patch its int value 23→30). Then `zipalign -p 4`
+ `apksigner sign` (v1+v2+v3).
LESSON: valid-signed APK failing install on a NEW device but passing
aapt/apksigner = suspect a policy block (targetSdk too low, or 31+ exported),
NOT file corruption.

### 2b. Launch crash "MenuShim init FAILED" — MISSING arm64 .so
After install, v1/v2 crashed instantly. Instrumentation showed
`loadLibrary(MyGame) SUCCESS` (arm64 engine loads fine, no 16KB page issue),
reached onResume, then **`MenuShim init FAILED`**. Cause: the Java class
`org.cocos2dx.cpp.MenuShim` does `System.loadLibrary("menushim")`, but
`lib/arm64-v8a/libmenushim.so` **didn't exist** (the porter only built it for
v7a) → `UnsatisfiedLinkError`.
**Fix:** rebuild `libmenushim.so` for arm64 from scratch (no source). See §3.

### 2c. v3 boots further, crashes deep in engine — IN PROGRESS
With the rebuilt arm64 `libmenushim.so`, v3 logged `MenuShim init OK`,
`gamepad overlay added`, `virtual game controller registered`, reached
`onResume`, sized GL surface `w=1440 h=720` — then crashed **inside the
engine's GL/scene startup** (a `libMyGame.so` crash, NOT the shim). No fatal
native line was capturable (RTL auto-scroll). → built v4 with a crash handler
(see §4) to capture it. **Awaiting the resulting `native_crash.txt`.**

---

## 3. The rebuilt arm64 `libmenushim.so` (src/menushim.cpp)

`libmenushim.so` is the porter's tiny custom JNI shim that bridges Java input
to the engine. The 32-bit original (`libs/libmenushim-armv7-original.so`,
~10.7KB) imports ONLY libc/liblog/libdl — it finds engine functions at runtime
via `dlopen("libMyGame.so", RTLD_NOLOAD) + dlsym`. So it is fully
self-contained and re-buildable for any ABI without its source.

**How the source was reconstructed (no original source existed):**
1. `strings` + `objdump -d -C` (NDK r17c) of the 32-bit `.so` revealed the
   mangled engine symbols it dlsyms and the log-format strings (which expose
   every argument).
2. **Exact JNI signatures** came from the app dex, not guesses:
   `dexdump -d classes.dex`, class `Lorg/cocos2dx/cpp/MenuShim;`, methods
   marked `NATIVE`:
   - `nativeInit ()I`
   - `nativeInjectKey (IZ)Z`
   - `nativePrecedeTriggered (IIII)Z`
   - `nativePrecedeReleased (IIII)Z`
   - `nativeSetCommonVariable (ID)I`
   - `nativeGetCommonVariable (I)D`
   - `nativeSetDiagPath (Ljava/lang/String;)V`
3. The shim dlsyms ~11 engine C++ symbols and **null-guards every call** so a
   missing one never crashes.

### ⚠️ KEY CONSTRAINT — TouchGamepad is NOT in the arm64 engine
The three `TouchGamepad::{getInstance,injectKeyPress,injectKeyRelease}` symbols
(`KeyCode = int`) are the porter's custom **on-screen movement-key injector**,
compiled ONLY into the 32-bit engine. They are **absent from the arm64
`libMyGame.so`** (verified: `readelf --dyn-syms libMyGame.so | grep TouchGamepad`
→ 0 hits). The standard `InputManager` / `GameManager` / `agtk::data` symbols
(menu/interact/precede-input/common-variables) ARE present.
**Consequence:** on arm64, `nativeInjectKey` (movement) is a guarded no-op; the
menu/interact/common-var paths resolve.
➡️ **Full movement controls on arm64 require rebuilding the ENGINE with the
porter's `TouchGamepad` class** (the bigger, eventual job — see §6).

### Build recipe (arm64 libmenushim.so)
NDK **r17c** standalone toolchain:
```
python3 $NDK/build/tools/make_standalone_toolchain.py --arch arm64 --api 21 \
        --install-dir ta64 --force
```
GOTCHA 1: r17c clang needs `libtinfo.so.5` (missing on modern hosts):
`ln -sf <libtinfo.so.6> shims_lib/libtinfo.so.5` and compile with
`LD_LIBRARY_PATH=shims_lib`.
Compile:
```
aarch64-linux-android-clang++ -fPIC -O2 -fvisibility=hidden -shared \
  -static-libstdc++ -Wl,-soname,libmenushim.so \
  -o libmenushim.so menushim.cpp -llog -ldl
```
GOTCHA 2: **use `-static-libstdc++`** or the linker adds a NEEDED
`libc++_shared.so` that isn't in the APK → load fails. Confirm with
`readelf -d`: NEEDED must be ONLY liblog/libdl/libm/libc (matches original).
The v4 build (with crash handler) links the unwinder statically too → still no
extra NEEDED libs; size ~123KB (vs ~11KB without the handler).

### Inserting into the APK
The app sets `android:extractNativeLibs=false`, so ALL `.so` are **Stored
(uncompressed)** and must be **page-aligned**. Add
`lib/arm64-v8a/libmenushim.so` as **STORED**, keep the v7a original, then
`zipalign -p 4` + `apksigner sign` (v1+v2+v3).

---

## 4. v4 embedded native crash handler (the current diagnostic lever)
Because the RTL Logs panel auto-scrolls, v4 bakes a SIGSEGV/SIGABRT/SIGBUS/
SIGILL/SIGFPE handler INTO `libmenushim.so` (loads early, before GL). On crash
it uses `_Unwind_Backtrace` + `dladdr` to resolve each PC to
`library+offset (symbol+off)`, writes them to **`<diagDir>/native_crash.txt`**
(same folder as the app's `boot.log`/`input.log`, so the owner can zip it) AND
logs each frame at `ANDROID_LOG_FATAL`, then restores `SIG_DFL` and re-raises
for a normal tombstone. Installed in `JNI_OnLoad` + `nativeInit` +
`nativeSetDiagPath` (crash path derived from the diag path the app passes).
Uses `sigaltstack` + `SA_ONSTACK` so stack-overflow SIGSEGV is still caught.

**How to use the output:** each line like `#03 pc 0000000abc12 libMyGame.so
(?+0x...)` → take the `libMyGame.so` offset and resolve it against the arm64
engine:
```
aarch64-linux-android-addr2line -e libMyGame.so -f -C 0xABC12
# or: readelf -W --dyn-syms libMyGame.so | sort by addr, find nearest <= offset
```
That gives the exact engine function crashing → fix from there.

GENERAL TECHNIQUE worth remembering: when you ship any custom early-loading
`.so` to a device whose logcat you can't read, embed this crash handler to
self-capture native backtraces to app-accessible storage.

---

## 5. Files in this checkpoint

```
mod64/
├── HANDOFF.md                  ← this file
├── build_recipe.md             ← fuller running build notes (skill reference copy)
├── src/menushim.cpp            ← reconstructed arm64 bridge source (with crash handler)
├── libs/
│   ├── libmenushim-arm64-v4.so       ← built arm64 bridge + crash handler (in v4 APK)
│   └── libmenushim-armv7-original.so ← porter's original 32-bit shim (reference)
├── scripts/
│   ├── patch_targetsdk.py      ← AXML targetSdk bump 23→30
│   └── dump_axml.py            ← dump compiled AndroidManifest AXML
├── signing/fobs.keystore       ← signing key (see signing note below)
└── logs/v3_crash/              ← v3 launch logs (showed MenuShim init OK, then engine crash)
```

**Large binaries are attached to the GitHub Release `arm64-savepoint`** (too
big for git): `FOBS_universal_v4.apk` (current build), the arm64
`libMyGame.so` engine (33MB, needed to resolve crash offsets),
`forestblueskin_swd_v2.apk` (working 32-bit reference), and
`universal_ts30_unsigned.apk` (the targetSdk-30 base used for repackaging).

**Signing:** keystore `signing/fobs.keystore`, alias **`fobs`**, store/key
password **`fobsmod`**, CN=FOBSMod. Re-sign every modified APK with this same
key so updates install over the existing app.

App facts: package `com.sthdk.forestblueskin`, versionCode 1, versionName 1.0,
minSdk 23, targetSdk 30 (patched), ABIs arm64-v8a + armeabi-v7a,
`extractNativeLibs=false`. arm64 `libMyGame.so` = 33,351,280 bytes.

---

## 6. Roadmap / next steps for whoever picks this up
1. **NOW:** get `native_crash.txt` from a v4 run → resolve the offset against
   `libMyGame.so` → identify and fix the engine GL/scene-startup crash.
   (Common suspects for a 32→64 port: an ABI/size assumption in the engine or
   PGMMV runtime data loading, a GL context/EGL config issue, or a resource
   path/asset read. The backtrace will disambiguate.)
2. **Then:** get a stable boot to the title/menu on arm64 with menu+interact
   inputs working (those engine paths already resolve in the shim).
3. **FULL controls milestone:** rebuild the arm64 **engine** `libMyGame.so`
   WITH the porter's `TouchGamepad` class so `nativeInjectKey` (movement) works.
   - Engine source lives in this repo (`hell-after-school-android`, private,
     PGMMV Player / cocos2d-x). FIRST verify whether the `TouchGamepad` source
     is present in the repo (grep `TouchGamepad`); the porter added it on top
     of stock PGMMV so it may need to be re-added.
   - This is a large NDK build, almost certainly via **GitHub Actions** (the
     App token CANNOT write `.github/workflows/`; the human owner must add the
     workflow file via the web once — a boot-test workflow YAML may already be
     staged in this repo for them to rename into place).

## 7. Build toolchain quick-ref (host)
- NDK r17c (arm + aarch64 GCC 4.9 binutils for objdump/readelf, llvm clang).
- Android build-tools r34: `aapt`, `apksigner`, `zipalign`, `dexdump`.
- JDK 17 (for apksigner).
- arm64 standalone toolchain `ta64` (api 21) via make_standalone_toolchain.py.
- `shims_lib/libtinfo.so.5` → symlink to host `libtinfo.so.6` (r17c clang fix).

---
*Checkpoint authored by Viktor AI. Last updated 2026-06-15. Resume from §0/§6.*
