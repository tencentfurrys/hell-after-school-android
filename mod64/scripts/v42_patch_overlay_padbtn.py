#!/usr/bin/env python3
"""
v42 controls patch: neutralise the virtual-gamepad (padInject) branch in
GamepadOverlay$1.smali.

WHY
---
v41 input.log proof: every on-screen button injects its key fine, but the
THREE dead buttons (Attack X cc=147/padBtn=0, Dash C cc=126/padBtn=3,
Menu V cc=145/padBtn=2) are the ONLY ones with padBtn >= 0. Because padBtn>=0
they ALSO fire padInject() -> a virtual gamepad button. The PGMMV engine then
treats the gamepad as the active input source for that frame; the game has no
operation bound to those pad-button indices, so the action never fires, and
the simultaneous keyboard inject (which WOULD fire it) is discarded. Every
button that works uses padBtn=-1 (keyboard path only).

FIX
---
In GamepadOverlay$1.run() the guard is:

    iget v0, p0, ...$1;->val$padBtn:I
    if-ltz v0, :cond_XX       # skip padInject when padBtn < 0
    ...padInject...
    :cond_XX                  # keyboard path (works)

Replace the conditional `if-ltz vN, :label` with an unconditional `goto :label`
so padInject is NEVER reached. Movement buttons already skipped it (padBtn=-1),
so they are unchanged; the three action buttons stop double-injecting the
phantom pad button and fall through to the keyboard+precede path.

This is a single-instruction, register-preserving edit. No .registers change.

USAGE
-----
    python3 v42_patch_overlay_padbtn.py <path-to-GamepadOverlay$1.smali>
"""
import re, sys

def die(msg):
    print("PATCH-FAIL:", msg); sys.exit(1)

if len(sys.argv) != 2:
    die("usage: v42_patch_overlay_padbtn.py <GamepadOverlay$1.smali>")

path = sys.argv[1]
src = open(path, "r", encoding="utf-8").read()

# Find the padBtn read followed by an if-ltz guard, tolerant of whitespace and
# the exact register / label names. The `iget ... val$padBtn:I` uniquely marks
# the padInject guard site.
pat = re.compile(
    r"(iget\s+(v\d+),\s*p0,\s*[^\n]*->val\$padBtn:I\s*\n"   # iget vN ...val$padBtn:I
    r"(?:\s*\.line\s+\d+\s*\n)?"                             # optional .line
    r"\s*)if-ltz\s+(\2),\s*(:[A-Za-z0-9_]+)",               # if-ltz vN, :label
    re.M,
)

m = pat.search(src)
if not m:
    die("could not locate `iget val$padBtn` + `if-ltz` guard (smali shape changed?)")

label = m.group(4)
patched = src[:m.start()] + m.group(1) + "goto " + label + src[m.end():]

if patched == src:
    die("no change produced")
if "padInject" in "" or patched.count("goto " + label) < 1:
    die("goto not inserted")

open(path, "w", encoding="utf-8").write(patched)
print("PATCH-OK: padInject branch neutralised ->", "goto", label)
print("  padBtn>=0 buttons (X/C/V) now take the keyboard+precede path only.")
