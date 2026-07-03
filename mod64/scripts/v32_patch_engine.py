#!/usr/bin/env python3
# v32 engine patcher -- runs on the CI runner against REAL unredacted source.
#
# Fix: on arm64 Android, agtk::Scene::start() crashes (SIGSEGV, fault addr
# 0x276d0000126d) inside agtk::ChangeScreenResolutionSize(Size, float). That is
# desktop window-resizing code (window magnification / fullscreen). It sits in a
# block guarded only for Switch (CC_PLATFORM_NX), so it still runs on Android,
# where the OS owns the surface and the call dereferences a bad pointer.
#
# We guard JUST the crashing call for Android (the sibling calls in the same
# block ran fine in the v31 device log, so this is the minimal, safe change).
import sys, io

PATH = sys.argv[1] if len(sys.argv) > 1 else "Player/Classes/Lib/Scene.cpp"

with io.open(PATH, "r", encoding="utf-8", errors="surrogateescape", newline="") as f:
    s = f.read()

nl = "\r\n" if "\r\n" in s else "\n"

if "v32: desktop-only window resize" in s:
    print("V32-PATCH-SKIP: already patched")
    sys.exit(0)

# Anchor on the exact crashing call. The args make it unique in the file.
needle = "agtk::ChangeScreenResolutionSize(screenSize, magnifyWindow);"
n = s.count(needle)
if n != 1:
    print("V32-PATCH-FAIL: anchor count=%d (expected 1) for %r" % (n, needle))
    sys.exit(1)

# Preserve the leading indentation of the matched line.
idx = s.index(needle)
line_start = s.rfind(nl, 0, idx)
line_start = 0 if line_start == -1 else line_start + len(nl)
indent = s[line_start:idx]  # whitespace before the call

guarded = (
    "#if (CC_TARGET_PLATFORM != CC_PLATFORM_ANDROID)  // v32: desktop-only window resize; crashes on arm64" + nl +
    indent + needle + nl +
    indent + "#endif  // v32"
)

# Replace the whole physical line (indent + needle) with the guarded version.
s = s.replace(indent + needle, guarded, 1)

with io.open(PATH, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
    f.write(s)
print("V32-PATCH-OK: guarded ChangeScreenResolutionSize for Android")
