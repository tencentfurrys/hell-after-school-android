.class Lorg/cocos2dx/cpp/GamepadOverlay$4$1$1;
.super Ljava/lang/Object;
.source "GamepadOverlay.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lorg/cocos2dx/cpp/GamepadOverlay$4$1;->run()V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic this$2:Lorg/cocos2dx/cpp/GamepadOverlay$4$1;


# direct methods
.method constructor <init>(Lorg/cocos2dx/cpp/GamepadOverlay$4$1;)V
    .registers 2

    .line 717
    iput-object p1, p0, Lorg/cocos2dx/cpp/GamepadOverlay$4$1$1;->this$2:Lorg/cocos2dx/cpp/GamepadOverlay$4$1;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .registers 5

    .line 719
    iget-object v0, p0, Lorg/cocos2dx/cpp/GamepadOverlay$4$1$1;->this$2:Lorg/cocos2dx/cpp/GamepadOverlay$4$1;

    iget-object v0, v0, Lorg/cocos2dx/cpp/GamepadOverlay$4$1;->this$1:Lorg/cocos2dx/cpp/GamepadOverlay$4;

    iget-object v0, v0, Lorg/cocos2dx/cpp/GamepadOverlay$4;->this$0:Lorg/cocos2dx/cpp/GamepadOverlay;

    iget-object v1, p0, Lorg/cocos2dx/cpp/GamepadOverlay$4$1$1;->this$2:Lorg/cocos2dx/cpp/GamepadOverlay$4$1;

    iget-object v1, v1, Lorg/cocos2dx/cpp/GamepadOverlay$4$1;->this$1:Lorg/cocos2dx/cpp/GamepadOverlay$4;

    iget v1, v1, Lorg/cocos2dx/cpp/GamepadOverlay$4;->val$arrowKey:I

    const/4 v2, 0x0

    # invokes: Lorg/cocos2dx/cpp/GamepadOverlay;->rawInject(IZ)V
    invoke-static {v0, v1, v2}, Lorg/cocos2dx/cpp/GamepadOverlay;->access$500(Lorg/cocos2dx/cpp/GamepadOverlay;IZ)V

    .line 720
    iget-object v0, p0, Lorg/cocos2dx/cpp/GamepadOverlay$4$1$1;->this$2:Lorg/cocos2dx/cpp/GamepadOverlay$4$1;

    iget-object v0, v0, Lorg/cocos2dx/cpp/GamepadOverlay$4$1;->this$1:Lorg/cocos2dx/cpp/GamepadOverlay$4;

    iget-object v0, v0, Lorg/cocos2dx/cpp/GamepadOverlay$4;->this$0:Lorg/cocos2dx/cpp/GamepadOverlay;

    # getter for: Lorg/cocos2dx/cpp/GamepadOverlay;->comboHandler:Landroid/os/Handler;
    invoke-static {v0}, Lorg/cocos2dx/cpp/GamepadOverlay;->access$600(Lorg/cocos2dx/cpp/GamepadOverlay;)Landroid/os/Handler;

    move-result-object v0

    new-instance v1, Lorg/cocos2dx/cpp/GamepadOverlay$4$1$1$1;

    invoke-direct {v1, p0}, Lorg/cocos2dx/cpp/GamepadOverlay$4$1$1$1;-><init>(Lorg/cocos2dx/cpp/GamepadOverlay$4$1$1;)V

    const-wide/16 v2, 0x1e

    invoke-virtual {v0, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 723
    return-void
.end method
