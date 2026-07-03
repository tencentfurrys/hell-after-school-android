#!/usr/bin/env python3
# v34 engine patcher -- runs on the CI runner against REAL unredacted source.
#
# ROOT CAUSE (confirmed by disassembling the v33 .so):
#   Scene::start() runs a desktop window/resolution-setup block guarded only by
#     #if (CC_TARGET_PLATFORM != CC_PLATFORM_NX) // #AGTK-NX
#   On Android that block IS compiled in and calls agtk::IsFullScreen,
#   agtk::ChangeScreen, agtk::GetScreenResolutionSize, agtk::GetFrameSize and
#   agtk::ChangeScreenResolutionSize -- desktop/window management that
#   dereferences a bad GLView/window pointer on arm64 -> SIGSEGV
#   (fault addr 0x276d0000xxxx).
#
# Why v32/v33 were no-ops: they guarded only the single
#   agtk::ChangeScreenResolutionSize(screenSize, magnifyWindow);
# line, but the compiler did NOT emit a direct call there (it is reached
# indirectly), so removing that one line changed nothing -> identical binary.
#
# v34 excludes the ENTIRE block on Android by ANDing the existing NX guard with
# !defined(__ANDROID__). __ANDROID__ is defined unconditionally by the NDK
# compiler for every TU. The disassembly proves Scene::start calls the other
# helpers directly, so this WILL change the binary (verifiable by re-disasm).
import sys, io

PATH = sys.argv[1] if len(sys.argv) > 1 else "Player/Classes/Lib/Scene.cpp"

with io.open(PATH, "r", encoding="utf-8", errors="surrogateescape", newline="") as f:
    s = f.read()

MARK = "v34: skip desktop window/resolution setup on Android"
if MARK in s:
    print("V34-PATCH-SKIP: already patched")
    sys.exit(0)

# Unique anchor: the only NX guard with parentheses AND the // #AGTK-NX comment.
anchor = "#if (CC_TARGET_PLATFORM != CC_PLATFORM_NX) // #AGTK-NX"
n = s.count(anchor)
if n != 1:
    print("V34-PATCH-FAIL: anchor count=%d (expected 1) for %r" % (n, anchor))
    sys.exit(1)

replacement = (
    "#if (CC_TARGET_PLATFORM != CC_PLATFORM_NX) && !defined(__ANDROID__) "
    "// #AGTK-NX + " + MARK
)
s = s.replace(anchor, replacement, 1)

with io.open(PATH, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
    f.write(s)
print("V34-PATCH-OK: excluded desktop window/resolution block on Android")
