.class Lorg/cocos2dx/cpp/GamepadOverlay$3$1$1;
.super Ljava/lang/Object;
.source "GamepadOverlay.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lorg/cocos2dx/cpp/GamepadOverlay$3$1;->run()V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic this$2:Lorg/cocos2dx/cpp/GamepadOverlay$3$1;


# direct methods
.method constructor <init>(Lorg/cocos2dx/cpp/GamepadOverlay$3$1;)V
    .registers 2

    .line 699
    iput-object p1, p0, Lorg/cocos2dx/cpp/GamepadOverlay$3$1$1;->this$2:Lorg/cocos2dx/cpp/GamepadOverlay$3$1;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .registers 4

    .line 700
    iget-object v0, p0, Lorg/cocos2dx/cpp/GamepadOverlay$3$1$1;->this$2:Lorg/cocos2dx/cpp/GamepadOverlay$3$1;

    iget-object v0, v0, Lorg/cocos2dx/cpp/GamepadOverlay$3$1;->this$1:Lorg/cocos2dx/cpp/GamepadOverlay$3;

    iget-object v0, v0, Lorg/cocos2dx/cpp/GamepadOverlay$3;->this$0:Lorg/cocos2dx/cpp/GamepadOverlay;

    iget-object v1, p0, Lorg/cocos2dx/cpp/GamepadOverlay$3$1$1;->this$2:Lorg/cocos2dx/cpp/GamepadOverlay$3$1;

    iget-object v1, v1, Lorg/cocos2dx/cpp/GamepadOverlay$3$1;->this$1:Lorg/cocos2dx/cpp/GamepadOverlay$3;

    iget v1, v1, Lorg/cocos2dx/cpp/GamepadOverlay$3;->val$modKey:I

    const/4 v2, 0x0

    # invokes: Lorg/cocos2dx/cpp/GamepadOverlay;->rawInject(IZ)V
    invoke-static {v0, v1, v2}, Lorg/cocos2dx/cpp/GamepadOverlay;->access$500(Lorg/cocos2dx/cpp/GamepadOverlay;IZ)V

    return-void
.end method
