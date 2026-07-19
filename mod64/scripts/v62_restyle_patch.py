#!/usr/bin/env python3
# v62 Build: restyle on-screen controls to FIT the FOBS look (Kincaid was only a reference).
# FOBS palette = warm wood-brown + gold/amber ornate HUD frames over green forest.
# Change: translucent "glass" fills so the game shows through, glowing AMBER/GOLD rings that
# match the game's gold HUD frames, bright warm labels. Colors/alpha/stroke ONLY -- no layout,
# no memory change (safe on top of the v61 32-bit crash-isolation build).
# Implemented as a restyle() method that overrides paints AFTER init creates them, called just
# before init's return-void. Leaves the fragile drawing/layout code untouched.
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
CLS = "Lorg/cocos2dx/cpp/GamepadOverlay;"

# --- 1. call restyle() at end of init(Landroid/content/Context;)V ---
# init uses .registers 20 with v0 = p0 (this) via move-object/from16 v0, p0.
# The method's ONLY return-void is its last instruction.
anchor = (
    "    invoke-virtual {v0, v3}, Lorg/cocos2dx/cpp/GamepadOverlay;->setBackgroundColor(I)V\n\n"
    "    .line 249\n"
    "    return-void\n"
    ".end method\n"
)
assert s.count(anchor) == 1, "init tail anchor not unique/found"
inject = (
    "    invoke-virtual {v0, v3}, Lorg/cocos2dx/cpp/GamepadOverlay;->setBackgroundColor(I)V\n\n"
    "    invoke-direct {v0}, " + CLS + "->restyle()V\n\n"
    "    .line 249\n"
    "    return-void\n"
    ".end method\n"
)
s = s.replace(anchor, inject, 1)

# --- 2. append restyle(): override paint colors/alpha/stroke to the FOBS amber-glass look ---
# helper pattern per paint: load field, argb(a,r,g,b) via Color.argb, setColor. STROKE paints
# also get a thicker glowing stroke. Registers: v0=this(param p0), v1=paint, v2..v5 argb ints.
def set_color(field, a, r, g, b):
    return (
        "    iget-object v1, p0, " + CLS + "->" + field + ":Landroid/graphics/Paint;\n"
        "    const/16 v2, " + hex(a) + "\n"
        "    const/16 v3, " + hex(r) + "\n"
        "    const/16 v4, " + hex(g) + "\n"
        "    const/16 v5, " + hex(b) + "\n"
        "    invoke-static {v2, v3, v4, v5}, Landroid/graphics/Color;->argb(IIII)I\n"
        "    move-result v2\n"
        "    invoke-virtual {v1, v2}, Landroid/graphics/Paint;->setColor(I)V\n"
    )

def set_stroke(field, width_hex, comment):
    return (
        "    iget-object v1, p0, " + CLS + "->" + field + ":Landroid/graphics/Paint;\n"
        "    const/high16 v2, " + width_hex + "    # " + comment + "\n"
        "    invoke-virtual {v1, v2}, Landroid/graphics/Paint;->setStrokeWidth(F)V\n"
    )

body = ""
# Idle button fills -> translucent dark glass (alpha ~0x26 = ~15%) so forest shows through
for f in ["paintBase", "paintDash", "paintCombo", "paintShoot"]:
    body += set_color(f, 0x26, 0x1a, 0x12, 0x08)
# Pressed states -> warm amber glow (alpha ~0x8c) matching FOBS gold
for f in ["paintPressed", "paintDashPressed", "paintComboPressed", "paintShootPressed"]:
    body += set_color(f, 0x8c, 0xff, 0xc0, 0x50)
# Ring outline -> glowing amber/gold, and a bit thicker (3.0f)
body += set_color("paintOutline", 0xeb, 0xff, 0xbe, 0x5a)
body += set_stroke("paintOutline", "0x40400000", "3.0f amber ring")
# Direction arrows -> bright amber
body += set_color("paintArrow", 0xeb, 0xff, 0xc8, 0x6e)
# Labels -> bright warm white
for f in ["paintLabel", "paintLabelSmall"]:
    body += set_color(f, 0xff, 0xff, 0xf5, 0xdc)

restyle = (
    "\n.method private restyle()V\n"
    "    .registers 6\n"
    + body +
    "    return-void\n"
    ".end method\n"
)
s = s.rstrip() + "\n" + restyle + "\n"

open(p, "w", encoding="utf-8").write(s)
print("patched OK")
