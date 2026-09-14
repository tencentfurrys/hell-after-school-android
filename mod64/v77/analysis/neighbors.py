import json, sys
sys.stdout.reconfigure(encoding="utf-8")

base = "mod64/v77/analysis/"
for oid in (136, 137, 138, 139, 140, 142, 163, 164, 165, 166):
    try:
        o = json.load(open(base + f"obj_{oid}.json", encoding="utf-8"))
        acts = {a["id"]: a.get("name", "") for a in o.get("actionList", [])}
        links = o.get("actionLinkList", [])
        print(f"obj {oid}: {o.get('name')!r} anim={o.get('animationId')} actions={len(acts)} links={len(links)}")
        if oid in (164, 166, 136, 140, 142):
            print("   action names:", dict(list(acts.items())[:30]))
    except FileNotFoundError:
        print(f"obj {oid}: (no dump)")
