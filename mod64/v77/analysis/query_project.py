import re, sys, json
sys.stdout.reconfigure(encoding="utf-8")

p = "C:/Users/runneradmin/Downloads/project.json"
data = open(p, encoding="utf-8").read()
print("file len:", len(data))

# --- switch names: entries are id-first, name second ---
want = set(list(range(2205, 2233)) + list(range(2276, 2294)) + list(range(2305, 2310)))
found = {}
for m in re.finditer(r'\{"id":(\d+),"name":"((?:[^"\\]|\\.)*)"', data):
    sid = int(m.group(1))
    if sid in want and sid not in found:
        found[sid] = m.group(2)
print("switch names found:", len(found), "of", len(want))
for sid in sorted(found):
    print(f"  sw {sid}: {found[sid]}")

# --- variableList ---
vm = data.find('"variableList":[')
seg = data[vm:vm + 6_000_000]
end = seg.find(',"switchList":[')
seg = seg[:end]
ids = [int(x) for x in re.findall(r'"id":(\d+)', seg)]
print("\nvariable entries:", len(ids), "min:", min(ids), "max:", max(ids))
print("id 500 exists:", 500 in ids)
first = re.search(r'\{[^{}]*\}', seg)
print("first entry verbatim:", first.group(0)[:300])

# --- obj165 verification on real file ---
om = re.search(r'\{"id":165,"name":"', data)
print("\nobj165 at offset:", om.start() if om else None)
if om:
    i = om.start()
    depth = 0; j = i; instr = False; esc = False
    while j < len(data):
        ch = data[j]
        if esc: esc = False
        elif ch == '\\': esc = True
        elif ch == '"': instr = not instr
        elif not instr:
            if ch == '{': depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0: break
        j += 1
    obj = json.loads(data[i:j+1])
    print("obj165 parsed: actions:", len(obj.get("actionList", [])), "links:", len(obj.get("actionLinkList", [])))
    froms = sorted({l["typeIdPair"][0][1] for l in obj["actionLinkList"]})
    orphans = sorted({a["id"] for a in obj["actionList"]} - set(froms))
    print("orphan actions (no outgoing link):", orphans)
    # links that DO leave fog-area actions in 165: 19/20 from 54, 24/25 from 55 etc.
    for l in sorted(obj["actionLinkList"], key=lambda x: x["id"]):
        a, b = l["typeIdPair"][0][1], l["typeIdPair"][1][1]
        conds = [(c.get("switchVariableChanged") or {}) for c in l.get("linkConditionList", [])]
        desc = [(("sw" if s.get("swtch") else "var"), s.get("switchId") if s.get("swtch") else s.get("variableId")) for s in conds]
        print(f"  link {l['id']:>2}: {a:>2}->{b:<2} {desc}")

    # what do the orphan actions DO? show command types
    def action(aid):
        return next(a for a in obj["actionList"] if a["id"] == aid)
    for aid in orphans[:3] + [1, 2, 20, 21, 22, 53, 54, 55]:
        a = action(aid)
        cmds = a.get("actionCommandList", [])
        print(f"  action {aid}: {len(cmds)} cmds, types: {[c.get('type') for c in cmds][:10]}")

# --- obj137 same treatment for cross-check ---
om2 = re.search(r'\{"id":137,"name":"', data)
i = om2.start(); depth = 0; j = i; instr = False; esc = False
while j < len(data):
    ch = data[j]
    if esc: esc = False
    elif ch == '\\': esc = True
    elif ch == '"': instr = not instr
    elif not instr:
        if ch == '{': depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0: break
    j += 1
o137 = json.loads(data[i:j+1])
froms137 = sorted({l["typeIdPair"][0][1] for l in o137["actionLinkList"]})
orphans137 = sorted({a["id"] for a in o137["actionList"]} - set(froms137))
print("\nobj137 orphans (should be []):", orphans137)
