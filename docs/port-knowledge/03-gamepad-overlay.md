# Java on-screen gamepad overlay

The original Hot Dog King v71 ships a built-in `agtk::TouchGamepad` C++
overlay with eight tiny corner buttons (`L / R / SE / ST / X / Y / A / B`)
that don't expose Shift, Ctrl, or Space — so reload, DNA sample, dash,
and aim are physically unbindable on Android. We replaced it with a
purpose-built Java overlay laid out Xbox-style, pulled inward from the
edges, with multi-touch combo presses.

## Architecture

Three layers:

1. **C++ TouchGamepad neutered** via binary patches #4–#8 in
   [02-binary-patches.md](02-binary-patches.md). The C++ singleton still
   initializes (so internal state stays sane) but draws nothing and
   captures no touches.
2. **`com.cooolkidds.hellafterschool.GamepadOverlay` (Java)** — a custom
   `View` added to the activity's window above the GL surface. Owns all
   button bitmaps, hit testing, multi-touch tracking, and combo state
   machines. Compiled with `javac` → `d8` → packed into `classes2.dex`
   inside the APK.
3. **`AppActivity` (Java)** — the cocos2d-x Android entry point. Hosts
   the `Cocos2dxGLSurfaceView` and adds the overlay to its
   `FrameLayout`. Also provides the GL-thread-safe key inject
   (`queueEvent`) used by the overlay.

## Final keymap

Source of truth: `Tutorial_Keybind.txt` provided by Coolkids on
2026-05-28 (mirror in [`references/Tutorial_Keybind.txt`](references/Tutorial_Keybind.txt)).

| Visible button | Sends to cocos2d | In-game meaning |
|---|---|---|
| D-Pad ↑ ↓ ← → | Arrow keys (double-tap → sprint) | Walk / select |
| Z (A position) | `Z` | Attack / Shoot / Confirm |
| C (B position) | `C` | Change Weapon |
| X (X position) | `X` | Cancel / Exit Menu / Search |
| V (Y position) | `V` | Open Menu *(currently freezes — see [06](06-open-bugs-and-next-steps.md))* |
| CROUCH | `Ctrl` (toggle) | Crouch — combine with X on body for DNA |
| RELOAD | `Shift + X` combo | Reload gun |
| DNA | `Ctrl + X` combo | Take DNA sample (stand on body) |
| SHOOT ↑ | `Shift + Up + Z` combo | Aim up + fire |
| SHOOT ↓ | `Shift + Down + Z` combo | Aim down + fire |
| DASH (bottom center) | `Space` | Dash |

The AIM-drag zone that briefly existed in v72f was removed in v72g per
Coolkids' annotated screenshot — replaced by the two SHOOT buttons.

## Layout (final, v72g+)

```
[RELOAD]                                [  DNA   ]
[CROUCH]                                [SHOOT ↑]
                                        [SHOOT ↓]
      ↑                                       V
  ←     →                                X     C
      ↓                                       Z
                  [   DASH   ]
```

Buttons inset ~16% from each edge so they're not pinned to corners.
D-Pad and face-button gap was tightened to `1.55r` (from `1.05r` in
v72f) so circles don't visually overlap.

## Multi-touch + combos

Each touch is tracked by `MotionEvent` pointer ID. The combo presses use
a small state machine because cocos2d's keyboard dispatcher samples key
state per frame, so:

- `Shift down → wait 35 ms → X down → wait 50 ms → X up → wait 35 ms →
  Shift up` (RELOAD)

That ~120 ms total guarantees the engine sees both keys held in the
same frame (60 fps = 16.6 ms, dropping to ~20 fps under load = 50 ms).
Same pattern for DNA (Ctrl + X) and SHOOT (Shift + ↑/↓ + Z).

The combos run on a `Handler` posted with `View.postDelayed`. Each step
calls `injectKey(keyCode, pressed)` which is the thread-safety wrapper
described below.

## GL-thread safety wrapper

This is the patch that turned the v72i "V-menu crash that looked like a
freeze" into a non-issue (verified — v72j+ no longer throws
`updateDirtyFlagForSceneGraph` SIGSEGV).

Before:

