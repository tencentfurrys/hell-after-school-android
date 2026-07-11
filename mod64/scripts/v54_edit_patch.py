#!/usr/bin/env python3
# v54 control-editor patcher. Runs against REAL GamepadOverlay.smali.
# Adds an on-screen edit mode: tap EDIT pill to toggle; in edit mode drag a
# button to move it, pinch it with two fingers to resize; tap SAVE to dump the
# full layout to hell_runtime.log. Gameplay input is untouched when not editing.
import sys, re

path = sys.argv[1]
s = open(path, encoding="utf-8").read()
CLS = "Lorg/cocos2dx/cpp/GamepadOverlay;"

# ---- 1. static state fields (defaults false/0 are fine; DOWN always sets edSel) ----
if "edMode:Z" not in s:
    anchor = ".field private static diagFile:Ljava/io/File;\n"
    assert anchor in s, "diagFile field anchor missing"
    s = s.replace(anchor, anchor +
        ".field private static edMode:Z\n"
        ".field private static edSel:I\n", 1)

# ---- 2. onTouchEvent prologue: let the editor consume the event first ----
# .registers 13 -> this=v11, event=v12 ; v0/v1 are locals reused right after.
ote = ".method public onTouchEvent(Landroid/view/MotionEvent;)Z\n    .registers 13\n"
assert ote in s, "onTouchEvent signature/regs not as expected"
prologue = ote + (
    "    invoke-direct {p0, p1}, " + CLS + "->edHandle(Landroid/view/MotionEvent;)I\n"
    "    move-result v0\n"
    "    const/4 v1, 0x1\n"
    "    if-ne v0, v1, :ed_passthru\n"
    "    const/4 v0, 0x1\n"
    "    return v0\n"
    "    :ed_passthru\n"
)
s = s.replace(ote, prologue, 1)

# ---- 3. onDraw epilogue: draw EDIT/SAVE pills + selected outline ----
# insert before the final 'return-void' of onDraw.
draw_marker = "    .line 407\n    return-void\n.end method\n\n.method protected onSizeChanged(IIII)V"
assert draw_marker in s, "onDraw tail anchor missing"
draw_call = (
    "    invoke-direct {p0, p1}, " + CLS + "->edDraw(Landroid/graphics/Canvas;)V\n"
    "    .line 407\n    return-void\n.end method\n\n.method protected onSizeChanged(IIII)V"
)
s = s.replace(draw_marker, draw_call, 1)

