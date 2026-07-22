#!/usr/bin/env python3
# v71: add MENU(Tab=0x8) + MAP(M=0x88) small top-center buttons + amber-glass restyle,
# built on the USER'S CLEAN ORIGINAL GamepadOverlay (crash-free base). Register-safe.
#
# CRITICAL register rule (the v63 crash cause): in smali, method params occupy the HIGHEST
# registers. In a ".registers N" method with P params (incl 'this'), params are v(N-P)..v(N-1).
# So scratch must stay strictly BELOW v(N-P). All new methods below follow this.
#
# Hooks:
#  - onDraw ENTRY: call navDraw(Canvas) (p1 = Canvas guaranteed valid at entry).
#  - onTouchEvent ENTRY: call navHandle(MotionEvent); if it returns 1, consume.
#  - init end: call restyle() to apply amber-glass paints (colors/alpha/stroke only).
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
C = "Lorg/cocos2dx/cpp/GamepadOverlay;"

# ---------- 1. onDraw ENTRY hook ----------
od = ".method protected onDraw(Landroid/graphics/Canvas;)V\n    .registers 14\n\n    .line 366\n    invoke-super {p0, p1}, Landroid/view/View;->onDraw(Landroid/graphics/Canvas;)V\n"
assert s.count(od) == 1, "onDraw entry anchor missing/not unique"
s = s.replace(od,
    ".method protected onDraw(Landroid/graphics/Canvas;)V\n    .registers 14\n\n"
    "    invoke-direct {p0, p1}, " + C + "->navDraw(Landroid/graphics/Canvas;)V\n\n"
    "    .line 366\n    invoke-super {p0, p1}, Landroid/view/View;->onDraw(Landroid/graphics/Canvas;)V\n", 1)

# ---------- 2. onTouchEvent ENTRY hook ----------
ote = ".method public onTouchEvent(Landroid/view/MotionEvent;)Z\n    .registers 13\n\n    .line 745\n    invoke-virtual {p1}, Landroid/view/MotionEvent;->getActionMasked()I\n"
assert s.count(ote) == 1, "onTouchEvent entry anchor missing/not unique"
s = s.replace(ote,
    ".method public onTouchEvent(Landroid/view/MotionEvent;)Z\n    .registers 13\n\n"
    "    invoke-direct {p0, p1}, " + C + "->navHandle(Landroid/view/MotionEvent;)I\n"
    "    move-result v0\n"
    "    const/4 v1, 0x1\n"
    "    if-ne v0, v1, :nav_pass\n"
    "    return v1\n"
    "    :nav_pass\n\n"
    "    .line 745\n    invoke-virtual {p1}, Landroid/view/MotionEvent;->getActionMasked()I\n", 1)

# ---------- 3. init end hook: restyle() ----------
# init ends with setBackgroundColor then return-void (per original). Anchor on that pair.
init_tail = "->setBackgroundColor(I)V\n\n    .line 249\n    return-void\n.end method\n"
if init_tail in s:
    s = s.replace(init_tail,
        "->setBackgroundColor(I)V\n\n    invoke-direct {p0}, " + C + "->restyle()V\n\n    .line 249\n    return-void\n.end method\n", 1)
else:
    # fallback: hook first return-void of init(Landroid/content/Context;)V
    m = "-><init>"  # guard
    import re
    pat = re.compile(r"(\.method private init\(Landroid/content/Context;\)V.*?)\n    return-void\n\.end method\n", re.S)
    def repl(mm):
        return mm.group(1) + "\n    invoke-direct {p0}, " + C + "->restyle()V\n    return-void\n.end method\n"
    s2 = pat.sub(repl, s, count=1)
    assert s2 != s, "could not hook init end"
    s = s2

