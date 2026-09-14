#!/usr/bin/env python3
# v77 dex patcher -- adds two always-visible nav pills to GamepadOverlay.
# Written against the real baksmali output of the v76 baseline classes.dex
# (line-based anchors inside method regions, no byte offsets).
#
#   SLOW pill (id 5, second row left): toggles Foresight bullet-time by writing
#       common variable 500 (1.0 = on, 0.0 = off) via MenuShim.setCommonVariable(ID)I.
#       The new arm64 engine's GameManager::updateForesight() polls var 500 each
#       frame: world 0.35x, effects/tiles 0.25x, player stays 100%. On the 32-bit
#       stock engine MenuShim.setCommonVariable is a caught no-op.
#       Label shows state: SLOW / SLOW*.
#
#   MASH pill (id 6, next to SLOW): one tap = one alternating RETURN <-> SHIFT
#       pulse through rawInject (same channel as navPulse). Verified root cause
#       of the escape-gauge bug: the gauge needs op11/op12 to ALTERNATE per press;
#       op11 = pcInput 13 = SHIFT (cocos 0x0c) exists on the pad, but op12 =
#       pcInput 11 = RETURN (cocos 0x0a) is never injected by any pad control.
#       Each MASH tap fires the missing half of the alternation.
#
# Usage: python3 v77_dex_patch.py <smali-dir>
import sys, os

SMALI = sys.argv[1] if len(sys.argv) > 1 else "."
OVERLAY = os.path.join(SMALI, "org/cocos2dx/cpp/GamepadOverlay.smali")
text = open(OVERLAY, encoding="utf-8").read()
assert ".field private slowMode:Z" not in text, "already patched"
lines = text.splitlines()

CLAZZ = "Lorg/cocos2dx/cpp/GamepadOverlay;"


def method_bounds(name_sig):
    start = None
    for i, l in enumerate(lines):
        if l.strip() == ".method " + name_sig:
            start = i
            break
    assert start is not None, "method not found: " + name_sig
    for j in range(start + 1, len(lines)):
        if lines[j].strip() == ".end method":
            return start, j
    raise AssertionError(".end method missing for " + name_sig)


def find_in_method(name_sig, needle, occurrence=1):
    s, e = method_bounds(name_sig)
    hits = [i for i in range(s, e + 1) if needle in lines[i]]
    assert len(hits) >= occurrence, (
        f"{needle!r} x{occurrence} not found in {name_sig} (hits={len(hits)})")
    return hits[occurrence - 1]


def insert_after(idx, block):
    lines[idx + 1:idx + 1] = block


def pad(*stmts):
    """Smali statements separated by blank lines, matching baksmali style."""
    out = []
    for s in stmts:
        out.append(s)
        out.append("")
    return out[:-1]


# ---------------------------------------------------------------- 1. fields
fi = next(i for i, l in enumerate(lines)
          if l.strip() == ".field private cfgMode:Z")
lines[fi + 1:fi + 1] = [
    "",
    "# v77 Foresight/MASH pill state",
    ".field private mashAlt:Z",
    "",
    ".field private slowMode:Z",
]

# --------------------------------------------- 2. navDraw: draw SLOW + MASH
# Insert right before the cfgMode check so both pills are always visible.
anchor = "iget-boolean v0, p0, " + CLAZZ + "->cfgMode:Z"
idx = find_in_method("private navDraw(Landroid/graphics/Canvas;)V", anchor)
insert_after(idx, pad(
    "const/4 v0, 0x5",
    "invoke-direct {p0, v0}, " + CLAZZ + "->navPill(I)Landroid/graphics/RectF;",
    "move-result-object v1",
    "iget-boolean v0, p0, " + CLAZZ + "->slowMode:Z",
    'const-string v2, "SLOW"',
    "if-eqz v0, :cond_7d5",
    'const-string v2, "SLOW*"',
    ":cond_7d5",
    "invoke-direct {p0, p1, v1, v2}, " + CLAZZ
    + "->drawPill(Landroid/graphics/Canvas;Landroid/graphics/RectF;Ljava/lang/String;)V",
    "const/4 v0, 0x6",
    "invoke-direct {p0, v0}, " + CLAZZ + "->navPill(I)Landroid/graphics/RectF;",
    "move-result-object v1",
    'const-string v2, "MASH"',
    "invoke-direct {p0, p1, v1, v2}, " + CLAZZ
    + "->drawPill(Landroid/graphics/Canvas;Landroid/graphics/RectF;Ljava/lang/String;)V",
))

