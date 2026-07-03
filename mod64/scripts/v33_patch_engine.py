#!/usr/bin/env python3
# v33 engine patcher -- runs on the CI runner against REAL unredacted source.
#
# Supersedes v32. v32 tried to guard the crashing desktop call with
#   #if (CC_TARGET_PLATFORM != CC_PLATFORM_ANDROID)
# but CC_TARGET_PLATFORM resolves to CC_PLATFORM_UNKNOWN inside Scene.cpp
# (no effective CCPlatformConfig.h in that translation unit), so the guard was
# always true and the call was NOT compiled out -> identical crash in v32.
#
# v33 uses __ANDROID__, which the Android NDK compiler defines unconditionally
# for EVERY translation unit, no include required. Bulletproof.
#
# Crash: agtk::Scene::start() -> agtk::ChangeScreenResolutionSize(Size,float)
# SIGSEGV, fault addr 0x276d0000xxxx (bad pointer). Desktop window-resize code;
# meaningless on Android where the OS owns the surface. Guard it out.
import sys, io

PATH = sys.argv[1] if len(sys.argv) > 1 else "Player/Classes/Lib/Scene.cpp"

with io.open(PATH, "r", encoding="utf-8", errors="surrogateescape", newline="") as f:
    s = f.read()

nl = "\r\n" if "\r\n" in s else "\n"

if "v33: skip desktop window-resize on Android" in s:
    print("V33-PATCH-SKIP: already patched")
    sys.exit(0)

# Remove any (ineffective) v32 guard first so we don't nest guards.
# v32 inserted these two directive lines around the call; strip them if present.
s = s.replace("#if (CC_TARGET_PLATFORM != CC_PLATFORM_ANDROID)  // v32: desktop-only window resize; crashes on arm64" + nl, "")
s = s.replace("#endif  // v32" + nl, "")

needle = "agtk::ChangeScreenResolutionSize(screenSize, magnifyWindow);"
n = s.count(needle)
if n != 1:
    print("V33-PATCH-FAIL: anchor count=%d (expected 1) for %r" % (n, needle))
    sys.exit(1)

idx = s.index(needle)
ls = s.rfind(nl, 0, idx)
ls = 0 if ls == -1 else ls + len(nl)
indent = s[ls:idx]  # whitespace before the call

guarded = (
    "#if !defined(__ANDROID__)  // v33: skip desktop window-resize on Android (crashes on arm64)" + nl +
    indent + needle + nl +
    "#endif  // v33"
)
s = s.replace(indent + needle, guarded, 1)

with io.open(PATH, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
    f.write(s)
print("V33-PATCH-OK: guarded ChangeScreenResolutionSize with __ANDROID__")
