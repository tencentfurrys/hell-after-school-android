#!/usr/bin/env python3
# v63: add two always-on top-bar buttons MENU (Tab) and MAP (M), styled to fit FOBS.
# Uses the proven "pill" pattern (like the editor's EDIT/SAVE pills) so we do NOT touch the
# fragile 14-entry button arrays / layout / hit loops -> no VerifyError or index risk.
# - Draw: hook edDraw-style pills at onDraw ENTRY (Canvas reg guaranteed valid there).
# - Touch: hit-test at onTouchEvent ENTRY (before edit handling); on DOWN fire a down+up
#   key pulse via nativeInjectCocos2dKey. Tab=0x8 (menu), M=0x88 (map) -- cocos2d codes
#   triangulated from existing constants (SHIFT=0xc, CTRL=0xe, SPACE=0x3b, arrows 0x1a-0x1d;
#   letters read lowercase e.g. 'a'=0x7c). Amber-glass style matches v62.
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
CLS = "Lorg/cocos2dx/cpp/GamepadOverlay;"

# --- 1. onDraw ENTRY: draw the two nav pills first ---
od = ".method protected onDraw(Landroid/graphics/Canvas;)V\n    .registers 14\n\n    invoke-direct {p0, p1}, " + CLS + "->edDraw(Landroid/graphics/Canvas;)V\n"
assert s.count(od) == 1, "onDraw entry anchor not found/unique"
s = s.replace(od, od + "\n    invoke-direct {p0, p1}, " + CLS + "->navDraw(Landroid/graphics/Canvas;)V\n", 1)

# --- 2. onTouchEvent ENTRY: consume nav taps before anything else ---
ote = ".method public onTouchEvent(Landroid/view/MotionEvent;)Z\n    .registers 13\n\n    invoke-direct {p0, p1}, " + CLS + "->edHandle(Landroid/view/MotionEvent;)I\n"
assert s.count(ote) == 1, "onTouchEvent entry anchor not found/unique"
nav_prologue = (
    ".method public onTouchEvent(Landroid/view/MotionEvent;)Z\n    .registers 13\n\n"
    "    invoke-direct {p0, p1}, " + CLS + "->navHandle(Landroid/view/MotionEvent;)I\n"
    "    move-result v0\n"
    "    const/4 v1, 0x1\n"
    "    if-ne v0, v1, :nav_pass\n"
    "    const/4 v0, 0x1\n"
    "    return v0\n"
    "    :nav_pass\n"
    "    invoke-direct {p0, p1}, " + CLS + "->edHandle(Landroid/view/MotionEvent;)I\n"
)
s = s.replace(ote, nav_prologue, 1)

