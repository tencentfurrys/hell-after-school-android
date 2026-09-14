import re, sys, json
sys.stdout.reconfigure(encoding="utf-8")

data = open("C:/Users/runneradmin/Downloads/project.json", encoding="utf-8").read()

im = data.find('"inputMapping"')
print("inputMapping at:", im)
seg = data[im:im + 3000]
print(seg[:1500])
