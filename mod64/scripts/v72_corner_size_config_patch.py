#!/usr/bin/env python3
# v72: build on v71 APK smali. Changes:
#  1. Move MENU -> top-LEFT corner, MAP -> top-RIGHT corner (was top-center).
#  2. Add SIZE config pill (top-center). Tap toggles config mode -> shows - / + pills.
#     - / + resize GAMEPLAY CONTROLS ONLY (scales layoutButtons min-dim by ctrlScale).
#  3. Persist ctrlScale permanently via SharedPreferences ("fobs_ctrl"/"ctrlScale").
#  4. Periwinkle-glow style to match user's mockup: translucent navy fill, bright
#     periwinkle outline, cream centered labels with a soft glow shadow.
#
# REGISTER RULE (v63 crash cause): params occupy the HIGHEST registers. In .registers N
# with P params, params are v(N-P)..v(N-1); scratch must stay strictly below v(N-P).
import sys, re
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
C = "Lorg/cocos2dx/cpp/GamepadOverlay;"

def replace_method(src, header, new_text):
    # match from header line to its .end method
    pat = re.compile(re.escape(header) + r".*?\n\.end method\n", re.S)
    m = pat.search(src)
    assert m, "method not found: " + header
    assert len(pat.findall(src)) == 1, "method not unique: " + header
    return src[:m.start()] + new_text + src[m.end():]

# ---------- 1. fields ----------
anchor = ".field private btnRadius:F\n"
assert s.count(anchor) == 1, "btnRadius field anchor"
s = s.replace(anchor,
    anchor +
    "\n.field private cfgMode:Z\n" +
    "\n.field private ctrlScale:F\n" +
    "\n.field private paintNav:Landroid/graphics/Paint;\n", 1)

# ---------- 2. navPill: 5 positions (0 MENU-left, 1 MAP-right, 2 SIZE-center, 3 minus, 4 plus) ----------
navPill = (
".method private navPill(I)Landroid/graphics/RectF;\n"
"    .registers 10\n"
"    invoke-virtual {p0}, " + C + "->getWidth()I\n"
"    move-result v0\n"
"    int-to-float v0, v0\n"
"    invoke-virtual {p0}, " + C + "->getHeight()I\n"
"    move-result v1\n"
"    int-to-float v1, v1\n"
"    const v2, 0x3ca3d70a\n"          # MENU left 0.02
"    const/4 v3, 0x1\n"
"    if-ne p1, v3, :np1\n"
"    const v2, 0x3f6147ae\n"          # MAP left 0.88
"    :np1\n"
"    const/4 v3, 0x2\n"
"    if-ne p1, v3, :np2\n"
"    const v2, 0x3ee66666\n"          # SIZE left 0.45
"    :np2\n"
"    const/4 v3, 0x3\n"
"    if-ne p1, v3, :np3\n"
"    const v2, 0x3ea3d70a\n"          # minus left 0.32
"    :np3\n"
"    const/4 v3, 0x4\n"
"    if-ne p1, v3, :np4\n"
"    const v2, 0x3f147ae1\n"          # plus left 0.58
"    :np4\n"
"    mul-float v2, v2, v0\n"          # left px
"    const v3, 0x3c75c28f\n"          # top 0.015
"    mul-float v3, v3, v1\n"
"    const v4, 0x3dcccccd\n"          # width 0.10
"    mul-float v4, v4, v0\n"
"    add-float v5, v2, v4\n"          # right
"    const v6, 0x3d4ccccd\n"          # height 0.05
"    mul-float v6, v6, v1\n"
"    add-float v6, v3, v6\n"          # bottom
"    new-instance v0, Landroid/graphics/RectF;\n"
"    invoke-direct {v0, v2, v3, v5, v6}, Landroid/graphics/RectF;-><init>(FFFF)V\n"
"    return-object v0\n"
".end method\n"
)
s = replace_method(s, ".method private navPill(I)Landroid/graphics/RectF;", navPill)

