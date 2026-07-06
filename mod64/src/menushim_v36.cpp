// Reconstructed arm64 libmenushim.so for [redacted-secret]
// Bridges the Java on-screen controls to the cocos2d/PGMMV engine (libMyGame.so)
// via runtime dlsym. TouchGamepad symbols are absent in the arm64 engine build, so
// injectKey degrades to a no-op (guarded); InputManager/GameManager paths work.
#include <jni.h>
#include <dlfcn.h>
#include <android/log.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <fcntl.h>
#include <unwind.h>
#include <stdint.h>

#define LOGI(...) __android_log_print(ANDROID_LOG_INFO,  "MenuShim", __VA_ARGS__)
#define LOGW(...) __android_log_print(ANDROID_LOG_WARN,  "MenuShim", __VA_ARGS__)

// ---- engine function pointer types (C++ member functions; first arg = this) ----
typedef void* (*fn_tg_getInstance)();
typedef void  (*fn_tg_inject)(void* self, int keyCode);          // TouchGamepad::injectKeyPress/Release(cocos2d::EventKeyboard::KeyCode)
typedef void* (*fn_im_getInstance)();
typedef void  (*fn_im_setPrecede)(void* self, int a, int b, int triggerType, int inst);
typedef void  (*fn_im_setJudge)(void* self);
typedef void* (*fn_gm_getInstance)();
typedef void* (*fn_gm_getPlayData)(void* self);
typedef void* (*fn_pd_getCommonVar)(void* self, int varId);
typedef void  (*fn_pv_setValue)(void* self, double value);

static int   s_initState = 0;          // 0=not tried, 1=ok, -1=failed
static void* s_libHandle = nullptr;
static char  s_diagPath[512] = {0};

static fn_tg_getInstance  s_tg_getInstance  = nullptr;
static fn_tg_inject       s_tg_injectPress  = nullptr;
static fn_tg_inject       s_tg_injectRelease= nullptr;
static fn_im_getInstance  s_im_getInstance  = nullptr;
static fn_im_setPrecede   s_im_setPrecedeTrig= nullptr;
static fn_im_setPrecede   s_im_setPrecedeRel = nullptr;
static fn_im_setJudge     s_im_setPrecedeJudge= nullptr;
static fn_gm_getInstance  s_gm_getInstance  = nullptr;
static fn_gm_getPlayData  s_gm_getPlayData  = nullptr;
static fn_pd_getCommonVar s_pd_getCommonVar = nullptr;
static fn_pv_setValue     s_pv_setValue     = nullptr;

// v36 additions
static fn_idr_registerKeyPressed  s_idr_registerKeyPressed  = nullptr;
static fn_idr_registerKeyReleased s_idr_registerKeyReleased = nullptr;
static fn_ic_isPressedPc          s_ic_isPressedPc          = nullptr;
static fn_im_isPressedKeyboard    s_im_isPressedKeyboard    = nullptr;

// Same-frame press+release guard. If a press+release for the same cc arrive
// inside the same InputManager::update() drain window, the release would
// overwrite the press and the tap is swallowed. We enforce a minimum
// one-frame hold by remembering the last frame each cc was pressed on and
// deferring any release that arrives on the same "frame tick" (tracked by a
// coarse monotonic counter incremented by the poller probe below; falls back
// to CLOCK_MONOTONIC millis if the probe never runs).
#include <time.h>
#include <atomic>
static std::atomic<uint64_t> s_frameTick{0};          // bumped by probe (once per frame)
static uint64_t s_lastPressTick[512] = {0};           // indexed by (cc & 0x1FF)
static uint64_t nowMonoMs() {
    struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000ull + (uint64_t)(ts.tv_nsec / 1000000ull);
}
static uint64_t currentTick() {
    uint64_t t = s_frameTick.load(std::memory_order_relaxed);
    return t ? t : nowMonoMs();
}

static void writeDiagFmt(const char* fmt, ...) {
    if (!s_diagPath[0]) return;
    FILE* f = fopen(s_diagPath, "a");
    if (!f) return;
    va_list ap; va_start(ap, fmt);
    vfprintf(f, fmt, ap);
    va_end(ap);
    fclose(f);
}

