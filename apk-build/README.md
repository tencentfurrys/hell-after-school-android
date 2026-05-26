# Manual APK build pipeline

Bypasses Gradle. Used because the upstream PGMMV Gradle config targets desktop and old Android Studio versions; manual is faster + more controllable for diagnostics.

## Pipeline

1. `aapt2 compile` resources (`app/res/`) → `compiled/app-res.zip`
2. `aapt2 link` (manifest + compiled res) → `resources.ap_`
3. `javac` (all `org.cocos2dx.*` + `com.sthdk.*` Java sources, from `srclist.txt`) → `javac-out/*.class`
4. `d8 --release` → `classes.dex`
5. Python `zipfile` assembles APK:
   - `resources.ap_` baseline
   - `classes.dex`
   - `lib/armeabi-v7a/libMyGame.so` *(STORED, must not be compressed for `extractNativeLibs=false`)*
   - `assets/` *(DEFLATED, 481 files)*
6. `zipalign -p 4` (4KB align with page-align for native libs)
7. `apksigner sign --v1-signing-enabled true --v2-signing-enabled true`

## Files in this dir

- `build_apk.sh` — bash script wrapping steps 5-7
- `srclist.txt` — list of all `.java` files for `javac`
- `classlist.txt` — list of all `.class` files for `d8`
