#!/usr/bin/env python3
# v68: MAX LOW - aggressive global particle reduction across EVERYTHING (water, glows, portals,
# all effects). User asked to push all particles as low as possible for performance.
# Strategy: hard-cap emitVolume for ALL emitters. Looping (continuous) go lowest since they cost
# most; one-shots slightly higher so brief effects still register. Never below MINFLOOR so an
# effect never becomes fully invisible (0 particles). Byte-faithful edit of plaintext project.json.
import re, sys, collections

LOOP_CAP = 4      # continuous glows/water/portals -> barely-there
ONESHOT_CAP = 8   # brief bursts -> still visible but minimal
MINFLOOR = 1      # never zero out an effect

src, dst = sys.argv[1], sys.argv[2]
d = open(src, encoding="utf-8").read()

parts = re.split(r'("emitVolume":\d+)', d)
out = [parts[0]]
loop_changed = oneshot_changed = 0
for i in range(1, len(parts), 2):
    tag = parts[i]
    block = parts[i+1] if i+1 < len(parts) else ""
    v = int(re.match(r'"emitVolume":(\d+)', tag).group(1))
    lp = re.search(r'"loop":(true|false)', block[:2000])
    is_loop = (lp and lp.group(1) == "true")
    cap = LOOP_CAP if is_loop else ONESHOT_CAP
    if v > cap:
        newv = max(cap, MINFLOOR)
        if is_loop: loop_changed += 1
        else: oneshot_changed += 1
        tag = '"emitVolume":' + str(newv)
    out.append(tag); out.append(block)

res = "".join(out)
open(dst, "w", encoding="utf-8").write(res)
after = [int(x) for x in re.findall(r'"emitVolume":(\d+)', res)]
print("LOOP_CAP", LOOP_CAP, "ONESHOT_CAP", ONESHOT_CAP)
print("looping reduced:", loop_changed, "one-shot reduced:", oneshot_changed)
print("max after:", max(after), "min after:", min(after))
print("dist after:", collections.Counter(after).most_common(8))
