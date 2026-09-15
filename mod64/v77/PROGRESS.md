# v77 Session Handoff — FOBS Android (Forest of the Blue Skin port)

**Session date:** 2026-09-14. Ran on an ephemeral RDP (wipes on restart).
Everything needed to resume lives in this repo, branch **`main`** (v77 commits
are on top of origin/main; see git log), plus APK baselines on GitHub Releases
(see bottom).

## User's original complaint
1. **Escape mash broken** — during the mushroom/plant-girl H-scene near the house,
   escape is impossible no matter what; the player gets stuck and the save resets.
2. **Wilderness map fully revealed** — no fog of war on the 荒野 map; kills exploration.
   Forest map works correctly.
3. **Lag with many entities/animations** — gameplay slows when the area is busy
   (excl. some boss fights). User asked for a slow-time item instead.
4. **New feature:** a slow-time (Foresight) item to foresee attacks.

## Architecture recap (verified this session)
- Repo = PGMMV/Cocos2d-x engine source (`Player/Classes`) + Java overlay
  (`Player/proj.android-studio`) + `mod64/` delivery system (python smali/data
  patch scripts, build recipes, handoff docs).
- **arm64 APK:** engine built from this repo (CI: `.github/workflows/build-arm64.yml`),
  so C++ fixes apply natively.
- **32-bit APK:** **stock** PGMMV engine (`libMyGame.so` — it has TouchGamepad).
  Only data patches and menushim/dex patches apply.
- Game data = plaintext `assets/Resources/data/project.json` (~246MB) — identical
  in both APKs. Top-level keys, `variableList` / `switchList` are **arrays**.
- Overlay buttons (MENU/MAP pills) = dex patches (`mod64/scripts/v63_menumap_patch.py`),
  Java classes `org.cocos2dx.cpp.{MenuShim, GamepadOverlay}`.
- `MenuShim` (source: `mod64/src/menushim.cpp`) dlsyms `libMyGame.so` — works on
  **both** ABIs when the symbols exist.
- v76 baseline APKs were in `C:\Users\runneradmin\Downloads` (wiped) → backed up
  to GitHub Releases.

## Root causes (verified)
### 1. Escape mash impossible (mushroom girl) → save resets
- Escape gauge object = **obj 12** (`エスケープゲージ`). Its mash links require
  **alternating operation keys 11 ↔ 12** each press (+5 to var 2030 per alternation;
  a loop drains −1).
- Touch overlay's 13 pad buttons inject arrows, Z, SHIFT, A, V, SPACE, X, C, D —
  **no button injects the op11/op12 pair**, and stuck-key edges (lost releases from
  async injection) kill alternation even on arrows. Hence escape is impossible on touch.
- Fix = engine edge-regen (done, arm64) + dex MASH pill pulsing alternating keys (todo).

### 2. Wilderness map fully revealed — **v77 CORRECTION: old theory DISPROVEN**
- The earlier handoff claimed obj 165 was missing 8 action links (ids 2, 19–25)
  compared to obj 163. **That is false.** Full re-forensics this session
  (scripts preserved in repo root: `verify_165.py`, `diff_fog.py`,
  `count_assigns.py`, `action_full.py`, `placements.py`, `neighbors.py`,
  `context_shapes.py`, `parts_overrides.py`) proved:
  - obj 165's hide links are **complete and correct**: 21 square actions, each
    wired to a `linkConditionList` switch-guard on 荒野1–18 (switch ids
    2276–2293), firing 消え (motion 4 = hidden) when the switch turns ON
    (`kSwitchConditionOn = 0` ⇒ `switchValue:0` = ON — polarity verified in
    engine source).
  - Switch-assignment counts are symmetric between forest and wilderness
    (荒野1 has 1228 ON-assignments; forest switches ~84 each — 荒野 has more
    placements, consistent).
  - Per-instance command overrides in parts data are portal-teleport handlers,
    symmetric with forest.
  - Obj 163 (踏破率計算表示) is a different graph by design; its gaps vs 165
    are not shared.
- **Conclusion: the fog DATA is healthy.** The visible-map symptom is a
  RUNTIME issue (switch states never turning ON in play, or the menu scene's
  obj165 instances not evaluating their links) and needs on-device diagnosis —
  e.g. capture which 荒野N switches are ON when the menu map opens. Blind data
  edits were correctly skipped in v77.
- Evidence: `mod64/v77/analysis/` dumps + the repo-root probe scripts above.
  Raw 246MB project.json extractable from either baseline APK.

