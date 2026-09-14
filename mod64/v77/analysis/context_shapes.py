import re, sys, collections
sys.stdout.reconfigure(encoding="utf-8")

data = open("C:/Users/runneradmin/Downloads/project.json", encoding="utf-8").read()

for sid, label in ((2276, "wild 荒野1"), (2205, "forest sw003")):
    print(f"=== switch {sid} ({label}) ===")
    shapes = collections.Counter()
    samples = {}
    for m in re.finditer(rf'"switchId":{sid}\b', data):
        # what key follows switchId?
        tail = data[m.end():m.end() + 40]
        after = re.match(r',"(\w+)"', tail)
        key = after.group(1) if after else "?"
        # and the preceding swtch flag
        head = data[max(0, m.start() - 300):m.start()]
        swtch = "swtch:true" if '"swtch":true' in head else ("swtch:false" if '"swtch":false' in head else "no-swtch")
        shape = f"{swtch} -> next key: {key}"
        shapes[shape] += 1
        samples.setdefault(shape, data[max(0, m.start() - 120):m.end() + 160])
    for s, c in shapes.most_common():
        print(f"  {c:>5}x {s}")
    print("  sample of most common with swtch:true:")
    for s, c in shapes.most_common():
        if "swtch:true" in s:
            print("   ", samples[s].replace("\n", " ")[:300])
            break
    print()
