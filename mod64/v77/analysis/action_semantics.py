import json, sys, pickle, re
sys.stdout.reconfigure(encoding="utf-8")

base = "mod64/v77/analysis/"

def show_actions(path, aids, label):
    o = json.load(open(base + path, encoding="utf-8"))
    print(f"=== {label} ({path}) ===")
    print("object keys:", list(o.keys()))
    for a in o.get("actionList", []):
        if a["id"] in aids:
            cmds = a.get("actionCommandList", [])
            print(f" action {a['id']}: label={a.get('label','')!r} {len(cmds)} cmds")
            for c in cmds:
                # print command type + any display/visible related fields
                interesting = {k: v for k, v in c.items() if k in (
                    "type", "id", "objectDisplayType", "displayType", "visible",
                    "alpha", "alpha2", "changeType", "positionType", "label", "text",
                    "switchId", "variableId", "operationType", "value")}
                print("   cmd:", interesting)

show_actions("obj_165.json", {1, 2, 23, 54, 55}, "obj165 wilderness fog")
show_actions("obj_137.json", {1, 2, 30, 31}, "obj137 forest fog")
show_actions("obj_136.json", {1, 2}, "obj136 (for reference)")

# menu scene placements
print("\n=== scenes_dump.txt (obj 165 / 137 mentions) ===")
try:
    txt = open(base + "scenes_dump.txt", encoding="utf-8").read()
    print("lines:", len(txt.splitlines()))
    hits = [l for l in txt.splitlines() if re.search(r"\b(165|137)\b", l)]
    print("\n".join(hits[:40]))
except Exception as e:
    print("ERR", e)

print("\n=== menu_parts.pkl ===")
try:
    with open(base + "menu_parts.pkl", "rb") as f:
        parts = pickle.load(f)
    print(type(parts), len(parts) if hasattr(parts, "__len__") else "")
    sample = parts[:3] if isinstance(parts, list) else list(parts.items())[:3]
    for s in sample:
        print(s)
    if isinstance(parts, list):
        for p in parts:
            oid = p.get("objectId") if isinstance(p, dict) else None
            if oid in (165, 137):
                print("placement:", {k: p.get(k) for k in ("objectId", "x", "y", "switchId", "initialActionId", "id")})
except Exception as e:
    print("ERR", e)
