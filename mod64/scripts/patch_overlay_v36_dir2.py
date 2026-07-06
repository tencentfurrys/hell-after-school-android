#!/usr/bin/env python3
"""
v36 overlay patch (dir-walker).

Removes the `if-ne <regA>, <regB>(=0x91), :cond_XX` gate that guards the
existing MenuShim.injectKey call inside GamepadOverlay$2, so injectKey fires
for EVERY button cc, not just V (0x91). Everything else in the smali is left
alone; the v36 keyboard-path fix happens inside libmenushim.so.

Accepts either a direct .smali file or a smali root directory. When passed
a directory, walks it looking for a smali that contains both:
  - a `const/16 <reg>, 0x91` followed by an `if-ne <reg>, <reg>, :label` gate
  - a `->injectKey(IZ)Z` invoke-static call (or the ->nativeInjectKey(IZ)Z
    variant, if the porter named the native that way)
"""
import re, sys, os

def die(msg, extra=""):
    print("PATCH-FAIL:", msg, file=sys.stderr)
    if extra: print(extra, file=sys.stderr)
    sys.exit(1)

if len(sys.argv) < 2:
    die("usage: patch_overlay_v36_dir.py <smali-root-or-file>")

target = sys.argv[1]

# --- accept both name variants -----------------------------------------------
INJECT_RX = re.compile(r'->((?:native)?[Ii]njectKey)\(IZ\)Z')
GATE_RX = re.compile(
    r'(const/16\s+(v\d+),\s*0x91\s*\n\s*)'
    r'if-ne\s+(v\d+),\s*\2,\s*(:cond_[0-9a-fA-F]+)',
    re.M,
)

def find_target(root):
    """Return (path, gate_match_object) for the file that has both the gate and
    the injectKey call. Also collect near-miss info for diagnostics."""
    near = []
    for base, _, files in os.walk(root):
        for f in files:
            if not f.endswith(".smali"): continue
            p = os.path.join(base, f)
            try:
                t = open(p, encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            has_gate = GATE_RX.search(t)
            has_call = INJECT_RX.search(t)
            if has_gate and has_call:
                return p, t, has_gate, has_call, near
            if has_gate or has_call:
                near.append((p, bool(has_gate), bool(has_call)))
    return None, None, None, None, near

def dump_near(near):
    print("--- near-miss files (has_gate, has_injectKey) ---", file=sys.stderr)
    for p, g, c in near[:20]:
        print(f"  gate={int(g)} call={int(c)}  {p}", file=sys.stderr)

if os.path.isdir(target):
    path, src, gate_m, call_m, near = find_target(target)
    if not path:
        # Also try any file that has just the gate (in case the injectKey call
        # is in a sibling inner class of the overlay, which is common).
        print("no single-file match; searching for gate anywhere:", file=sys.stderr)
        for base, _, files in os.walk(target):
            for f in files:
                if not f.endswith(".smali"): continue
                p = os.path.join(base, f)
                t = open(p, encoding="utf-8", errors="replace").read()
                if GATE_RX.search(t):
                    print("  gate-only:", p, file=sys.stderr)
        dump_near(near)
        die("no smali file contained both a 0x91 if-ne gate AND an injectKey call")
    print("patch target:", path)
    print("gate:", gate_m.group(0).strip().replace("\n", " | "))
    print("injectKey call:", call_m.group(0))
else:
    path = target
    src = open(path, encoding="utf-8").read()
    gate_m = GATE_RX.search(src)
    if not gate_m:
        die("no 0x91 if-ne gate found in " + path)

# --- do the patch ------------------------------------------------------------
const_line = gate_m.group(1)
sentinel_reg = gate_m.group(2)
val_reg = gate_m.group(3)
label = gate_m.group(4)

new_src, n = GATE_RX.subn(
    lambda mm: mm.group(1) + f"# v36: gate removed (was: if-ne {val_reg}, {sentinel_reg}, {label})\n    nop",
    src, count=1,
)
if n != 1:
    die(f"unexpected replacement count: {n}")

open(path, "w", encoding="utf-8").write(new_src)

# --- sanity checks -----------------------------------------------------------
chk = open(path, encoding="utf-8").read()
if "v36: gate removed" not in chk:
    die("post-write: v36 marker missing")
if not INJECT_RX.search(chk):
    die("post-write: injectKey call disappeared")
if re.search(r'^\s*if-ne\s+v\d+,\s*' + sentinel_reg + r',\s*' + label, chk, re.M):
    die("post-write: if-ne gate still active")

print("PATCH-OK:", path)
