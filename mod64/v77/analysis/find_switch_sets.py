import re, sys, json
sys.stdout.reconfigure(encoding="utf-8")

data = open("C:/Users/runneradmin/Downloads/project.json", encoding="utf-8").read()

# Switch assignments in commands: 'switchVariableChange' with swtch true + switchId N.
# Count every occurrence of each target switch id in a switchId context.
targets = list(range(2276, 2294)) + [2304, 2305, 2306, 2309]
counts = {t: 0 for t in targets}
for m in re.finditer(r'"switchId":(\d+)', data):
    sid = int(m.group(1))
    if sid in counts:
        counts[sid] += 1
print("switchId occurrences (conditions + assignments):")
for t in targets:
    print(f"  sw {t}: {counts[t]}")

# Sample contexts for a couple: find assignment-style (switchValue near it) occurrences
def contexts(sid, limit=3):
    out = []
    for m in re.finditer(rf'"switchId":{sid}\b', data):
        s = max(0, m.start() - 260)
        ctx = data[s:m.end() + 120]
        # keep only assignment-looking (switchVariableChange with switchValue 1 or operator)
        if '"switchValue":1' in ctx or '"swtch":true' in ctx:
            out.append(ctx[-380:].replace("\n", " "))
        if len(out) >= limit:
            break
    return out

for sid in (2276, 2280, 2293, 2304):
    print(f"\n=== contexts for sw {sid} (assignment-like) ===")
    for c in contexts(sid):
        print(" ...", c[-330:])

# obj165 appearCondition
om = re.search(r'\{"id":165,"name":"', data)
print("\nobj165 appearCondition field:")
seg = data[om.start():om.start() + 4000]
m = re.search(r'"appearCondition":\{[^}]*\}', seg)
print(m.group(0)[:400] if m else "not found in first 4KB")
m2 = re.search(r'"reappearCondition":\{[^}]*\}', seg)
print("reappearCondition:", m2.group(0)[:400] if m2 else "not found")

# compare: forest switches 2205-2230 assignment counts
print("\nforest switch usage (2205-2230):")
fc = {t: 0 for t in range(2205, 2231)}
for m in re.finditer(r'"switchId":(\d+)', data):
    sid = int(m.group(1))
    if sid in fc:
        fc[sid] += 1
print({k: v for k, v in sorted(fc.items())})
