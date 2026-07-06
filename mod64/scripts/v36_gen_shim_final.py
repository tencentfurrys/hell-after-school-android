#!/usr/bin/env python3
"""
v36 shim generator (runs on the CI runner where smali is UNMASKED).

Discovers:
  - The MenuShim class package/name (searches all .smali for `System.loadLibrary("menushim")`
    or the declared `.method native injectKey(IZ)Z` and friends).
  - The exact set of `native` methods declared on that class.

Emits an arm64 shim source `mod64/src/menushim_gen.cpp` that:
  - Preserves every existing native's JNI export name exactly (so the app's
    System.loadLibrary + resolveNatives still works). Existing methods keep
    their v34 semantics EXCEPT:
      * `injectKey(IZ)Z` (or its `nativeInjectKey` equivalent) is REWRITTEN to
        route into InputManager::getInputDataRaw()->registerKeyPressed/Released
        (the v36 real-input path).
  - Includes the rich probe (isPressedKeyboard) on every press.
  - Includes the one-frame minimum-hold guard for same-tick press+release.

Usage: python3 v36_gen_shim.py <smali-root> <output-cpp-path>
"""
import re, sys, os

def die(msg):
    print("V36-GEN-FAIL:", msg, file=sys.stderr); sys.exit(1)

if len(sys.argv) != 3:
    die("usage: v36_gen_shim.py <smali-root> <output-cpp>")

smali_root, out_cpp = sys.argv[1], sys.argv[2]

# 1) Find MenuShim.smali by content: it will be a .smali with a
#    `System.loadLibrary("menushim")` call AND declare native methods matching
#    the porter's known set (injectKey / precedeTriggered / precedeReleased).
menushim_path = None
for base, _, files in os.walk(smali_root):
    for f in files:
        if not f.endswith(".smali"): continue
        p = os.path.join(base, f)
        txt = open(p, encoding="utf-8", errors="replace").read()
        if 'System;->loadLibrary(Ljava/lang/String;)V' in txt and 'menushim' in txt:
            # class declares native methods?
            if re.search(r'\.method[^\n]*\snative\s', txt):
                menushim_path = p
                break
    if menushim_path: break
if not menushim_path:
    die("could not locate MenuShim smali (System.loadLibrary(\"menushim\") + .method native)")
print("V36-GEN: MenuShim smali =", menushim_path)

src = open(menushim_path, encoding="utf-8").read()

# 2) Extract fully-qualified class descriptor.
m = re.search(r'^\.class[^\n]*\s(L[\w/$]+;)\s*$', src, re.M)
if not m: die("no .class descriptor in " + menushim_path)
class_desc = m.group(1)              # e.g. Lorg/cocos2dx/cpp/MenuShim;
class_slash = class_desc[1:-1]        # org/cocos2dx/cpp/MenuShim
jni_prefix = "Java_" + class_slash.replace("/", "_").replace("$", "_00024") + "_"
print("V36-GEN: class =", class_desc)
print("V36-GEN: JNI prefix =", jni_prefix)

# 3) Enumerate native methods and their JNI signatures.
#    Line form: .method public static native <name>(<argTypes>)<retType>
natives = []
for line in src.splitlines():
    mm = re.match(r'\s*\.method\s+([\w\s]+?)\s+([A-Za-z][\w$]*)\(([^)]*)\)(\S+)\s*$', line)
    if not mm: continue
    mods, name, args, ret = mm.group(1), mm.group(2), mm.group(3), mm.group(4)
    if 'native' not in mods.split(): continue
    natives.append((name, args, ret))
    print(f"V36-GEN: native {name}({args}){ret}")

if not natives:
    die("no native methods found in " + menushim_path)

# Map smali types to C JNI types.
def jni_type(t):
    if t == 'V': return 'void'
    if t == 'Z': return 'jboolean'
    if t == 'B': return 'jbyte'
    if t == 'S': return 'jshort'
    if t == 'I': return 'jint'
    if t == 'J': return 'jlong'
    if t == 'F': return 'jfloat'
    if t == 'D': return 'jdouble'
    if t == 'C': return 'jchar'
    if t.startswith('L') and t.endswith(';'):
        if t == 'Ljava/lang/String;': return 'jstring'
        return 'jobject'
    if t.startswith('['): return 'jobject'
    die("unknown smali type: " + t)