# --- 3. append helper methods ---
# Pills: top-center row. MENU at 0.36w, MAP at 0.52w; width 0.12w, height 0.06h, top 0.01h.
NEW = r'''
.method private navPill(I)Landroid/graphics/RectF;
    .registers 10
    invoke-virtual {p0}, LORG;->getWidth()I
    move-result v0
    int-to-float v0, v0
    invoke-virtual {p0}, LORG;->getHeight()I
    move-result v1
    int-to-float v1, v1
    const v2, 0x3eb851ec    # 0.36f (MENU left)
    const/4 v7, 0x0
    if-ne p1, v7, :np_x
    const v2, 0x3f051eb8    # 0.52f (MAP left)
    :np_x
    mul-float v2, v2, v0
    const v3, 0x3c23d70a    # 0.01f (top)
    mul-float v3, v3, v1
    const v4, 0x3df5c28f    # 0.12f (width)
    mul-float v4, v4, v0
    add-float v5, v2, v4
    const v6, 0x3d75c28f    # 0.06f (height)
    mul-float v6, v6, v1
    add-float v6, v3, v6
    new-instance p0, Landroid/graphics/RectF;
    invoke-direct {p0, v2, v3, v5, v6}, Landroid/graphics/RectF;-><init>(FFFF)V
    return-object p0
.end method

.method private navDraw(Landroid/graphics/Canvas;)V
    .registers 8
    iget-object v2, p0, LORG;->paintBase:Landroid/graphics/Paint;
    iget-object v3, p0, LORG;->paintOutline:Landroid/graphics/Paint;
    iget-object v6, p0, LORG;->paintLabelSmall:Landroid/graphics/Paint;
    const/16 v7, 0x8    # rounded corner radius
    int-to-float v7, v7
    # MENU pill
    const/4 v0, 0x0
    invoke-direct {p0, v0}, LORG;->navPill(I)Landroid/graphics/RectF;
    move-result-object v1
    invoke-virtual {p1, v1, v7, v7, v2}, Landroid/graphics/Canvas;->drawRoundRect(Landroid/graphics/RectF;FFLandroid/graphics/Paint;)V
    invoke-virtual {p1, v1, v7, v7, v3}, Landroid/graphics/Canvas;->drawRoundRect(Landroid/graphics/RectF;FFLandroid/graphics/Paint;)V
    iget v4, v1, Landroid/graphics/RectF;->left:F
    iget v5, v1, Landroid/graphics/RectF;->bottom:F
    const-string v0, "MENU"
    invoke-virtual {p1, v0, v4, v5, v6}, Landroid/graphics/Canvas;->drawText(Ljava/lang/String;FFLandroid/graphics/Paint;)V
    # MAP pill
    const/4 v0, 0x1
    invoke-direct {p0, v0}, LORG;->navPill(I)Landroid/graphics/RectF;
    move-result-object v1
    invoke-virtual {p1, v1, v7, v7, v2}, Landroid/graphics/Canvas;->drawRoundRect(Landroid/graphics/RectF;FFLandroid/graphics/Paint;)V
    invoke-virtual {p1, v1, v7, v7, v3}, Landroid/graphics/Canvas;->drawRoundRect(Landroid/graphics/RectF;FFLandroid/graphics/Paint;)V
    iget v4, v1, Landroid/graphics/RectF;->left:F
    iget v5, v1, Landroid/graphics/RectF;->bottom:F
    const-string v0, "MAP"
    invoke-virtual {p1, v0, v4, v5, v6}, Landroid/graphics/Canvas;->drawText(Ljava/lang/String;FFLandroid/graphics/Paint;)V
    return-void
.end method

.method private navHandle(Landroid/view/MotionEvent;)I
    .registers 8
    invoke-virtual {p1}, Landroid/view/MotionEvent;->getActionMasked()I
    move-result v0
    if-nez v0, :nav_no
    sget-boolean v0, LORG;->edMode:Z
    if-nez v0, :nav_no
    const/4 v0, 0x0
    invoke-virtual {p1, v0}, Landroid/view/MotionEvent;->getX(I)F
    move-result v2
    invoke-virtual {p1, v0}, Landroid/view/MotionEvent;->getY(I)F
    move-result v3
    # MENU?
    const/4 v0, 0x0
    invoke-direct {p0, v0}, LORG;->navPill(I)Landroid/graphics/RectF;
    move-result-object v4
    invoke-virtual {v4, v2, v3}, Landroid/graphics/RectF;->contains(FF)Z
    move-result v4
    if-eqz v4, :nav_chkmap
    const/16 v0, 0x8
    invoke-direct {p0, v0}, LORG;->navPulse(I)V
    const/4 v0, 0x1
    return v0
    :nav_chkmap
    const/4 v0, 0x1
    invoke-direct {p0, v0}, LORG;->navPill(I)Landroid/graphics/RectF;
    move-result-object v4
    invoke-virtual {v4, v2, v3}, Landroid/graphics/RectF;->contains(FF)Z
    move-result v4
    if-eqz v4, :nav_no
    const/16 v0, 0x88
    invoke-direct {p0, v0}, LORG;->navPulse(I)V
    const/4 v0, 0x1
    return v0
    :nav_no
    const/4 v0, 0x0
    return v0
.end method

.method private navPulse(I)V
    .registers 4
    const/4 v0, 0x1
    invoke-static {p1, v0}, LORG;->nativeInjectCocos2dKey(IZ)V
    const/4 v0, 0x0
    invoke-static {p1, v0}, LORG;->nativeInjectCocos2dKey(IZ)V
    invoke-virtual {p0}, LORG;->invalidate()V
    return-void
.end method
'''.replace("LORG;", CLS)
s = s.rstrip() + "\n" + NEW + "\n"

open(p, "w", encoding="utf-8").write(s)
print("patched OK")
