#!/usr/bin/env python3
# v65: remove the controls editor (per user request), from the last launch-good base v61.
# Just unhooks the editor entry points; leaves gameplay controls fully intact.
#  - onDraw: drop the edDraw(Canvas) call at method entry.
#  - onTouchEvent: drop the edHandle short-circuit block at method entry.
# The edDraw/edHandle/ed* methods remain in the class but are never called (harmless dead code),
# which keeps this a minimal, low-risk change.
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
CLS = "Lorg/cocos2dx/cpp/GamepadOverlay;"

# 1) onDraw: remove edDraw call
od_bad = (
    "    invoke-direct {p0, p1}, " + CLS + "->edDraw(Landroid/graphics/Canvas;)V\n\n"
    "    .line 366\n"
)
assert s.count(od_bad) == 1, "onDraw edDraw anchor not unique/found"
s = s.replace(od_bad, "    .line 366\n", 1)

# 2) onTouchEvent: remove the edHandle short-circuit (from edHandle call through :cond_9 label)
ote_bad = (
    "    invoke-direct {p0, p1}, " + CLS + "->edHandle(Landroid/view/MotionEvent;)I\n\n"
    "    move-result v0\n\n"
    "    const/4 v1, 0x1\n\n"
    "    if-ne v0, v1, :cond_9\n\n"
    "    const/4 v0, 0x1\n\n"
    "    return v0\n\n"
    "    .line 745\n"
    "    :cond_9\n"
)
assert s.count(ote_bad) == 1, "onTouchEvent edHandle short-circuit anchor not unique/found"
s = s.replace(ote_bad, "    .line 745\n", 1)

open(p, "w", encoding="utf-8").write(s)
print("patched OK")
