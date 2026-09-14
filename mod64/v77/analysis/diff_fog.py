import json, sys
sys.stdout.reconfigure(encoding="utf-8")

base = "mod64/v77/analysis/"
o137 = json.load(open(base + "obj_137.json", encoding="utf-8"))
o165 = json.load(open(base + "obj_165.json", encoding="utf-8"))

def linkmap(o):
    return {l["id"]: l for l in o.get("actionLinkList", [])}

def conds(l):
    out = []
    for c in l.get("linkConditionList", []):
        sw = c.get("switchVariableChanged") or {}
        out.append((c.get("type"), "sw" if sw.get("swtch") else "var", sw.get("switchId") if sw.get("swtch") else sw.get("variableId"), sw.get("switchCondition") if sw.get("swtch") else sw.get("compareValue")))
    return out

L137, L165 = linkmap(o137), linkmap(o165)
common = sorted(set(L137) & set(L165))

print(f"{'id':>3} {'137->':>10} {'165->':>10} {'cond137':<24} {'cond165':<24} same?")
ndiff = 0
for i in common:
    a, b = L137[i], L165[i]
    same = json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    if not same:
        ndiff += 1
        print(f"{i:>3} {a['typeIdPair'][0][1]}->{a['typeIdPair'][1][1]:<4} {b['typeIdPair'][0][1]}->{b['typeIdPair'][1][1]:<4} {str(conds(a)):<24} {str(conds(b)):<24} DIFF")
print("same-id links differing:", ndiff, "of", len(common))

# actions each link targets, per object
def edges(o):
    return {l["id"]: (l["typeIdPair"][0][1], l["typeIdPair"][1][1]) for l in o.get("actionLinkList", [])}

E137, E165 = edges(o137), edges(o165)
print("\n137 graph (id: from->to):")
print({k: f"{v[0]}->{v[1]}" for k, v in sorted(E137.items())})
print("\n165 graph (id: from->to):")
print({k: f"{v[0]}->{v[1]}" for k, v in sorted(E165.items())})

# which switches appear in 137 conditions
sw137 = sorted({c.get("switchVariableChanged", {}).get("switchId") for l in L137.values() for c in l.get("linkConditionList", []) if (c.get("switchVariableChanged") or {}).get("swtch")})
sw165 = sorted({c.get("switchVariableChanged", {}).get("switchId") for l in L165.values() for c in l.get("linkConditionList", []) if (c.get("switchVariableChanged") or {}).get("swtch")})
print("\n137 condition switches:", sw137)
print("165 condition switches:", sw165)
