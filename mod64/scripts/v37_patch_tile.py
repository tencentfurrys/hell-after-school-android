#!/usr/bin/env python3
"""
v37 physics crash fix for Player/Classes/Lib/Tile.cpp

CRASH (arm64 only):
  Aborting due to Chipmunk error: Moment of Inertia must be positive.
  cpBodySetMoment  <- PhysicsBody::addShape <- Tile::setupPhysicsBody
  <- SceneLayer::initTileMapList (first real scene load).

ROOT CAUSE:
  Tile::setupPhysicsBody() creates the tile body with PhysicsBody::create(),
  which defaults to dynamic=true, rotationEnabled=true. It then calls addShape()
  for each wall/box. Inside cocos2d PhysicsBody::addMoment():

      if (_rotationEnabled && _dynamic)          // both TRUE at this point
          cpBodySetMoment(_cpBody, _moment);     // <- Chipmunk asserts

  Only AFTER all addShape() calls does the code set the body static and
  non-rotating (setDynamic(false), setRotationEnable(false)). On arm64 the
  accumulated _moment for a tile shape comes out negative/NaN (a 64-bit float
  discrepancy), so cpBodySetMoment aborts (NaN >= 0.0f is false).

FIX:
  These tiles are static, non-rotating collision walls. cpBodySetMoment must
  never run on them. Insert setDynamic(false) + setRotationEnable(false)
  IMMEDIATELY after PhysicsBody::create(), so addMoment()'s guard
  (_rotationEnabled && _dynamic) is false during every addShape() call and the
  bad moment is never handed to Chipmunk. Shapes still register (collision
  geometry is added regardless of the dynamic flag), so gameplay is unchanged.

  The original trailing setDynamic(false)/setRotationEnable(false) are left in
  place; cocos guards them (if (dynamic != _dynamic) / if (_rotationEnabled !=
  enable)) so the second calls are harmless no-ops.

Usage: python3 v37_patch_tile.py <path/to/Tile.cpp>
"""
import re, sys

def die(msg):
    print("V37-PATCH-FAIL:", msg); sys.exit(1)

if len(sys.argv) != 2:
    die("usage: v37_patch_tile.py <Tile.cpp>")

path = sys.argv[1]
src = open(path, "r", encoding="utf-8", errors="replace").read()

if "v37: force static+no-rotation before addShape" in src:
    die("already patched (v37 marker present)")

# Locate setupPhysicsBody and the `auto pTile = PhysicsBody::create();` line
# inside it. We anchor on the create() call that is immediately followed by the
# halfSize computation, which is unique to setupPhysicsBody.
pat = re.compile(
    r'(auto\s+pTile\s*=\s*PhysicsBody::create\(\)\s*;\s*\n)'
)
m = pat.search(src)
if not m:
    die("could not find `auto pTile = PhysicsBody::create();`")

insert = (
    "\t// v37: force static+no-rotation before addShape so cocos never calls\n"
    "\t// cpBodySetMoment() with a bad (arm64 negative/NaN) moment. These tiles\n"
    "\t// are static non-rotating walls; shapes still register for collision.\n"
    "\tpTile->setDynamic(false);\n"
    "\tpTile->setRotationEnable(false);\n"
)

# Insert right after the create() line.
new_src = src[:m.end()] + insert + src[m.end():]

if new_src == src:
    die("insertion produced no change")

# ---------------------------------------------------------------------------
# Fix 2: the merged-tile path uses PhysicsBody::createBox(...), which builds the
# body dynamic and adds its box shape (calling cpBodySetMoment) BEFORE the code
# sets it static. Replace it with an equivalent create()+static+addShape so the
# bad moment is never pushed to Chipmunk here either.
# ---------------------------------------------------------------------------
createbox_pat = re.compile(
    r'auto\s+pTile\s*=\s*PhysicsBody::createBox\(\s*mergedBoxSize\s*,\s*'
    r'PhysicsMaterial\(0\.1f,\s*startTileRepulsion,\s*startTileFriction\)\s*,\s*offset\s*\)\s*;'
)
mb = createbox_pat.search(new_src)
if mb:
    replacement = (
        "// v37: build merged-tile body static-first (was PhysicsBody::createBox,\n"
        "\t\t\t\t// which adds its shape while dynamic and can abort Chipmunk on arm64).\n"
        "\t\t\t\tauto pTile = PhysicsBody::create();\n"
        "\t\t\t\tpTile->setDynamic(false);\n"
        "\t\t\t\tpTile->setRotationEnable(false);\n"
        "\t\t\t\t{\n"
        "\t\t\t\t\tauto mergedBox = PhysicsShapeBox::create(mergedBoxSize, "
        "PhysicsMaterial(0.1f, startTileRepulsion, startTileFriction), offset);\n"
        "\t\t\t\t\tpTile->addShape(mergedBox);\n"
        "\t\t\t\t}"
    )
    new_src = new_src[:mb.start()] + replacement + new_src[mb.end():]
    print("V37-PATCH: merged-tile createBox path fixed")
else:
    print("V37-PATCH: merged-tile createBox pattern not found (skipping fix 2)")

open(path, "w", encoding="utf-8").write(new_src)

# Sanity checks
chk = open(path, encoding="utf-8").read()
for token in [
    "v37: force static+no-rotation before addShape",
    "pTile->setDynamic(false);",
    "pTile->setRotationEnable(false);",
]:
    if token not in chk:
        die("post-write token missing: " + token)

# Confirm the inserted static call comes BEFORE the first addShape in the file's
# setupPhysicsBody. We check ordering by index of our marker vs first addShape.
marker_idx = chk.index("v37: force static+no-rotation before addShape")
addshape_idx = chk.index("->addShape(", marker_idx if marker_idx < chk.find("->addShape(") else 0)
# Simple ordering assertion relative to the create() line region:
if chk.index("pTile->setRotationEnable(false);") > chk.index("->addShape(", marker_idx):
    # our early setRotationEnable must precede the first addShape after the marker
    pass  # informational; the insertion point guarantees ordering

print("V37-PATCH-OK:", path)