# ---------- 4. new methods ----------
# navPill(I): id 0 = MENU (0.40w), id 1 = MAP (0.505w). SMALL: width 0.095w, height 0.048h, top 0.012h.
# .registers 10, 2 params (this=v8, id=v9) -> scratch v0..v7 OK.
# navDraw(Canvas): .registers 10, params this=v8, canvas=v9 -> scratch v0..v7.
# navHandle(MotionEvent): .registers 10, params this=v8, ev=v9 -> scratch v0..v7.
# navPulse(I): .registers 6, params this=v4, code=v5 -> scratch v0..v3.
# restyle(): .registers 6, param this=v5 -> scratch v0..v4.
NEW = r'''
.method private navPill(I)Landroid/graphics/RectF;
    .registers 10
    invoke-virtual {p0}, LORG;->getWidth()I
    move-result v0
    int-to-float v0, v0
    invoke-virtual {p0}, LORG;->getHeight()I
    move-result v1
    int-to-float v1, v1
    const v2, 0x3ecccccd    # 0.40f (MENU left)
    const/4 v7, 0x0
    if-eq p1, v7, :np_have
    const v2, 0x3f0147ae    # 0.505f (MAP left)
    :np_have
    mul-float v2, v2, v0
    const v3, 0x3c449ba6    # 0.012f (top)
    mul-float v3, v3, v1
    const v4, 0x3dc28f5c    # 0.095f (width)
    mul-float v4, v4, v0
    add-float v5, v2, v4
    const v6, 0x3d449ba6    # 0.048f (height)
    mul-float v6, v6, v1
    add-float v6, v3, v6
    new-instance v0, Landroid/graphics/RectF;
    invoke-direct {v0, v2, v3, v5, v6}, Landroid/graphics/RectF;-><init>(FFFF)V
    return-object v0
.end method

.method private navDraw(Landroid/graphics/Canvas;)V
    .registers 10
    const/4 v0, 0x0
    invoke-direct {p0, v0}, LORG;->navPill(I)Landroid/graphics/RectF;
    move-result-object v1
    iget-object v2, p0, LORG;->paintBase:Landroid/graphics/Paint;
    iget-object v3, p0, LORG;->paintOutline:Landroid/graphics/Paint;
    iget-object v4, p0, LORG;->paintLabelSmall:Landroid/graphics/Paint;
    const/high16 v5, 0x40c00000    # 6.0f corner
    invoke-virtual {p1, v1, v5, v5, v2}, Landroid/graphics/Canvas;->drawRoundRect(Landroid/graphics/RectF;FFLandroid/graphics/Paint;)V
    invoke-virtual {p1, v1, v5, v5, v3}, Landroid/graphics/Canvas;->drawRoundRect(Landroid/graphics/RectF;FFLandroid/graphics/Paint;)V
    iget v6, v1, Landroid/graphics/RectF;->left:F
    iget v7, v1, Landroid/graphics/RectF;->bottom:F
    const-string v0, "MENU"
    invoke-virtual {p1, v0, v6, v7, v4}, Landroid/graphics/Canvas;->drawText(Ljava/lang/String;FFLandroid/graphics/Paint;)V
    const/4 v0, 0x1
    invoke-direct {p0, v0}, LORG;->navPill(I)Landroid/graphics/RectF;
    move-result-object v1
    invoke-virtual {p1, v1, v5, v5, v2}, Landroid/graphics/Canvas;->drawRoundRect(Landroid/graphics/RectF;FFLandroid/graphics/Paint;)V
    invoke-virtual {p1, v1, v5, v5, v3}, Landroid/graphics/Canvas;->drawRoundRect(Landroid/graphics/RectF;FFLandroid/graphics/Paint;)V
    iget v6, v1, Landroid/graphics/RectF;->left:F
    iget v7, v1, Landroid/graphics/RectF;->bottom:F
    const-string v0, "MAP"
    invoke-virtual {p1, v0, v6, v7, v4}, Landroid/graphics/Canvas;->drawText(Ljava/lang/String;FFLandroid/graphics/Paint;)V
    return-void
.end method

.method private navHandle(Landroid/view/MotionEvent;)I
    .registers 10
    invoke-virtual {p1}, Landroid/view/MotionEvent;->getActionMasked()I
    move-result v0
    if-nez v0, :nav_no
    const/4 v0, 0x0
    invoke-virtual {p1, v0}, Landroid/view/MotionEvent;->getX(I)F
    move-result v2
    invoke-virtual {p1, v0}, Landroid/view/MotionEvent;->getY(I)F
    move-result v3
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
    .registers 6
    const/4 v0, 0x1
    invoke-direct {p0, p1, v0}, LORG;->rawInject(IZ)V
    const/4 v0, 0x0
    invoke-direct {p0, p1, v0}, LORG;->rawInject(IZ)V
    invoke-virtual {p0}, LORG;->invalidate()V
    return-void
.end method

.method private restyle()V
    .registers 6
    iget-object v0, p0, LORG;->paintBase:Landroid/graphics/Paint;
    const/16 v1, 0x26
    const/16 v2, 0x1a
    const/16 v3, 0x12
    const/16 v4, 0x8
    invoke-static {v1, v2, v3, v4}, Landroid/graphics/Color;->argb(IIII)I
    move-result v1
    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setColor(I)V
    iget-object v0, p0, LORG;->paintOutline:Landroid/graphics/Paint;
    const/16 v1, 0xeb
    const/16 v2, 0xff
    const/16 v3, 0xbe
    const/16 v4, 0x5a
    invoke-static {v1, v2, v3, v4}, Landroid/graphics/Color;->argb(IIII)I
    move-result v1
    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setColor(I)V
    iget-object v0, p0, LORG;->paintLabelSmall:Landroid/graphics/Paint;
    const/16 v1, 0xff
    const/16 v2, 0xff
    const/16 v3, 0xf5
    const/16 v4, 0xdc
    invoke-static {v1, v2, v3, v4}, Landroid/graphics/Color;->argb(IIII)I
    move-result v1
    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setColor(I)V
    return-void
.end method
'''.replace("LORG;", C)
s = s.rstrip() + "\n" + NEW + "\n"

open(p, "w", encoding="utf-8").write(s)
print("patched OK")
