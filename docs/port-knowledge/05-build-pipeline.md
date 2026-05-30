# Build pipeline

## Toolchain

Pinned exact versions known to produce a working `libMyGame.so`:

| Tool | Version | Notes |
|---|---|---|
| NDK | r17c | PGMMV / cocos2d-x 3.17.1 was authored against this. r18+ breaks several STL guarantees the engine relies on. |
| Android build-tools | 30.0.3 | For `aapt2`, `d8`, `zipalign`, `apksigner`. Newer is fine but 30.0.3 is what we've actually shipped with. |
| Android SDK platform | 30 | `compileSdkVersion 30`. |
| JDK | 17 | OpenJDK 17 LTS works; 21 is fine too. 8 will fail because `d8` requires `--release 8` target output but ≥ 11 to run. |
| `libtinfo.so.5` | required by ndk-build's bundled binaries | On modern Linux (Ubuntu 22.04+) you have to install `libtinfo5` from a backports PPA or symlink `libtinfo.so.6 → .5`. Hit this exact issue during v72 first compile. |

Install once:

```sh
# NDK r17c
wget https://dl.google.com/android/repository/android-ndk-r17c-linux-x86_64.zip
unzip android-ndk-r17c-linux-x86_64.zip -d /opt/
export NDK_HOME=/opt/android-ndk-r17c
export PATH="$NDK_HOME:$PATH"

# SDK / build-tools
sdkmanager "platform-tools" "platforms;android-30" "build-tools;30.0.3"
export ANDROID_HOME=$HOME/Android/Sdk
export PATH="$ANDROID_HOME/build-tools/30.0.3:$ANDROID_HOME/platform-tools:$PATH"

# libtinfo5 fix (Ubuntu 22.04+)
sudo apt install libtinfo5 || \
  sudo ln -s /usr/lib/x86_64-linux-gnu/libtinfo.so.6 \
             /usr/lib/x86_64-linux-gnu/libtinfo.so.5
```

## External deps the repo doesn't include

Cocos2d-x 3.17.1 needs its "external" submodule and its "extensions" pack:

```sh
git clone https://github.com/cocos2d/cocos2d-x-3rd-party-libs-bin.git \
  Player/cocos2d/external -b v3-deps-153 --depth 1

git clone https://github.com/cocos2d/cocos2d-x-extensions.git \
  Player/cocos2d/extensions --depth 1
```

### rapidjson gotcha (showed up in v72 first compile)

The version of `rapidjson` that `cocos2d-x v3-deps-153` ships is older
than what PGMMV's code expects. Specifically, PGMMV calls:

```cpp
doc.AddMember(GenericValue&&, const char *, Allocator&);
```

The shipped header only has the `(GenericValue&&, GenericValue&&, Allocator&)`
overload. Symptom: dozens of `no matching function for call to AddMember`
errors during ndk-build.

