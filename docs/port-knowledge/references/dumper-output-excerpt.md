# In-game dumper output — key excerpts

The dumper was Coolkids' addition to v71's `libMyGame.so` — it writes
per-frame scene/layer state into `hell_runtime.log`. These two
excerpts are what broke the black-world bug open on 2026-05-27.

## Loading scene (works — direct visit path)

```
visitScene: camera pos=(0,0)
layer 4 direct visit visible=1 children=6 pos=(0,0) size=(1366,768)
layer 3 direct visit visible=1 children=6 pos=(0,0) size=(1366,768)
layer 2 direct visit visible=1 children=4 pos=(0,0) size=(1366,768)
layer 1 direct visit visible=1 children=2 pos=(0,0) size=(1366,768)
```

Every layer reports:
- `direct visit` — the working render path
- `pos=(0,0)` — camera at origin
- `size=(1366,768)` — RT allocated at screen size (no oversized RT)
- `visible=1` — all layers active

## Tutorial scene (black — RT shader path)

```
visitScene: camera pos=(8196,0)
bg  via RT sprite  visible=1 pos=(8196,0) size=(1366,768)
layer 12 via RT shader visible=1 pos=(8196,0)
layer 11 via RT shader visible=1 pos=(8196,0)
layer 10 via RT shader visible=1 pos=(8196,0)
layer 9  via RT shader visible=1 pos=(8196,0)
layer 8  via RT shader visible=1 pos=(8196,0)
layer 7  via RT shader visible=1 pos=(8196,0)
layer 6  via RT shader visible=1 pos=(8196,0)
layer 5  via RT shader visible=1 pos=(8196,0)
layer 4  via RT shader visible=1 pos=(8196,0)
layer 3  via RT shader visible=1 pos=(8196,0)
layer 2  via RT shader visible=1 pos=(8196,0)
layer 1  via RT shader visible=1 pos=(8196,0)
```

Same `size=(1366,768)` — RT allocation is fine.
Different `via RT shader` path — this is what comes back black.
Same `pos=(8196,0)` for every layer — that's the camera offset.

The two scenes differ in exactly one thing: which render path
`isUseShader()` selects. Hence the patch in
[01-world-not-rendering-fix.md](../01-world-not-rendering-fix.md)
targets exactly that function.

## Crash backtrace — v72c (Scene::setShader)

The signature that led to patch #3:

```
signal: 11 (SIGSEGV), fault addr 0x0
#00 pc 0x????????  RenderTextureCtrl::addShader+0x1f
#01 pc 0x????????  Scene::setShader+0x153
#02 pc 0x????????  ObjectAction::execActionSceneEffect+...
#03 pc 0x????????  Object::update+...
#04 pc 0x????????  Scene::update+...
```

`addShader+0x1f` on a null `this` pointer (fault addr `0x0`).

## Crash backtrace — v72g (ObjectCollision::updateWall)

Reverted-from patch (don't reapply):

```
signal: 11 (SIGSEGV), fault addr 0x41600004
#00 pc 0x????????  ObjectCollision::updateWall+...
#01 pc 0x????????  Scene::update+...
```

`0x41600004` is `14.0f` reinterpreted as a pointer — a clear "we read an
uninitialized float member as a pointer" signature. Caused by NOPing
`TouchGamepad::attachToScene` prologue (which prevented init of the
gamepad singleton's fields, which some other agtk subsystem then
deref'd).

## Crash backtrace — v72i (EventDispatcher race)

The signature that led to v72j's `queueEvent` wrap:

```
signal: 11 (SIGSEGV)
#03 pc 0x????????  cocos2d::EventDispatcher::updateDirtyFlagForSceneGraph+0x184
#04 pc 0x????????  cocos2d::EventDispatcher::dispatchEvent+0x3c
#05 pc 0x????????  cocos2d::Director::drawScene+0xf0
#06 pc 0x????????  cocos2d::Director::mainLoop+0x88
```

GL thread crashed inside the event dispatcher walking a corrupted
listener tree. Race condition with my UI-thread `dispatchEvent` call.
