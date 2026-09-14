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

for oid in (163, 164, 166, 136, 139):
    ps = [p for p in allp if p.get("objectId") == oid]
    print(f"\n=== placements of obj {oid}: {len(ps)} ===")
    for p in sorted(ps, key=lambda x: (x.get('layerIndex', 0), x.get('priority', 0)))[:12]:
        print(f"  part {p.get('id'):>4} name={p.get('name')!r:>24} layer={p.get('layerIndex')} prio={p.get('priority')} dispPrio={p.get('dispPriority')} initialAction={p.get('initialActionId')} visible={p.get('visible')} x={p.get('x')} y={p.get('y')}")

# For obj165 instances, show their layer/priority too
ps165 = [p for p in allp if p.get("objectId") == 165]
print(f"\n=== obj165 layers ===")
layers165 = sorted({(p.get('layerIndex'), p.get('dispPriority')) for p in ps165})
print(layers165)