# ---- 4. new methods appended at end of class ----
# Insert before the final line of file (last .end method). We append fresh methods.
NEW = r'''
.method private edPillEdit()Landroid/graphics/RectF;
    .registers 9
    invoke-virtual {p0}, LORG;->getWidth()I
    move-result v0
    int-to-float v0, v0
    invoke-virtual {p0}, LORG;->getHeight()I
    move-result v1
    int-to-float v1, v1
    const v2, 0x3ee66666    # 0.45f
    mul-float v2, v2, v0
    const v3, 0x3ca3d70a    # 0.02f
    mul-float v3, v3, v1
    const v4, 0x3e19999a    # 0.15f
    mul-float v4, v4, v0
    add-float v5, v2, v4
    const v6, 0x3d4ccccd    # 0.05f
    mul-float v6, v6, v1
    add-float v6, v3, v6
    new-instance v8, Landroid/graphics/RectF;
    invoke-direct {v8, v2, v3, v5, v6}, Landroid/graphics/RectF;-><init>(FFFF)V
    return-object v8
.end method

.method private edPillSave()Landroid/graphics/RectF;
    .registers 9
    invoke-virtual {p0}, LORG;->getWidth()I
    move-result v0
    int-to-float v0, v0
    invoke-virtual {p0}, LORG;->getHeight()I
    move-result v1
    int-to-float v1, v1
    const v2, 0x3f19999a    # 0.6f
    mul-float v2, v2, v0
    const v3, 0x3ca3d70a    # 0.02f
    mul-float v3, v3, v1
    const v4, 0x3e19999a    # 0.15f
    mul-float v4, v4, v0
    add-float v5, v2, v4
    const v6, 0x3d4ccccd    # 0.05f
    mul-float v6, v6, v1
    add-float v6, v3, v6
    new-instance v8, Landroid/graphics/RectF;
    invoke-direct {v8, v2, v3, v5, v6}, Landroid/graphics/RectF;-><init>(FFFF)V
    return-object v8
.end method

.method private edNearest(FF)I
    .registers 12
    const/4 v0, -0x1
    const v1, 0x7f7fffff    # Float.MAX
    const/4 v2, 0x0
    :ed_loop
    const/16 v3, 0xe
    if-ge v2, v3, :ed_done
    const/16 v3, 0xb
    if-eq v2, v3, :ed_next
    iget-object v3, p0, LORG;->btnRects:[Landroid/graphics/RectF;
    aget-object v3, v3, v2
    iget v4, v3, Landroid/graphics/RectF;->left:F
    iget v5, v3, Landroid/graphics/RectF;->right:F
    add-float/2addr v4, v5
    const/high16 v5, 0x40000000    # 2.0
    div-float/2addr v4, v5
    iget v6, v3, Landroid/graphics/RectF;->top:F
    iget v7, v3, Landroid/graphics/RectF;->bottom:F
    add-float/2addr v6, v7
    div-float/2addr v6, v5
    const v5, -0x39e00000    # -10240.0 (offscreen sentinel)
    cmpg-float v7, v4, v5
    if-ltz v7, :ed_next
    sub-float v7, p1, v4
    sub-float v8, p2, v6
    mul-float/2addr v7, v7
    mul-float/2addr v8, v8
    add-float/2addr v7, v8
    cmpg-float v8, v7, v1
    if-gez v8, :ed_next
    move v1, v7
    move v0, v2
    :ed_next
    add-int/lit8 v2, v2, 0x1
    goto :ed_loop
    :ed_done
    return v0
.end method

.method private edRadius(I)F
    .registers 5
    iget-object v0, p0, LORG;->btnRects:[Landroid/graphics/RectF;
    aget-object v0, v0, p1
    iget v1, v0, Landroid/graphics/RectF;->right:F
    iget v2, v0, Landroid/graphics/RectF;->left:F
    sub-float/2addr v1, v2
    const/high16 v2, 0x40000000    # 2.0
    div-float/2addr v1, v2
    return v1
.end method

.method private edHandle(Landroid/view/MotionEvent;)I
    .registers 16
    invoke-virtual {p1}, Landroid/view/MotionEvent;->getActionMasked()I
    move-result v0
    const/4 v1, 0x0
    invoke-virtual {p1, v1}, Landroid/view/MotionEvent;->getX(I)F
    move-result v2
    invoke-virtual {p1, v1}, Landroid/view/MotionEvent;->getY(I)F
    move-result v3
    # pills only on DOWN
    if-nez v0, :ed_editactive
    invoke-direct {p0}, LORG;->edPillEdit()Landroid/graphics/RectF;
    move-result-object v4
    invoke-virtual {v4, v2, v3}, Landroid/graphics/RectF;->contains(FF)Z
    move-result v4
    if-eqz v4, :ed_chksave
    sget-boolean v5, LORG;->edMode:Z
    if-nez v5, :ed_turnoff
    const/4 v5, 0x1
    sput-boolean v5, LORG;->edMode:Z
    const-string v6, "EDITMODE on"
    invoke-direct {p0, v6}, LORG;->logD(Ljava/lang/String;)V
    invoke-virtual {p0}, LORG;->invalidate()V
    const/4 v0, 0x1
    return v0
    :ed_turnoff
    sput-boolean v1, LORG;->edMode:Z
    const-string v6, "EDITMODE off"
    invoke-direct {p0, v6}, LORG;->logD(Ljava/lang/String;)V
    invoke-virtual {p0}, LORG;->invalidate()V
    const/4 v0, 0x1
    return v0
    :ed_chksave
    sget-boolean v5, LORG;->edMode:Z
    if-eqz v5, :ed_editactive
    invoke-direct {p0}, LORG;->edPillSave()Landroid/graphics/RectF;
    move-result-object v4
    invoke-virtual {v4, v2, v3}, Landroid/graphics/RectF;->contains(FF)Z
    move-result v4
    if-eqz v4, :ed_editactive
    invoke-direct {p0}, LORG;->edExport()V
    const/4 v0, 0x1
    return v0
    :ed_editactive
    sget-boolean v4, LORG;->edMode:Z
    if-nez v4, :ed_on
    const/4 v0, 0x0
    return v0
    :ed_on
    if-nez v0, :ed_notseldown
    invoke-direct {p0, v2, v3}, LORG;->edNearest(FF)I
    move-result v4
    sput v4, LORG;->edSel:I
    invoke-virtual {p0}, LORG;->invalidate()V
    const/4 v0, 0x1
    return v0
    :ed_notseldown
    const/4 v5, 0x2
    if-eq v0, v5, :ed_move
    const/4 v0, 0x1
    return v0
    :ed_move
    sget v4, LORG;->edSel:I
    const/4 v5, -0x1
    if-ne v4, v5, :ed_havesel
    const/4 v0, 0x1
    return v0
    :ed_havesel
    invoke-virtual {p1}, Landroid/view/MotionEvent;->getPointerCount()I
    move-result v5
    const/4 v6, 0x2
    if-lt v5, v6, :ed_single
    # pinch resize (low-register recycling)
    invoke-virtual {p1, v1}, Landroid/view/MotionEvent;->getX(I)F
    move-result v6
    invoke-virtual {p1, v1}, Landroid/view/MotionEvent;->getY(I)F
    move-result v7
    const/4 v8, 0x1
    invoke-virtual {p1, v8}, Landroid/view/MotionEvent;->getX(I)F
    move-result v8
    const/4 v9, 0x1
    invoke-virtual {p1, v9}, Landroid/view/MotionEvent;->getY(I)F
    move-result v9
    add-float v10, v6, v8
    const/high16 v11, 0x40000000    # 2.0
    div-float/2addr v10, v11
    add-float v12, v7, v9
    div-float/2addr v12, v11
    sub-float v8, v8, v6
    sub-float v9, v9, v7
    mul-float v8, v8, v8
    mul-float v9, v9, v9
    add-float v8, v8, v9
    float-to-double v6, v8
    invoke-static {v6, v7}, Ljava/lang/Math;->sqrt(D)D
    move-result-wide v6
    double-to-float v6, v6
    div-float/2addr v6, v11
    invoke-direct {p0, v4, v10, v12, v6}, LORG;->setRect(IFFF)V
    invoke-virtual {p0}, LORG;->invalidate()V
    const/4 v0, 0x1
    return v0
    :ed_single
    invoke-direct {p0, v4}, LORG;->edRadius(I)F
    move-result v5
    invoke-direct {p0, v4, v2, v3, v5}, LORG;->setRect(IFFF)V
    invoke-virtual {p0}, LORG;->invalidate()V
    const/4 v0, 0x1
    return v0
.end method

.method private edExport()V
    .registers 12
    invoke-virtual {p0}, LORG;->getWidth()I
    move-result v0
    invoke-virtual {p0}, LORG;->getHeight()I
    move-result v1
    new-instance v2, Ljava/lang/StringBuilder;
    invoke-direct {v2}, Ljava/lang/StringBuilder;-><init>()V
    const-string v3, "LAYOUT W="
    invoke-virtual {v2, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    move-result-object v2
    invoke-virtual {v2, v0}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;
    move-result-object v2
    const-string v3, " H="
    invoke-virtual {v2, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    move-result-object v2
    invoke-virtual {v2, v1}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;
    move-result-object v2
    invoke-virtual {v2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v2
    invoke-direct {p0, v2}, LORG;->logD(Ljava/lang/String;)V
    const/4 v3, 0x0
    :ex_loop
    const/16 v4, 0xe
    if-ge v3, v4, :ex_done
    iget-object v4, p0, LORG;->btnRects:[Landroid/graphics/RectF;
    aget-object v4, v4, v3
    iget v5, v4, Landroid/graphics/RectF;->left:F
    iget v6, v4, Landroid/graphics/RectF;->right:F
    add-float v7, v5, v6
    const/high16 v8, 0x40000000    # 2.0
    div-float/2addr v7, v8
    iget v9, v4, Landroid/graphics/RectF;->top:F
    iget v10, v4, Landroid/graphics/RectF;->bottom:F
    add-float v9, v9, v10
    div-float/2addr v9, v8
    sub-float v6, v6, v5
    div-float/2addr v6, v8
    new-instance v5, Ljava/lang/StringBuilder;
    invoke-direct {v5}, Ljava/lang/StringBuilder;-><init>()V
    const-string v10, "BTN "
    invoke-virtual {v5, v10}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    move-result-object v5
    invoke-virtual {v5, v3}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;
    move-result-object v5
    const-string v10, " cx="
    invoke-virtual {v5, v10}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    move-result-object v5
    invoke-virtual {v5, v7}, Ljava/lang/StringBuilder;->append(F)Ljava/lang/StringBuilder;
    move-result-object v5
    const-string v10, " cy="
    invoke-virtual {v5, v10}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    move-result-object v5
    invoke-virtual {v5, v9}, Ljava/lang/StringBuilder;->append(F)Ljava/lang/StringBuilder;
    move-result-object v5
    const-string v10, " r="
    invoke-virtual {v5, v10}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    move-result-object v5
    invoke-virtual {v5, v6}, Ljava/lang/StringBuilder;->append(F)Ljava/lang/StringBuilder;
    move-result-object v5
    invoke-virtual {v5}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v5
    invoke-direct {p0, v5}, LORG;->logD(Ljava/lang/String;)V
    add-int/lit8 v3, v3, 0x1
    goto :ex_loop
    :ex_done
    const-string v3, "LAYOUT END"
    invoke-direct {p0, v3}, LORG;->logD(Ljava/lang/String;)V
    return-void
.end method

.method private edDraw(Landroid/graphics/Canvas;)V
    .registers 9
    sget-boolean v0, LORG;->edMode:Z
    if-nez v0, :ed_drawon
    invoke-direct {p0}, LORG;->edPillEdit()Landroid/graphics/RectF;
    move-result-object v1
    iget-object v2, p0, LORG;->paintOutline:Landroid/graphics/Paint;
    invoke-virtual {p1, v1, v2}, Landroid/graphics/Canvas;->drawRect(Landroid/graphics/RectF;Landroid/graphics/Paint;)V
    iget v3, v1, Landroid/graphics/RectF;->left:F
    iget v4, v1, Landroid/graphics/RectF;->bottom:F
    const-string v5, "EDIT"
    iget-object v6, p0, LORG;->paintLabelSmall:Landroid/graphics/Paint;
    invoke-virtual {p1, v5, v3, v4, v6}, Landroid/graphics/Canvas;->drawText(Ljava/lang/String;FFLandroid/graphics/Paint;)V
    return-void
    :ed_drawon
    invoke-direct {p0}, LORG;->edPillEdit()Landroid/graphics/RectF;
    move-result-object v1
    iget-object v2, p0, LORG;->paintOutline:Landroid/graphics/Paint;
    invoke-virtual {p1, v1, v2}, Landroid/graphics/Canvas;->drawRect(Landroid/graphics/RectF;Landroid/graphics/Paint;)V
    iget v3, v1, Landroid/graphics/RectF;->left:F
    iget v4, v1, Landroid/graphics/RectF;->bottom:F
    const-string v5, "DONE"
    iget-object v6, p0, LORG;->paintLabelSmall:Landroid/graphics/Paint;
    invoke-virtual {p1, v5, v3, v4, v6}, Landroid/graphics/Canvas;->drawText(Ljava/lang/String;FFLandroid/graphics/Paint;)V
    invoke-direct {p0}, LORG;->edPillSave()Landroid/graphics/RectF;
    move-result-object v1
    invoke-virtual {p1, v1, v2}, Landroid/graphics/Canvas;->drawRect(Landroid/graphics/RectF;Landroid/graphics/Paint;)V
    iget v3, v1, Landroid/graphics/RectF;->left:F
    iget v4, v1, Landroid/graphics/RectF;->bottom:F
    const-string v5, "SAVE"
    invoke-virtual {p1, v5, v3, v4, v6}, Landroid/graphics/Canvas;->drawText(Ljava/lang/String;FFLandroid/graphics/Paint;)V
    return-void
.end method
'''
NEW = NEW.replace("LORG;", CLS)

# append new methods at very end of file
s = s.rstrip() + "\n" + NEW + "\n"

open(path, "w", encoding="utf-8").write(s)
print("patched OK")
