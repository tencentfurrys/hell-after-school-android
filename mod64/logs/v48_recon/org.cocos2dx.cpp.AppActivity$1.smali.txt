.class Lorg/cocos2dx/cpp/AppActivity$1;
.super Ljava/lang/Object;
.source "AppActivity.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingClass;
    value = Lorg/cocos2dx/cpp/AppActivity;
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic this$0:Lorg/cocos2dx/cpp/AppActivity;


# direct methods
.method constructor <init>(Lorg/cocos2dx/cpp/AppActivity;)V
    .registers 2

    .line 221
    iput-object p1, p0, Lorg/cocos2dx/cpp/AppActivity$1;->this$0:Lorg/cocos2dx/cpp/AppActivity;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .registers 4

    .line 224
    :try_start_0
    iget-object v0, p0, Lorg/cocos2dx/cpp/AppActivity$1;->this$0:Lorg/cocos2dx/cpp/AppActivity;

    const-string v1, "periodic20s"

    # invokes: Lorg/cocos2dx/cpp/AppActivity;->emergencyCachePurge(Ljava/lang/String;)V
    invoke-static {v0, v1}, Lorg/cocos2dx/cpp/AppActivity;->access$000(Lorg/cocos2dx/cpp/AppActivity;Ljava/lang/String;)V
    :try_end_7
    .catchall {:try_start_0 .. :try_end_7} :catchall_8

    goto :goto_9

    .line 225
    :catchall_8
    move-exception v0

    :goto_9
    nop

    .line 226
    iget-object v0, p0, Lorg/cocos2dx/cpp/AppActivity$1;->this$0:Lorg/cocos2dx/cpp/AppActivity;

    # getter for: Lorg/cocos2dx/cpp/AppActivity;->mPurgeHandler:Landroid/os/Handler;
    invoke-static {v0}, Lorg/cocos2dx/cpp/AppActivity;->access$100(Lorg/cocos2dx/cpp/AppActivity;)Landroid/os/Handler;

    move-result-object v0

    if-eqz v0, :cond_1e

    .line 229
    iget-object v0, p0, Lorg/cocos2dx/cpp/AppActivity$1;->this$0:Lorg/cocos2dx/cpp/AppActivity;

    # getter for: Lorg/cocos2dx/cpp/AppActivity;->mPurgeHandler:Landroid/os/Handler;
    invoke-static {v0}, Lorg/cocos2dx/cpp/AppActivity;->access$100(Lorg/cocos2dx/cpp/AppActivity;)Landroid/os/Handler;

    move-result-object v0

    const-wide/32 v1, 0xea60

    invoke-virtual {v0, p0, v1, v2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 231
    :cond_1e
    return-void
.end method
