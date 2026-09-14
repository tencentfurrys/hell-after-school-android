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

### 2. Wilderness map fully revealed
- Map UI lives in the MENU scene; fog parts = object 137 (forest, works) vs
  object 165 (wilderness, broken). Menu scene places obj165 ×28, obj137 ×40.
- **Structural anomaly:** obj 165 is **missing 8 action links (ids 2, 19–25)**
  that its twin obj 163 has — they connect fog-hide actions 54/55/20/21/22 to
  their switch conditions. Evidence preserved:
  `mod64/v77/analysis/165_links.txt` (+ `obj_165.json`, `obj_163.json`).
- Fix = data patch merging the missing links into obj 165 (todo).

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

## Remaining steps (exact, in order)
1. **`mod64/scripts/v77_data_patch.py`** (operates on extracted project.json):
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
  as rebuild inputs:
  - `fobs-v76-arm64.apk`
  - `fobs-v76-armv7a.apk`
  (If names differ, list with: `gh release view v76-baseline` equivalent via API.)
