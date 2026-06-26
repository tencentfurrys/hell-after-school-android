#!/usr/bin/env bash
set +e
echo "=== publish_so: waiting for arm64 libMyGame.so ==="
SO=""
for i in $(seq 1 400); do
  f=$(find . -name libMyGame.so -path '*arm64-v8a*' 2>/dev/null | head -1)
  if [ -n "$f" ] && [ -s "$f" ]; then
    s1=$(stat -c%s "$f"); sleep 3; s2=$(stat -c%s "$f")
    if [ "$s1" = "$s2" ]; then SO="$f"; break; fi
  fi
  sleep 5
done
if [ -z "$SO" ]; then echo "publish_so: .so NOT found"; exit 0; fi
echo "PUBLISH_SO_PATH=$SO"
echo "PUBLISH_SO_SIZE=$(stat -c%s "$SO")"
echo "PUBLISH_SO_SHA=$(sha256sum "$SO" | cut -d' ' -f1)"
readelf -l "$SO" | awk '/LOAD/{getline; print "PUBLISH_ALIGN="$NF}' | sort -u
echo "=== upload litterbox (72h) ==="
echo "PUBLISH_URL_LITTER=$(curl -fsS -F reqtype=fileupload -F time=72h -F "fileToUpload=@$SO" https://litterbox.catbox.moe/resources/internals/api.php 2>/dev/null)"
echo "=== upload catbox (perm) ==="
echo "PUBLISH_URL_CATBOX=$(curl -fsS -H 'User-Agent: Mozilla/5.0' -F reqtype=fileupload -F "fileToUpload=@$SO" https://catbox.moe/user/api.php 2>/dev/null)"
echo "=== upload oshi ==="
curl -fsS -T "$SO" 'https://oshi.at/?expire=4320' 2>/dev/null | grep -io 'https[^ ]*' | sed 's/^/PUBLISH_URL_OSHI=/'
echo "=== publish_so done ==="