# ---------- 3. drawPill helper (centered label, periwinkle glass) ----------
drawPill = (
".method private drawPill(Landroid/graphics/Canvas;Landroid/graphics/RectF;Ljava/lang/String;)V\n"
"    .registers 11\n"
"    iget-object v0, p0, " + C + "->paintBase:Landroid/graphics/Paint;\n"
"    iget-object v1, p0, " + C + "->paintOutline:Landroid/graphics/Paint;\n"
"    iget-object v2, p0, " + C + "->paintNav:Landroid/graphics/Paint;\n"
"    const/high16 v3, 0x40c00000\n"    # 6.0f corner
"    invoke-virtual {p1, p2, v3, v3, v0}, Landroid/graphics/Canvas;->drawRoundRect(Landroid/graphics/RectF;FFLandroid/graphics/Paint;)V\n"
"    invoke-virtual {p1, p2, v3, v3, v1}, Landroid/graphics/Canvas;->drawRoundRect(Landroid/graphics/RectF;FFLandroid/graphics/Paint;)V\n"
"    iget v3, p2, Landroid/graphics/RectF;->left:F\n"
"    iget v4, p2, Landroid/graphics/RectF;->right:F\n"
"    add-float/2addr v3, v4\n"
"    const/high16 v4, 0x40000000\n"    # 2.0
"    div-float/2addr v3, v4\n"         # centerX
"    iget v4, p2, Landroid/graphics/RectF;->top:F\n"
"    iget v5, p2, Landroid/graphics/RectF;->bottom:F\n"
"    add-float/2addr v4, v5\n"
"    const/high16 v5, 0x40000000\n"
"    div-float/2addr v4, v5\n"         # centerY
"    invoke-virtual {v2}, Landroid/graphics/Paint;->getTextSize()F\n"
"    move-result v5\n"
"    const v6, 0x3eb33333\n"           # 0.35
"    mul-float v5, v5, v6\n"
"    add-float/2addr v4, v5\n"         # baseline
"    invoke-virtual {p1, p3, v3, v4, v2}, Landroid/graphics/Canvas;->drawText(Ljava/lang/String;FFLandroid/graphics/Paint;)V\n"
"    return-void\n"
".end method\n"
)

# ---------- 4. navDraw: MENU, MAP, SIZE, (+/- when cfgMode) ----------
navDraw = (
".method private navDraw(Landroid/graphics/Canvas;)V\n"
"    .registers 6\n"
"    const/4 v0, 0x0\n"
"    invoke-direct {p0, v0}, " + C + "->navPill(I)Landroid/graphics/RectF;\n"
"    move-result-object v1\n"
"    const-string v2, \"MENU\"\n"
"    invoke-direct {p0, p1, v1, v2}, " + C + "->drawPill(Landroid/graphics/Canvas;Landroid/graphics/RectF;Ljava/lang/String;)V\n"
"    const/4 v0, 0x1\n"
"    invoke-direct {p0, v0}, " + C + "->navPill(I)Landroid/graphics/RectF;\n"
"    move-result-object v1\n"
"    const-string v2, \"MAP\"\n"
"    invoke-direct {p0, p1, v1, v2}, " + C + "->drawPill(Landroid/graphics/Canvas;Landroid/graphics/RectF;Ljava/lang/String;)V\n"
"    const/4 v0, 0x2\n"
"    invoke-direct {p0, v0}, " + C + "->navPill(I)Landroid/graphics/RectF;\n"
"    move-result-object v1\n"
"    const-string v2, \"SIZE\"\n"
"    invoke-direct {p0, p1, v1, v2}, " + C + "->drawPill(Landroid/graphics/Canvas;Landroid/graphics/RectF;Ljava/lang/String;)V\n"
"    iget-boolean v0, p0, " + C + "->cfgMode:Z\n"
"    if-eqz v0, :nd_done\n"
"    const/4 v0, 0x3\n"
"    invoke-direct {p0, v0}, " + C + "->navPill(I)Landroid/graphics/RectF;\n"
"    move-result-object v1\n"
"    const-string v2, \"-\"\n"
"    invoke-direct {p0, p1, v1, v2}, " + C + "->drawPill(Landroid/graphics/Canvas;Landroid/graphics/RectF;Ljava/lang/String;)V\n"
"    const/4 v0, 0x4\n"
"    invoke-direct {p0, v0}, " + C + "->navPill(I)Landroid/graphics/RectF;\n"
"    move-result-object v1\n"
"    const-string v2, \"+\"\n"
"    invoke-direct {p0, p1, v1, v2}, " + C + "->drawPill(Landroid/graphics/Canvas;Landroid/graphics/RectF;Ljava/lang/String;)V\n"
"    :nd_done\n"
"    return-void\n"
".end method\n"
)
s = replace_method(s, ".method private navDraw(Landroid/graphics/Canvas;)V", navDraw)