static void* sym(void* h, const char* name) {
    void* p = dlsym(h, name);
    return p;
}

// ----------------------- native crash handler ------------------------------
// Catches SIGSEGV/SIGABRT/etc, writes faulting addr + backtrace (resolved to
// library+offset via dladdr) to <diagDir>/native_crash.txt, then re-raises so a
// normal tombstone still happens. Lets us see the real crash on devices where
// we cannot read logcat (e.g. Samsung RTL auto-scrolling Logs panel).
static char s_crashPath[600] = {0};
static struct sigaction s_old[8];
static const int s_sigs[] = { SIGSEGV, SIGABRT, SIGBUS, SIGILL, SIGFPE };

struct BtState { void** pcs; int count; int max; };
static _Unwind_Reason_Code unwindCb(_Unwind_Context* ctx, void* arg) {
    BtState* st = (BtState*)arg;
    uintptr_t ip = _Unwind_GetIP(ctx);
    if (ip && st->count < st->max) st->pcs[st->count++] = (void*)ip;
    return st->count >= st->max ? _URC_END_OF_STACK : _URC_NO_REASON;
}

static void writeAll(int fd, const char* b, int n){ while(n>0){ int w=write(fd,b,n); if(w<=0) break; b+=w; n-=w; } }
static void writeStr(int fd, const char* s){ writeAll(fd, s, (int)strlen(s)); }

static void crashHandler(int sig, siginfo_t* info, void* uc) {
    int fd = -1;
    if (s_crashPath[0]) fd = open(s_crashPath, O_WRONLY|O_CREAT|O_TRUNC, 0644);
    char line[512];
    snprintf(line, sizeof(line), "NATIVE CRASH sig=%d code=%d faultAddr=%p\n",
             sig, info?info->si_code:0, info?info->si_addr:(void*)0);
    __android_log_print(ANDROID_LOG_FATAL, "MenuShim", "%s", line);
    if (fd>=0) writeStr(fd, line);

    void* pcs[64]; BtState st = { pcs, 0, 64 };
    _Unwind_Backtrace(unwindCb, &st);
    for (int i=0;i<st.count;i++) {
        Dl_info di; const char* lib="?"; const char* sym="?"; uintptr_t off=0, soff=0;
        if (dladdr(pcs[i], &di)) {
            if (di.dli_fname) { const char* sl=strrchr(di.dli_fname,'/'); lib = sl?sl+1:di.dli_fname; }
            if (di.dli_fbase) off = (uintptr_t)pcs[i] - (uintptr_t)di.dli_fbase;   // offset in library
            if (di.dli_sname) { sym = di.dli_sname; soff = (uintptr_t)pcs[i] - (uintptr_t)di.dli_saddr; }
        }
        snprintf(line, sizeof(line), "#%02d pc %012lx  %s  (%s+0x%lx)\n",
                 i, (unsigned long)off, lib, sym, (unsigned long)soff);
        __android_log_print(ANDROID_LOG_FATAL, "MenuShim", "%s", line);
        if (fd>=0) writeStr(fd, line);
    }
    if (fd>=0) close(fd);

    // restore default and re-raise so the process dies normally / tombstone
    for (unsigned k=0;k<sizeof(s_sigs)/sizeof(s_sigs[0]);k++)
        if (s_sigs[k]==sig) sigaction(sig, &s_old[k], nullptr);
    raise(sig);
}

static void installCrashHandler() {
    static int done = 0; if (done) return; done = 1;
    // alt stack so SIGSEGV from stack overflow is still catchable
    static char altstk[64*1024];
    stack_t ss; ss.ss_sp = altstk; ss.ss_size = sizeof(altstk); ss.ss_flags = 0;
    sigaltstack(&ss, nullptr);
    struct sigaction sa; memset(&sa,0,sizeof(sa));
    sa.sa_sigaction = crashHandler; sa.sa_flags = SA_SIGINFO | SA_ONSTACK; sigemptyset(&sa.sa_mask);
    for (unsigned k=0;k<sizeof(s_sigs)/sizeof(s_sigs[0]);k++)
        sigaction(s_sigs[k], &sa, &s_old[k]);
    LOGI("crash handler installed -> %s", s_crashPath[0]?s_crashPath:"(no path yet)");
}