# ------------------------------- 3. navPill: geometry for pills 5 and 6
# X: add branches after the pill-4 block (label :cond_25). Row-2 y: override
# the 0.015f row-1 y with 0.08f for pills 5/6, right after v3 is computed.
PILL = "private navPill(I)Landroid/graphics/RectF;"
idx = find_in_method(PILL, ":cond_25")
insert_after(idx, pad(
    "const/4 v3, 0x5",
    "if-ne p1, v3, :cond_7d6",
    "const v2, 0x3ca3d70a    # 0.02f  SLOW (row 2)",
    ":cond_7d6",
    "const/4 v3, 0x6",
    "if-ne p1, v3, :cond_7d7",
    "const v2, 0x3d8f5c29    # 0.07f  MASH (row 2)",
    ":cond_7d7",
))
# y override: after the single `mul-float v3, v3, v1` in navPill. v7 is free
# (navPill is .registers 10 and never touches v7).
idx = find_in_method(PILL, "mul-float v3, v3, v1")
insert_after(idx, pad(
    "const/4 v7, 0x5",
    "if-eq p1, v7, :cond_7d8",
    "const/4 v7, 0x6",
    "if-eq p1, v7, :cond_7d8",
    "goto :cond_7d9",
    ":cond_7d8",
    "const v3, 0x3da3d70a    # 0.08f  row-2 y",
    ":cond_7d9",
))

# ------------------------------------ 4. navHandle: hit tests for pills 5/6
# Insert right after the existing :cond_33 label (start of the SIZE check);
# x/y live in v2/v3 at that point and are still valid for our RectF tests.
HANDLE = "private navHandle(Landroid/view/MotionEvent;)I"
idx = find_in_method(HANDLE, ":cond_33")
insert_after(idx, pad(
    # ---- pill 5: SLOW toggle ----
    "const/4 v0, 0x5",
    "invoke-direct {p0, v0}, " + CLAZZ + "->navPill(I)Landroid/graphics/RectF;",
    "move-result-object v4",
    "invoke-virtual {v4, v2, v3}, Landroid/graphics/RectF;->contains(FF)Z",
    "move-result v4",
    "if-eqz v4, :cond_7da",
    "iget-boolean v0, p0, " + CLAZZ + "->slowMode:Z",
    "xor-int/lit8 v0, v0, 0x1",
    "iput-boolean v0, p0, " + CLAZZ + "->slowMode:Z",
    "const-wide/16 v4, 0x0",
    "if-eqz v0, :cond_7db",
    "const-wide v4, 0x3ff0000000000000L",
    ":cond_7db",
    "const/16 v0, 0x1f4             # common variable id 500",
    "invoke-static {v0, v4, v5}, Lorg/cocos2dx/cpp/MenuShim;->setCommonVariable(ID)I",
    "invoke-virtual {p0}, Landroid/view/View;->invalidate()V",
    "const/4 v0, 0x1",
    "return v0",
    ":cond_7da",
    # ---- pill 6: MASH pulse ----
    "const/4 v0, 0x6",
    "invoke-direct {p0, v0}, " + CLAZZ + "->navPill(I)Landroid/graphics/RectF;",
    "move-result-object v4",
    "invoke-virtual {v4, v2, v3}, Landroid/graphics/RectF;->contains(FF)Z",
    "move-result v4",
    "if-eqz v4, :cond_7dc",
    "invoke-direct {p0}, " + CLAZZ + "->mashPulse()V",
    "const/4 v0, 0x1",
    "return v0",
    ":cond_7dc",
))

# --------------------------------------------- 5. mashPulse helper method
MASH = """
.method private mashPulse()V
    .registers 4

    # v77 MASH: fire the missing half of the escape-gauge alternation.
    # cocos 0x0c = SHIFT (op11, also on the pad) <-> cocos 0x0a = RETURN (op12,
    # never injectable from the stock pad). First tap = RETURN, then alternate.

    iget-boolean v0, p0, Lorg/cocos2dx/cpp/GamepadOverlay;->mashAlt:Z

    xor-int/lit8 v0, v0, 0x1

    iput-boolean v0, p0, Lorg/cocos2dx/cpp/GamepadOverlay;->mashAlt:Z

    const/16 v1, 0xa

    if-eqz v0, :cond_7dd

    const/16 v1, 0xc

    :cond_7dd
    const/4 v0, 0x1

    invoke-direct {p0, v1, v0}, Lorg/cocos2dx/cpp/GamepadOverlay;->rawInject(IZ)V

    const/4 v0, 0x0

    invoke-direct {p0, v1, v0}, Lorg/cocos2dx/cpp/GamepadOverlay;->rawInject(IZ)V

    invoke-virtual {p0}, Landroid/view/View;->invalidate()V

    return-void
.end method
""".strip("\n").splitlines()
lines.extend(MASH)

open(OVERLAY, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("v77 dex patch applied OK")
