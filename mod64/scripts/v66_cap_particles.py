#!/usr/bin/env python3
# v66: reduce particle memory/lag by capping emitVolume in project.json (plaintext assets).
# 712 emitters; the big ones (1000/500/200/100) flood the 2GB phone -> mid-game OOM + lag.
# Cap emitVolume at CAP; values <= CAP are untouched so small effects look identical.
# Byte-faithful: only the digits of oversized "emitVolume":N are rewritten; nothing else moves.
import re, sys, collections

CAP = 60
src = sys.argv[1]
dst = sys.argv[2]

data = open(src, encoding="utf-8").read()

before = collections.Counter(int(v) for v in re.findall(r'"emitVolume":(\d+)', data))
changed = [0]

def repl(m):
    v = int(m.group(1))
    if v > CAP:
        changed[0] += 1
        return '"emitVolume":' + str(CAP)
    return m.group(0)

out = re.sub(r'"emitVolume":(\d+)', repl, data)
after = collections.Counter(int(v) for v in re.findall(r'"emitVolume":(\d+)', out))

open(dst, "w", encoding="utf-8").write(out)

print("CAP =", CAP)
print("emitters changed (>CAP):", changed[0])
print("before top:", before.most_common(8))
print("after  top:", after.most_common(8))
print("max emitVolume after:", max(after))
print("size before:", len(data), "after:", len(out))
