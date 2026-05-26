// Native crash + log handler for the Hell After School Android port.
// Catches SIGSEGV/SIGBUS/SIGABRT/SIGILL/SIGFPE, dumps a backtrace to
// /sdcard/Download/hell_crash_<unix>.log (or app-private storage if perms denied),
// and mirrors all stdout/stderr/CCLOG output to a rolling log file at
// /sdcard/Download/hell_runtime.log.
//
// Called from JNI_OnLoad in the cocos2d-x Android activity setup.

#include <android/log.h>
// execinfo.h is not available on Android NDK; using _Unwind_Backtrace only.
#include <signal.h>
#include <unistd.h>
#include <unwind.h>
#include <dlfcn.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <sys/stat.h>
#include <sys/types.h>
#include <fcntl.h>
#include <string>

#define TAG "HellCrash"

namespace {

struct UnwindCtx { void **frames; int max; int count; };

_Unwind_Reason_Code unwindCb(struct _Unwind_Context *ctx, void *arg) {
    UnwindCtx *u = (UnwindCtx *)arg;
    if (u->count >= u->max) return _URC_END_OF_STACK;
    uintptr_t pc = _Unwind_GetIP(ctx);
    if (pc) u->frames[u->count++] = (void *)pc;
    return _URC_NO_REASON;
}

std::string g_logDir;

std::string chooseLogDir() {
    // Prefer app-scoped external storage (no runtime permission required on Android 4.4+
    // and visible to file managers under /sdcard/Android/data/<pkg>/files/).
    const char *candidates[] = {
        "/sdcard/Android/data/com.sthdk.hellafterschool/files",
        "/storage/emulated/0/Android/data/com.sthdk.hellafterschool/files",
        "/sdcard/Download",
        "/storage/emulated/0/Download",
        "/data/data/com.sthdk.hellafterschool/files",
        "/data/local/tmp",
        nullptr
    };
    for (int i = 0; candidates[i]; ++i) {
        mkdir(candidates[i], 0755);
        if (access(candidates[i], W_OK) == 0) return candidates[i];
    }
    return "/data/local/tmp";
}

void dumpCrash(int sig, siginfo_t *info, void *) {
    char path[512];
    std::snprintf(path, sizeof(path), "%s/hell_crash_%ld.log",
                  g_logDir.c_str(), (long)time(nullptr));
    int fd = open(path, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd < 0) fd = STDERR_FILENO;

    auto W = [&](const char *s){ write(fd, s, strlen(s)); };
    char buf[256];

    W("=== Hell After School native crash ===\n");
    std::snprintf(buf, sizeof(buf), "signal: %d (%s)\n", sig, strsignal(sig));   W(buf);
    std::snprintf(buf, sizeof(buf), "fault addr: %p\n", info ? info->si_addr : nullptr); W(buf);
    std::snprintf(buf, sizeof(buf), "pid/tid: %d/%d\n\n", getpid(), gettid());   W(buf);

    W("--- backtrace ---\n");
    void *frames[64];
    UnwindCtx u = {frames, 64, 0};
    _Unwind_Backtrace(unwindCb, &u);
    for (int i = 0; i < u.count; ++i) {
        Dl_info dli;
        if (dladdr(frames[i], &dli) && dli.dli_sname) {
            std::snprintf(buf, sizeof(buf), "  #%02d %p %s+0x%lx  (%s)\n",
                          i, frames[i], dli.dli_sname,
                          (unsigned long)((char*)frames[i] - (char*)dli.dli_saddr),
                          dli.dli_fname ? dli.dli_fname : "?");
        } else {
            std::snprintf(buf, sizeof(buf), "  #%02d %p\n", i, frames[i]);
        }
        W(buf);
    }

    fsync(fd);
    if (fd != STDERR_FILENO) close(fd);
    __android_log_print(ANDROID_LOG_FATAL, TAG, "Crash dumped to %s", path);

    // Re-raise default so logcat & system get the signal.
    signal(sig, SIG_DFL);
    raise(sig);
}

} // namespace

extern "C" void HellCrashHandler_install() {
    g_logDir = chooseLogDir();

    // Mirror stdout/stderr to a rolling log.
    char runtimeLog[512];
    std::snprintf(runtimeLog, sizeof(runtimeLog), "%s/hell_runtime.log", g_logDir.c_str());
    freopen(runtimeLog, "w", stdout);
    freopen(runtimeLog, "w", stderr);
    setvbuf(stdout, nullptr, _IOLBF, 0);
    setvbuf(stderr, nullptr, _IOLBF, 0);

    struct sigaction sa{};
    sa.sa_sigaction = dumpCrash;
    sa.sa_flags = SA_SIGINFO | SA_ONSTACK;
    sigemptyset(&sa.sa_mask);

    int sigs[] = {SIGSEGV, SIGBUS, SIGABRT, SIGILL, SIGFPE};
    for (int s : sigs) sigaction(s, &sa, nullptr);

    __android_log_print(ANDROID_LOG_INFO, TAG,
                        "crash handler installed; logs at %s", g_logDir.c_str());

    // Mark "we got here" trace so we know dlopen + constructors ran.
    char boot[512];
    std::snprintf(boot, sizeof(boot), "%s/native_boot.log", g_logDir.c_str());
    FILE *fp = fopen(boot, "a");
    if (fp) {
        fprintf(fp, "%ld HellCrashHandler_install done\n", (long)time(nullptr));
        fclose(fp);
    }
}

// Force the handler to install at .so load time so even crashes during static
// init or JNI_OnLoad are captured. Priority 101 runs after libc init.
__attribute__((constructor(101)))
static void HellCrashHandler_autoInstall() {
    HellCrashHandler_install();
}
