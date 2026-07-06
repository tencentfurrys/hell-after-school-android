#!/usr/bin/env python3
"""
v36 controls patch for GamepadOverlay smali.

STRATEGY
--------
The v36 fix lives in libmenushim.so: MenuShim.injectKey(cc, pressed) now
routes into InputManager::getInputDataRaw()->registerKeyPressed/Released
(cc, 0), the ONLY channel the arm64 engine polls per frame.

The overlay ALREADY calls MenuShim.injectKey(v0, v4) inside $2.run(), but the
call is gated by an if-ne (val$i, 0x91) branch so only the V (cc=0x91) button
ever reaches it. Every other button falls through and no injection happens.

The v36 patch is a SINGLE surgical edit: neutralise that gate so injectKey
fires for every cc the overlay dispatches (dpad + X/C/V/Z + Jump/S/W/D).

Before:
        iget v0, p0, GamepadOverlay$2;->val$i:I
        const-string v1, " ok="
        const/16 v3, 0x91
        if-ne v0, v3, :cond_8a        <-- SKIPS injectKey for anything != V
        iget-boolean v4, ...->val$z:Z
        invoke-static {v0, v4}, MenuShim;->injectKey(IZ)Z
        ...
        :cond_8a
        nop

After:
        iget v0, p0, GamepadOverlay$2;->val$i:I
        const-string v1, " ok="
        const/16 v3, 0x91
        # if-ne removed -- fall through so injectKey ALWAYS runs
        iget-boolean v4, ...->val$z:Z
        invoke-static {v0, v4}, MenuShim;->injectKey(IZ)Z
        ...
        :cond_8a
        nop

The v35 mapping edits are NOT applied here; v35's cocos2dToAndroidKey and
stdKeyInject chord targeted the DEAD Android keyboard channel. v36 uses the
overlay's raw cocos2d keycode (val$i) directly.

The V chord (Shift+Ctrl+Q for inventory) is handled Java-side already through
the toggleMenu() path lower in $2.run(); the raw injectKey(V=0x91, pressed)
also fires and lands harmlessly in the InputManager since cc=0x91 is bound
to opKid 1014 (Menu) in project.json.

USAGE
-----
    python3 patch_overlay_v36.py <path-to-GamepadOverlay$2.smali>
"""
import re, sys, os

def die(msg):
    print("PATCH-FAIL:", msg); sys.exit(1)

if len(sys.argv) != 2:
    die("usage: patch_overlay_v36.py <GamepadOverlay$2.smali>")

path = sys.argv[1]
src = open(path, "r", encoding="utf-8").read()

# The gate we want to neutralise. Match:
#   const/16 vX, 0x91
#   if-ne vY, vX, :cond_LABEL
# where vX and vY are single-digit or two-hex registers and LABEL is any smali label.
pat = re.compile(
    r'(const/16\s+(v\d+),\s*0x91\s*\n\s*)'
    r'if-ne\s+(v\d+),\s*\2,\s*(:cond_[0-9a-fA-F]+)',
    re.M)

m = pat.search(src)
if not m:
    die("could not find the 'if-ne <val$i>, 0x91, :cond_XX' gate in GamepadOverlay$2")

const_line, sentinel_reg, val_reg, label = m.group(1), m.group(2), m.group(3), m.group(4)
print(f"gate found: const/16 {sentinel_reg}, 0x91 ; if-ne {val_reg}, {sentinel_reg}, {label}")

# Replace the if-ne with a nop so control falls through to the injectKey call.
# We keep the const/16 line intact (harmless), just remove the branch.
new_src, n = pat.subn(
    lambda mm: mm.group(1) + f"# v36: gate removed (was: if-ne {val_reg}, {sentinel_reg}, {label})\n    nop",
    src, count=1)
if n != 1:
    die(f"unexpected replacement count: {n}")

open(path, "w", encoding="utf-8").write(new_src)

# Sanity assertions
chk = open(path, encoding="utf-8").read()
if "v36: gate removed" not in chk:
    die("post-write: v36 marker missing")
# The injectKey invocation must still be present, unchanged.
if "->injectKey(IZ)Z" not in chk:
    die("post-write: MenuShim.injectKey(IZ)Z call disappeared")
# The old gate must be gone. Match only executable smali (not a `#` comment).
if re.search(r'^\s*if-ne\s+v\d+,\s*' + sentinel_reg + r',\s*' + label, chk, re.M):
    die("post-write: if-ne gate still present")

print("PATCH-OK:", path)
