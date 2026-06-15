# Signing key
- File: `fobs.keystore`
- Alias: `fobs`
- Store password: `fobsmod`
- Key password: `fobsmod`
- CN=FOBSMod (self-signed)

Re-sign every modified APK with this SAME key so updates install over the
existing app without an uninstall:

    apksigner sign --ks fobs.keystore --ks-key-alias fobs \
      --ks-pass pass:fobsmod --key-pass pass:fobsmod \
      --v1-signing-enabled true --v2-signing-enabled true --v3-signing-enabled true \
      --out OUT.apk IN_aligned.apk
