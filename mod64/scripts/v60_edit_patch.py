#!/usr/bin/env python3
# v60 Build #2: replace two-finger pinch with on-screen +/- size buttons.
# Adds MINUS/PLUS pills in the top bar right of SAVE (0.76w / 0.88w), drawn in edit mode.
# Tap a button to select it, then tap - (x0.9) or + (x1.1) ~= 10%/tap, keeping its center.
# Reuses existing setRect(idx,cx,cy,radius). Selection/drag/DONE/SAVE unchanged.
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
CLS = "Lorg/cocos2dx/cpp/GamepadOverlay;"

# --- 1. inject +/- pill hit-test at top of edHandle (consume tap before normal logic) ---
anchor_eh = (
    ".method private edHandle(Landroid/view/MotionEvent;)I\n"
    "    .registers 16\n\n"
    "    invoke-virtual {p1}, Landroid/view/MotionEvent;->getActionMasked()I\n"
)
assert s.count(anchor_eh) == 1, "edHandle start anchor not unique/found"
inject_eh = (
    ".method private edHandle(Landroid/view/MotionEvent;)I\n"
    "    .registers 16\n\n"
    "    invoke-direct {p0, p1}, " + CLS + "->edPillPM(Landroid/view/MotionEvent;)I\n"
    "    move-result v0\n"
    "    const/4 v1, 0x1\n"
    "    if-ne v0, v1, :pm_skip\n"
    "    const/4 v0, 0x1\n"
    "    return v0\n"
    "    :pm_skip\n"
    "    invoke-virtual {p1}, Landroid/view/MotionEvent;->getActionMasked()I\n"
)
s = s.replace(anchor_eh, inject_eh, 1)

# --- 2. draw the +/- pills in edit mode (append before the return-void after SAVE label) ---
anchor_draw = (
    '    const-string v5, "SAVE"\n\n'
    "    invoke-virtual {p1, v5, v3, v4, v6}, Landroid/graphics/Canvas;->drawText(Ljava/lang/String;FFLandroid/graphics/Paint;)V\n\n"
    "    return-void\n"
)
assert s.count(anchor_draw) == 1, "edDraw SAVE tail anchor not unique/found"
draw_pm = (
    '    const-string v5, "SAVE"\n\n'
    "    invoke-virtual {p1, v5, v3, v4, v6}, Landroid/graphics/Canvas;->drawText(Ljava/lang/String;FFLandroid/graphics/Paint;)V\n\n"
    "    invoke-direct {p0}, " + CLS + "->edPillMinus()Landroid/graphics/RectF;\n"
    "    move-result-object v1\n"
    "    invoke-virtual {p1, v1, v2}, Landroid/graphics/Canvas;->drawRect(Landroid/graphics/RectF;Landroid/graphics/Paint;)V\n"
    "    iget v3, v1, Landroid/graphics/RectF;->left:F\n"
    "    iget v4, v1, Landroid/graphics/RectF;->bottom:F\n"
    '    const-string v5, "-"\n'
    "    invoke-virtual {p1, v5, v3, v4, v6}, Landroid/graphics/Canvas;->drawText(Ljava/lang/String;FFLandroid/graphics/Paint;)V\n"
    "    invoke-direct {p0}, " + CLS + "->edPillPlus()Landroid/graphics/RectF;\n"
    "    move-result-object v1\n"
    "    invoke-virtual {p1, v1, v2}, Landroid/graphics/Canvas;->drawRect(Landroid/graphics/RectF;Landroid/graphics/Paint;)V\n"
    "    iget v3, v1, Landroid/graphics/RectF;->left:F\n"
    "    iget v4, v1, Landroid/graphics/RectF;->bottom:F\n"
    '    const-string v5, "+"\n'
    "    invoke-virtual {p1, v5, v3, v4, v6}, Landroid/graphics/Canvas;->drawText(Ljava/lang/String;FFLandroid/graphics/Paint;)V\n\n"
    "    return-void\n"
)
s = s.replace(anchor_draw, draw_pm, 1)

