#!/usr/bin/env python3
# v77 data patcher for project.json (byte-faithful string edits on the
# minified original -- no re-serialization, no key reordering).
#
#   1. Add common variable 500 "★予知 (Foresight)" to variableList.
#      The Foresight engine (GameManager::updateForesight, arm64 build only)
#      polls this variable every frame: non-zero = bullet-time on.
#      The SLOW pill writes it via MenuShim.setCommonVariable(500, 0/1).
#      Idempotent: skips if id 500 already exists.
#
#   2. Cap particle emitVolume (v68 recipe: looping -> 4, one-shot -> 8,
#      floor 1) to mitigate the entity-heavy slowdown. The v68 script is
#      idempotent by construction (only lowers values above the caps).
#
#   NOT touched: obj 165 / the wilderness fog. Full data forensics this
#   session proved obj 165's link graph, action graph, switch polarity, and
#   per-instance overrides are complete and symmetric with the working forest
#   twin (obj 137). The old "8 missing links" handoff theory is DISPROVEN;
#   blind edits there would risk corrupting a healthy object.
#
# Usage: python3 v77_data_patch.py <in-project.json> <out-project.json>
import re, sys, json

src, dst = sys.argv[1], sys.argv[2]
d = open(src, encoding="utf-8", newline="").read()
orig_len = len(d)

# ------------------------------------------------- 1. variable 500 entry
MARK = '"name":"★予知 (Foresight)"'
if MARK in d:
    print("var 500: already present, skipping")
else:
    m = re.search(r'\{"folder":false,"id":2062,', d)
    assert m, "variableList first entry (id 2062) not found"
    entry = ('{"folder":false,"id":500,"initialValue":0,'
             '"memo":"v77 Foresight: 0=off, 1=bullet-time",'
             '"name":"★予知 (Foresight)","toBeSaved":false},')
    d = d[:m.start()] + entry + d[m.start():]
    print("var 500: inserted before id 2062")

# ---------------------------------------------- 2. particle emitVolume caps
LOOP_CAP, ONESHOT_CAP, MINFLOOR = 4, 8, 1
parts = re.split(r'("emitVolume":\d+)', d)
out = [parts[0]]
loop_changed = oneshot_changed = 0
for i in range(1, len(parts), 2):
    tag = parts[i]
    block = parts[i + 1] if i + 1 < len(parts) else ""
    v = int(re.match(r'"emitVolume":(\d+)', tag).group(1))
    lp = re.search(r'"loop":(true|false)', block[:2000])
    is_loop = bool(lp and lp.group(1) == "true")
    cap = LOOP_CAP if is_loop else ONESHOT_CAP
    if v > cap:
        tag = '"emitVolume":' + str(max(cap, MINFLOOR))
        if is_loop:
            loop_changed += 1
        else:
            oneshot_changed += 1
    out.append(tag)
    out.append(block)
d = "".join(out)

open(dst, "w", encoding="utf-8", newline="").write(d)
print(f"particles: looping reduced {loop_changed}, one-shot reduced {oneshot_changed}")
print(f"size: {orig_len} -> {len(d)} bytes")
json.loads(d)  # hard gate: output must still be valid JSON
print("JSON validity: OK")