### 3. Lag with many entities/animations
- **v68 particle caps were lost**: shipped v76 data has emitVolume up to 60 with
  ~190 emitters at cap and no caps. v68 caps were data patches lost when v75/v76
  rebuilt from fresh project.json. Re-apply (todo; find v68 script in git history:
  `git log --all --oneline -- mod64/scripts | grep -i 68`).
- Cocos `Scheduler::setTimeScale` does NOT affect gameplay (GameScene::update
  overrides dt with fixed 1/60). The engine's own `SceneGameSpeed` ("Change Game
  Speed" command) is the correct lever — used for Foresight.

### 4. Foresight = common variable 500 + SceneGameSpeed (implemented, arm64)
- `GameManager::updateForesight()` runs each frame in `GameManager::update()`.
  Reads `PlayData::getCommonVariableData(500)->getValue() != 0`.
- On activate: `SceneGameSpeed::set(eTYPE_OBJECT, kTargettingByGroup,
  kObjectGroupAll, -1, kQualifierSingle, nullptr, 35.0f, DURATION_UNLIMITED)`
  (world 0.35×) + `set(eTYPE_EFFECT, 25.0f, UNLIMITED)` + `set(eTYPE_TILE,
  25.0f, UNLIMITED)` (0.25× effects/tiles), then the player exemption
  `set(eTYPE_OBJECT, kTargettingByGroup, kObjectGroupPlayer, ..., 100.0f,
  UNLIMITED)`.
- `getTimeScale` scans entries **back-to-front**, so the player entry (registered
  after the world entry) wins → player keeps full speed. Entries with the same
  Target replace each other (`SceneGameSpeed::find`) → idempotent. Registered
  **once per activation** so the game's own later speed commands still win.
- On deactivate: same targets reset to 100%. On scene change while active:
  re-apply (SceneGameSpeed is per-scene; tracked via `_foresightScene`
  `RefPtr<agtk::Scene>` + `_foresightApplied`).
- **32-bit path needs no new menushim code**: `nativeSetCommonVariable` already
  resolves `PlayData::getCommonVariableData` / `PlayVariableData::setValue` on the
  stock engine (symbol strings verified in its libMyGame.so). The dex SLOW pill
  just calls `MenuShim.nativeSetCommonVariable(500, 1/0)`.
- arm64 uses the same pill; engine poller picks it up. Var 500 must exist in game
  data → data patch (todo).

## Completed this session
1. **Save-corruption guard (arm64)** — merged `origin/fix/save-nan-truncation-android`
   into this branch → commit `a528c66` (prettywriter truncation fix + NaN guards).
   32-bit save path not addressed.
2. **InputManager edge-regen (arm64)** — `Player/Classes/Manager/InputManager.cpp`
   (+19 lines): `setPressData` and the gamepad-button branch synthesize a release
   before re-press of an already-down key (lost-release protection).
3. **GameManager Foresight (arm64)** — `Player/Classes/Manager/GameManager.h` (+10)
   and `.cpp` (+66): `updateForesight()` as described above. Header adds
   `_foresightApplied`, `_foresightScene`, `FOBS_FORESIGHT_VAR=500`,
   `void updateForesight();`.
4. **Forensics preserved** — `mod64/v77/analysis/`: obj dumps (12, 89, 116, 122,
   127, 136–140, 142, 163–166), `137_links.txt` / `165_links.txt`,
   `scenes_dump.txt`, `menu_parts.pkl`, and v76 dex smali of GamepadOverlay /
   MenuShim / AppActivity in `analysis/dex_smali/`.
5. **APK baselines** — both v76 APKs uploaded to GitHub Releases (see bottom).

## v77.1: 32-bit boot crash FIXED (2026-09-15)
- **User crash report:** SIGILL (signal 4) at `agtk::GetScreenResolutionSize+0x5b`
  called from `agtk::Scene::start` — 32-bit only; the 64-bit build ran fine.
- **Root cause (from the actual .so disassembly):** the stock armeabi-v7a engine
  kept the desktop window-resolution block in `Scene::start` that our arm64
  build removes with the v34 source patch. On Android the GLView is NOT an
  `IMGUIGLViewImpl`, so `static_cast<IMGUIGLViewImpl*>(glview)` yields a bogus
  pointer. `GetScreenResolutionSize` loads a garbage "vtable" from [x+140],
  survives via a CC_ASSERT-failure printf branch, then the next call in the
  same Scene::start block, `GetFrameSize`, does `blx r1` through the garbage
  slot → SIGILL whose PC (0xca8fd10c) actually lands INSIDE
  GetScreenResolutionSize's code range (+0x5b, data executed as code — classic
  off-by-one-symbol backtrace). The porter had already stubbed
  IsFullScreen/ChangeScreen/RestoreScreen/FocusWindow to `bx lr` but left both
  size getters live.
