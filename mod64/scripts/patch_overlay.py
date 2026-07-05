#!/usr/bin/env python3
"""
v35 controls patch for GamepadOverlay.smali.

Two edits, both inside the GamepadOverlay class:

1) Replace cocos2dToAndroidKey(I)I so every on-screen button maps to the
   correct Android keycode delivered through the (working) stdKeyInject ->
   handleKeyDown/Up channel:

     ccKey 0x93 (X / attack)          -> 29  (KEYCODE_A)
     ccKey 0x7e (C / dash)            -> 59  (KEYCODE_SHIFT_LEFT)
     ccKey 0x92 (W / switch ability)  -> 51  (KEYCODE_W)
     ccKey 0x7f (D / activate)        -> 32  (KEYCODE_D)
     ccKey 0x8e (S)                   -> 47  (KEYCODE_S)
     ccKey 0x3b (Jump)                -> 62  (KEYCODE_SPACE)
     ccKey 0x1a/0x1b/0x1c/0x1d (dpad) -> 21/22/19/20 (DPAD L/R/U/D)
     ccKey 0x91 (V / inventory)       -> 45  (KEYCODE_Q)  chord sentinel
     everything else                  -> 0

2) Prepend a chord expander to stdKeyInject(IZ)Z: when the incoming key is
   KEYCODE_Q (45), first inject SHIFT_LEFT(59) and CTRL_LEFT(113) via a
   recursive self-call, then fall through to inject Q. Because the recursive
   calls pass 59/113 (never 45) they do not re-enter the chord branch.
   Net: V press => Shift down, Ctrl down, Q down; V release => Shift up,
   Ctrl up, Q up. This realises the Shift+Ctrl+Q inventory chord.
"""
import re, sys

def die(msg):
    print("PATCH-FAIL:", msg); sys.exit(1)

path = sys.argv[1]
src = open(path, "r", encoding="utf-8").read()

# --- class descriptor (e.g. Lcom/fobs/mod/GamepadOverlay;) ---
m = re.search(r'^\.class[^\n]*\s(L[\w/$]+;)\s*$', src, re.M)
if not m:
    die("could not find .class descriptor")
CLS = m.group(1)
print("class descriptor:", CLS)

# ------------------------------------------------------------------
# Edit 1: replace cocos2dToAndroidKey(I)I entirely
# ------------------------------------------------------------------
new_c2a = """.method private static cocos2dToAndroidKey(I)I
    .registers 2

    const/16 v0, 0x93

    if-ne p0, v0, :llev_c1

    const/16 p0, 0x1d

    return p0

    :llev_c1
    const/16 v0, 0x7e

    if-ne p0, v0, :llev_c2

    const/16 p0, 0x3b

    return p0

    :llev_c2
    const/16 v0, 0x92

    if-ne p0, v0, :llev_c3

    const/16 p0, 0x33

    return p0

    :llev_c3
    const/16 v0, 0x7f

    if-ne p0, v0, :llev_c4

    const/16 p0, 0x20

    return p0

    :llev_c4
    const/16 v0, 0x8e

    if-ne p0, v0, :llev_c5

    const/16 p0, 0x2f

    return p0

    :llev_c5
    const/16 v0, 0x3b

    if-ne p0, v0, :llev_c6

    const/16 p0, 0x3e

    return p0

    :llev_c6
    const/16 v0, 0x1a

    if-ne p0, v0, :llev_c7

    const/16 p0, 0x15

    return p0

    :llev_c7
    const/16 v0, 0x1b

    if-ne p0, v0, :llev_c8

    const/16 p0, 0x16

    return p0

    :llev_c8
    const/16 v0, 0x1c

    if-ne p0, v0, :llev_c9

    const/16 p0, 0x13

    return p0

    :llev_c9
    const/16 v0, 0x1d

    if-ne p0, v0, :llev_c10

    const/16 p0, 0x14

    return p0

    :llev_c10
    const/16 v0, 0x91

    if-ne p0, v0, :llev_c11

    const/16 p0, 0x2d

    return p0

    :llev_c11
    const/4 p0, 0x0

    return p0
.end method"""

pat_c2a = re.compile(
    r'\.method private static cocos2dToAndroidKey\(I\)I.*?\.end method',
    re.S)
if not pat_c2a.search(src):
    die("cocos2dToAndroidKey method not found")
src, n = pat_c2a.subn(lambda _: new_c2a, src, count=1)
if n != 1:
    die("cocos2dToAndroidKey replaced %d times" % n)
print("edit1 OK: cocos2dToAndroidKey replaced")

# ------------------------------------------------------------------
# Edit 2: prepend chord expander to stdKeyInject(IZ)Z
# ------------------------------------------------------------------
prologue = (
    "\n"
    "    const/16 v0, 0x2d\n\n"
    "    if-ne p0, v0, :llev_notchord\n\n"
    "    const/16 v0, 0x3b\n\n"
    "    invoke-static {v0, p1}, %s->stdKeyInject(IZ)Z\n\n"
    "    const/16 v0, 0x71\n\n"
    "    invoke-static {v0, p1}, %s->stdKeyInject(IZ)Z\n\n"
    "    :llev_notchord\n" % (CLS, CLS)
)

pat_std = re.compile(
    r'(\.method private static stdKeyInject\(IZ\)Z\n\s*\.registers\s+\d+\n)')
mm = pat_std.search(src)
if not mm:
    die("stdKeyInject header (.method + .registers) not found")
src = src[:mm.end()] + prologue + src[mm.end():]
print("edit2 OK: stdKeyInject chord prologue inserted")

open(path, "w", encoding="utf-8").write(src)

# sanity assertions
chk = open(path, encoding="utf-8").read()
for token in ["const/16 p0, 0x1d", ":llev_c11", ":llev_notchord",
              "->stdKeyInject(IZ)Z"]:
    if token not in chk:
        die("post-write missing token: " + token)
print("PATCH-OK:", path)
