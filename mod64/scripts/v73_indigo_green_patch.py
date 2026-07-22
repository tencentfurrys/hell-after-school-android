#!/usr/bin/env python3
# v73: color-only restyle on top of v72 smali. Applied AFTER v72_patch.py.
#  Outline  -> deep indigo-blue argb(255, 90,106,230)
#  Fill     -> semi-transparent deep indigo argb(80, 40,45,120)
#  Text+arrows (paintLabel, paintLabelSmall, paintArrow, paintNav) -> glowing light green
#                argb(255,170,255,150) + green glow shadow
# Register-safe: restyle .registers 6 (this=v5, scratch v0-v4); tintGreen .registers 8 (this=v6,paint=v7).
import sys, re
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
C = "Lorg/cocos2dx/cpp/GamepadOverlay;"

def replace_method(src, header, new_text):
    pat = re.compile(re.escape(header) + r".*?\n\.end method\n", re.S)
    m = pat.search(src)
    assert m, "method not found: " + header
    assert len(pat.findall(src)) == 1, "method not unique: " + header
    return src[:m.start()] + new_text + src[m.end():]

restyle = (
".method private restyle()V\n"
"    .registers 6\n"
# base fill: semi-transparent deep indigo argb(80,40,45,120)
"    iget-object v0, p0, " + C + "->paintBase:Landroid/graphics/Paint;\n"
"    const/16 v1, 0x50\n"
"    const/16 v2, 0x28\n"
"    const/16 v3, 0x2d\n"
"    const/16 v4, 0x78\n"
"    invoke-static {v1, v2, v3, v4}, Landroid/graphics/Color;->argb(IIII)I\n"
"    move-result v1\n"
"    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setColor(I)V\n"
# outline: deep indigo-blue argb(255,90,106,230)
"    iget-object v0, p0, " + C + "->paintOutline:Landroid/graphics/Paint;\n"
"    const/16 v1, 0xff\n"
"    const/16 v2, 0x5a\n"
"    const/16 v3, 0x6a\n"
"    const/16 v4, 0xe6\n"
"    invoke-static {v1, v2, v3, v4}, Landroid/graphics/Color;->argb(IIII)I\n"
"    move-result v1\n"
"    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setColor(I)V\n"
"    iget v1, p0, " + C + "->density:F\n"
"    const v2, 0x400ccccd\n"          # 2.2f
"    mul-float v1, v1, v2\n"
"    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setStrokeWidth(F)V\n"
# create paintNav (center, bold, sized)
"    new-instance v0, Landroid/graphics/Paint;\n"
"    const/4 v1, 0x1\n"
"    invoke-direct {v0, v1}, Landroid/graphics/Paint;-><init>(I)V\n"
"    iput-object v0, p0, " + C + "->paintNav:Landroid/graphics/Paint;\n"
"    sget-object v1, Landroid/graphics/Paint$Align;->CENTER:Landroid/graphics/Paint$Align;\n"
"    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setTextAlign(Landroid/graphics/Paint$Align;)V\n"
"    const/4 v1, 0x1\n"
"    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setFakeBoldText(Z)V\n"
"    iget v1, p0, " + C + "->density:F\n"
"    const/high16 v2, 0x41500000\n"   # 13.0f
"    mul-float v1, v1, v2\n"
"    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setTextSize(F)V\n"
# tint text+arrows glowing light green
"    iget-object v0, p0, " + C + "->paintLabel:Landroid/graphics/Paint;\n"
"    invoke-direct {p0, v0}, " + C + "->tintGreen(Landroid/graphics/Paint;)V\n"
"    iget-object v0, p0, " + C + "->paintLabelSmall:Landroid/graphics/Paint;\n"
"    invoke-direct {p0, v0}, " + C + "->tintGreen(Landroid/graphics/Paint;)V\n"
"    iget-object v0, p0, " + C + "->paintArrow:Landroid/graphics/Paint;\n"
"    invoke-direct {p0, v0}, " + C + "->tintGreen(Landroid/graphics/Paint;)V\n"
"    iget-object v0, p0, " + C + "->paintNav:Landroid/graphics/Paint;\n"
"    invoke-direct {p0, v0}, " + C + "->tintGreen(Landroid/graphics/Paint;)V\n"
"    return-void\n"
".end method\n"
)
s = replace_method(s, ".method private restyle()V", restyle)

tintGreen = (
".method private tintGreen(Landroid/graphics/Paint;)V\n"
"    .registers 8\n"
# color argb(255,170,255,150)
"    const/16 v0, 0xff\n"
"    const/16 v1, 0xaa\n"
"    const/16 v2, 0xff\n"
"    const/16 v3, 0x96\n"
"    invoke-static {v0, v1, v2, v3}, Landroid/graphics/Color;->argb(IIII)I\n"
"    move-result v0\n"
"    invoke-virtual {p1, v0}, Landroid/graphics/Paint;->setColor(I)V\n"
# green glow shadow
"    const/16 v0, 0xff\n"
"    const/16 v1, 0xaa\n"
"    const/16 v2, 0xff\n"
"    const/16 v3, 0x96\n"
"    invoke-static {v0, v1, v2, v3}, Landroid/graphics/Color;->argb(IIII)I\n"
"    move-result v4\n"
"    iget v0, p0, " + C + "->density:F\n"
"    const/high16 v1, 0x40800000\n"   # 4.0f
"    mul-float v0, v0, v1\n"
"    const/4 v1, 0x0\n"
"    const/4 v2, 0x0\n"
"    invoke-virtual {p1, v0, v1, v2, v4}, Landroid/graphics/Paint;->setShadowLayer(FFFI)V\n"
"    return-void\n"
".end method\n"
)
s = s.rstrip() + "\n\n" + tintGreen + "\n"

open(p, "w", encoding="utf-8").write(s)
print("v73 patched OK")
