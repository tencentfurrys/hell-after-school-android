# v72M — diagnostic + fix spec

Scope: confirm the "render alive, update paused" hypothesis from
[`08-v72L-log-1-analysis.md`](08-v72L-log-1-analysis.md) and either
land the actual fix in the same build or set up the next log to
identify the broken callsite within 60 seconds of grepping.

Two tracks, both shippable in one APK:

- **Track A — diag**: add the missing instrumentation around
  pause/resume + scene push/pop + V-button overlay path, and reword
  the misleading OOM log line.
- **Track B — bypass-prep**: stub the V button's overlay handler so it
  routes through a *Java-side* short-circuit we can later swap for a
  real Java menu (the v72M-bypass path Coolkids approved in 06.§v72M).
  Track B's behaviour in v72M itself is identical to current — it just
  moves the dispatch through a single, named function we can replace
  in v72N without touching the overlay.

## Track A — diagnostics

### A1. V button overlay path coverage

Currently a tap on the V button injects keycode 50 to cocos2d. The
inject is invisible in the log because the v72L diag only logs
`JAVA GP inject queued/fired`, but **the v72L diag does in fact log
this** — see `03-gamepad-overlay.md`. The fact that no key=50 line
appears in `logsnew (2).zip` means *the V slot wasn't tapped* in that
session (or its hit-zone is shadowed).

Add the following to `GamepadOverlay.onTouchEvent`, right before the
existing `injectKey(keyCode, ...)` call for face buttons:

```java
// v72M-A1 — V-button trace
if (keyCode == NATIVE_KEY_V) {  // cocos2d KEY_V — confirm the int constant against current AppActivity
    writeDiag("hell_runtime.log",
        "V_BTN tap btn=" + btn +
        " x=" + (int)x + " y=" + (int)y +
        " hitZone=(" + hitL + "," + hitT + "," + hitR + "," + hitB + ")");
}
```

If after v72M a `V_BTN tap` line appears but no `JAVA GP inject queued
key=50` line follows: the overlay is intercepting the tap but the
inject step is being skipped. If `V_BTN tap` doesn't appear at all on
a confirmed-tapped session: the hit-zone is shadowed (likely by the
status-bar inset on the current `FrameLayout`). Either way the next
move is clear.

### A2. Director pause/resume + scene push/pop trace

Add to wherever `nativeInjectCocos2dKey` lands on the native side
(`AppActivity.cpp` / `JniCocos2dxBridge.cpp` — wherever Hot Dog King's
v71 source has the equivalent). Wrap each pause/resume/push/pop in:

```cpp
// v72M-A2 — pause/resume + scene transition trace
extern "C" void agtkLog(const char* fmt, ...);  // existing diag fn

// Patch each of:
void Director::pause() {
    agtkLog("DIRECTOR pause caller=%p paused=%d sched=%d am=%d",
        __builtin_return_address(0),
        _paused, _scheduler->isPaused(), _actionManager->isPaused());
    /* original body */
}
void Director::resume() {
    agtkLog("DIRECTOR resume caller=%p paused=%d", __builtin_return_address(0), _paused);
    /* original body */
}
bool Director::pushScene(Scene* s) {
    agtkLog("DIRECTOR pushScene name=%s ptr=%p stackDepth=%zu",
        s ? typeid(*s).name() : "(null)", s, _scenesStack.size());
    return /* original body */;
}
Scene* Director::popScene() {
    agtkLog("DIRECTOR popScene stackDepth=%zu", _scenesStack.size());
    return /* original body */;
}
```

If the source is unavailable for these (Hot Dog King's `.so` was
binary-patched, not rebuilt — see `02-binary-patches.md`), do this as
a **trampoline patch**: at each of the four function entries, branch
to a small thunk in our injected `.text` region that calls `agtkLog`
then jumps back to the original prologue. ~24 bytes per site; same
toolchain as patches #1–#8.

### A3. Scene::onEnter / onExit trace

Same shape as A2, on `cocos2d::Scene::onEnter` and `::onExit`. Logs
the scene's class name and `getTag()`. Gives us a definitive "menu
scene was pushed *and* its onEnter ran" vs. "menu scene was pushed
but onEnter never fired" signal.

```cpp
void Scene::onEnter() {
    agtkLog("SCENE onEnter name=%s tag=%d", typeid(*this).name(), getTag());
    /* original */
}
void Scene::onExit() {
    agtkLog("SCENE onExit  name=%s tag=%d", typeid(*this).name(), getTag());
    /* original */
}
```

### A4. Reword the misleading OOM line

In whichever Java file handles `onTrimMemory` (likely the
`AppActivity` or a `Cocos2dxActivity` override):

```java
// before
@Override public void onTrimMemory(int level) {
    super.onTrimMemory(level);
    writeDiag("hell_runtime.log", "JAVA onTrimMemory level=" + level);
    if (level >= 15) {
        writeDiag("hell_runtime.log", "CRITICAL memory level! OOM kill imminent.");
    }
}

// after
@Override public void onTrimMemory(int level) {
    super.onTrimMemory(level);
    String tag = level >= 80 ? "TRIM_COMPLETE (backgrounded, normal)"
               : level >= 60 ? "TRIM_MODERATE (backgrounded)"
               : level >= 40 ? "TRIM_BACKGROUND (backgrounded)"
               : level >= 20 ? "TRIM_UI_HIDDEN (backgrounded UI)"
               : level >= 15 ? "RUNNING_CRITICAL (foreground pressure)"
               : level >= 10 ? "RUNNING_LOW (foreground)"
               :               "RUNNING_MODERATE";
    writeDiag("hell_runtime.log",
        "JAVA onTrimMemory level=" + level + " " + tag);
}
```

