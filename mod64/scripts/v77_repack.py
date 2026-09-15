#!/usr/bin/env python3
# v77 repack: swap patched dex/data (+ optionally a new arm64 engine .so) into a
# baseline APK, preserving every other entry byte-for-byte with its compression.
# Same logic as .github/workflows/v77-build.yml.
#
# Usage:
#   python3 v77_repack.py --base BASE.apk --dex classes.dex --data project.json \
#            --out out.apk [--arm64-so libMyGame.so]
import argparse, zipfile

ap = argparse.ArgumentParser()
ap.add_argument("--base", required=True)
ap.add_argument("--dex", required=True)
ap.add_argument("--data", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--arm64-so", dest="arm64_so", default=None,
                help="new lib/arm64-v8a/libMyGame.so (arm64 builds only)")
ap.add_argument("--lib32-so", dest="lib32_so", default=None,
                help="replacement lib/armeabi-v7a/libMyGame.so (32-bit builds only)")
args = ap.parse_args()

new = {
    "classes.dex": open(args.dex, "rb").read(),
    "assets/Resources/data/project.json": open(args.data, "rb").read(),
}
drop = set()
if args.arm64_so:
    new["lib/arm64-v8a/libMyGame.so"] = open(args.arm64_so, "rb").read()
    drop = {"lib/armeabi-v7a/libMyGame.so", "lib/armeabi-v7a/libmenushim.so"}
if args.lib32_so:
    new["lib/armeabi-v7a/libMyGame.so"] = open(args.lib32_so, "rb").read()

zin = zipfile.ZipFile(args.base, "r")
zout = zipfile.ZipFile(args.out, "w")
got = set()
for info in zin.infolist():
    if info.filename in drop:
        continue
    raw = new.get(info.filename)
    if raw is not None:
        got.add(info.filename)
    zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
    zi.compress_type = info.compress_type
    zi.external_attr = info.external_attr
    zi.internal_attr = info.internal_attr
    zi.create_system = info.create_system
    zi.flag_bits = info.flag_bits
    zout.writestr(zi, raw if raw is not None else zin.read(info.filename))
zout.close()
zin.close()

assert got == set(new), f"swap missing: {set(new) - got}"
chk = zipfile.ZipFile(args.out, "r")
for name, blob in new.items():
    assert chk.read(name) == blob, f"content mismatch after pack: {name}"
chk.close()
print("repack OK:", args.out)