```java
void injectKey(int code, boolean pressed) {
    nativeInjectCocos2dKey(code, pressed);   // called from UI thread
}
```

`nativeInjectCocos2dKey` internally calls
`cocos2d::EventDispatcher::dispatchEvent(...)`, which walks the listener
tree. The GL thread also walks the listener tree every frame. Concurrent
mutation → torn pointer → SIGSEGV in
`EventDispatcher::updateDirtyFlagForSceneGraph`.

After (v72j+):

```java
void injectKey(final int code, final boolean pressed) {
    Cocos2dxGLSurfaceView glView = Cocos2dxGLSurfaceView.getInstance();
    if (glView == null) return;
    glView.queueEvent(new Runnable() {
        @Override public void run() {
            nativeInjectCocos2dKey(code, pressed);
        }
    });
}
```

`Cocos2dxGLSurfaceView.queueEvent` posts to the GL thread's looper.
Inject now happens in the same thread as the render loop, no race.

## Diagnostic logging (v72L)

To debug the remaining V/save/load freezes, v72L adds the following log
calls — all of them write to the same `hell_runtime.log` the engine
uses (`/Android/data/com.sthdk.hellafterschool/files/hell_runtime.log`),
appending a timestamped line:

- `JAVA GP touch DOWN x=... y=... btn=...` — finger touches the overlay
- `JAVA GP inject queued key=... pressed=...` — `queueEvent` posted
- `JAVA GP inject fired key=... pressed=...` — Runnable ran on GL thread
- `INPUT KEY act=... code=...` — any hardware/keyboard key
  (`AppActivity.dispatchKeyEvent` override) — catches physical keyboard
  V on PC/emulator + phone hardware keys
- `INPUT TOUCH act=... x=... y=...` — any touch reaching the activity
- `FOCUS hasFocus=...` — window focus changes
- `LIFE onPause` / `LIFE onResume` — activity lifecycle

These are spec'd to be left in by default until the freezes are fully
diagnosed — they don't measurably impact framerate (1 log line per key
event ≈ a few hundred per minute of play).

## Files (target locations in repo)

When this work is ported back to source, the Java side lives in:

- `Player/proj.android-studio/app/src/org/cocos2dx/cpp/AppActivity.java`
- `Player/proj.android-studio/app/src/com/cooolkidds/hellafterschool/GamepadOverlay.java`
- `Player/proj.android-studio/app/src/com/cooolkidds/hellafterschool/GamepadOverlay$ButtonState.java` (inner class)
- `Player/proj.android-studio/app/src/main/AndroidManifest.xml` —
  references the activity, NO `largeHeap` / `extractNativeLibs`
  overrides (those made memory worse — see [04](04-memory-and-oom.md)).

For shipped APKs the Java is compiled to dex and merged into the
existing `classes2.dex` (or added as `classes3.dex` if size requires).

## Resources

Bitmaps are loaded from `res/drawable-xxhdpi/`:
- `pad_dpad.png` — 4-direction D-pad sprite sheet
- `pad_face_z.png`, `pad_face_x.png`, `pad_face_c.png`, `pad_face_v.png` — face buttons
- `pad_reload.png`, `pad_dna.png`, `pad_crouch.png` — left/right shoulder area
- `pad_shoot_up.png`, `pad_shoot_down.png` — under DNA
- `pad_dash.png` — bottom center

Sizes are computed at runtime from the GL surface size (touch targets
scale with screen width).

## Open issues with the overlay itself

- The v72k–v72L logs from MEMU showed **zero `JAVA GP touch` lines** even
  though Coolkids tapped the V button on screen. Two possibilities:
  - The user pressed the *physical* V key on a PC keyboard, which goes
    through `Cocos2dxGLSurfaceView.dispatchKeyEvent`, bypassing the
    overlay's touch listener entirely. In that case the bug is in the
    cocos2d key path, not the overlay.
  - The overlay's touch listener is being shadowed by another `View` in
    the z-order. To check: `adb shell dumpsys window | grep AppActivity`
    and confirm the overlay is on top.

  v72L's `INPUT KEY` logging will disambiguate — if `INPUT KEY code=47`
  fires (47 = `KEYCODE_V`) but no `JAVA GP` lines do, it was the
  keyboard path.
