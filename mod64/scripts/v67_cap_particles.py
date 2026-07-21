#!/usr/bin/env python3
# v67: targeted particle reduction for lag (esp. glowing portals/beams), building on v66.
# Two caps, applied per-emitter block:
#   - LOOPING emitters (loop:true) -> cap emitVolume at LOOP_CAP (they run forever = biggest lag)
#   - one-shot emitters            -> cap emitVolume at ONESHOT_CAP
# Values already below the cap are untouched. Byte-faithful edit of plaintext project.json.
import re, sys, collections

LOOP_CAP = 20
ONESHOT_CAP = 40

src, dst = sys.argv[1], sys.argv[2]
d = open(src, encoding="utf-8").read()

# Split on emitVolume so each piece after the first begins with the value + that emitter's fields.
# We rebuild the string, deciding the cap per-emitter by scanning that emitter's own block for loop:.
parts = re.split(r'("emitVolume":\d+)', d)
# parts = [pre, '"emitVolume":N', block, '"emitVolume":M', block2, ...]
out = [parts[0]]
loop_changed = 0
oneshot_changed = 0
for i in range(1, len(parts), 2):
    tag = parts[i]                       # '"emitVolume":N'
    block = parts[i+1] if i+1 < len(parts) else ""
    v = int(re.match(r'"emitVolume":(\d+)', tag).group(1))
    # this emitter's loop flag lives within its own block (before the next emitVolume)
    lp = re.search(r'"loop":(true|false)', block[:2000])
    is_loop = (lp and lp.group(1) == "true")
    cap = LOOP_CAP if is_loop else ONESHOT_CAP
    if v > cap:
        newv = cap
        if is_loop: loop_changed += 1
        else: oneshot_changed += 1
        tag = '"emitVolume":' + str(newv)
    out.append(tag)
    out.append(block)

res = "".join(out)
open(dst, "w", encoding="utf-8").write(res)

after = [int(x) for x in re.findall(r'"emitVolume":(\d+)', res)]
print("LOOP_CAP", LOOP_CAP, "ONESHOT_CAP", ONESHOT_CAP)
print("looping emitters reduced:", loop_changed)
print("one-shot emitters reduced:", oneshot_changed)
print("max emitVolume after:", max(after))
print("dist after:", collections.Counter(after).most_common(8))
print("size before", len(d), "after", len(res))
