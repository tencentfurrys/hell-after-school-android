.class public final Lorg/cocos2dx/cpp/MenuShim;
.super Ljava/lang/Object;
.source "MenuShim.java"


# static fields
.field public static final KEYID_CANCEL:I = 0x2

.field public static final KEYID_INTERACT:I = 0x1

.field public static final KEYID_MENU:I = 0x3

.field public static final KEYID_S:I = 0x7

.field public static final KEYID_SUB:I = 0x4

.field public static final KEY_C:I = 0x7e

.field public static final KEY_ESCAPE:I = 0x6

.field public static final KEY_MENU:I = 0x12

.field public static final KEY_S:I = 0x8e

.field public static final KEY_V:I = 0x91

.field public static final KEY_X:I = 0x93

.field public static final KEY_Z:I = 0x95

.field public static final TRIG_PRESSED:I = 0x1

.field public static final VAR_MENU_ID:I = 0x7fc

.field private static sInitOk:Z

.field private static sLibLoaded:Z

.field private static sMenuOpen:Z


# direct methods
.method static constructor <clinit>()V
    .registers 1

    .line 27
    const/4 v0, 0x0

    sput-boolean v0, Lorg/cocos2dx/cpp/MenuShim;->sLibLoaded:Z

    .line 28
    sput-boolean v0, Lorg/cocos2dx/cpp/MenuShim;->sInitOk:Z

    .line 147
    sput-boolean v0, Lorg/cocos2dx/cpp/MenuShim;->sMenuOpen:Z

    return-void
.end method

.method private constructor <init>()V
    .registers 1

    .line 30
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

.method public static closeMainMenu()I
    .registers 3

    .line 138
    const/4 v0, 0x0

    sput-boolean v0, Lorg/cocos2dx/cpp/MenuShim;->sMenuOpen:Z

    const/16 v0, 0x7fc

    const-wide/16 v1, 0x0

    invoke-static {v0, v1, v2}, Lorg/cocos2dx/cpp/MenuShim;->setCommonVariable(ID)I

    move-result v0

    return v0
.end method

.method public static fireMenuKey(Z)Z
    .registers 5

    .line 118
    const/4 v0, -0x1

    const/4 v1, 0x1

    const/4 v2, 0x3

    const/4 v3, 0x0

    if-eqz p0, :cond_b

    invoke-static {v3, v2, v1, v0}, Lorg/cocos2dx/cpp/MenuShim;->precedeTriggered(IIII)Z

    move-result p0

    return p0

    .line 119
    :cond_b
    invoke-static {v3, v2, v1, v0}, Lorg/cocos2dx/cpp/MenuShim;->precedeReleased(IIII)Z

    move-result p0

    return p0
.end method