// derive <dir>/native_crash.txt from the diag file path the app gave us
static void deriveCrashPath() {
    if (!s_diagPath[0]) return;
    strncpy(s_crashPath, s_diagPath, sizeof(s_crashPath)-1);
    char* sl = strrchr(s_crashPath, '/');
    if (sl) { strcpy(sl+1, "native_crash.txt"); }
    else    { snprintf(s_crashPath, sizeof(s_crashPath), "native_crash.txt"); }
}

static void ensureInit() {
    if (s_initState != 0) return;

    // The engine lib is already loaded by the app; grab a handle to it.
    s_libHandle = dlopen("libMyGame.so", RTLD_NOW | RTLD_NOLOAD | RTLD_GLOBAL);
    if (!s_libHandle) s_libHandle = dlopen("libMyGame.so", RTLD_NOW | RTLD_GLOBAL);
    if (!s_libHandle) {
        LOGW("dlopen FAILED: %s", dlerror());
        s_initState = -1;
        return;
    }

    s_tg_getInstance   = (fn_tg_getInstance) sym(s_libHandle, "[redacted-secret]");
    s_tg_injectPress   = (fn_tg_inject)      sym(s_libHandle, "[redacted-secret]");
    s_tg_injectRelease = (fn_tg_inject)      sym(s_libHandle, "[redacted-secret]");
    s_im_getInstance   = (fn_im_getInstance) sym(s_libHandle, "[redacted-secret]");
    s_im_setPrecedeTrig= (fn_im_setPrecede)  sym(s_libHandle, "[redacted-secret]");
    s_im_setPrecedeRel = (fn_im_setPrecede)  sym(s_libHandle, "[redacted-secret]");
    s_im_setPrecedeJudge=(fn_im_setJudge)    sym(s_libHandle, "[redacted-secret]");
    s_gm_getInstance   = (fn_gm_getInstance) sym(s_libHandle, "[redacted-secret]");
    s_gm_getPlayData   = (fn_gm_getPlayData) sym(s_libHandle, "[redacted-secret]");
    s_pd_getCommonVar  = (fn_pd_getCommonVar)sym(s_libHandle, "[redacted-secret]");
    s_pv_setValue      = (fn_pv_setValue)    sym(s_libHandle, "[redacted-secret]");

    // v36: real fix + probe symbols (confirmed present in arm64 libMyGame.so 2026-07-06)
    s_idr_registerKeyPressed  = (fn_idr_registerKeyPressed ) sym(s_libHandle, "_ZN12InputDataRaw18registerKeyPressedEii");
    s_idr_registerKeyReleased = (fn_idr_registerKeyReleased) sym(s_libHandle, "_ZN12InputDataRaw19registerKeyReleasedEii");
    s_ic_isPressedPc          = (fn_ic_isPressedPc         ) sym(s_libHandle, "_ZN15InputController11isPressedPcEi");
    s_im_isPressedKeyboard    = (fn_im_isPressedKeyboard   ) sym(s_libHandle, "_ZN12InputManager17isPressedKeyboardEi");
    LOGI("v36 sym: idrPress=%p idrRel=%p isPressedPc=%p isPressedKbd=%p",
         (void*)s_idr_registerKeyPressed,(void*)s_idr_registerKeyReleased,
         (void*)s_ic_isPressedPc,(void*)s_im_isPressedKeyboard);
    writeDiagFmt("v36 sym idrP=%p idrR=%p pc=%p kb=%p\n",
         (void*)s_idr_registerKeyPressed,(void*)s_idr_registerKeyReleased,
         (void*)s_ic_isPressedPc,(void*)s_im_isPressedKeyboard);

    LOGI("init: tg(%p,%p,%p) im(%p,%p,%p,%p) gm(%p,%p) pd(%p) pv(%p)",
         (void*)s_tg_getInstance,(void*)s_tg_injectPress,(void*)s_tg_injectRelease,
         (void*)s_im_getInstance,(void*)s_im_setPrecedeTrig,(void*)s_im_setPrecedeRel,(void*)s_im_setPrecedeJudge,
         (void*)s_gm_getInstance,(void*)s_gm_getPlayData,(void*)s_pd_getCommonVar,(void*)s_pv_setValue);
    writeDiagFmt("MenuShim init tg=%p im=%p gm=%p pv=%p\n",
         (void*)s_tg_getInstance,(void*)s_im_getInstance,(void*)s_gm_getInstance,(void*)s_pv_setValue);

    // Consider init OK if the InputManager OR variable API is available. We do NOT
    // hard-fail on missing TouchGamepad so the engine still boots on arm64.
    if (s_im_getInstance || s_gm_getInstance) {
        s_initState = 1;
    } else {
        LOGW("init FAILED: missing variable API symbols");
        s_initState = -1;
    }
}

