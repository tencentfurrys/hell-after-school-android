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

ps = [p for p in allp if p.get("objectId") == 165]
print("obj165 placements with NON-EMPTY per-instance overrides:")
for p in sorted(ps, key=lambda x: x.get("initialActionId", 0)):
    ovr = p.get("actionCommandListObject") or {}
    nonempty = {k: v for k, v in ovr.items() if v}
    if nonempty:
        print(f"  part {p['id']} (action {p.get('initialActionId')}): overridden actions {sorted(nonempty, key=int)}")
        for k, cmds in sorted(nonempty.items(), key=lambda kv: int(kv[0])):
            for c in cmds:
                sw = c.get("switchVariableChange") or {}
                desc = ""
                if sw:
                    desc = f" swtch={sw.get('swtch')} id={sw.get('switchId') if sw.get('swtch') else sw.get('variableId')} val/op={sw.get('switchValue') if sw.get('swtch') else sw.get('assignValue')}"
                print(f"      action {k} cmd type={c.get('commandType')}{desc}")
else:
    pass

# summary: how many have any overrides
n_ovr = sum(1 for p in ps if any(p.get("actionCommandListObject") or {}).values()) if False else sum(1 for p in ps if any((p.get("actionCommandListObject") or {}).values()))
print("\nplacements with overrides:", n_ovr, "of", len(ps))

# check the base object's own animation vs the fog instance start motion: does part override initialActionId?
print("\ninitialActionId per part (should map to distinct squares):")
print(sorted(p.get("initialActionId") for p in ps))
