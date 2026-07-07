#!/usr/bin/env python3
# v40 engine patcher -- runs on the CI runner against REAL unredacted source.
#
# TARGET: Player/Classes/Lib/Tile.cpp
#
# ROOT CAUSE (finally pinned down from v39 crash log):
#   agtk::Tile::setupPhysicsBody builds a static collision body per tile and
#   calls PhysicsBody::addShape(shape) for each wall/box. addShape's second
#   parameter, addMassAndMoment, defaults to TRUE, so cocos2d accumulates
#   mass + moment and calls Chipmunk's cpBodySetMoment. For arm64 edge-segment
#   tile shapes the resulting moment is non-positive / NaN, and Chipmunk aborts
#   ("Moment of Inertia must be positive", cpBody.c:274). Every crash so far
#   (v36..v39) has been in this exact block:
#       PhysicsBody::addShape+... -> Tile::setupPhysicsBody+0x280
#   Chipmunk is linked as a PREBUILT static lib, so the assert cannot be patched
#   out at the Chipmunk level; and cocos2d-level moment clamping (v39) did not
#   stop it. The definitive fix is to not compute mass/moment for these shapes
#   at all.
#
# FIX: pass addMassAndMoment=false to every addShape() call in
#   setupPhysicsBody. These bodies are static collision walls -- mass and
#   moment are irrelevant to them, and skipping the accumulation means
#   cpBodySetMoment is never called from this path. Collision geometry is
#   unaffected (the shapes are still added to the body and the space).
#
# Minimal: 5 call sites, no behavioural change to collision, no 32-bit impact.
import sys, io

PATH = sys.argv[1] if len(sys.argv) > 1 else "Player/Classes/Lib/Tile.cpp"

with io.open(PATH, "r", encoding="utf-8", errors="surrogateescape", newline="") as f:
    s = f.read()

MARK = "v40"
if "addShape(wall, false)" in s or "addShape(box, false)" in s:
    print("V40-PATCH-SKIP: already patched")
    sys.exit(0)

# Targeted, exact replacements. Both call shapes appear ONLY inside
# setupPhysicsBody (verified: 5 total addShape() sites, lines ~1482-1504).
repls = [
    ("pTile->addShape(wall);", "pTile->addShape(wall, false); // v40: static tile, skip mass/moment"),
    ("pTile->addShape(box);",  "pTile->addShape(box, false);  // v40: static tile, skip mass/moment"),
]

total = 0
for old, new in repls:
    c = s.count(old)
    if c:
        s = s.replace(old, new)
        total += c
        print("V40: replaced %d x %r" % (c, old))

if total != 5:
    print("V40-PATCH-FAIL: expected 5 addShape replacements, made %d" % total)
    sys.exit(1)

with io.open(PATH, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
    f.write(s)

chk = io.open(PATH, "r", encoding="utf-8", errors="surrogateescape").read()
# No unqualified pTile->addShape( left in the file (all must be ", false").
import re
bad = re.findall(r'pTile->addShape\([A-Za-z_]+\);', chk)
if bad:
    print("V40-PATCH-FAIL: %d addShape call(s) still without addMassAndMoment=false" % len(bad))
    sys.exit(1)
if chk.count("addShape(wall, false)") != 4 or chk.count("addShape(box, false)") != 1:
    print("V40-PATCH-FAIL: post-write count mismatch")
    sys.exit(1)

print("V40-PATCH-OK: 5 tile addShape() calls now skip mass/moment (no cpBodySetMoment)")