The `level >= 15 ⇒ CRITICAL OOM kill imminent` line was firing on
every routine background transition (Android sends `level=80` to
backgrounded apps as a normal LRU eligibility signal). Roughly five
minutes per log triage have been lost reading it as a smoking gun.
Drop it.

## Track B — bypass prep (overlay-side)

Goal: make v72N's optional bypass be a *one-function swap*.

Currently `GamepadOverlay.onTouchEvent` for the V button does
something like:

```java
case BTN_V:
    injectKey(KEY_V, true);
    postDelayed(() -> injectKey(KEY_V, false), 50);
    break;
```

Replace with:

```java
case BTN_V:
    onVButtonTap();
    break;

// Default impl in v72M: identical to before. v72N-bypass swaps this
// for a Java-side openMenu() that doesn't go through the broken
// native menu scene.
void onVButtonTap() {
    writeDiag("hell_runtime.log", "V_BTN onVButtonTap dispatch=NATIVE_KEY");
    injectKey(KEY_V, true);
    postDelayed(() -> {
        injectKey(KEY_V, false);
        writeDiag("hell_runtime.log", "V_BTN onVButtonTap returned");
    }, 50);
}
```

No behaviour change in v72M. Gives us:
- "tap was received by overlay" log (`V_BTN onVButtonTap dispatch=...`)
- "tap finished sending key inject" log (`V_BTN ... returned`)
- a clean swap point for v72N-bypass.

## Patch list & cumulative cost

| # | Patch | Track | Where | Bytes |
|---|---|---|---|---|
| 9 | V_BTN tap trace | A1 | `GamepadOverlay.java::onTouchEvent` | source-only |
| 10 | Director pause/resume trace | A2 | source or 4× trampoline patches in `libMyGame.so` | source-only OR ~96 bytes |
| 11 | Scene onEnter/onExit trace | A3 | source or 2× trampoline patches | source-only OR ~48 bytes |
| 12 | onTrimMemory reword | A4 | `Cocos2dxActivity.java` (or `AppActivity.java`) | source-only |
| 13 | V button dispatch shim | B | `GamepadOverlay.java` | source-only |

Cumulative binary delta in `libMyGame.so` ≤ 144 bytes worst case.
All track-A patches are pure logging — *no behaviour change* — so
v72M is functionally equivalent to v72L for gameplay and can be
shipped to Coolkids the moment it builds. Track B is also behaviour-
neutral.

## What "good" looks like after a v72M repro

In `hell_runtime.log`, the freeze window should look like:

```
... JAVA GP touch DOWN ... btn=<V slot>
V_BTN tap btn=<V slot> x=... y=... hitZone=...
V_BTN onVButtonTap dispatch=NATIVE_KEY
JAVA GP inject queued key=50 pressed=true
JAVA GP inject fired key=50 pressed=true
DIRECTOR pause caller=0x... paused=1 sched=1 am=1     ← if this fires, hypothesis confirmed
DIRECTOR pushScene name=<menu> ptr=0x... stackDepth=2  ← if this fires too, menu IS pushed
SCENE onEnter name=<menu> tag=<n>                      ← if this is MISSING, menu never enters
visitScene: ... (keeps ticking)
JAVA GP inject fired key=50 pressed=false
V_BTN onVButtonTap returned
... (no SCENE onExit, no DIRECTOR resume)
```

Three possible outcomes and what they tell us:

| Outcome | What's missing | Root cause | v72N plan |
|---|---|---|---|
| No `V_BTN tap` at all | Tap doesn't reach overlay | Hit-zone shadowed by another view | Bring the overlay to front with `bringToFront()` on every resume |
| `V_BTN tap` ✅, `DIRECTOR pause` ✅, `DIRECTOR pushScene` ✅, `SCENE onEnter` ❌ | Menu scene constructed but `onEnter` skipped | Null in the push path or scene's `init()` returned false | Source-patch (or binary trampoline) the specific menu-scene init that nulls out |
| `V_BTN tap` ✅, `DIRECTOR pause` ✅, `DIRECTOR pushScene` ✅, `SCENE onEnter` ✅, then no `SCENE onExit` and no `DIRECTOR resume` | Menu entered but renders invisible | Same family as the original RT-shader bug — menu's postprocess RT comes up empty (camera offset != 0) | Extend patch #1 / source `isUseShader` guard to cover the menu controller type, or skip RT capture on top-most |

## Out of scope for v72M

- Real menu fix (depends on which of the three outcomes lands).
- v72M-bypass (the Java-side reimplementation of the V menu). That's
  v72N if we choose that fork.
- The bed-save and load-save freezes — same family, will be addressed
  by the same fix once V is root-caused.
- Memory footprint work (still parked, see 04).
