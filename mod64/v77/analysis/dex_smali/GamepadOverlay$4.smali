.class Lorg/cocos2dx/cpp/GamepadOverlay$4;
.super Ljava/lang/Object;
.source "GamepadOverlay.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lorg/cocos2dx/cpp/GamepadOverlay;->fireShootCombo(I)V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic this$0:Lorg/cocos2dx/cpp/GamepadOverlay;

.field final synthetic val$arrowKey:I


# direct methods
.method constructor <init>(Lorg/cocos2dx/cpp/GamepadOverlay;I)V
    .registers 3
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "()V"
        }
    .end annotation

    .line 711
    iput-object p1, p0, Lorg/cocos2dx/cpp/GamepadOverlay$4;->this$0:Lorg/cocos2dx/cpp/GamepadOverlay;

    iput p2, p0, Lorg/cocos2dx/cpp/GamepadOverlay$4;->val$arrowKey:I

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .registers 5

    .line 713
    iget-object v0, p0, Lorg/cocos2dx/cpp/GamepadOverlay$4;->this$0:Lorg/cocos2dx/cpp/GamepadOverlay;

    const/16 v1, 0x95

    const/4 v2, 0x1

    # invokes: Lorg/cocos2dx/cpp/GamepadOverlay;->rawInject(IZ)V
    invoke-static {v0, v1, v2}, Lorg/cocos2dx/cpp/GamepadOverlay;->access$500(Lorg/cocos2dx/cpp/GamepadOverlay;IZ)V

    .line 714
    iget-object v0, p0, Lorg/cocos2dx/cpp/GamepadOverlay$4;->this$0:Lorg/cocos2dx/cpp/GamepadOverlay;

    # getter for: Lorg/cocos2dx/cpp/GamepadOverlay;->comboHandler:Landroid/os/Handler;
    invoke-static {v0}, Lorg/cocos2dx/cpp/GamepadOverlay;->access$600(Lorg/cocos2dx/cpp/GamepadOverlay;)Landroid/os/Handler;

    move-result-object v0

    new-instance v1, Lorg/cocos2dx/cpp/GamepadOverlay$4$1;

    invoke-direct {v1, p0}, Lorg/cocos2dx/cpp/GamepadOverlay$4$1;-><init>(Lorg/cocos2dx/cpp/GamepadOverlay$4;)V

    const-wide/16 v2, 0x37

    invoke-virtual {v0, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 727
    return-void
.end method
