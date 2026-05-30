# Key log-line signatures in `hell_runtime.log`

When triaging a freeze or crash report, grep for these. Most of the
debugging this project has done was driven by 4–5 distinctive log
lines — knowing them by sight saves hours.

## Engine state

| Line | Meaning |
|---|---|
| `visitScene: camera pos=(X,Y)` | Rendering this frame, camera at (X,Y). If `pos != (0,0)` the scene is scrolling — this is the regime where the original RT-shader bug manifested. |
| `layer N direct visit visible=1 children=K pos=...` | The layer is being rendered through the **working** direct-visit path. Should be the case for all scene layers after v72b's patch. |
| `layer N via RT shader visible=1 pos=...` | The layer is being rendered through the **broken** RT-shader path. Should NOT appear for scene layers post-v72b. If it does, the RT-shader-kill patch is missing or didn't take. |
| `bg via RT sprite visible=1 ...` | Background layer captured into an RT and drawn as a sprite. Hot Dog King's original code, unrelated to the bug. |
| `Scene::init id=N` | Scene N is being initialized. Useful for tracking menu/save/load scene transitions. |

## Memory

| Line | Meaning |
|---|---|
| `VmPeak: N kB` | Peak virtual memory. Anything above 2.5 GB on 32-bit is dangerous (3 GB ceiling). 1.75 GB is the normal post-v72c value. |
| `RSS: N kB` | Resident set size. 720 MB steady-state is normal in Tutorial. |
| `onTrimMemory level=20` | "UI hidden" — fires whenever the activity goes to background. **Normal**, not a crash signal. |
| `onTrimMemory level=80` | "Complete" — only matters when foregrounded. **Otherwise normal.** |
| `CRITICAL memory level! OOM kill imminent.` | Misleading — the engine prints this on any level ≥ 15, which includes the routine level-20 background transition. Always cross-check with `LIFE onPause`. |

## Lifecycle (added in v72L)

| Line | Meaning |
|---|---|
| `LIFE onPause` | Activity went to background (user task-switched, dialog appeared, etc.). |
| `LIFE onResume` | Activity returned to foreground. |
| `FOCUS hasFocus=true` | Window has input focus. |
| `FOCUS hasFocus=false` | Lost input focus (e.g. system dialog popped up). |

## Input (added in v72L)

| Line | Meaning |
|---|---|
| `INPUT KEY act=0 code=47` | Hardware key DOWN, keycode 47 (`KEYCODE_V`). Catches physical V on a PC keyboard or phone hardware keys. |
| `INPUT KEY act=1 code=...` | Hardware key UP. |
| `INPUT TOUCH act=0 x=... y=...` | Touch DOWN on the activity surface. |
| `INPUT TOUCH act=1 x=... y=...` | Touch UP. |
| `JAVA GP touch DOWN x=... y=... btn=...` | Touch was inside our Java overlay and bound to a specific button. If `JAVA GP` lines are absent but `INPUT TOUCH` is present, the user is touching outside the overlay's hit zone or the overlay is shadowed by another view. |
| `JAVA GP inject queued key=... pressed=...` | Java side posted the key inject to the GL thread. |
| `JAVA GP inject fired key=... pressed=...` | The Runnable ran on the GL thread and called `nativeInjectCocos2dKey`. If `queued` appears but `fired` doesn't, the GL thread is stuck. |

## Crashes

| Line | Meaning |
|---|---|
| `signal: 11 (Segmentation fault)` | SIGSEGV — null/bad pointer deref. Usually code bug. |
| `signal: 7 (Bus error)` | SIGBUS — usually heap corruption or unaligned access. v72h saw this in `Bullet::init`, was actually the EventDispatcher race (fixed in v72j). |
| `fault addr: 0x0` | Null deref. |
| `fault addr: 0x1`, `0x2`, `0x3` | Near-null deref via small struct offset. |
| `fault addr: 0x41???????` | Suspicious: that's the range where `float` 4.0–64.0 reinterpreted as a pointer lives. Strongly suggests an uninitialized float field being treated as a pointer. (Saw this in v72g's `ObjectCollision::updateWall` crash.) |

## Crash backtrace tells

| Last frame contains | What it usually is |
|---|---|
| `EventDispatcher::updateDirtyFlagForSceneGraph` | UI-thread / GL-thread race on the listener tree. Wrap inject calls in `queueEvent`. |
| `RenderTextureCtrl::addShader` | Null `RenderTextureCtrl` deref. Need a null check on the caller (see patch #3 in [02](../02-binary-patches.md)). |
| `ObjectCollision::updateWall` | Almost always uninit-field-as-pointer. Check if any TouchGamepad or similar singleton init was nopped. |
| `JavascriptManager::addObject` | `GameManager::getAppName()` returned null on Android. Hot Dog King had source-level fallbacks that aren't in this GitHub repo. Patch the v71 binary or port the fallbacks back into source. |

## Quick triage script (pseudocode)

```sh
LOG=hell_runtime.log

# 1. Crashes
grep -E 'signal:|fault addr:' "$LOG"

# 2. Last scene state
grep 'visitScene:' "$LOG" | tail -3

# 3. Memory
grep -E '^(VmPeak|RSS):' "$LOG" | tail -5

# 4. Lifecycle (was the app backgrounded right before the "freeze"?)
grep -E '^(LIFE|FOCUS) ' "$LOG" | tail -10

# 5. Input path during the freeze window
grep -E '^(INPUT|JAVA GP) ' "$LOG" | tail -20
```

If steps 1–5 don't pinpoint the issue in under 5 minutes, ask for a
clean log run starting from a force-stop + log-delete.