def split_args(sig):
    """Split a smali arg-signature into individual types."""
    out = []; i = 0
    while i < len(sig):
        c = sig[i]
        if c in "ZBSIJFDC V":
            out.append(c); i += 1
        elif c == 'L':
            e = sig.index(';', i)
            out.append(sig[i:e+1]); i = e+1
        elif c == '[':
            j = i
            while sig[j] == '[': j += 1
            if sig[j] == 'L':
                e = sig.index(';', j)
                out.append(sig[i:e+1]); i = e+1
            else:
                out.append(sig[i:j+1]); i = j+1
        else:
            die("bad sig char: " + c)
    return out

# 4) Emit the C++ shim.
def emit_stub(name, args, ret):
    """Emit the JNI stub for one native. injectKey / nativeInjectKey get the v36 body;
    everything else gets a safe pass-through / guarded no-op."""
    arg_types = split_args(args)
    c_args = []
    c_names = []
    for i, t in enumerate(arg_types):
        c_args.append(f"{jni_type(t)} a{i}")
        c_names.append(f"a{i}")
    export = f"{jni_prefix}{name}"
    c_ret = jni_type(ret)

    if name in ("injectKey", "nativeInjectKey") and args == "IZ" and ret == "Z":
        body = f"""    ensureInit();
    if (!s_im_getInstance || !s_idr_regPressed || !s_idr_regReleased) return JNI_FALSE;
    void* im = s_im_getInstance();
    if (!im) return JNI_FALSE;
    if (!s_im_getInputDataRaw) return JNI_FALSE;
    void* idr = s_im_getInputDataRaw(im);
    if (!idr) return JNI_FALSE;
    int cc = (int)a0;
    bool pressed = (a1 == JNI_TRUE);
    int idx = ((unsigned)cc) & 0x1FF;
    if (pressed) {{
        v36_probe(cc);
        s_lastPressTick[idx] = currentTick();
        LOGI("v36 injectKey PRESS  cc=%d idr=%p", cc, idr);
        s_idr_regPressed(idr, cc, 0);
    }} else {{
        uint64_t now = currentTick();
        if (s_lastPressTick[idx] && now == s_lastPressTick[idx]) {{
            LOGI("v36 injectKey RELEASE cc=%d SAME-TICK -> hold 20ms", cc);
            struct timespec ts = {{ 0, 20 * 1000 * 1000 }};
            nanosleep(&ts, nullptr);
        }}
        LOGI("v36 injectKey RELEASE cc=%d idr=%p", cc, idr);
        s_idr_regReleased(idr, cc, 0);
    }}
    return JNI_TRUE;"""
    elif name in ("nativeSetDiagPath",) and args == "Ljava/lang/String;" and ret == "V":
        body = """    if (!a0) { s_diagPath[0] = 0; return; }
    const char* p = env->GetStringUTFChars(a0, nullptr);
    if (p) { strncpy(s_diagPath, p, sizeof(s_diagPath)-1); s_diagPath[sizeof(s_diagPath)-1]=0;
             env->ReleaseStringUTFChars(a0, p); }
    deriveCrashPath();
    installCrashHandler();
    LOGI("diag path set; crash log -> %s", s_crashPath);"""
    elif name in ("nativeInit",) and args == "" and ret == "I":
        body = """    installCrashHandler();
    ensureInit();
    return s_initState == 1 ? 1 : 0;"""
    elif name in ("precedeTriggered", "nativePrecedeTriggered") and args == "IIII" and ret == "Z":
        body = """    ensureInit();
    if (!s_im_getInstance || !s_im_setPrecedeTrig) return JNI_FALSE;
    void* im = s_im_getInstance(); if (!im) return JNI_FALSE;
    s_im_setPrecedeTrig(im, (int)a0, (int)a1, (int)a2, (int)a3);
    if (s_im_setPrecedeJudge) s_im_setPrecedeJudge(im);
    return JNI_TRUE;"""
    elif name in ("precedeReleased", "nativePrecedeReleased") and args == "IIII" and ret == "Z":
        body = """    ensureInit();
    if (!s_im_getInstance || !s_im_setPrecedeRel) return JNI_FALSE;
    void* im = s_im_getInstance(); if (!im) return JNI_FALSE;
    s_im_setPrecedeRel(im, (int)a0, (int)a1, (int)a2, (int)a3);
    if (s_im_setPrecedeJudge) s_im_setPrecedeJudge(im);
    return JNI_TRUE;"""
    elif name in ("nativeSetCommonVariable",) and args == "ID" and ret == "I":
        body = """    ensureInit();
    if (!s_gm_getInstance || !s_gm_getPlayData || !s_pd_getCommonVar || !s_pv_setValue) return 0;
    void* gm = s_gm_getInstance();       if (!gm) return 0;
    void* pd = s_gm_getPlayData(gm);     if (!pd) return 0;
    void* pv = s_pd_getCommonVar(pd, (int)a0); if (!pv) return 0;
    s_pv_setValue(pv, (double)a1);
    return 1;"""
    elif name in ("nativeGetCommonVariable",) and args == "I" and ret == "D":
        body = """    ensureInit();
    return 0.0;"""
    else:
        # Safe default no-op returning zero-of-type.
        if c_ret == 'void':      body = "    // unrecognised native; no-op\n    return;"
        elif c_ret == 'jboolean':body = "    return JNI_FALSE;"
        elif c_ret == 'jdouble': body = "    return 0.0;"
        elif c_ret == 'jfloat':  body = "    return 0.0f;"
        elif c_ret == 'jobject' or c_ret == 'jstring': body = "    return nullptr;"
        else:                    body = "    return 0;"

    param_list = ", ".join(c_args) if c_args else ""
    return f"""JNIEXPORT {c_ret} JNICALL
{export}(JNIEnv* env, jclass{', ' + param_list if param_list else ''}) {{
{body}
}}
"""