- **ABI fact (decisive, from Scene::start disassembly):** Scene::start calls
  these getters with a hidden sret pointer in r0 (`add r0, sp, #36; blx
  GetScreenResolutionSize` @ 0x8613cc) — cocos2d::Size has a non-trivial copy
  ctor, so on this AAPCS toolchain the return ALWAYS goes through the sret
  pointer (both originals discard r0 as the hidden pointer). An earlier stub
  draft that returned {width,height} in r0/r1 was WRONG (callers would read an
  uninitialized stack buffer) and was replaced before shipping.
- **Binary fix:** `mod64/scripts/v77_fix32_screen_crash.py` overwrites both
  getters with a 22-byte Thumb-2 stub (NDK-assembler-verified encoding) that
  writes `Size{1024.0f, 768.0f}` (the project design resolution,
  screenWidth/screenHeight) through the sret pointer and returns it:
  - `GetScreenResolutionSize` @ vaddr 0x0088B338
  - `GetFrameSize`        @ vaddr 0x0088B388
  Bytes: `40F20001 C4F28041 40F20002 C4F24042 0160 4260 7047`
  (movw/movt 1024.0f→r1, 768.0f→r2, str r1,[r0], str r2,[r0,#4], bx lr).
  Fits inside both functions' original footprints; idempotent via prologue
  signature check; verified by re-disassembly.
- All callers of these two functions are desktop-window code paths (Scene.cpp
  11697, DebugManager 4001) or guarded by them — nothing Android-legit uses
  them; AppDelegate/LogoScene only use ChangeScreen/IsFullScreen (already
  stubbed).
- Redelivered: `FOBS_v77_32bit.apk` (197,814,122 bytes, md5
  `8e47e489a8df8d09dbdf014d8d0cc4ea`) on release `v77` + user's Music folder;
  patched lib sha256 `b37d9dca96526ea1bb0d5f04fbac4693c5d9aecaecaa8ae05959e9cc95c48cdc`
  (stock was `2a856aa8c30d6ceadbcce6f9560164267c8d2857745deba2302b1993eee7b178`).
  `v77_repack.py` grew a `--lib32-so` flag for this. arm64 APK unchanged.

## v77 DELIVERED (2026-09-14, second session)
- Both APKs built locally (GitHub Actions is DISABLED for this account —
  workflow_dispatch returns 422 "Actions has been disabled for this user";
  `.github/workflows/v77-build.yml` is committed for when it's re-enabled) and
  published to GitHub Release **`v77`**:
  - `FOBS_v77_arm64.apk` 202,180,454 bytes, md5 6c8715722c93c113cf7bba5aceb237a8
  - `FOBS_v77_32bit.apk` 197,814,122 bytes, md5 42dae2f4652c8a4ec5ce73af1a1c7faf
- arm64 engine: first successful compile of updateForesight (fix: qualify
  `agtk::SceneGameSpeed` / `agtk::GameSpeed` in GameManager.cpp — commit c880754);
  GamepadInjectV51.cpp registered in Android.mk (commit c880754); built with NDK
  r25c on the RDP, symbols verified (nativeInjectCocos2dKey,
  getCommonVariableData exported).
- Build-time gotchas fixed on the way (documented for future builds):
  - NTFS checkout: git materializes the `common`/`loader` symlinks under
    SSPlayer as plain files, deleting 20 real sources. Fix: delete the symlink
    files, re-extract every real path from `git ls-tree -r HEAD` (skip the two
    symlink entries). Only lowercase `loader`/`common` are referenced nowhere —
    safe to omit.
  - Local build: `cmd //c <NDK>\\ndk-build.cmd NDK_DEBUG=0 APP_ABI=arm64-v8a
    -j8` with `NDK_MODULE_PATH=<NDK>\\sources` works on the RDP.
- Data patch verified on the real project.json: var 500 inserted before id 2062,
  352 looping + 251 one-shot emitters capped, output JSON-valid, idempotent
  (second pass byte-identical).
- Map (wilderness fog) NOT changed — data proven healthy; runtime diagnosis
  still pending (see corrected root cause below). Ask user to re-test v77 and,
  if the map is still revealed, capture which 荒野N switches are ON when the
  menu map opens.

## v77 delivery status (earlier this session) — supersedes the older step list below
1. **`mod64/scripts/v77_dex_patch.py` — DONE & round-trip verified.** Adds
   SLOW + MASH pills to GamepadOverlay. Verified details:
   - SLOW pill toggles `MenuShim.setCommonVariable(500, 0.0/1.0)` — var id is
     **500 (0x1f4)**, NOT 50; an earlier draft wrongly used 0x32.
   - MASH pill keys verified from the real mapping chain: op11 = pcInput 13 =
     AGTK KEY_LEFT_SHIFT = cocos **0x0c**; op12 = pcInput 11 = AGTK KEY_RETURN
     = cocos **0x0a**. `rawInject` routes to `stdKeyInject` (renderer handleKey)
     + `nativeInjectCocos2dKey`, both support RETURN — so the MASH pulse works.
   - Pills render via the existing `navPill`/`drawPill` (ids 5/6, second row:
     x 0.02/0.07, y 0.08), hit-tested in `navHandle` after `:cond_33`.
   - Verified locally: baksmali → patch → smali → baksmali round-trip OK.
2. **`mod64/scripts/v77_data_patch.py` — DONE.** Byte-faithful project.json
   edit: inserts var 500 entry (`toBeSaved:false`) before the id-2062 entry,
   re-applies v68 particle caps (loop→4, one-shot→8), JSON-validates output.
   Does NOT touch obj 165 (see corrected root cause above).
3. **`.github/workflows/v77-build.yml` — DONE.** Builds arm64 engine from main
   (v34+v39+v41 patches + **registers GamepadInjectV51.cpp in Android.mk**,
   which main does NOT list — critical, else the rebuilt .so loses touch
   injection), then dex patch + data patch + repack of both v76-baseline APKs,
   zipalign+apksigner (repo keystore `mod64/signing/fobs.keystore`), publishes
   release **`v77`** with `FOBS_v77_arm64.apk` + `FOBS_v77_32bit.apk`.
4. Trigger the workflow, download both APKs to Downloads for the user.

## Older remaining steps (superseded by the block above; kept for context)
   - Add common variable **id 500** to `variableList` (name e.g.
     `★FORESIGHT_スロー`, `initialValue: 0`, `toBeSaved: false`, `folder: false`)
     so toggling doesn't persist in saves.
   - **obj 165 fix:** merge the 8 missing links (ids 2, 19–25) from
     `analysis/165_links.txt` into obj 165's actionLinkList (match by id; add
     missing only; don't duplicate).
   - **Particle caps re-patch:** re-apply v68-style emitVolume caps (find the v68
     script in git history for the emitter list).
2. **`mod64/scripts/v77_dex_patch.py`** (extend `v63_menumap_patch.py` pattern):
   - **SLOW pill** — toggles `MenuShim.nativeSetCommonVariable(500, 1/0)`.
   - **MASH pill** — per-tap alternating key injection of op11/op12
     (cocos `KEY_LEFT_ARROW=26` / `KEY_DOWN_ARROW` — confirm exact op11/op12
     physical mapping from `inputMapping.operationKeyList` in project.json and
     `CCEventKeyboard.h`; KEY_LEFT_ARROW=26, KEY_RIGHT_ARROW=27 confirmed).
3. **Build pipeline** `.github/workflows/v77.yml` following existing workflows:
   build arm64 engine (build-arm64.yml pattern) → build menushim (see mod64 docs
   for its build steps) → repack both APKs with data+.dex patches → zipalign+sign
   (keystore handling copied from prior workflows) → upload artifacts.
4. Run CI, download both APKs to Downloads (user deliverable), smoke-test notes.
5. Optional: verify final `updateForesight` registers the player-exemption entry
   once per activation (current code does; re-check with `git show`).

## Verification checklist for next session
- [ ] `git log --oneline -8` shows the v77 commits (save fix, input edge-regen,
      Foresight, v77 handoff) on top of origin/main.
- [ ] Re-read `GameManager::updateForesight` (GameManager.cpp) — confirm
      scene-change re-apply + player-exemption behavior.
- [ ] Confirm var 500 entry has `toBeSaved:false` once the data patch exists.
- [ ] Re-extract APKs only when needed (246MB project.json); analysis dumps are
      already in `mod64/v77/analysis/`.

## GitHub ops (token from user, same session)
- Repo: `sonicsonica701-cloud/hell-after-school-android`, branch `main`.
- Token works for push + release uploads (used this session).

## APK baselines (GitHub Releases)
- Release **`v76-baseline`** on the repo holds both v76 APKs uploaded this session
  as rebuild inputs (exact asset names):
  - `FOBS_v76_arm64_v2.save.hotfix.apk` (202,176,382 bytes)
  - `FOBS_UPD_32bit_v2.apk` (197,822,314 bytes)