# ---------- 5. navHandle: taps ----------
navHandle = (
".method private navHandle(Landroid/view/MotionEvent;)I\n"
"    .registers 10\n"
"    invoke-virtual {p1}, Landroid/view/MotionEvent;->getActionMasked()I\n"
"    move-result v0\n"
"    if-nez v0, :nh_no\n"
"    const/4 v0, 0x0\n"
"    invoke-virtual {p1, v0}, Landroid/view/MotionEvent;->getX(I)F\n"
"    move-result v2\n"
"    invoke-virtual {p1, v0}, Landroid/view/MotionEvent;->getY(I)F\n"
"    move-result v3\n"
# MENU (0) -> Tab 0x8
"    const/4 v0, 0x0\n"
"    invoke-direct {p0, v0}, " + C + "->navPill(I)Landroid/graphics/RectF;\n"
"    move-result-object v4\n"
"    invoke-virtual {v4, v2, v3}, Landroid/graphics/RectF;->contains(FF)Z\n"
"    move-result v4\n"
"    if-eqz v4, :nh_map\n"
"    const/16 v0, 0x8\n"
"    invoke-direct {p0, v0}, " + C + "->navPulse(I)V\n"
"    const/4 v0, 0x1\n"
"    return v0\n"
"    :nh_map\n"
# MAP (1) -> M 0x88
"    const/4 v0, 0x1\n"
"    invoke-direct {p0, v0}, " + C + "->navPill(I)Landroid/graphics/RectF;\n"
"    move-result-object v4\n"
"    invoke-virtual {v4, v2, v3}, Landroid/graphics/RectF;->contains(FF)Z\n"
"    move-result v4\n"
"    if-eqz v4, :nh_cfg\n"
"    const/16 v0, 0x88\n"
"    invoke-direct {p0, v0}, " + C + "->navPulse(I)V\n"
"    const/4 v0, 0x1\n"
"    return v0\n"
"    :nh_cfg\n"
# SIZE (2) -> toggle cfgMode
"    const/4 v0, 0x2\n"
"    invoke-direct {p0, v0}, " + C + "->navPill(I)Landroid/graphics/RectF;\n"
"    move-result-object v4\n"
"    invoke-virtual {v4, v2, v3}, Landroid/graphics/RectF;->contains(FF)Z\n"
"    move-result v4\n"
"    if-eqz v4, :nh_minus\n"
"    iget-boolean v0, p0, " + C + "->cfgMode:Z\n"
"    xor-int/lit8 v0, v0, 0x1\n"
"    iput-boolean v0, p0, " + C + "->cfgMode:Z\n"
"    invoke-virtual {p0}, " + C + "->invalidate()V\n"
"    const/4 v0, 0x1\n"
"    return v0\n"
"    :nh_minus\n"
# minus (3) only in cfgMode -> *0.9
"    iget-boolean v0, p0, " + C + "->cfgMode:Z\n"
"    if-eqz v0, :nh_no\n"
"    const/4 v0, 0x3\n"
"    invoke-direct {p0, v0}, " + C + "->navPill(I)Landroid/graphics/RectF;\n"
"    move-result-object v4\n"
"    invoke-virtual {v4, v2, v3}, Landroid/graphics/RectF;->contains(FF)Z\n"
"    move-result v4\n"
"    if-eqz v4, :nh_plus\n"
"    const v0, 0x3f666666\n"          # 0.9f
"    invoke-direct {p0, v0}, " + C + "->applyScale(F)V\n"
"    const/4 v0, 0x1\n"
"    return v0\n"
"    :nh_plus\n"
# plus (4) only in cfgMode -> *1.1
"    const/4 v0, 0x4\n"
"    invoke-direct {p0, v0}, " + C + "->navPill(I)Landroid/graphics/RectF;\n"
"    move-result-object v4\n"
"    invoke-virtual {v4, v2, v3}, Landroid/graphics/RectF;->contains(FF)Z\n"
"    move-result v4\n"
"    if-eqz v4, :nh_no\n"
"    const v0, 0x3f8ccccd\n"          # 1.1f
"    invoke-direct {p0, v0}, " + C + "->applyScale(F)V\n"
"    const/4 v0, 0x1\n"
"    return v0\n"
"    :nh_no\n"
"    const/4 v0, 0x0\n"
"    return v0\n"
".end method\n"
)
s = replace_method(s, ".method private navHandle(Landroid/view/MotionEvent;)I", navHandle)