# --- 3. append helper methods: edPillMinus, edPillPlus, edScale, edPillPM ---
NEW = r'''
.method private edPillMinus()Landroid/graphics/RectF;
    .registers 9
    invoke-virtual {p0}, LORG;->getWidth()I
    move-result v0
    int-to-float v0, v0
    invoke-virtual {p0}, LORG;->getHeight()I
    move-result v1
    int-to-float v1, v1
    const v2, 0x3f428f5c    # 0.76f
    mul-float v2, v2, v0
    const v3, 0x3ca3d70a    # 0.02f
    mul-float v3, v3, v1
    const v4, 0x3e19999a    # 0.15f
    mul-float v4, v4, v0
    add-float v5, v2, v4
    const v6, 0x3d4ccccd    # 0.05f
    mul-float v6, v6, v1
    add-float v6, v3, v6
    new-instance p0, Landroid/graphics/RectF;
    invoke-direct {p0, v2, v3, v5, v6}, Landroid/graphics/RectF;-><init>(FFFF)V
    return-object p0
.end method

.method private edPillPlus()Landroid/graphics/RectF;
    .registers 9
    invoke-virtual {p0}, LORG;->getWidth()I
    move-result v0
    int-to-float v0, v0
    invoke-virtual {p0}, LORG;->getHeight()I
    move-result v1
    int-to-float v1, v1
    const v2, 0x3f6147ae    # 0.88f
    mul-float v2, v2, v0
    const v3, 0x3ca3d70a    # 0.02f
    mul-float v3, v3, v1
    const v4, 0x3e19999a    # 0.15f
    mul-float v4, v4, v0
    add-float v5, v2, v4
    const v6, 0x3d4ccccd    # 0.05f
    mul-float v6, v6, v1
    add-float v6, v3, v6
    new-instance p0, Landroid/graphics/RectF;
    invoke-direct {p0, v2, v3, v5, v6}, Landroid/graphics/RectF;-><init>(FFFF)V
    return-object p0
.end method

.method private edScale(IF)V
    .registers 9
    iget-object v0, p0, LORG;->btnRects:[Landroid/graphics/RectF;
    aget-object v0, v0, p1
    iget v1, v0, Landroid/graphics/RectF;->left:F
    iget v2, v0, Landroid/graphics/RectF;->right:F
    iget v3, v0, Landroid/graphics/RectF;->top:F
    iget v4, v0, Landroid/graphics/RectF;->bottom:F
    const/high16 v5, 0x40000000    # 2.0f
    add-float v0, v1, v2
    div-float v0, v0, v5
    add-float v3, v3, v4
    div-float v3, v3, v5
    sub-float v2, v2, v1
    div-float v2, v2, v5
    mul-float v2, v2, p2
    invoke-direct {p0, p1, v0, v3, v2}, LORG;->setRect(IFFF)V
    return-void
.end method

.method private edPillPM(Landroid/view/MotionEvent;)I
    .registers 8
    invoke-virtual {p1}, Landroid/view/MotionEvent;->getActionMasked()I
    move-result v0
    if-nez v0, :pm_no
    sget-boolean v0, LORG;->edMode:Z
    if-eqz v0, :pm_no
    sget v0, LORG;->edSel:I
    const/4 v1, -0x1
    if-eq v0, v1, :pm_no
    const/4 v1, 0x0
    invoke-virtual {p1, v1}, Landroid/view/MotionEvent;->getX(I)F
    move-result v2
    invoke-virtual {p1, v1}, Landroid/view/MotionEvent;->getY(I)F
    move-result v3
    invoke-direct {p0}, LORG;->edPillMinus()Landroid/graphics/RectF;
    move-result-object v4
    invoke-virtual {v4, v2, v3}, Landroid/graphics/RectF;->contains(FF)Z
    move-result v4
    if-eqz v4, :pm_chkplus
    const v5, 0x3f666666    # 0.9f
    invoke-direct {p0, v0, v5}, LORG;->edScale(IF)V
    invoke-virtual {p0}, LORG;->invalidate()V
    const/4 v0, 0x1
    return v0
    :pm_chkplus
    invoke-direct {p0}, LORG;->edPillPlus()Landroid/graphics/RectF;
    move-result-object v4
    invoke-virtual {v4, v2, v3}, Landroid/graphics/RectF;->contains(FF)Z
    move-result v4
    if-eqz v4, :pm_no
    const v5, 0x3f8ccccd    # 1.1f
    invoke-direct {p0, v0, v5}, LORG;->edScale(IF)V
    invoke-virtual {p0}, LORG;->invalidate()V
    const/4 v0, 0x1
    return v0
    :pm_no
    const/4 v0, 0x0
    return v0
.end method
'''.replace("LORG;", CLS)
s = s.rstrip() + "\n" + NEW + "\n"

open(p, "w", encoding="utf-8").write(s)
print("patched OK")
