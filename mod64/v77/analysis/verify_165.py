import json

base = "mod64/v77/analysis/"

def load(p):
    return json.load(open(p, encoding="utf-8"))

o163 = load(base + "obj_163.json")
o165 = load(base + "obj_165.json")
o12 = load(base + "obj_12.json")

def links(o):
    return {l["id"]: l for l in o.get("actionLinkList", [])}

L163, L165 = links(o163), links(o165)
print("163 link ids:", sorted(L163))
print("165 link ids:", sorted(L165))
print("165 missing vs 163:", sorted(set(L163) - set(L165)))

missing = sorted(set(L163) - set(L165))
same = [i for i in missing if json.dumps(L163[i], sort_keys=True) == json.dumps(L165.get(i, ""), sort_keys=True)]
print("missing ids that differ textually:", [i for i in missing if i not in same] or "none; 163 copy is verbatim-usable" if missing else "no missing")

# actions referenced by the missing links must exist in 165
acts165 = {a["id"] for a in o165.get("actionList", [])}
acts163 = {a["id"] for a in o163.get("actionList", [])}
print("163 actions not in 165:", sorted(acts163 - acts165))

# escape gauge object: which operation keys its links/conditions reference
def walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("operationKeyId", "keyId", "operationKey"):
                print(f"{path}.{k} = {v}")
            walk(v, path + "." + k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, f"{path}[{i}]")

print("=== obj12 operation-key references (first 30) ===")
import io, contextlib
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    walk(o12)
lines = buf.getvalue().splitlines()
print("\n".join(lines[:30]))
print("total key refs in obj12:", len(lines))