stubs = "\n".join(emit_stub(n, a, r) for (n, a, r) in natives)

TEMPLATE = r'''// AUTO-GENERATED by mod64/scripts/v36_gen_shim.py
// Do not hand-edit. The template is embedded in v36_gen_shim.py.
//
// v36 arm64 libmenushim.so — routes MenuShim.injectKey into the InputManager
// keyboard queue that the running scene polls (registerKeyPressed/Released),
// with rich probe + one-frame minimum-hold guard for same-tick press+release.
// All other natives keep their v34 semantics. Existing JNI export names are
// preserved exactly so the loader keeps resolving them.

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
#include <time.h>
#include <atomic>

#define LOGI(...) __android_log_print(ANDROID_LOG_INFO,  "MenuShim", __VA_ARGS__)
#define LOGW(...) __android_log_print(ANDROID_LOG_WARN,  "MenuShim", __VA_ARGS__)

typedef void* (*fn_im_getInstance)();
typedef void  (*fn_im_setPrecede)(void* self, int a, int b, int triggerType, int inst);
typedef void  (*fn_im_setJudge)(void* self);
typedef void* (*fn_gm_getInstance)();
typedef void* (*fn_gm_getPlayData)(void* self);
typedef void* (*fn_pd_getCommonVar)(void* self, int varId);
typedef void  (*fn_pv_setValue)(void* self, double value);
typedef void* (*fn_im_getInputDataRaw)(void* self);              // const
typedef void  (*fn_idr_reg)(void* self, int keyCode, int scancode);
typedef bool  (*fn_im_isPressedKeyboard)(void* self, int keyCode);

static int   s_initState = 0;
static void* s_libHandle = nullptr;
static char  s_diagPath[512] = {0};
static char  s_crashPath[600] = {0};

static fn_im_getInstance  s_im_getInstance   = nullptr;
static fn_im_setPrecede   s_im_setPrecedeTrig= nullptr;
static fn_im_setPrecede   s_im_setPrecedeRel = nullptr;
static fn_im_setJudge     s_im_setPrecedeJudge=nullptr;
static fn_gm_getInstance  s_gm_getInstance   = nullptr;
static fn_gm_getPlayData  s_gm_getPlayData   = nullptr;
static fn_pd_getCommonVar s_pd_getCommonVar  = nullptr;
static fn_pv_setValue     s_pv_setValue      = nullptr;

// v36 -----------------------------------------------------------------------
static fn_im_getInputDataRaw   s_im_getInputDataRaw   = nullptr;
static fn_idr_reg              s_idr_regPressed       = nullptr;
static fn_idr_reg              s_idr_regReleased      = nullptr;
static fn_im_isPressedKeyboard s_im_isPressedKeyboard = nullptr;

static std::atomic<uint64_t> s_frameTick{0};
static uint64_t s_lastPressTick[512] = {0};

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
    FILE* f = fopen(s_diagPath, "a"); if (!f) return;
    va_list ap; va_start(ap, fmt); vfprintf(f, fmt, ap); va_end(ap);
    fclose(f);
}
static void deriveCrashPath() {
    if (!s_diagPath[0]) return;
    strncpy(s_crashPath, s_diagPath, sizeof(s_crashPath)-1);
    char* sl = strrchr(s_crashPath, '/');
    if (sl) strcpy(sl+1, "native_crash.txt");
    else snprintf(s_crashPath, sizeof(s_crashPath), "native_crash.txt");
}

// ----- crash handler (write faulting addr + backtrace, then re-raise) -----
static struct sigaction s_old[8];
static const int s_sigs[] = { SIGSEGV, SIGABRT, SIGBUS, SIGILL, SIGFPE };
struct BtState { void** pcs; int count; int max; };
static _Unwind_Reason_Code unwindCb(_Unwind_Context* ctx, void* arg) {
    BtState* st = (BtState*)arg;
    uintptr_t ip = _Unwind_GetIP(ctx);
    if (ip && st->count < st->max) st->pcs[st->count++] = (void*)ip;
    return st->count >= st->max ? _URC_END_OF_STACK : _URC_NO_REASON;
}
static void writeAll(int fd, const char* b, int n){ while(n>0){int w=write(fd,b,n); if(w<=0)break; b+=w; n-=w;} }
static void writeStr(int fd, const char* s){ writeAll(fd, s, (int)strlen(s)); }
static void crashHandler(int sig, siginfo_t* info, void*) {
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
        Dl_info di; const char* lib="?"; const char* symn="?"; uintptr_t off=0, soff=0;
        if (dladdr(pcs[i], &di)) {
            if (di.dli_fname) { const char* sl=strrchr(di.dli_fname,'/'); lib = sl?sl+1:di.dli_fname; }
            if (di.dli_fbase) off = (uintptr_t)pcs[i] - (uintptr_t)di.dli_fbase;
            if (di.dli_sname) { symn = di.dli_sname; soff = (uintptr_t)pcs[i] - (uintptr_t)di.dli_saddr; }
        }
        snprintf(line, sizeof(line), "#%02d pc %012lx  %s  (%s+0x%lx)\n",
                 i, (unsigned long)off, lib, symn, (unsigned long)soff);
        __android_log_print(ANDROID_LOG_FATAL, "MenuShim", "%s", line);
        if (fd>=0) writeStr(fd, line);
    }
    if (fd>=0) close(fd);
    for (unsigned k=0;k<sizeof(s_sigs)/sizeof(s_sigs[0]);k++)
        if (s_sigs[k]==sig) sigaction(sig, &s_old[k], nullptr);
    raise(sig);
}
static void installCrashHandler() {
    static int done = 0; if (done) return; done = 1;
    static char altstk[64*1024];
    stack_t ss; ss.ss_sp = altstk; ss.ss_size = sizeof(altstk); ss.ss_flags = 0;
    sigaltstack(&ss, nullptr);
    struct sigaction sa; memset(&sa,0,sizeof(sa));
    sa.sa_sigaction = crashHandler; sa.sa_flags = SA_SIGINFO | SA_ONSTACK; sigemptyset(&sa.sa_mask);
    for (unsigned k=0;k<sizeof(s_sigs)/sizeof(s_sigs[0]);k++)
        sigaction(s_sigs[k], &sa, &s_old[k]);
    LOGI("crash handler installed -> %s", s_crashPath[0]?s_crashPath:"(no path yet)");
}

static void* sym(void* h, const char* n) { return dlsym(h, n); }

static void ensureInit() {
    if (s_initState != 0) return;
    s_libHandle = dlopen("libMyGame.so", RTLD_NOW | RTLD_NOLOAD | RTLD_GLOBAL);
    if (!s_libHandle) s_libHandle = dlopen("libMyGame.so", RTLD_NOW | RTLD_GLOBAL);
    if (!s_libHandle) { LOGW("dlopen FAILED: %s", dlerror()); s_initState = -1; return; }

    s_im_getInstance      = (fn_im_getInstance) sym(s_libHandle, "_ZN12InputManager11getInstanceEv");
    s_gm_getInstance      = (fn_gm_getInstance) sym(s_libHandle, "_ZN11GameManager11getInstanceEv");

    // precede path (buffer only; kept for compat with older overlay call sites)
    // We try both possible template-argument mangling shapes seen in the wild.
    s_im_setPrecedeTrig  = (fn_im_setPrecede) sym(s_libHandle, "_ZN12InputManager25setPrecedeInputTriggeredIsEiiN4agtk4data24ObjectInputConditionData15EnumTriggerTypeEi");
    if (!s_im_setPrecedeTrig)
        s_im_setPrecedeTrig = (fn_im_setPrecede) sym(s_libHandle, "_ZN12InputManager24setPrecedeInputTriggeredEiiN4agtk4data24ObjectInputConditionData15EnumTriggerTypeEi");
    s_im_setPrecedeRel   = (fn_im_setPrecede) sym(s_libHandle, "_ZN12InputManager24setPrecedeInputReleasedIsEiiN4agtk4data24ObjectInputConditionData15EnumTriggerTypeEi");
    if (!s_im_setPrecedeRel)
        s_im_setPrecedeRel = (fn_im_setPrecede) sym(s_libHandle, "_ZN12InputManager23setPrecedeInputReleasedEiiN4agtk4data24ObjectInputConditionData15EnumTriggerTypeEi");
    s_im_setPrecedeJudge = (fn_im_setJudge) sym(s_libHandle, "_ZN12InputManager21setPrecedeInputJudgedEv");
    if (!s_im_setPrecedeJudge)
        s_im_setPrecedeJudge = (fn_im_setJudge) sym(s_libHandle, "_ZN12InputManager19setPrecedeInputJudgeEv");

    // GameManager / PlayData / PlayVariableData
    s_gm_getPlayData   = (fn_gm_getPlayData) sym(s_libHandle, "_ZNK11GameManager11getPlayDataEv");
    if (!s_gm_getPlayData)
        s_gm_getPlayData = (fn_gm_getPlayData) sym(s_libHandle, "_ZN11GameManager11getPlayDataEv");
    s_pd_getCommonVar  = (fn_pd_getCommonVar) sym(s_libHandle, "_ZN4agtk4data8PlayData20getCommonVariableDataEi");
    if (!s_pd_getCommonVar)
        s_pd_getCommonVar = (fn_pd_getCommonVar) sym(s_libHandle, "_ZN4agtk4data8PlayData19getCommonVariableDataEi");
    s_pv_setValue      = (fn_pv_setValue) sym(s_libHandle, "_ZN4agtk4data16PlayVariableData8setValueEd");

    // v36 real-input path
    s_im_getInputDataRaw   = (fn_im_getInputDataRaw)   sym(s_libHandle, "_ZNK12InputManager15getInputDataRawEv");
    s_idr_regPressed       = (fn_idr_reg)              sym(s_libHandle, "_ZN12InputDataRaw18registerKeyPressedEii");
    s_idr_regReleased      = (fn_idr_reg)              sym(s_libHandle, "_ZN12InputDataRaw19registerKeyReleasedEii");
    s_im_isPressedKeyboard = (fn_im_isPressedKeyboard) sym(s_libHandle, "_ZN12InputManager17isPressedKeyboardEi");

    LOGI("v36 init im=%p getRaw=%p regP=%p regR=%p isKb=%p gm=%p precTrig=%p precRel=%p",
         (void*)s_im_getInstance,(void*)s_im_getInputDataRaw,(void*)s_idr_regPressed,
         (void*)s_idr_regReleased,(void*)s_im_isPressedKeyboard,(void*)s_gm_getInstance,
         (void*)s_im_setPrecedeTrig,(void*)s_im_setPrecedeRel);
    writeDiagFmt("v36 init im=%p idr_get=%p regP=%p regR=%p\n",
         (void*)s_im_getInstance,(void*)s_im_getInputDataRaw,(void*)s_idr_regPressed,(void*)s_idr_regReleased);

    if (s_im_getInstance || s_gm_getInstance) s_initState = 1;
    else { LOGW("init FAILED"); s_initState = -1; }
}

// Rich probe: bumps our coarse frame tick and logs what the engine sees on
// the read side, so one test run confirms the arm64 build still polls the
// keyboard channel (isPressedKeyboard).
static void v36_probe(int cc) {
    s_frameTick.fetch_add(1, std::memory_order_relaxed);
    if (!s_im_getInstance) return;
    void* im = s_im_getInstance();
    if (!im) return;
    int kb = -1;
    if (s_im_isPressedKeyboard) kb = s_im_isPressedKeyboard(im, cc) ? 1 : 0;
    LOGI("v36 probe cc=%d tick=%llu isPressedKeyboard=%d",
         cc, (unsigned long long)s_frameTick.load(), kb);
    writeDiagFmt("v36 probe cc=%d kb=%d\n", cc, kb);
}

extern "C" JNIEXPORT jint JNI_OnLoad(JavaVM*, void*) {
    installCrashHandler();
    return JNI_VERSION_1_6;
}

extern "C" {
__V36_STUBS__
} // extern "C"
'''

out = TEMPLATE.replace("__V36_STUBS__", stubs)
os.makedirs(os.path.dirname(out_cpp), exist_ok=True)
open(out_cpp, "w", encoding="utf-8").write(out)
print("V36-GEN-OK:", out_cpp, "size=", len(out))
