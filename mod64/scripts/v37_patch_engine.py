#!/usr/bin/env python3
# v37 engine patcher -- runs on the CI runner against REAL unredacted source.
#
# ROOT CAUSE (confirmed from source reading, crash log 2026-07-07):
#   Picking Tutorial / Skip Tutorial loads the first playable scene, which
#   builds a physics body per map tile in agtk::Tile::setupPhysicsBody
#   (Player/Classes/Lib/Tile.cpp). The body is created DYNAMIC (the cocos2d
#   default) and only made non-dynamic / rotation-disabled AFTER all addShape
#   calls. Each addShape -> PhysicsBody::addMoment ends with:
#
#       if (_rotationEnabled && _dynamic)          // both still true here
#           cpBodySetMoment(_cpBody, _moment);     // Chipmunk asserts moment>=0
#
#   For FILLED_WALLBIT ground tiles the accumulated _moment reaching Chipmunk
#   is non-positive / NaN ON ARM64 (same 64-bit FP-path family as the earlier
#   arm64-only crashes), so Chipmunk aborts:
#       "Aborting due to Chipmunk error: Moment of Inertia must be positive."
#       cpBody.c:274  (cpBodySetMoment)
#   The 32-bit build computes a valid moment, so it never trips the assert.
#   The merged-box path (createBox) is unaffected -- it builds one valid box
#   shape whose moment is well-defined.
#
# FIX (minimal, arch-safe, behaviour-preserving):
#   Make the tile body non-dynamic and rotation-disabled IMMEDIATELY after
#   PhysicsBody::create(), BEFORE any addShape. Then _dynamic is already false
#   during shape-adding, so cpBodySetMoment is never invoked with the bad
#   value. Static/kinematic tiles do not need a computed moment (Chipmunk
#   gives them infinite mass/moment). The body's final state is identical to
#   today's (setDynamic(false)/setRotationEnable(false) are still called later;
#   the second call is a no-op), so 32-bit behaviour is unchanged.
#
# This inserts two lines, deletes nothing. Verifiable by re-reading the .so's
# Tile::setupPhysicsBody, or simply by the scene loading without the abort.
import sys, io

PATH = sys.argv[1] if len(sys.argv) > 1 else "Player/Classes/Lib/Tile.cpp"

with io.open(PATH, "r", encoding="utf-8", errors="surrogateescape", newline="") as f:
    s = f.read()

MARK = "v37: set static+no-rotation before addShape (arm64 Chipmunk moment guard)"
if MARK in s:
    print("V37-PATCH-SKIP: already patched")
    sys.exit(0)

# Unique anchor: the per-tile body creation in setupPhysicsBody. The repo
# checkout uses CRLF line endings, so match the line and its own newline
# style rather than assuming \n.
import re
m = re.search(r'([ \t]*)auto pTile = PhysicsBody::create\(\);(\r?\n)', s)
if not m:
    print("V37-PATCH-FAIL: could not find 'auto pTile = PhysicsBody::create();'")
    sys.exit(1)
# Ensure it is unique.
if len(re.findall(r'auto pTile = PhysicsBody::create\(\);', s)) != 1:
    print("V37-PATCH-FAIL: anchor not unique")
    sys.exit(1)

indent = m.group(1)
nl = m.group(2)
anchor = m.group(0)
insert = (
    anchor
    + indent + "// " + MARK + nl
    + indent + "pTile->setDynamic(false);       // static tile: no dynamic mass/moment recompute" + nl
    + indent + "pTile->setRotationEnable(false); // avoid cpBodySetMoment during addShape on arm64" + nl
)

s = s.replace(anchor, insert, 1)

with io.open(PATH, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
    f.write(s)

# sanity
chk = io.open(PATH, "r", encoding="utf-8", errors="surrogateescape").read()
if MARK not in chk:
    print("V37-PATCH-FAIL: marker missing after write"); sys.exit(1)
# The early setDynamic(false) must now appear before the first addShape.
i_dyn = chk.find("pTile->setDynamic(false);")
i_shape = chk.find("pTile->addShape(")
if i_dyn == -1 or i_shape == -1 or i_dyn > i_shape:
    print("V37-PATCH-FAIL: setDynamic(false) not positioned before first addShape"); sys.exit(1)

print("V37-PATCH-OK: tile body set static+no-rotation before addShape")
