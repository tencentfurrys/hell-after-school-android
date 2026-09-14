import json, sys
sys.stdout.reconfigure(encoding="utf-8")

base = "mod64/v77/analysis/"
o165 = json.load(open(base + "obj_165.json", encoding="utf-8"))
o137 = json.load(open(base + "obj_137.json", encoding="utf-8"))

def act(o, aid, label):
    a = next(x for x in o["actionList"] if x["id"] == aid)
    print(f"=== {label} action {aid} ===")
    print(json.dumps(a, ensure_ascii=False, indent=1)[:1800])
    print()

act(o165, 2, "obj165")   # square 1 initial action
act(o165, 1, "obj165")   # target action
act(o165, 20, "obj165")  # square 19 (chuchu) initial action
act(o137, 3, "obj137")   # square 2 initial action
act(o137, 1, "obj137")
act(o137, 30, "obj137")  # one of the extra squares
