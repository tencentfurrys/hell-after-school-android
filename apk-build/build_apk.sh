#!/bin/bash
set -e
export JAVA_HOME=/work/temp/jdk
export ANDROID_HOME=/work/temp/android-sdk
export PATH=$JAVA_HOME/bin:$ANDROID_HOME/build-tools/30.0.3:$PATH
APK_BUILD=/work/temp/apk-build

cp $APK_BUILD/resources.ap_ $APK_BUILD/hell59.apk
python3 << 'PYEOF'
import zipfile, os
apk='/work/temp/apk-build/hell59.apk'
with zipfile.ZipFile(apk, 'a', zipfile.ZIP_DEFLATED) as z:
    z.write('/work/temp/apk-build/classes.dex', 'classes.dex')
    # libs STORED
    for root, dirs, files in os.walk('/work/temp/apk-build/lib'):
        for f in files:
            p = os.path.join(root, f)
            arc = os.path.relpath(p, '/work/temp/apk-build/').replace(os.sep,'/')
            zi = zipfile.ZipInfo(arc)
            zi.compress_type = zipfile.ZIP_STORED
            with open(p,'rb') as fh:
                z.writestr(zi, fh.read())
    # assets DEFLATED
    ac=0
    for root, dirs, files in os.walk('/work/temp/apk-build/assets'):
        for f in files:
            p = os.path.join(root, f)
            arc = os.path.relpath(p, '/work/temp/apk-build/').replace(os.sep,'/')
            z.write(p, arc)
            ac+=1
print("assets:", ac, "size:", os.path.getsize(apk))
PYEOF

zipalign -p -f 4 $APK_BUILD/hell59.apk $APK_BUILD/hell59-aligned.apk
apksigner sign --ks $APK_BUILD/debug.keystore --ks-pass pass:android --key-pass pass:android \
  --v1-signing-enabled true --v2-signing-enabled true \
  --out $APK_BUILD/HellAfterSchool-v59.apk \
  $APK_BUILD/hell59-aligned.apk

ls -la $APK_BUILD/HellAfterSchool-v59.apk
md5sum $APK_BUILD/HellAfterSchool-v59.apk
apksigner verify $APK_BUILD/HellAfterSchool-v59.apk && echo "SIGN OK"
echo "DONE"
