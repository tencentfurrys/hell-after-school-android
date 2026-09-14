.class Lorg/cocos2dx/cpp/MenuShim$1;
.super Ljava/lang/Object;
.source "MenuShim.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lorg/cocos2dx/cpp/MenuShim;->tapKey(IJ)V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic val$cocos2dKeyCode:I


# direct methods
.method constructor <init>(I)V
    .registers 2
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "()V"
        }
    .end annotation

    .line 80
    iput p1, p0, Lorg/cocos2dx/cpp/MenuShim$1;->val$cocos2dKeyCode:I

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .registers 3

    .line 82
    iget v0, p0, Lorg/cocos2dx/cpp/MenuShim$1;->val$cocos2dKeyCode:I

    const/4 v1, 0x0

    invoke-static {v0, v1}, Lorg/cocos2dx/cpp/MenuShim;->injectKey(IZ)Z

    .line 83
    return-void
.end method
