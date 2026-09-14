.class Lorg/cocos2dx/cpp/GamepadOverlay$3$1;
.super Ljava/lang/Object;
.source "GamepadOverlay.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lorg/cocos2dx/cpp/GamepadOverlay$3;->run()V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic this$1:Lorg/cocos2dx/cpp/GamepadOverlay$3;


# direct methods
.method constructor <init>(Lorg/cocos2dx/cpp/GamepadOverlay$3;)V
    .registers 2

    .line 696
    iput-object p1, p0, Lorg/cocos2dx/cpp/GamepadOverlay$3$1;->this$1:Lorg/cocos2dx/cpp/GamepadOverlay$3;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .registers 5

    .line 698
    iget-object v0, p0, Lorg/cocos2dx/cpp/GamepadOverlay$3$1;->this$1:Lorg/cocos2dx/cpp/GamepadOverlay$3;

    iget-object v0, v0, Lorg/cocos2dx/cpp/GamepadOverlay$3;->this$0:Lorg/cocos2dx/cpp/GamepadOverlay;

    iget-object v1, p0, Lorg/cocos2dx/cpp/GamepadOverlay$3$1;->this$1:Lorg/cocos2dx/cpp/GamepadOverlay$3;

    iget v1, v1, Lorg/cocos2dx/cpp/GamepadOverlay$3;->val$actKey:I

    const/4 v2, 0x0

    # invokes: Lorg/cocos2dx/cpp/GamepadOverlay;->rawInject(IZ)V
    invoke-static {v0, v1, v2}, Lorg/cocos2dx/cpp/GamepadOverlay;->access$500(Lorg/cocos2dx/cpp/GamepadOverlay;IZ)V

    .line 699
    iget-object v0, p0, Lorg/cocos2dx/cpp/GamepadOverlay$3$1;->this$1:Lorg/cocos2dx/cpp/GamepadOverlay$3;

    iget-object v0, v0, Lorg/cocos2dx/cpp/GamepadOverlay$3;->this$0:Lorg/cocos2dx/cpp/GamepadOverlay;

    # getter for: Lorg/cocos2dx/cpp/GamepadOverlay;->comboHandler:Landroid/os/Handler;
    invoke-static {v0}, Lorg/cocos2dx/cpp/GamepadOverlay;->access$600(Lorg/cocos2dx/cpp/GamepadOverlay;)Landroid/os/Handler;

    move-result-object v0

    new-instance v1, Lorg/cocos2dx/cpp/GamepadOverlay$3$1$1;

    invoke-direct {v1, p0}, Lorg/cocos2dx/cpp/GamepadOverlay$3$1$1;-><init>(Lorg/cocos2dx/cpp/GamepadOverlay$3$1;)V

    const-wide/16 v2, 0x23

    invoke-virtual {v0, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 702
    return-void
.end method
