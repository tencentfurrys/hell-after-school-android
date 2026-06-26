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
#include <vector>

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

// Read this process's package name from /proc/self/cmdline (argv[0]).
// Strips any ":process" suffix. Works regardless of which APK the .so is
// injected into, so the log dir is always the *running* app's scoped dir.
static std::string selfPackage() {
    FILE *fp = fopen("/proc/self/cmdline", "r");
    if (!fp) return "";
    char buf[256] = {0};
    size_t n = fread(buf, 1, sizeof(buf) - 1, fp);
    fclose(fp);
    if (n == 0) return "";
    std::string pkg(buf);            // cmdline is NUL-delimited; argv[0] = package
    size_t colon = pkg.find(':');    // drop ":sandbox"/":remote" process suffix
    if (colon != std::string::npos) pkg = pkg.substr(0, colon);
    return pkg;
}

std::string chooseLogDir() {
    std::string pkg = selfPackage();
    std::vector<std::string> candidates;
    if (!pkg.empty()) {
        // App-scoped external dir: visible to file managers, writable w/o runtime perms.
        candidates.push_back("/sdcard/Android/data/" + pkg + "/files");
        candidates.push_back("/storage/emulated/0/Android/data/" + pkg + "/files");
        // App-private internal dir: ALWAYS writable by the app itself.
        candidates.push_back("/data/data/" + pkg + "/files");
        candidates.push_back("/data/user/0/" + pkg + "/files");
    }
    // Last-ditch shared locations (may be blocked by scoped storage).
    candidates.push_back("/sdcard/Download");
    candidates.push_back("/storage/emulated/0/Download");
    candidates.push_back("/data/local/tmp");
    for (const auto &c : candidates) {
        mkdir(c.c_str(), 0755);
        if (access(c.c_str(), W_OK) == 0) return c;
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

    // Mirror stdout/stderr to a rolling log. Guard every step: if the chosen
    // dir is NOT writable, do NOT let freopen close fd 1/2 (a closed stdout/stderr
    // gets its fd reused by later opens and silently corrupts them -> black screen).
    char runtimeLog[512];
    std::snprintf(runtimeLog, sizeof(runtimeLog), "%s/hell_runtime.log", g_logDir.c_str());
    FILE *probe = fopen(runtimeLog, "a");   // append: don't truncate Java-written log
    if (probe) {
        fclose(probe);
        int saveOut = dup(fileno(stdout));
        int saveErr = dup(fileno(stderr));
        if (!freopen(runtimeLog, "a", stdout) && saveOut >= 0) dup2(saveOut, fileno(stdout));
        if (!freopen(runtimeLog, "a", stderr) && saveErr >= 0) dup2(saveErr, fileno(stderr));
        if (saveOut >= 0) close(saveOut);
        if (saveErr >= 0) close(saveErr);
        setvbuf(stdout, nullptr, _IOLBF, 0);
        setvbuf(stderr, nullptr, _IOLBF, 0);
    } else {
        __android_log_print(ANDROID_LOG_WARN, TAG,
                            "log dir %s not writable; keeping stdout/stderr", g_logDir.c_str());
    }

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
