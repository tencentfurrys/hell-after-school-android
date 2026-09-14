import json, sys
sys.stdout.reconfigure(encoding="utf-8")

base = "mod64/v77/analysis/"
o163 = json.load(open(base + "obj_163.json", encoding="utf-8"))

print("obj163:", o163["name"], "initialAction:", o163.get("initialActionId"))
print("\nactions (id, name, animMotionId, alpha):")
for a in sorted(o163["actionList"], key=lambda x: x["id"]):
    print(f"  {a['id']:>3} {a.get('name','')!r:>16} motion={a.get('animMotionId')} a={a.get('a')}")

print("\nlinks (id, from->to, conditions):")
for l in sorted(o163["actionLinkList"], key=lambda x: x["id"]):
    a, b = l["typeIdPair"][0][1], l["typeIdPair"][1][1]
    conds = []
    for c in l.get("linkConditionList", []):
        sw = c.get("switchVariableChanged") or {}
        if sw.get("swtch"):
            conds.append(f"sw{sw.get('switchId')}={sw.get('switchCondition')}")
        else:
            conds.append(f"var{sw.get('variableId')}{sw.get('compareVariableOperator')}{sw.get('compareValue')}")
    print(f"  {l['id']:>3}: {a:>2}->{b:<3} {conds}")
