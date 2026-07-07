#!/usr/bin/env python3
# v39 engine patcher -- runs on the CI runner against REAL unredacted source.
#
# TARGET: Player/cocos2d/cocos/physics/CCPhysicsBody.cpp
#
# ROOT CAUSE (after v36/v37/v38):
#   Loading the first playable scene builds a physics body per tile. On arm64
#   the moment-of-inertia value that reaches Chipmunk's cpBodySetMoment comes
#   out negative or NaN (a 64-bit-only FP/def bug -- the 32-bit build computes
#   a valid moment). Chipmunk then aborts:
#       "Aborting due to Chipmunk error: Moment of Inertia must be positive.
#        Failed condition: moment >= 0.0f  (cpBody.c:274)"
#   Every attempted fix at the Tile level (v36 addShape timing, v37
#   setRotationEnable-first, v38 value swap) only moved WHICH caller trips it,
#   because all callers funnel through the same cpBodySetMoment choke point.
#
# FIX: sanitise the moment at THE SINGLE CHOKE POINT. Insert a helper
#   ccSafeMoment() and wrap every cpBodySetMoment(_cpBody, X) call (and the
#   cpBodyNew moment arg) with it. The helper leaves every legitimate positive
#   finite moment untouched (so dynamic-body physics and the 32-bit build are
#   unchanged) and only substitutes a large finite positive for the broken
#   values (NaN / <= 0 / +/-inf), which for our static tile bodies is
#   semantically "no rotation" -- exactly what the tile code already wants.
#   Also hardens internalBodySetMass against a divide-by-zero m_inv.
#
# This cannot "move" the crash: it is the last function before Chipmunk.
import sys, io, re

PATH = sys.argv[1] if len(sys.argv) > 1 else "Player/cocos2d/cocos/physics/CCPhysicsBody.cpp"

with io.open(PATH, "r", encoding="utf-8", errors="surrogateescape", newline="") as f:
    s = f.read()

MARK = "v39: sanitise moment/mass before Chipmunk (arm64 negative-moment guard)"
if MARK in s:
    print("V39-PATCH-SKIP: already patched")
    sys.exit(0)

nl = "\r\n" if "\r\n" in s else "\n"

# ------------------------------------------------------------------ helper
# Insert the helper immediately before the existing internalBodySetMass def.
anchor_fn = "static void internalBodySetMass(cpBody *body, cpFloat mass)"
if s.count(anchor_fn) != 1:
    print("V39-PATCH-FAIL: could not find internalBodySetMass (count=%d)" % s.count(anchor_fn))
    sys.exit(1)

helper = (
    "// " + MARK + nl +
    "#include <cmath>" + nl +
    "static inline cpFloat ccSafeMoment(cpFloat m)" + nl +
    "{" + nl +
    "    // Chipmunk asserts moment >= 0 and needs a finite, non-zero moment to" + nl +
    "    // simulate. On arm64 some tile bodies produce NaN/<=0/inf here; clamp" + nl +
    "    // only those to a large finite positive (== effectively no rotation)." + nl +
    "    // Legitimate positive finite moments pass through unchanged." + nl +
    "    if (!(m > 0.0f)) return (cpFloat)1.0e30;   // NaN, zero, negative" + nl +
    "    if (std::isinf((double)m)) return (cpFloat)1.0e30;" + nl +
    "    return m;" + nl +
    "}" + nl + nl
)

s = s.replace(anchor_fn, helper + anchor_fn, 1)

# ------------------------------------------------------ harden mass division
# body->m_inv = 1.0f/mass;  ->  guard against mass<=0 / NaN
old_minv = "body->m_inv = 1.0f/mass;"
if s.count(old_minv) == 1:
    s = s.replace(
        old_minv,
        "body->m_inv = (mass > 0.0f) ? 1.0f/mass : 0.0f; // v39: avoid 1/0 -> inf",
        1)
else:
    # non-fatal: mass path isn't the observed crash, but note it
    print("V39-PATCH-NOTE: m_inv line not found/!=1; skipping mass hardening")

# ------------------------------------------------------ wrap moment call sites
# 1) cpBodyNew(_mass, _moment)
n_new = 0
if "cpBodyNew(_mass, _moment)" in s:
    s = s.replace("cpBodyNew(_mass, _moment)",
                  "cpBodyNew(_mass, ccSafeMoment(_moment))", 1)
    n_new = 1

# 2) every cpBodySetMoment(_cpBody, <expr>);  -> wrap <expr> with ccSafeMoment(...)
#    Handles both `_moment` and the `enable ? _moment : PHYSICS_INFINITY` form.
pat = re.compile(r'cpBodySetMoment\(_cpBody,\s*(.+?)\);')
def _wrap(m):
    arg = m.group(1).strip()
    # don't double-wrap
    if arg.startswith("ccSafeMoment("):
        return m.group(0)
    return "cpBodySetMoment(_cpBody, ccSafeMoment(%s));" % arg
s, n_set = pat.subn(_wrap, s)

with io.open(PATH, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
    f.write(s)

# ------------------------------------------------------------------ sanity
chk = io.open(PATH, "r", encoding="utf-8", errors="surrogateescape").read()
if MARK not in chk:
    print("V39-PATCH-FAIL: marker missing"); sys.exit(1)
if "ccSafeMoment(" not in chk:
    print("V39-PATCH-FAIL: helper not referenced"); sys.exit(1)
# Every cpBodySetMoment must now be wrapped: count total vs wrapped.
total_set = len(re.findall(r'cpBodySetMoment\(_cpBody,', chk))
wrapped_set = len(re.findall(r'cpBodySetMoment\(_cpBody,\s*ccSafeMoment\(', chk))
if total_set != wrapped_set:
    print("V39-PATCH-FAIL: %d/%d cpBodySetMoment call(s) unwrapped"
          % (total_set - wrapped_set, total_set))
    sys.exit(1)

print("V39-PATCH-OK: wrapped cpBodyNew moment=%d, cpBodySetMoment sites=%d" % (n_new, n_set))
