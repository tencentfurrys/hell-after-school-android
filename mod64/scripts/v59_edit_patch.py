#!/usr/bin/env python3
# v59 Build #1: grab-offset fix for the control editor.
# In v58, dragging a button snaps its CENTER to the fingertip (setRect(sel,fingerX,fingerY,r)),
# which feels like "the button follows my finger." Fix: remember where inside the button you
# grabbed (edDX/edDY = center - touch on DOWN) and move by that delta on MOVE so the button
# tracks naturally. Single isolated behavior change; selection logic (touch inside) untouched.
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
CLS = "Lorg/cocos2dx/cpp/GamepadOverlay;"

# 1) add edDX/edDY fields after edSel
anchor_f = ".field private static edSel:I\n"
assert s.count(anchor_f) == 1, "edSel field anchor not unique"
s = s.replace(anchor_f, anchor_f + ".field private static edDX:F\n.field private static edDY:F\n", 1)

# 2) on DOWN (after edNearest sets edSel), capture grab offset
anchor_down = (
    "    invoke-direct {p0, v2, v3}, " + CLS + "->edNearest(FF)I\n\n"
    "    move-result v4\n\n"
    "    sput v4, " + CLS + "->edSel:I\n"
)
assert s.count(anchor_down) == 1, "DOWN anchor not unique/found"
s = s.replace(anchor_down, anchor_down +
    "\n    invoke-direct {p0, v4, v2, v3}, " + CLS + "->edGrab(IFF)V\n", 1)

# 3) on single-finger MOVE, apply offset instead of snapping center to finger
anchor_move = (
    "    move-result v5\n\n"
    "    invoke-direct {p0, v4, v2, v3, v5}, " + CLS + "->setRect(IFFF)V\n"
)
assert s.count(anchor_move) == 1, "MOVE anchor not unique/found"
repl_move = (
    "    move-result v5\n\n"
    "    sget v6, " + CLS + "->edDX:F\n\n"
    "    add-float v6, v2, v6\n\n"
    "    sget v7, " + CLS + "->edDY:F\n\n"
    "    add-float v7, v3, v7\n\n"
    "    invoke-direct {p0, v4, v6, v7, v5}, " + CLS + "->setRect(IFFF)V\n"
)
s = s.replace(anchor_move, repl_move, 1)

# 4) append edGrab helper: stores center-minus-touch, or 0 if no selection
edgrab = '''
.method private edGrab(IFF)V
    .registers 9
    const/4 v0, -0x1
    if-ne p1, v0, :grab_have
    const/4 v0, 0x0
    sput v0, LORG;->edDX:F
    sput v0, LORG;->edDY:F
    return-void
    :grab_have
    iget-object v0, p0, LORG;->btnRects:[Landroid/graphics/RectF;
    aget-object v0, v0, p1
    iget v1, v0, Landroid/graphics/RectF;->left:F
    iget v2, v0, Landroid/graphics/RectF;->right:F
    add-float/2addr v1, v2
    const/high16 v2, 0x40000000
    div-float/2addr v1, v2
    iget v3, v0, Landroid/graphics/RectF;->top:F
    iget v4, v0, Landroid/graphics/RectF;->bottom:F
    add-float/2addr v3, v4
    div-float/2addr v3, v2
    sub-float v1, v1, p2
    sub-float v3, v3, p3
    sput v1, LORG;->edDX:F
    sput v3, LORG;->edDY:F
    return-void
.end method
'''.replace("LORG;", CLS)
s = s.rstrip() + "\n" + edgrab + "\n"

open(p, "w", encoding="utf-8").write(s)
print("patched OK")
