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
echo "=== alignment ==="
readelf -l "$SO" | awk '/LOAD/{getline; print "PUBLISH_ALIGN="$NF}' | sort -u
echo "=== upload 0x0.st ==="
echo "PUBLISH_URL_0x0=$(curl -fsS -H 'User-Agent: Mozilla/5.0' -F "file=@$SO" https://0x0.st 2>/dev/null)"
echo "=== upload bashupload ==="
curl -fsS -T "$SO" https://bashupload.com 2>/dev/null | grep -io 'https[^ ]*' | head -1 | sed 's/^/PUBLISH_URL_BASH=/'
echo "=== upload file.io ==="
echo "PUBLISH_URL_FILEIO=$(curl -fsS -F "file=@$SO" https://file.io 2>/dev/null)"
echo "=== publish_so done ==="
