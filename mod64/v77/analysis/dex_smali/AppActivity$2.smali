.class Lorg/cocos2dx/cpp/AppActivity$2;
.super Ljava/lang/Object;
.source "AppActivity.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lorg/cocos2dx/cpp/AppActivity;->emergencyCachePurge(Ljava/lang/String;)V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic this$0:Lorg/cocos2dx/cpp/AppActivity;

.field final synthetic val$startMs:J


# direct methods
.method constructor <init>(Lorg/cocos2dx/cpp/AppActivity;J)V
    .registers 4
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "()V"
        }
    .end annotation

    .line 328
    iput-object p1, p0, Lorg/cocos2dx/cpp/AppActivity$2;->this$0:Lorg/cocos2dx/cpp/AppActivity;

    iput-wide p2, p0, Lorg/cocos2dx/cpp/AppActivity$2;->val$startMs:J

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .registers 8

    .line 331
    const-string v0, "hell_runtime.log"

    :try_start_2
    const-string v1, "org.cocos2dx.lib.Cocos2dxJavascriptJavaBridge"

    invoke-static {v1}, Ljava/lang/Class;->forName(Ljava/lang/String;)Ljava/lang/Class;

    move-result-object v1

    .line 332
    const-string v2, "evalString"

    const/4 v3, 0x1

    new-array v4, v3, [Ljava/lang/Class;

    const-class v5, Ljava/lang/String;

    const/4 v6, 0x0

    aput-object v5, v4, v6

    invoke-virtual {v1, v2, v4}, Ljava/lang/Class;->getMethod(Ljava/lang/String;[Ljava/lang/Class;)Ljava/lang/reflect/Method;

    move-result-object v1

    .line 333
    const/4 v2, 0x0

    new-array v3, v3, [Ljava/lang/Object;

    const-string v4, "(function(){try{  if (typeof cc!==\'undefined\' && cc.director){    var tc = cc.director.getTextureCache && cc.director.getTextureCache();    if (tc && tc.removeUnusedTextures) tc.removeUnusedTextures();    var sfc = cc.spriteFrameCache;    if (sfc && sfc.removeUnusedSpriteFrames) sfc.removeUnusedSpriteFrames();    if (cc.director.purgeCachedData) cc.director.purgeCachedData();  }}catch(e){}})();"

    aput-object v4, v3, v6

    invoke-virtual {v1, v2, v3}, Ljava/lang/reflect/Method;->invoke(Ljava/lang/Object;[Ljava/lang/Object;)Ljava/lang/Object;

    move-result-object v1

    .line 334
    iget-object v2, p0, Lorg/cocos2dx/cpp/AppActivity$2;->this$0:Lorg/cocos2dx/cpp/AppActivity;

    new-instance v3, Ljava/lang/StringBuilder;

    invoke-direct {v3}, Ljava/lang/StringBuilder;-><init>()V

    const-string v4, "JAVA cachePurge GLthread evalString rv="

    invoke-virtual {v3, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v3

    invoke-virtual {v3, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/Object;)Ljava/lang/StringBuilder;

    move-result-object v1

    const-string v3, " elapsedMs="

    invoke-virtual {v1, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    .line 336
    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v3

    iget-wide v5, p0, Lorg/cocos2dx/cpp/AppActivity$2;->val$startMs:J

    sub-long/2addr v3, v5

    invoke-virtual {v1, v3, v4}, Ljava/lang/StringBuilder;->append(J)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    .line 334
    # invokes: Lorg/cocos2dx/cpp/AppActivity;->writeDiag(Ljava/lang/String;Ljava/lang/String;)V
    invoke-static {v2, v0, v1}, Lorg/cocos2dx/cpp/AppActivity;->access$200(Lorg/cocos2dx/cpp/AppActivity;Ljava/lang/String;Ljava/lang/String;)V
    :try_end_4a
    .catchall {:try_start_2 .. :try_end_4a} :catchall_4b

    .line 340
    goto :goto_64

    .line 337
    :catchall_4b
    move-exception v1

    .line 338
    iget-object v2, p0, Lorg/cocos2dx/cpp/AppActivity$2;->this$0:Lorg/cocos2dx/cpp/AppActivity;

    new-instance v3, Ljava/lang/StringBuilder;

    invoke-direct {v3}, Ljava/lang/StringBuilder;-><init>()V

    const-string v4, "JAVA cachePurge GLthread evalString FAILED: "

    invoke-virtual {v3, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v3

    invoke-virtual {v3, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/Object;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    # invokes: Lorg/cocos2dx/cpp/AppActivity;->writeDiag(Ljava/lang/String;Ljava/lang/String;)V
    invoke-static {v2, v0, v1}, Lorg/cocos2dx/cpp/AppActivity;->access$200(Lorg/cocos2dx/cpp/AppActivity;Ljava/lang/String;Ljava/lang/String;)V

    .line 341
    :goto_64
    return-void
.end method
