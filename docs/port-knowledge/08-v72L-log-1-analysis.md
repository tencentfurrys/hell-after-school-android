# v72L log #1 analysis — Coolkids, 2026-05-30

First clean(ish) v72L capture from Coolkids. Source: `logsnew (2).zip`
posted in #general on 2026-05-30 02:33 ET. Contains `boot.log`,
`native_boot.log`, `input.log`, `hell_runtime.log`.

The headline finding is **the inverse** of the working hypothesis in
[`06-open-bugs-and-next-steps.md`](06-open-bugs-and-next-steps.md): the
GL render thread does *not* stop after V is pressed. `visitScene:`
keeps ticking for the entire session. What stops is the *update* path
— scheduler, action manager, physics step — i.e. `Director::pause()`
semantics, not "GL thread stuck".

Updating [`06-open-bugs-and-next-steps.md`](06-open-bugs-and-next-steps.md)
in the same PR.

## Session summary

| File | Lines | Span | Notable |
|---|---:|---|---|
| `boot.log` | a few | start | onLoadNativeLibraries + onCreate OK, no rethrow |
| `native_boot.log` | small | start | engine init OK |
| `input.log` | 1474 | 0–404.3 s | `LIFE onResume` + `FOCUS hasFocus=true` early, 1470 `INPUT TOUCH`, **0 `INPUT KEY`**, `LIFE onPause` + `FOCUS hasFocus=false` at end |
| `hell_runtime.log` | 5106 | 0–404.3 s | 3476 `visitScene*` lines, `JAVA GP touch`/`inject` covering the whole session, final two lines = `onTrimMemory level=80` + the misleading "CRITICAL OOM kill imminent" |

Total wall time: ~6:44, ended by user backgrounding (not by a crash).

### What's healthy

- Input dispatch — 1470 `INPUT TOUCH` events reach the activity.
  The v72k hypothesis that touch dispatch was being silently dropped
  by log-write contention is **disproven**: with the dedicated
  `input.log` writer, the full stream is captured.
- Native engine update — scene transitions fire continuously: Loading →
  Title → Tutorial movie → `SchoolMain_6-Clean` → `SchoolMain_6/F Right`
  → `SchoolMain_6-E` → back → back. Memory steady (`VmPeak` 1.75 GB,
  `VmRSS` 430–445 MB). No SIGSEGV, no GL error, no main-thread stall
  trace.
- GL-thread key inject (the v72j queueEvent wrapper) — every `JAVA GP
  inject queued` is followed by a matching `JAVA GP inject fired`
  within ~20 ms. No `queued`-without-`fired` pattern anywhere.

### What's notable

- **`INPUT KEY count = 0`.** Coolkids was on a touchscreen test bench
  for this session, so the absence of `INPUT KEY` lines is expected —
  but it also means *the V button is reached only through the Java
  overlay's touch path, which never injects keycode 50 (`KEYCODE_V`)*.
  Of the 1470 touches, every `JAVA GP inject` keycode is one of `12,
  14, 26, 27, 28, 29, 59, 145, 147, 149` — i.e. the 10 game-action
  mappings (D-pad, Z, C, X, RELOAD/DNA combos, etc.). **There is no
  inject for the V button anywhere in this log.** Either Coolkids did
  not tap V in this session, or the overlay's V hit-zone wasn't
  triggered. See "Open question to Coolkids" below.
- The clip Coolkids shared (80 s, ending where this log session ends)
  does show a visual freeze starting ~50 s before backgrounding —
  character locked in a running pose, gamepad overlay still composited
  on top, no menu UI ever drawn.
- That visual freeze is **consistent with the engine continuing to
  emit `visitScene:` while the update loop is paused** — render keeps
  drawing the same paused state, animations don't advance, but draw
  calls keep going.

## Updated hypothesis (replaces 06.§1.1–3)

The V-menu open path almost certainly calls `Director::pause()` (or
the AGTK equivalent — `GameScene::pauseGame`, `Scene::pauseAll`)
which suspends the scheduler + action manager + physics step, *without
suspending the GL surface visitor*. The menu scene then either:

1. fails to push (e.g. nulls out before `Scene::onEnter`),
2. pushes but renders empty because of a postprocess RT issue, or
3. pushes a transparent / zero-sized node tree.

In all three cases the visible result is the same: paused world,
overlay still drawn, no menu, no input progress, no exception.

The previous hypothesis ("GL render thread stops within 1 frame after
V press") was based on v72k data with much less coverage. v72L's
`visitScene` counter ticking through to `onPause` invalidates it.

## What this means for v72M

The next instrumentation gap is on the *menu-open* boundary, not the
input boundary:

- Log `Director::pause` / `Director::resume` callsites.
- Log `pushScene` / `replaceScene` / `popScene` calls (which scene
  was pushed, did `onEnter` run, did `onExit` run).
- Log `setSchedulerPaused` / `setActionManagerPaused` callsites if
  AGTK has its own wrappers.
- Inject a known V-key fire path through the overlay (currently the V
  button's keycode is missing from the inject log — fix that first or
  we won't even know we're entering the broken path).
- Reword the misleading "CRITICAL OOM kill imminent" line.

The actual v72M diff spec is in
[`09-v72M-spec.md`](09-v72M-spec.md).

## Open question to Coolkids

1. In the session captured here, did you actually *tap the V button*
   on the on-screen overlay? Or did you press something else and the
   freeze happened earlier? The log doesn't show any inject for V's
   keycode (50). If you tapped V and there's no `JAVA GP touch
   DOWN ... btn=<V slot>` line for it, the overlay's V hit-zone is
   shadowed by another view — that's a different (smaller) bug we
   can fix immediately.
2. Was screen-recording happening for the whole session, or only
   for the last 80 s? Confirms whether the freeze you saw in the
   clip is the same event as the end of this log session.

## Lessons added

- v72L's input/lifecycle/focus diag is well-scoped — keep it as the
  baseline.
- Always check whether `visitScene` ticked across the freeze window
  before assuming the GL thread stalled. Render-loop-alive + update-
  loop-paused looks identical from a player's POV to "GL thread
  stuck" but has a completely different root cause.
- The misleading `CRITICAL memory level! OOM kill imminent.` line
  needs to be downgraded. It fires from `onTrimMemory(level=80)`
  which is just "you're backgrounded" on Android, not a real OOM.
  Currently it costs ~5 minutes of triage time on every log read.
