import re, sys
sys.stdout.reconfigure(encoding="utf-8")

data = open("C:/Users/runneradmin/Downloads/project.json", encoding="utf-8").read()

# look for key-table-ish keys near the top of the file (inputMapping was at 836)
head = data[:20000]
# list all top-level-ish keys
for m in re.finditer(r'"(\w*[Kk]ey\w*)":', head):
    pass
keys = []
for m in re.finditer(r'"(\w+)":', head):
    k = m.group(1)
    if k not in keys:
        keys.append(k)
print("keys seen in first 20KB:", keys[:80])

# search for a list of numeric key codes (cocos): 26/27 (arrows per PROGRESS: KEY_LEFT=26?) 
# Actually GamepadOverlay used CC_KEY_LEFT_ARROW=0x1a=26! So custom table likely holds 26/27 etc.
for pat in ("customKeyList", "keyList", "operationKeyList", "custom1", "CustomKey"):
    i = data.find(pat)
    print(f"{pat}: {i}")

# dump around inputMappingList end + next structures
im = data.find('"inputMapping"')
print("\ncontext after inputMappingList:")
print(data[im + 1400:im + 4000])