Fix: replace `Player/cocos2d/external/rapidjson/` with the
`rapidjson` package vendored in
[PGMMV's own SDK](https://github.com/SmokingWOLF/PGMMV) or use upstream
rapidjson 1.1.0+. Verified working: 1.1.0.

### `(int)p1` pointer truncation (arm64-v8a only)

`Player/Classes/Scene.cpp` has three lines that cast a pointer to `int`
which truncates on 64-bit:

```cpp
(int)p1
```

Replace with `(intptr_t)p1` or `reinterpret_cast<intptr_t>(p1)`. Doesn't
affect armeabi-v7a builds. Hit during v72 arm64-v8a attempt — currently
arm64 build is parked because v71 only shipped armeabi-v7a anyway.

## ndk-build invocation

```sh
cd Player/proj.android-studio/app
$NDK_HOME/ndk-build \
    NDK_DEBUG=0 \
    APP_ABI=armeabi-v7a \
    APP_PLATFORM=android-19 \
    -j$(nproc)
```

This produces `Player/proj.android-studio/app/libs/armeabi-v7a/libMyGame.so`
(~29 MB). On a 1-core sandbox machine the compile takes ~30–45 minutes
because the cocos2d-x Particle3D + PU extensions alone are ~470 `.o`
files.

## Java / dex side

```sh
javac --release 8 -d build/classes \
  $(find src -name "*.java")

d8 --release --min-api 19 \
   --output build/dex \
   build/classes/**/*.class \
   $(find <android-jar-deps> -name "*.jar")
```

`d8` produces `classes.dex` (and optionally `classes2.dex`, `classes3.dex`
if you exceed the 64K-method limit). The current overlay easily fits in
a single dex.

## Two ways to ship

### Path A — full clean build (what we tried in v72)

```sh
# Compile native
$NDK_HOME/ndk-build NDK_DEBUG=0 APP_ABI=armeabi-v7a -j4

# Assemble APK (gradle inside Android Studio handles this normally;
# headless equivalent below)
aapt2 compile --dir res -o build/res.zip
aapt2 link -o build/app-unsigned.apk \
    -I $ANDROID_HOME/platforms/android-30/android.jar \
    --manifest AndroidManifest.xml \
    -R build/res.zip

cd build && unzip -q app-unsigned.apk -d apk
cp ../../libs/armeabi-v7a/libMyGame.so apk/lib/armeabi-v7a/
cp ../classes.dex apk/
# repack
cd apk && zip -r ../app-repack.apk . && cd ..

zipalign -p 4 app-repack.apk app-aligned.apk
apksigner sign --ks debug.keystore \
  --ks-pass pass:android --key-pass pass:android \
  --v1-signing-enabled true \
  --v2-signing-enabled true \
  --v3-signing-enabled true \
  --out app-signed.apk app-aligned.apk
apksigner verify -v app-signed.apk
```

Took ~5 hours end-to-end the first time (clean compile of the entire
engine). The `libMyGame.so` that came out of this for v72 was correct
in isolation but crashed at runtime because Hot Dog King's v71 has
undocumented fallbacks in `GameManager::getAppName()` etc. that aren't
in this repo (the source fixes for those would need to be ported in).

### Path B — binary-patch v71's `.so` and re-sign (what we ship in practice)

This is the actual workflow that produced v72b–v72L:

```sh
# 1. Pull v71 apart
unzip hell-after-school-v71.apk -d v71

# 2. Patch the existing .so (see 02-binary-patches.md for offsets)
python3 apk-build/patch_libmygame.py \
    v71/lib/armeabi-v7a/libMyGame.so \
    -o v71/lib/armeabi-v7a/libMyGame.so

# 3. Optionally swap classes.dex (for the Java overlay updates)
cp build/classes2.dex v71/classes2.dex
cp build/AndroidManifest.xml v71/AndroidManifest.xml   # if changed

# 4. Re-pack, align, sign
cd v71 && zip -r ../v72X-repack.apk . && cd ..
zipalign -p 4 v72X-repack.apk v72X-aligned.apk
apksigner sign --ks viktor-debug.keystore \
  --ks-pass pass:android --key-pass pass:android \
  --v1-signing-enabled true --v2-signing-enabled true --v3-signing-enabled true \
  --out hell-after-school-v72X.apk v72X-aligned.apk
```

End-to-end this takes ~2 minutes. **This is the recommended workflow
for all future releases** until the repo has all of Hot Dog King's
post-build-59 changes merged back in.

## The signing key gotcha

Every v72 build is signed with our own keystore (debug). v71 was signed
with Hot Dog King's release key. Android refuses in-place upgrades
across signing keys. **Every new v72X requires `adb uninstall
com.sthdk.hellafterschool` (or "Uninstall" via Settings) before
installing.** This is non-negotiable for the user — make it the
first line of every release post.

If we ever want true in-place updates between our own versions, generate
one keystore once, reuse it for every v72X. The keystore is currently
`apk-build/viktor-debug.keystore` (or should be — TODO commit it
intentionally to a release-key location, NOT the public repo).

## Filebin upload notes

Filebin blocks `.apk` extension uploads but accepts `.zip`. Every
release goes up as `hell-after-school-v72X.zip` with the user told to
rename to `.apk` after download. Bins expire in 6 days; the Slack
upload is the long-term mirror.

## Recap: which path for which task

| Task | Path |
|---|---|
| Java overlay change only (gamepad buttons, layout, keymap) | Path B — repack v71 with new `classes2.dex` + manifest. |
| Binary patch change (RT-shader, SceneLayer RT, TouchGamepad) | Path B — patch `libMyGame.so`, repack. |
| New native C++ function or non-trivial logic change | Path A — but expect to port Hot Dog King's missing patches over first. |
| arm64-v8a support | Path A — fix `(int)p1` casts first. Currently parked. |
