#!/usr/bin/env python3
# v41 arm64 ABI fix.
#
# Root cause of the "Moment of Inertia must be positive" abort on scene load:
# the prebuilt android-arm64 chipmunk static lib (cocos2d-x-3rd-party-libs,
# contrib/android-arm64/chipmunk) is compiled with cpFloat = float, but cocos2d
# itself compiles chipmunk_types.h with the stock default CP_USE_DOUBLES = 1,
# i.e. cpFloat = double. Caller (cocos2d PhysicsBody) passes/stores 64-bit
# doubles; callee (prebuilt chipmunk) reads/stores 32-bit floats. The cpBody
# struct layout and the by-value cpFloat arguments therefore disagree, so the
# moment reaching cpBodySetMoment is a garbage bit pattern (often <0 / NaN) and
# the hard assert aborts. This is why every value-level fix (v37/v38/v39) failed:
# chipmunk never read the double we were sanitising.
#
# Fix: force cocos2d to compile with cpFloat = float on arm64, matching the
# prebuilt lib's ABI and struct layout. Insert an unconditional arm64 override
# right after the stock CP_USE_DOUBLES default block, so it wins even if some
# build flag defines CP_USE_DOUBLES. Non-arm64 builds are untouched.
import sys

path = sys.argv[1]
raw = open(path, "rb").read()
nl = b"\r\n" if b"\r\n" in raw else b"\n"
text = raw.decode("utf-8")

MARKER = "v41: arm64 cpFloat ABI fix"
if MARKER in text:
    print("v41: already patched, no-op")
    sys.exit(0)

anchor = "#ifndef CP_USE_DOUBLES"
idx = text.find(anchor)
if idx == -1:
    print("v41 ERROR: CP_USE_DOUBLES default block not found")
    sys.exit(1)

endif_idx = text.find("#endif", idx)
if endif_idx == -1:
    print("v41 ERROR: closing #endif for CP_USE_DOUBLES block not found")
    sys.exit(1)
insert_at = endif_idx + len("#endif")

use_nl = "\r\n" if nl == b"\r\n" else "\n"
block = (
    use_nl + use_nl +
    "/* " + MARKER + ": the prebuilt android-arm64 chipmunk static lib is built" + use_nl +
    "   with cpFloat = float. Force cocos2d to match on arm64 so cpBody struct" + use_nl +
    "   layout and by-value cpFloat args agree with the prebuilt lib. Without" + use_nl +
    "   this the moment passed to cpBodySetMoment is read as the wrong 32 bits" + use_nl +
    "   and the 'Moment of Inertia must be positive' hard assert aborts on load. */" + use_nl +
    "#if defined(__aarch64__) || defined(__arm64__)" + use_nl +
    "\t#undef CP_USE_DOUBLES" + use_nl +
    "\t#define CP_USE_DOUBLES 0" + use_nl +
    "#endif"
)

patched = text[:insert_at] + block + text[insert_at:]
open(path, "wb").write(patched.encode("utf-8"))

check = open(path, "rb").read().decode("utf-8")
assert MARKER in check, "marker missing after write"
assert "#undef CP_USE_DOUBLES" in check, "undef missing after write"
print("v41: patched", path, "- arm64 forced to CP_USE_DOUBLES=0 (cpFloat=float)")