# ---------- 6. applyScale / loadScale / saveScale ----------
applyScale = (
".method private applyScale(F)V\n"
"    .registers 6\n"
"    iget v0, p0, " + C + "->ctrlScale:F\n"
"    mul-float v0, v0, p1\n"
"    const/high16 v1, 0x3f000000\n"   # 0.5f
"    cmpg-float v2, v0, v1\n"
"    if-gez v2, :as_lo\n"
"    move v0, v1\n"
"    :as_lo\n"
"    const/high16 v1, 0x40000000\n"   # 2.0f
"    cmpl-float v2, v0, v1\n"
"    if-lez v2, :as_hi\n"
"    move v0, v1\n"
"    :as_hi\n"
"    iput v0, p0, " + C + "->ctrlScale:F\n"
"    invoke-virtual {p0}, " + C + "->getWidth()I\n"
"    move-result v0\n"
"    invoke-virtual {p0}, " + C + "->getHeight()I\n"
"    move-result v1\n"
"    invoke-direct {p0, v0, v1}, " + C + "->layoutButtons(II)V\n"
"    invoke-direct {p0}, " + C + "->saveScale()V\n"
"    invoke-virtual {p0}, " + C + "->invalidate()V\n"
"    return-void\n"
".end method\n"
)
loadScale = (
".method private loadScale()V\n"
"    .registers 4\n"
"    invoke-virtual {p0}, " + C + "->getContext()Landroid/content/Context;\n"
"    move-result-object v0\n"
"    const-string v1, \"fobs_ctrl\"\n"
"    const/4 v2, 0x0\n"
"    invoke-virtual {v0, v1, v2}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;\n"
"    move-result-object v0\n"
"    const-string v1, \"ctrlScale\"\n"
"    const/high16 v2, 0x3f800000\n"   # 1.0f default
"    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences;->getFloat(Ljava/lang/String;F)F\n"
"    move-result v0\n"
"    iput v0, p0, " + C + "->ctrlScale:F\n"
"    return-void\n"
".end method\n"
)
saveScale = (
".method private saveScale()V\n"
"    .registers 4\n"
"    invoke-virtual {p0}, " + C + "->getContext()Landroid/content/Context;\n"
"    move-result-object v0\n"
"    const-string v1, \"fobs_ctrl\"\n"
"    const/4 v2, 0x0\n"
"    invoke-virtual {v0, v1, v2}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;\n"
"    move-result-object v0\n"
"    invoke-interface {v0}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;\n"
"    move-result-object v0\n"
"    const-string v1, \"ctrlScale\"\n"
"    iget v2, p0, " + C + "->ctrlScale:F\n"
"    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences$Editor;->putFloat(Ljava/lang/String;F)Landroid/content/SharedPreferences$Editor;\n"
"    move-result-object v0\n"
"    invoke-interface {v0}, Landroid/content/SharedPreferences$Editor;->apply()V\n"
"    return-void\n"
".end method\n"
)

