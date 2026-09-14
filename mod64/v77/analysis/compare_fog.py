import json

base = "mod64/v77/analysis/"

def load(p):
    return json.load(open(p, encoding="utf-8"))

o137 = load(base + "obj_137.json")
o165 = load(base + "obj_165.json")

for name, o in (("137 forest fog (WORKS)", o137), ("165 wilderness fog (BROKEN)", o165)):
    print(f"=== obj {name} ===")
    print(" name:", o.get("name"), "| anim:", o.get("animationId"), "| initialAction:", o.get("initialActionId"))
    acts = o.get("actionList", [])
    links = o.get("actionLinkList", [])
    print(" actions:", len(acts), "ids:", sorted(a["id"] for a in acts))
    print(" links:", len(links), "ids:", sorted(l["id"] for l in links))
    # action types and key commands
    for a in acts:
        cmds = a.get("actionCommandList", [])
        ctypes = [c.get("type") for c in cmds]
        print(f"  action {a['id']}: priority={a.get('priority')} commands={ctypes}")

# What switches does each graph's conditions reference?
def switches(o):
    out = set()
    for l in o.get("actionLinkList", []):
        for c in l.get("conditionList", []):
            sw = c.get("switchVariableChanged") or {}
            if sw.get("swtch"):
                out.add(sw.get("switchId"))
    return out

print("137 switches:", sorted(x for x in switches(o137) if x is not None and x >= 0))
print("165 switches:", sorted(x for x in switches(o165) if x is not None and x >= 0))
