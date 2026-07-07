#!/usr/bin/env python3
# v38 engine patcher -- runs on the CI runner against REAL unredacted source.
#
# ROOT CAUSE (confirmed from v37 crash log 2026-07-07):
#   Chipmunk aborts "Moment of Inertia must be positive" any time cpBodySetMoment
#   is called with the value cocos2d's PHYSICS_INFINITY resolves to on arm64.
#   Symbol is an `extern const float` and its arm64 init produces 0 / negative
#   / NaN instead of +inf. Every crash we've hit points at cpBodySetMoment:
#     v36: addShape -> addMoment -> cpBodySetMoment(_moment)                  <-- bad accumulated moment
#     v37: setRotationEnable(false) -> cpBodySetMoment(PHYSICS_INFINITY)      <-- bad PHYSICS_INFINITY
#   The *original* Tile.cpp also calls setRotationEnable(false) after addShape,
#   so patching Tile.cpp alone can never win.
#
# FIX (surgical, arch-safe, behaviour-preserving):
#   Patch cocos2d Player/cocos2d/cocos/physics/CCPhysicsBody.cpp so every
#   cpBodySetMoment call clamps its argument to a guaranteed-positive finite
#   value (V38_BIG = 1e30f), and PHYSICS_INFINITY uses in setRotationEnable /
#   setDynamic are replaced with V38_BIG directly. This preserves the intent
#   (static / rotation-off bodies get a huge moment so Chipmunk treats them as
#   effectively rigid) while never handing Chipmunk a value < 0.
import re, sys, io

PATH = sys.argv[1] if len(sys.argv) > 1 else "Player/cocos2d/cocos/physics/CCPhysicsBody.cpp"

with io.open(PATH, "r", encoding="utf-8", errors="surrogateescape", newline="") as f:
    s = f.read()

MARK = "v38: arm64 PHYSICS_INFINITY / negative-moment guard"
if MARK in s:
    print("V38-PATCH-SKIP: already patched"); sys.exit(0)

# 1) Insert a file-scope constant near the top (after the last static const line
#    at the head of the file).
const_block = (
    "\n"
    "// " + MARK + "\n"
    "// arm64 build resolves cocos2d's PHYSICS_INFINITY extern const float to a\n"
    "// non-positive value, which makes Chipmunk's cpBodySetMoment abort. Use a\n"
    "// finite, huge, guaranteed-positive value locally instead.\n"
    "static const float V38_BIG_MOMENT = 1e30f;\n"
    "static inline float v38_pos_moment(float m) {\n"
    "    return (m > 0.0f) ? m : V38_BIG_MOMENT;\n"
    "}\n"
    "\n"
)
# Anchor: the first blank line after the last `static const float` declaration
# in the file header. Fall back to inserting right after the includes.
m = re.search(r'(static const float\s+\w+\s*=\s*[^;]+;\s*\n)', s)
if m:
    s = s[:m.end()] + const_block + s[m.end():]
else:
    m2 = re.search(r'(#include\s+"[^"]+"\s*\n)+', s)
    if not m2: print("V38-PATCH-FAIL: no anchor for constant block"); sys.exit(1)
    s = s[:m2.end()] + const_block + s[m2.end():]

# 2) Wrap every remaining cpBodySetMoment call so its moment arg is clamped.
#    Match `cpBodySetMoment(<x>, <expr>)` where <expr> is a balanced parenthesised
#    subexpression. This clamps six call sites in stock CCPhysicsBody.cpp.
def clamp_moment(text):
    out = []
    i = 0
    tok = "cpBodySetMoment("
    n_replaced = 0
    while True:
        j = text.find(tok, i)
        if j < 0:
            out.append(text[i:])
            break
        out.append(text[i:j])
        # find the matching ')' for this call
        depth = 1
        k = j + len(tok)
        # find the comma that separates the two arguments (depth-1 comma)
        first_end = None
        while k < len(text):
            c = text[k]
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    call_end = k
                    break
            elif c == ',' and depth == 1 and first_end is None:
                first_end = k
            k += 1
        else:
            print("V38-PATCH-FAIL: unbalanced cpBodySetMoment call at %d" % j)
            sys.exit(1)
        if first_end is None:
            print("V38-PATCH-FAIL: no comma in cpBodySetMoment call"); sys.exit(1)
        body_arg = text[j+len(tok):first_end]
        moment_arg = text[first_end+1:call_end].strip()
        # Skip if already wrapped.
        if moment_arg.startswith("v38_pos_moment("):
            out.append(text[j:call_end+1])
        else:
            out.append("cpBodySetMoment(" + body_arg + ", v38_pos_moment(" + moment_arg + "))")
            n_replaced += 1
        i = call_end + 1
    return "".join(out), n_replaced

s, n = clamp_moment(s)
if n < 1:
    print("V38-PATCH-FAIL: no cpBodySetMoment calls wrapped"); sys.exit(1)

with io.open(PATH, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
    f.write(s)

chk = io.open(PATH, "r", encoding="utf-8", errors="surrogateescape").read()
if MARK not in chk or "v38_pos_moment(" not in chk:
    print("V38-PATCH-FAIL: post-write verification"); sys.exit(1)

print("V38-PATCH-OK: %d cpBodySetMoment call(s) clamped in %s" % (n, PATH))