# ---------- 7. replace restyle (periwinkle glass + paintNav) ----------
restyle = (
".method private restyle()V\n"
"    .registers 6\n"
# paintBase: translucent navy
"    iget-object v0, p0, " + C + "->paintBase:Landroid/graphics/Paint;\n"
"    const/16 v1, 0x38\n"
"    const/16 v2, 0x14\n"
"    const/16 v3, 0x16\n"
"    const/16 v4, 0x2c\n"
"    invoke-static {v1, v2, v3, v4}, Landroid/graphics/Color;->argb(IIII)I\n"
"    move-result v1\n"
"    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setColor(I)V\n"
# paintOutline: bright periwinkle
"    iget-object v0, p0, " + C + "->paintOutline:Landroid/graphics/Paint;\n"
"    const/16 v1, 0xff\n"
"    const/16 v2, 0xbf\n"
"    const/16 v3, 0xc4\n"
"    const/16 v4, 0xff\n"
"    invoke-static {v1, v2, v3, v4}, Landroid/graphics/Color;->argb(IIII)I\n"
"    move-result v1\n"
"    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setColor(I)V\n"
"    iget v1, p0, " + C + "->density:F\n"
"    const v2, 0x400ccccd\n"          # 2.2f stroke
"    mul-float v1, v1, v2\n"
"    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setStrokeWidth(F)V\n"
# paintNav: cream centered bold w/ glow
"    new-instance v0, Landroid/graphics/Paint;\n"
"    const/4 v1, 0x1\n"
"    invoke-direct {v0, v1}, Landroid/graphics/Paint;-><init>(I)V\n"
"    iput-object v0, p0, " + C + "->paintNav:Landroid/graphics/Paint;\n"
"    const/16 v1, 0xff\n"
"    const/16 v2, 0xff\n"
"    const/16 v3, 0xf5\n"
"    const/16 v4, 0xdc\n"
"    invoke-static {v1, v2, v3, v4}, Landroid/graphics/Color;->argb(IIII)I\n"
"    move-result v1\n"
"    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setColor(I)V\n"
"    sget-object v1, Landroid/graphics/Paint$Align;->CENTER:Landroid/graphics/Paint$Align;\n"
"    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setTextAlign(Landroid/graphics/Paint$Align;)V\n"
"    const/4 v1, 0x1\n"
"    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setFakeBoldText(Z)V\n"
"    iget v1, p0, " + C + "->density:F\n"
"    const/high16 v2, 0x41500000\n"   # 13.0f
"    mul-float v1, v1, v2\n"
"    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setTextSize(F)V\n"
# glow shadow
"    const/16 v1, 0xff\n"
"    const/16 v2, 0xbf\n"
"    const/16 v3, 0xc4\n"
"    const/16 v4, 0xff\n"
"    invoke-static {v1, v2, v3, v4}, Landroid/graphics/Color;->argb(IIII)I\n"
"    move-result v4\n"
"    iget v1, p0, " + C + "->density:F\n"
"    const/high16 v2, 0x40800000\n"   # 4.0f radius
"    mul-float v1, v1, v2\n"
"    const/4 v2, 0x0\n"
"    const/4 v3, 0x0\n"
"    invoke-virtual {v0, v1, v2, v3, v4}, Landroid/graphics/Paint;->setShadowLayer(FFFI)V\n"
"    return-void\n"
".end method\n"
)
s = replace_method(s, ".method private restyle()V", restyle)

# append new methods
s = s.rstrip() + "\n\n" + applyScale + "\n" + drawPill + "\n" + loadScale + "\n" + saveScale + "\n"

# ---------- 8. layoutButtons: scale min-dim by ctrlScale ----------
lb_anchor = "    move-result v2\n\n    int-to-float v2, v2\n\n    const v3, 0x3da7ef9e"
assert s.count(lb_anchor) == 1, "layoutButtons scale anchor"
s = s.replace(lb_anchor,
    "    move-result v2\n\n    int-to-float v2, v2\n\n"
    "    iget v3, p0, " + C + "->ctrlScale:F\n"
    "    mul-float v2, v2, v3\n\n"
    "    const v3, 0x3da7ef9e", 1)

# ---------- 9. init: call loadScale after restyle ----------
init_anchor = "    invoke-direct {v0}, " + C + "->restyle()V\n"
assert s.count(init_anchor) == 1, "init restyle anchor"
s = s.replace(init_anchor,
    init_anchor + "\n    invoke-direct {v0}, " + C + "->loadScale()V\n", 1)

open(p, "w", encoding="utf-8").write(s)
print("patched OK")
