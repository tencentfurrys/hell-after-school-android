import re, sys
sys.stdout.reconfigure(encoding="utf-8")

data = open("C:/Users/runneradmin/Downloads/project.json", encoding="utf-8").read()

# Assignment command shape: "switchVariableChange":{"swtch":true,...,"switchId":N,"switchValue":V,...
# Condition shape (links): inside linkConditionList uses "switchCondition":C (no switchValue)
pat = re.compile(r'"swtch":true,"switchObjectId":-?\d+,"switchQualifierId":-?\d+,"switchId":(\d+),"switchValue":(\d+)')

on_counts = {}
off_counts = {}
for m in pat.finditer(data):
    sid, val = int(m.group(1)), int(m.group(2))
    if val == 1:
        on_counts[sid] = on_counts.get(sid, 0) + 1
    elif val == 0:
        off_counts[sid] = off_counts.get(sid, 0) + 1

forest = list(range(2205, 2231))
wild = list(range(2276, 2294)) + [2305, 2306, 2309]

print(f"{'sw':>6} {'ON-assigns':>10} {'OFF-assigns':>11}   set")
for sid in forest + wild:
    o = on_counts.get(sid, 0)
    f = off_counts.get(sid, 0)
    label = "forest" if sid < 2276 else "wild"
    print(f"{sid:>6} {o:>10} {f:>11}   {label}")
