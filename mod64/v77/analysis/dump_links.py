import json, sys
sys.stdout.reconfigure(encoding="utf-8")

base = "mod64/v77/analysis/"
o137 = json.load(open(base + "obj_137.json", encoding="utf-8"))
o165 = json.load(open(base + "obj_165.json", encoding="utf-8"))

def linkmap(o):
    return {l["id"]: l for l in o.get("actionLinkList", [])}

L137, L165 = linkmap(o137), linkmap(o165)

print("=== 137 link 26 full ===")
print(json.dumps(L137[26], ensure_ascii=False, indent=1))
print("=== 137 link 27 full ===")
print(json.dumps(L137[27], ensure_ascii=False, indent=1))
print("=== 165 link 28 (its successor) keys ===")
print(json.dumps({k: (v if not isinstance(v, list) else f"<list len={len(v)}>") for k, v in L165[28].items()}, ensure_ascii=False, indent=1))
print("=== 137 link 28 (same-id, for structure reference) full ===")
print(json.dumps(L137[28], ensure_ascii=False, indent=1))

# Also show the top-level keys of a link to learn the schema
print("=== link top-level keys (137-26) ===")
print(list(L137[26].keys()))
print("=== conditionList[0] keys ===")
print(list(L137[26]["conditionList"][0].keys()) if L137[26].get("conditionList") else "no conditionList key")
