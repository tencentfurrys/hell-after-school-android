import json, sys, pickle
sys.stdout.reconfigure(encoding="utf-8")

base = "mod64/v77/analysis/"
with open(base + "menu_parts.pkl", "rb") as f:
    data = pickle.load(f)

parts = data["parts"]

def flatten(parts, out):
    for p in parts:
        out.append(p)
        if p.get("children"):
            flatten(p["children"], out)

allp = []
flatten(parts, allp)
print("total parts:", len(allp))

for oid in (165, 137):
    ps = [p for p in allp if p.get("objectId") == oid]
    print(f"\n=== placements of obj {oid}: {len(ps)} ===")
    for p in sorted(ps, key=lambda x: x.get("initialActionId", 0)):
        print(f"  part {p.get('id'):>4} name={p.get('name')!r:>20} initialAction={p.get('initialActionId')} x={p.get('x')} y={p.get('y')}")

# Also: what switches does obj137 use per square? (already have links; just print compact)
o137 = json.load(open(base + "obj_137.json", encoding="utf-8"))
print("\nobj137 link switch map (action_from -> switch):")
for l in sorted(o137["actionLinkList"], key=lambda x: x["id"]):
    a, b = l["typeIdPair"][0][1], l["typeIdPair"][1][1]
    sws = [(c.get("switchVariableChanged") or {}) for c in l.get("linkConditionList", [])]
    sw = next((s.get("switchId") for s in sws if s.get("swtch")), None)
    if b == 1:
        print(f"  action {a:>2} -> hide (sw {sw})")
