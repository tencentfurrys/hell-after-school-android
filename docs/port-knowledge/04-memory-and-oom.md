# Memory pressure & OOM analysis

## The numbers

| Metric | v72d (pre-RT-skip) | v72j (current, RT-skip) |
|---|---|---|
| VmPeak | ~1.96 GB | ~1.75 GB |
| RSS, Tutorial steady-state | ~1.0 GB | ~720 MB |
| Layer RT allocation | 12 × 1366×768 × 8 B ≈ 96 MB | 0 (patch #2) |

The process is 32-bit (armeabi-v7a), so its virtual address space hard
ceiling is **3 GB on Android** (the 4 GB usable minus the 1 GB kernel
split). VmPeak at 1.75 GB is uncomfortably close to that ceiling — at
roughly 2.5 GB you start getting `mmap` failures and the allocator
fragments badly.

## What the J3 Orbit can actually give us

- **Total RAM**: 1.5 GB physical.
- **Android + system services + launcher**: typically 600–700 MB at idle.
- **Available to a foreground app**: ~700–900 MB before the LMK
  (low-memory killer) starts trimming.

Our game wants 1.0+ GB just to render the Tutorial. The OS handles this
via swap / file-backed eviction, but it presents as:

- `onTrimMemory level=15` (RUNNING_LOW) every few seconds
- `onTrimMemory level=80` (COMPLETE) when backgrounded
- `CRITICAL memory level! OOM kill imminent.` log lines

That last string in the log **looks scary but does not always mean a
crash is coming**. `level=80` fires on *every* backgrounded foreground
app. It only matters as an OOM warning if it shows up while you're
actively foregrounded.

## What v72i tried and why it failed

I added `android:largeHeap="true"` + `android:extractNativeLibs="true"`
in v72i thinking they'd help. They made things *worse*:

- `largeHeap="true"` only affects the **Dalvik/ART managed heap**, not
  native allocations. PGMMV/cocos2d-x runs almost entirely native, so
  it does nothing useful while telling the OS we want more.
- `extractNativeLibs="true"` forces Android to unpack the `.so` to a
  separate file under `/data/app/.../lib/` and `dlopen` it from there
  instead of `mmap`-ing it directly from the APK. The extracted copy
  consumed an additional ~30 MB of file-backed pages and didn't
  meaningfully help paging behavior.

Net result: VmPeak went from 1.75 GB to **2.3 GB**, and the J3 Orbit
started hitting `onTrimMemory level=80` even in foreground. Both
overrides were reverted in v72j and **must not be re-added** without
overwhelming evidence they help.

## What v72c–v72d actually did help with

Patch #2 (`SceneLayer::createRenderTexture` → no-op) saves ~60–96 MB
depending on how many layers a scene has. That's a real and free win
because patch #1 already made those RTs unused. This is the only
memory-saving patch in the cumulative set.

## Things we have NOT tried but probably should

In order of expected ROI:

1. **PNG asset downscale**. The game ships textures at PC resolution
   (often 4K+ atlases). Re-encoding the `assets/` folder at 50% with
   `pngquant --quality=70-90 --strip` would likely cut VmPeak by 200–400
   MB without visible quality loss on a 5–6" device. Risk: a few PGMMV
   asset-loading paths assume original dimensions and might mis-position
   sprites. Spot-check by running the level select after re-encoding.
2. **Strip iCCP profiles** from every PNG (`pngcrush -rem allb`). Smaller
   wins, ~10–20 MB, zero risk.
3. **Drop unused asset preloads**. PGMMV preloads scenes' worth of
   sprites and audio at boot to avoid hitching. The Tutorial probably
   only needs ~30% of what's preloaded. Identifying which by reading
   `project.json` scene definitions and conditionally skipping unused
   preloads in the runtime would save ~100–200 MB. Higher risk — could
   cause LOAD-time hitches mid-scene the first time a never-preloaded
   asset is accessed.
4. **Migrate to arm64-v8a** (separate from memory but related). 64-bit
   removes the 3 GB virtual-address ceiling. The build attempt during
   v72 hit a `(int)p1` pointer-truncation bug in `Scene.cpp` (3
   occurrences) that needs `(intptr_t)` casts. Not blocked, just hadn't
   gotten to it. **Even on a 64-bit build the J3 Orbit only has 1.5 GB
   physical** so this only helps emulators and newer devices.

## Recommendations for testing

- Use **MEMU** (or any emulator with ≥ 3 GB RAM allocated to the VM) as
  the primary test bench. It rules memory out instantly. If a bug
  reproes on MEMU, it's a real code bug.
- Treat the **J3 Orbit** as a stretch goal. Many fixes that look like
  "the game is broken on hardware" are actually "the game is over
  budget for this device class." If we want to support the J3 Orbit as
  a first-class target, we need (1)–(3) above.
- **`hell_runtime.log` is the source of truth** for OOM — not the JVM
  side. Look for:
  - `VmPeak: ... kB` line at scene transitions
  - `RSS: ... kB` at the same points
  - any `mmap` failures (`__libc_android_log_print: mmap failed`)
  - `onTrimMemory level=` lines (only matter if foregrounded)

## What `onTrimMemory` levels mean

| Level | Constant | Meaning |
|---|---|---|
| 5 | RUNNING_MODERATE | Whole device is getting low. Trim caches if convenient. |
| 10 | RUNNING_LOW | Whole device is low. Trim now. |
| 15 | RUNNING_CRITICAL | Whole device is critical. Free everything you can. |
| 20 | UI_HIDDEN | *Your app's UI* is no longer visible. Drop UI bitmaps. |
| 40 | BACKGROUND | You're in the background list. |
| 60 | MODERATE | You're well into background and the OS is considering killing you. |
| 80 | COMPLETE | You're next on the LMK chopping block. |

`hell_runtime.log` prints "CRITICAL memory level! OOM kill imminent."
on any level ≥ 15. That message includes the *informational* level-20
(UI hidden — perfectly normal when you task-switch). Don't conflate
"app showed level-80 in log" with "app crashed from OOM" — the v72k
MEMU log demonstrated this clearly: level-80 fired *after* a real
freeze, because the user backgrounded the frozen app.

## Practical heuristic

When debugging a "freeze" report:

1. Grep `hell_runtime.log` for `signal:` — if present, it's a crash,
   not memory.
2. Grep for `LIFE onPause` — if it appears *before* the freeze, the
   user backgrounded the app (and any subsequent `onTrimMemory` is
   normal).
3. Look at the last `VmPeak:` line — if < 2 GB, memory is fine.
4. Look at the last `visitScene:` line — if its timestamp is > 1 sec
   before the end-of-log, the GL render loop hung (not OOM, code bug).

All four of those checks took under 5 minutes per log in v72j-L. They
should be the first thing the next agent does on any freeze report.