.method public static declared-synchronized init(Landroid/content/Context;)Z
    .registers 6

    const-class v0, Lorg/cocos2dx/cpp/MenuShim;

    monitor-enter v0

    .line 34
    :try_start_3
    sget-boolean v1, Lorg/cocos2dx/cpp/MenuShim;->sInitOk:Z
    :try_end_5
    .catchall {:try_start_3 .. :try_end_5} :catchall_6d

    const/4 v2, 0x1

    if-eqz v1, :cond_a

    monitor-exit v0

    return v2

    .line 35
    :cond_a
    :try_start_a
    sget-boolean v1, Lorg/cocos2dx/cpp/MenuShim;->sLibLoaded:Z
    :try_end_c
    .catchall {:try_start_a .. :try_end_c} :catchall_6d

    const/4 v3, 0x0

    if-nez v1, :cond_21

    .line 37
    :try_start_f
    const-string v1, "menushim"

    invoke-static {v1}, Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V

    .line 38
    sput-boolean v2, Lorg/cocos2dx/cpp/MenuShim;->sLibLoaded:Z
    :try_end_16
    .catchall {:try_start_f .. :try_end_16} :catchall_17

    .line 42
    goto :goto_21

    .line 39
    :catchall_17
    move-exception p0

    .line 40
    :try_start_18
    const-string v1, "MenuShim"

    const-string v2, "loadLibrary FAILED"

    invoke-static {v1, v2, p0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I
    :try_end_1f
    .catchall {:try_start_18 .. :try_end_1f} :catchall_6d

    .line 41
    monitor-exit v0

    return v3

    .line 47
    :cond_21
    :goto_21
    :try_start_21
    new-instance v1, Ljava/io/File;

    invoke-virtual {p0}, Landroid/content/Context;->getFilesDir()Ljava/io/File;

    move-result-object p0

    const-string v4, "hell_runtime.log"

    invoke-direct {v1, p0, v4}, Ljava/io/File;-><init>(Ljava/io/File;Ljava/lang/String;)V

    .line 48
    invoke-virtual {v1}, Ljava/io/File;->getAbsolutePath()Ljava/lang/String;

    move-result-object p0

    invoke-static {p0}, Lorg/cocos2dx/cpp/MenuShim;->nativeSetDiagPath(Ljava/lang/String;)V
    :try_end_33
    .catchall {:try_start_21 .. :try_end_33} :catchall_34

    .line 51
    goto :goto_3c

    .line 49
    :catchall_34
    move-exception p0

    .line 50
    :try_start_35
    const-string v1, "MenuShim"

    const-string v4, "diag path set failed"

    invoke-static {v1, v4, p0}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I
    :try_end_3c
    .catchall {:try_start_35 .. :try_end_3c} :catchall_6d

    .line 53
    :goto_3c
    :try_start_3c
    invoke-static {}, Lorg/cocos2dx/cpp/MenuShim;->nativeInit()I

    move-result p0

    .line 54
    if-ne p0, v2, :cond_43

    goto :goto_44

    :cond_43
    move v2, v3

    :goto_44
    sput-boolean v2, Lorg/cocos2dx/cpp/MenuShim;->sInitOk:Z

    .line 55
    const-string v1, "MenuShim"

    new-instance v2, Ljava/lang/StringBuilder;

    invoke-direct {v2}, Ljava/lang/StringBuilder;-><init>()V

    const-string v4, "nativeInit rv="

    invoke-virtual {v2, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v2

    invoke-virtual {v2, p0}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object p0

    invoke-virtual {p0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p0

    invoke-static {v1, p0}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I
    :try_end_5e
    .catchall {:try_start_3c .. :try_end_5e} :catchall_5f

    .line 59
    goto :goto_69

    .line 56
    :catchall_5f
    move-exception p0

    .line 57
    :try_start_60
    const-string v1, "MenuShim"

    const-string v2, "nativeInit threw"

    invoke-static {v1, v2, p0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    .line 58
    sput-boolean v3, Lorg/cocos2dx/cpp/MenuShim;->sInitOk:Z

    .line 60
    :goto_69
    sget-boolean p0, Lorg/cocos2dx/cpp/MenuShim;->sInitOk:Z
    :try_end_6b
    .catchall {:try_start_60 .. :try_end_6b} :catchall_6d

    monitor-exit v0

    return p0

    .line 33
    :catchall_6d
    move-exception p0

    monitor-exit v0

    throw p0
.end method

.method public static injectKey(IZ)Z
    .registers 4

    .line 67
    sget-boolean v0, Lorg/cocos2dx/cpp/MenuShim;->sInitOk:Z

    const/4 v1, 0x0

    if-nez v0, :cond_6

    return v1

    .line 69
    :cond_6
    :try_start_6
    invoke-static {p0, p1}, Lorg/cocos2dx/cpp/MenuShim;->nativeInjectKey(IZ)Z

    move-result p0
    :try_end_a
    .catchall {:try_start_6 .. :try_end_a} :catchall_b

    return p0

    .line 70
    :catchall_b
    move-exception p0

    .line 71
    const-string p1, "MenuShim"

    const-string v0, "injectKey threw"

    invoke-static {p1, v0, p0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    .line 72
    return v1
.end method

.method public static isMenuOpen()Z
    .registers 1

    .line 158
    sget-boolean v0, Lorg/cocos2dx/cpp/MenuShim;->sMenuOpen:Z

    return v0
.end method

.method public static isReady()Z
    .registers 1

    .line 63
    sget-boolean v0, Lorg/cocos2dx/cpp/MenuShim;->sInitOk:Z

    return v0
.end method

.method private static native nativeGetCommonVariable(I)D
.end method

.method private static native nativeInit()I
.end method

.method private static native nativeInjectKey(IZ)Z
.end method

.method private static native nativePrecedeReleased(IIII)Z
.end method

.method private static native nativePrecedeTriggered(IIII)Z
.end method

.method private static native nativeSetCommonVariable(ID)I
.end method

.method private static native nativeSetDiagPath(Ljava/lang/String;)V
.end method

.method public static openMainMenu()I
    .registers 3

    .line 137
    const/4 v0, 0x1

    sput-boolean v0, Lorg/cocos2dx/cpp/MenuShim;->sMenuOpen:Z

    const/16 v0, 0x7fc

    const-wide/high16 v1, 0x3ff0000000000000L    # 1.0

    invoke-static {v0, v1, v2}, Lorg/cocos2dx/cpp/MenuShim;->setCommonVariable(ID)I

    move-result v0

    return v0
.end method

.method public static precedeReleased(IIII)Z
    .registers 6

    .line 111
    sget-boolean v0, Lorg/cocos2dx/cpp/MenuShim;->sInitOk:Z

    const/4 v1, 0x0

    if-nez v0, :cond_6

    return v1

    .line 112
    :cond_6
    :try_start_6
    invoke-static {p0, p1, p2, p3}, Lorg/cocos2dx/cpp/MenuShim;->nativePrecedeReleased(IIII)Z

    move-result p0
    :try_end_a
    .catchall {:try_start_6 .. :try_end_a} :catchall_b

    return p0

    .line 113
    :catchall_b
    move-exception p0

    const-string p1, "MenuShim"

    const-string p2, "precedeRel threw"

    invoke-static {p1, p2, p0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    return v1
.end method

.method public static precedeTriggered(IIII)Z
    .registers 6

    .line 105
    sget-boolean v0, Lorg/cocos2dx/cpp/MenuShim;->sInitOk:Z

    const/4 v1, 0x0

    if-nez v0, :cond_6

    return v1

    .line 106
    :cond_6
    :try_start_6
    invoke-static {p0, p1, p2, p3}, Lorg/cocos2dx/cpp/MenuShim;->nativePrecedeTriggered(IIII)Z

    move-result p0
    :try_end_a
    .catchall {:try_start_6 .. :try_end_a} :catchall_b

    return p0

    .line 107
    :catchall_b
    move-exception p0

    const-string p1, "MenuShim"

    const-string p2, "precedeTrig threw"

    invoke-static {p1, p2, p0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    return v1
.end method

.method public static resetMenuState()V
    .registers 1

    .line 150
    const/4 v0, 0x0

    sput-boolean v0, Lorg/cocos2dx/cpp/MenuShim;->sMenuOpen:Z

    return-void
.end method

.method public static setCommonVariable(ID)I
    .registers 4

    .line 131
    sget-boolean v0, Lorg/cocos2dx/cpp/MenuShim;->sInitOk:Z

    if-nez v0, :cond_6

    const/4 p0, 0x0

    return p0

    .line 132
    :cond_6
    :try_start_6
    invoke-static {p0, p1, p2}, Lorg/cocos2dx/cpp/MenuShim;->nativeSetCommonVariable(ID)I

    move-result p0
    :try_end_a
    .catchall {:try_start_6 .. :try_end_a} :catchall_b

    return p0

    .line 133
    :catchall_b
    move-exception p0

    const-string p1, "MenuShim"

    const-string p2, "setCommonVar threw"

    invoke-static {p1, p2, p0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    const/4 p0, -0x1

    return p0
.end method

.method public static tapKey(IJ)V
    .registers 7

    .line 78
    sget-boolean v0, Lorg/cocos2dx/cpp/MenuShim;->sInitOk:Z

    if-nez v0, :cond_5

    return-void

    .line 79
    :cond_5
    const/4 v0, 0x1

    invoke-static {p0, v0}, Lorg/cocos2dx/cpp/MenuShim;->injectKey(IZ)Z

    .line 80
    new-instance v0, Landroid/os/Handler;

    invoke-static {}, Landroid/os/Looper;->getMainLooper()Landroid/os/Looper;

    move-result-object v1

    invoke-direct {v0, v1}, Landroid/os/Handler;-><init>(Landroid/os/Looper;)V

    new-instance v1, Lorg/cocos2dx/cpp/MenuShim$1;

    invoke-direct {v1, p0}, Lorg/cocos2dx/cpp/MenuShim$1;-><init>(I)V

    const-wide/16 v2, 0x1

    .line 84
    invoke-static {v2, v3, p1, p2}, Ljava/lang/Math;->max(JJ)J

    move-result-wide p0

    .line 80
    invoke-virtual {v0, v1, p0, p1}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 85
    return-void
.end method

.method public static toggleMenu()I
    .registers 1

    .line 154
    sget-boolean v0, Lorg/cocos2dx/cpp/MenuShim;->sMenuOpen:Z

    if-eqz v0, :cond_9

    invoke-static {}, Lorg/cocos2dx/cpp/MenuShim;->closeMainMenu()I

    move-result v0

    return v0

    .line 155
    :cond_9
    invoke-static {}, Lorg/cocos2dx/cpp/MenuShim;->openMainMenu()I

    move-result v0

    return v0
.end method
