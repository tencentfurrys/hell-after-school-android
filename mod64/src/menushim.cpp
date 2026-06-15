// Reconstructed arm64 libmenushim.so for org.cocos2dx.cpp.MenuShim
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

    s_tg_getInstance   = (fn_tg_getInstance) sym(s_libHandle, "_ZN12TouchGamepad11getInstanceEv");
    s_tg_injectPress   = (fn_tg_inject)      sym(s_libHandle, "_ZN12TouchGamepad14injectKeyPressEN7cocos2d13EventKeyboard7KeyCodeE");
    s_tg_injectRelease = (fn_tg_inject)      sym(s_libHandle, "_ZN12TouchGamepad16injectKeyReleaseEN7cocos2d13EventKeyboard7KeyCodeE");
    s_im_getInstance   = (fn_im_getInstance) sym(s_libHandle, "_ZN12InputManager11getInstanceEv");
    s_im_setPrecedeTrig= (fn_im_setPrecede)  sym(s_libHandle, "_ZN12InputManager24setPrecedeInputTriggeredEiiN4agtk4data24ObjectInputConditionData15EnumTriggerTypeEi");
    s_im_setPrecedeRel = (fn_im_setPrecede)  sym(s_libHandle, "_ZN12InputManager23setPrecedeInputReleasedEiiN4agtk4data24ObjectInputConditionData15EnumTriggerTypeEi");
    s_im_setPrecedeJudge=(fn_im_setJudge)    sym(s_libHandle, "_ZN12InputManager24setPrecedeInputJudgeDataEv");
    s_gm_getInstance   = (fn_gm_getInstance) sym(s_libHandle, "_ZN11GameManager11getInstanceEv");
    s_gm_getPlayData   = (fn_gm_getPlayData) sym(s_libHandle, "_ZNK11GameManager11getPlayDataEv");
    s_pd_getCommonVar  = (fn_pd_getCommonVar)sym(s_libHandle, "_ZN4agtk4data8PlayData21getCommonVariableDataEi");
    s_pv_setValue      = (fn_pv_setValue)    sym(s_libHandle, "_ZN4agtk4data16PlayVariableData8setValueEd");

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
Java_org_cocos2dx_cpp_MenuShim_nativeSetDiagPath(JNIEnv* env, jclass, jstring path) {
    if (!path) { s_diagPath[0] = 0; return; }
    const char* p = env->GetStringUTFChars(path, nullptr);
    if (p) { strncpy(s_diagPath, p, sizeof(s_diagPath) - 1); s_diagPath[sizeof(s_diagPath)-1] = 0;
             env->ReleaseStringUTFChars(path, p); }
    deriveCrashPath();
    installCrashHandler();
    LOGI("diag path set; crash log -> %s", s_crashPath);
}

JNIEXPORT jint JNICALL
Java_org_cocos2dx_cpp_MenuShim_nativeInit(JNIEnv*, jclass) {
    installCrashHandler();
    ensureInit();
    return s_initState == 1 ? 1 : 0;
}

JNIEXPORT jint JNI_OnLoad(JavaVM*, void*) {
    installCrashHandler();
    return JNI_VERSION_1_6;
}

JNIEXPORT jboolean JNICALL
Java_org_cocos2dx_cpp_MenuShim_nativeInjectKey(JNIEnv*, jclass, jint keyCode, jboolean pressed) {
    ensureInit();
    if (!s_tg_getInstance) return JNI_FALSE;              // TouchGamepad not present (arm64) -> no-op
    void* tg = s_tg_getInstance();
    if (!tg) return JNI_FALSE;
    LOGI("injectKey keyCode=%d pressed=%d inst=%p", keyCode, (int)pressed, tg);
    if (pressed) { if (s_tg_injectPress)   s_tg_injectPress(tg, keyCode); }
    else         { if (s_tg_injectRelease) s_tg_injectRelease(tg, keyCode); }
    return JNI_TRUE;
}

JNIEXPORT jboolean JNICALL
Java_org_cocos2dx_cpp_MenuShim_nativePrecedeTriggered(JNIEnv*, jclass, jint a, jint b, jint type, jint inst) {
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
Java_org_cocos2dx_cpp_MenuShim_nativePrecedeReleased(JNIEnv*, jclass, jint a, jint b, jint type, jint inst) {
    ensureInit();
    if (!s_im_getInstance || !s_im_setPrecedeRel) return JNI_FALSE;
    void* im = s_im_getInstance();
    if (!im) return JNI_FALSE;
    s_im_setPrecedeRel(im, a, b, type, inst);
    if (s_im_setPrecedeJudge) s_im_setPrecedeJudge(im);
    return JNI_TRUE;
}

JNIEXPORT jint JNICALL
Java_org_cocos2dx_cpp_MenuShim_nativeSetCommonVariable(JNIEnv*, jclass, jint varId, jdouble value) {
    ensureInit();
    if (!s_gm_getInstance || !s_gm_getPlayData || !s_pd_getCommonVar || !s_pv_setValue) return 0;
    void* gm = s_gm_getInstance();              if (!gm) return 0;
    void* pd = s_gm_getPlayData(gm);            if (!pd) return 0;
    void* pv = s_pd_getCommonVar(pd, varId);    if (!pv) return 0;
    s_pv_setValue(pv, value);
    return 1;
}

JNIEXPORT jdouble JNICALL
Java_org_cocos2dx_cpp_MenuShim_nativeGetCommonVariable(JNIEnv*, jclass, jint /*varId*/) {
    ensureInit();
    return 0.0;   // no getValue symbol resolved in original; safe default
}

} // extern "C"