extern "C" {

JNIEXPORT void JNICALL
[redacted-secret](JNIEnv* env, jclass, jstring path) {
    if (!path) { s_diagPath[0] = 0; return; }
    const char* p = env->GetStringUTFChars(path, nullptr);
    if (p) { strncpy(s_diagPath, p, sizeof(s_diagPath) - 1); s_diagPath[sizeof(s_diagPath)-1] = 0;
             env->ReleaseStringUTFChars(path, p); }
    deriveCrashPath();
    installCrashHandler();
    LOGI("diag path set; crash log -> %s", s_crashPath);
}

JNIEXPORT jint JNICALL
[redacted-secret](JNIEnv*, jclass) {
    installCrashHandler();
    ensureInit();
    return s_initState == 1 ? 1 : 0;
}

JNIEXPORT jint JNI_OnLoad(JavaVM*, void*) {
    installCrashHandler();
    return JNI_VERSION_1_6;
}

// v36 rich probe: bumps a coarse frame tick and logs what the engine's
// poll-side readers see for this cc, so one run empirically confirms the
// arm64 build still polls the keyboard path (isPressedKeyboard etc.).
static void v36_probe(int cc) {
    s_frameTick.fetch_add(1, std::memory_order_relaxed);
    if (!s_im_getInstance) return;
    void* im = s_im_getInstance();
    if (!im) return;
    int kb = -1;
    if (s_im_isPressedKeyboard) kb = s_im_isPressedKeyboard(im, cc) ? 1 : 0;
    LOGI("v36 probe cc=%d tick=%llu isPressedKeyboard=%d",
         cc, (unsigned long long)s_frameTick.load(), kb);
    writeDiagFmt("v36 probe cc=%d tick=%llu kb=%d\n",
         cc, (unsigned long long)s_frameTick.load(), kb);
}

// v36: injectKey is repurposed. The Java-declared native remains
// MenuShim.injectKey(int keyCode, boolean pressed) so we do NOT need any
// RegisterNatives changes, and existing overlay smali call sites keep resolving.
//
// In v34 this dlsymed TouchGamepad::injectKey{Press,Release} which are absent
// on the arm64 engine -> no-op. v36 routes into the REAL path the game polls:
//
//   InputManager::getInstance()
//     ->getInputDataRaw()
//     ->registerKeyPressed / registerKeyReleased(cc, 0)
//
// then the engine's own per-frame InputManager::update() drains
// applyRegisteredData() and the poller sees _press across frames.
//
// scancode=0 is safe (release matches on mapped keyCode only). Same-tick
// press+release would be swallowed by a single frame drain, so we hold any
// release that arrives on the same tick as its press for ~20 ms (>= 1 frame
// at 60 Hz). The tick counter is bumped by nativeProbeInput below; when the
// probe isn't attached we fall back to CLOCK_MONOTONIC millis.
JNIEXPORT jboolean JNICALL
[redacted-secret](JNIEnv*, jclass, jint keyCode, jboolean pressed) {
    ensureInit();
    if (!s_im_getInstance || !s_idr_registerKeyPressed || !s_idr_registerKeyReleased) {
        LOGW("v36 injectKey MISS-SYMS im=%p p=%p r=%p",
             (void*)s_im_getInstance, (void*)s_idr_registerKeyPressed, (void*)s_idr_registerKeyReleased);
        return JNI_FALSE;
    }
    void* im = s_im_getInstance();
    if (!im) { LOGW("v36 injectKey im=null"); return JNI_FALSE; }
    // InputManager::getInputDataRaw() is a const member; ABI same as non-const.
    typedef void* (*fn_im_getIdr)(void* self);
    static fn_im_getIdr s_getIdr = nullptr;
    if (!s_getIdr) s_getIdr = (fn_im_getIdr) sym(s_libHandle, "_ZNK12InputManager15getInputDataRawEv");
    if (!s_getIdr) { LOGW("v36 injectKey getInputDataRaw sym missing"); return JNI_FALSE; }
    void* idr = s_getIdr(im);
    if (!idr) { LOGW("v36 injectKey idr=null"); return JNI_FALSE; }

    int idx = ((unsigned)keyCode) & 0x1FF;
    if (pressed) {
        v36_probe(keyCode);                                  // rich probe + tick bump
        s_lastPressTick[idx] = currentTick();
        LOGI("v36 injectKey PRESS  cc=%d idr=%p tick=%llu",
             keyCode, idr, (unsigned long long)s_lastPressTick[idx]);
        s_idr_registerKeyPressed(idr, keyCode, 0);
    } else {
        uint64_t now = currentTick();
        if (s_lastPressTick[idx] && now == s_lastPressTick[idx]) {
            LOGI("v36 injectKey RELEASE cc=%d SAME-TICK -> hold 20ms", keyCode);
            struct timespec ts = { 0, 20 * 1000 * 1000 };
            nanosleep(&ts, nullptr);
        }
        LOGI("v36 injectKey RELEASE cc=%d idr=%p", keyCode, idr);
        s_idr_registerKeyReleased(idr, keyCode, 0);
    }
    return JNI_TRUE;
}

JNIEXPORT jboolean JNICALL
[redacted-secret](JNIEnv*, jclass, jint a, jint b, jint type, jint inst) {
    ensureInit();
    if (!s_im_getInstance || !s_im_setPrecedeTrig) return JNI_FALSE;
    void* im = s_im_getInstance();
    if (!im) return JNI_FALSE;
    LOGI("precedeTrig im=%p ctrl=%d keyId=%d type=%d inst=%d", im, a, b, type, inst);
    s_im_setPrecedeTrig(im, a, b, type, inst);
    if (s_im_setPrecedeJudge) s_im_setPrecedeJudge(im);
    return JNI_TRUE;
}

JNIEXPORT jboolean JNICALL
[redacted-secret](JNIEnv*, jclass, jint a, jint b, jint type, jint inst) {
    ensureInit();
    if (!s_im_getInstance || !s_im_setPrecedeRel) return JNI_FALSE;
    void* im = s_im_getInstance();
    if (!im) return JNI_FALSE;
    s_im_setPrecedeRel(im, a, b, type, inst);
    if (s_im_setPrecedeJudge) s_im_setPrecedeJudge(im);
    return JNI_TRUE;
}

JNIEXPORT jint JNICALL
[redacted-secret](JNIEnv*, jclass, jint varId, jdouble value) {
    ensureInit();
    if (!s_gm_getInstance || !s_gm_getPlayData || !s_pd_getCommonVar || !s_pv_setValue) return 0;
    void* gm = s_gm_getInstance();              if (!gm) return 0;
    void* pd = s_gm_getPlayData(gm);            if (!pd) return 0;
    void* pv = s_pd_getCommonVar(pd, varId);    if (!pv) return 0;
    s_pv_setValue(pv, value);
    return 1;
}

JNIEXPORT jdouble JNICALL
[redacted-secret](JNIEnv*, jclass, jint /*varId*/) {
    ensureInit();
    return 0.0;   // no getValue symbol resolved in original; safe default
}

} // extern "C"
