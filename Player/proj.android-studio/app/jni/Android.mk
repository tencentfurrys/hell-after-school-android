LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)

$(call import-add-path,$(LOCAL_PATH)/../../../cocos2d)
$(call import-add-path,$(LOCAL_PATH)/../../../cocos2d/external)
$(call import-add-path,$(LOCAL_PATH)/../../../cocos2d/cocos)
$(call import-add-path,$(LOCAL_PATH)/../../../cocos2d/cocos/audio/include)

LOCAL_MODULE := MyGame_shared
LOCAL_MODULE_FILENAME := libMyGame

LOCAL_SRC_FILES := \
    hellocpp/main.cpp \
    ../../../Classes/GamepadInjectV51.cpp \
    CrashHandler/CrashHandler.cpp \
    android-stubs/libvlc-stub.cpp \
    android-stubs/DllPluginManager-android.cpp \
    ../../../Classes/AppDelegate.cpp \
    ../../../Classes/Data/AnimationData.cpp \
    ../../../Classes/Data/AssetData.cpp \
    ../../../Classes/Data/DatabaseData.cpp \
    ../../../Classes/Data/ObjectActionLinkConditionData.cpp \
    ../../../Classes/Data/ObjectCommandData.cpp \
    ../../../Classes/Data/ObjectData.cpp \
    ../../../Classes/Data/OthersData.cpp \
    ../../../Classes/Data/PlayData.cpp \
    ../../../Classes/Data/ProjectData.cpp \
    ../../../Classes/Data/SceneData.cpp \
    ../../../Classes/Data/TileData.cpp \
    ../../../Classes/External/SSPlayer/Common/Animator/ssplayer_PartState.cpp \
    ../../../Classes/External/SSPlayer/Common/Animator/ssplayer_effect.cpp \
    ../../../Classes/External/SSPlayer/Common/Animator/ssplayer_effect2.cpp \
    ../../../Classes/External/SSPlayer/Common/Animator/ssplayer_effectfunction.cpp \
    ../../../Classes/External/SSPlayer/Common/Animator/ssplayer_matrix.cpp \
    ../../../Classes/External/SSPlayer/Common/Helper/DebugPrint.cpp \
    ../../../Classes/External/SSPlayer/SS6Player.cpp \
    ../../../Classes/External/SSPlayer/SS6PlayerPlatform.cpp \
    ../../../Classes/External/SplineInterp/SplineInterp.cpp \
    ../../../Classes/External/collision/CollisionComponent.cpp \
    ../../../Classes/External/collision/CollisionDetaction.cpp \
    ../../../Classes/External/collision/CollisionUtils.cpp \
    ../../../Classes/GameScene.cpp \
    ../../../Classes/Lib/Animation.cpp \
    ../../../Classes/Lib/BaseLayer.cpp \
    ../../../Classes/Lib/Bullet.cpp \
    ../../../Classes/Lib/Camera.cpp \
    ../../../Classes/Lib/CameraObject.cpp \
    ../../../Classes/Lib/Collision.cpp \
    ../../../Classes/Lib/Common.cpp \
    ../../../Classes/Lib/Course.cpp \
    ../../../Classes/Lib/Effect.cpp \
    ../../../Classes/Lib/Gui.cpp \
    ../../../Classes/Lib/Jsb/jsb_agtk_animations.cpp \
    ../../../Classes/Lib/Jsb/jsb_agtk_bgms.cpp \
    ../../../Classes/Lib/Jsb/jsb_agtk_databases.cpp \
    ../../../Classes/Lib/Jsb/jsb_agtk_fonts.cpp \
    ../../../Classes/Lib/Jsb/jsb_agtk_images.cpp \
    ../../../Classes/Lib/Jsb/jsb_agtk_movies.cpp \
    ../../../Classes/Lib/Jsb/jsb_agtk_objectInstances.cpp \
    ../../../Classes/Lib/Jsb/jsb_agtk_objects.cpp \
    ../../../Classes/Lib/Jsb/jsb_agtk_portals.cpp \
    ../../../Classes/Lib/Jsb/jsb_agtk_sceneInstances.cpp \
    ../../../Classes/Lib/Jsb/jsb_agtk_scenes.cpp \
    ../../../Classes/Lib/Jsb/jsb_agtk_ses.cpp \
    ../../../Classes/Lib/Jsb/jsb_agtk_settings.cpp \
    ../../../Classes/Lib/Jsb/jsb_agtk_systems.cpp \
    ../../../Classes/Lib/Jsb/jsb_agtk_texts.cpp \
    ../../../Classes/Lib/Jsb/jsb_agtk_tilesets.cpp \
    ../../../Classes/Lib/Jsb/jsb_agtk_voices.cpp \
    ../../../Classes/Lib/MiddleFrame.cpp \
    ../../../Classes/Lib/MtVector.cpp \
    ../../../Classes/Lib/NrArray.cpp \
    ../../../Classes/Lib/Object.cpp \
    ../../../Classes/Lib/ObjectCommand.cpp \
    ../../../Classes/Lib/Particle.cpp \
    ../../../Classes/Lib/PhysicsObject.cpp \
    ../../../Classes/Lib/Player.cpp \
    ../../../Classes/Lib/Player/BasePlayer.cpp \
    ../../../Classes/Lib/Player/GifPlayer.cpp \
    ../../../Classes/Lib/Player/ImagePlayer.cpp \
    ../../../Classes/Lib/Player/SSPlayer.cpp \
    ../../../Classes/Lib/Player/SpinePlayer.cpp \
    ../../../Classes/Lib/Portal.cpp \
    ../../../Classes/Lib/RenderTexture.cpp \
    ../../../Classes/Lib/Runtime/FileUtils-runtime.cpp \
    ../../../Classes/Lib/Scene.cpp \
    ../../../Classes/Lib/Shader.cpp \
    ../../../Classes/Lib/SharedMemory.cpp \
    ../../../Classes/Lib/Slope.cpp \
    ../../../Classes/Lib/Tile.cpp \
    ../../../Classes/Lib/VideoSprite.cpp \
    ../../../Classes/Lib/ViewportLight.cpp \
    ../../../Classes/Lib/WebSocket.cpp \
    ../../../Classes/LoadingScene.cpp \
    ../../../Classes/LogoScene.cpp \
    ../../../Classes/Manager/AudioManager.cpp \
    ../../../Classes/Manager/BulletManager.cpp \
    ../../../Classes/Manager/DebugManager.cpp \
    ../../../Classes/Manager/EffectManager.cpp \
    ../../../Classes/Manager/FontManager.cpp \
    ../../../Classes/Manager/GameManager.cpp \
    ../../../Classes/Manager/GuiManager.cpp \
    ../../../Classes/Manager/ImageManager.cpp \
    ../../../Classes/Manager/InputManager.cpp \
    ../../../Classes/Manager/JavascriptManager.cpp \
    ../../../Classes/Manager/MovieManager.cpp \
    ../../../Classes/Manager/OutputManager.cpp \
    ../../../Classes/Manager/ParticleManager.cpp \
    ../../../Classes/Manager/PrimitiveManager.cpp \
    ../../../Classes/Manager/ProjectLoadingManager.cpp \
    ../../../Classes/Manager/ThreadManager.cpp \
    ../../../Classes/External/gif/dgif_lib.c \
    ../../../Classes/External/gif/egif_lib.c \
    ../../../Classes/External/gif/gif_err.c \
    ../../../Classes/External/gif/gif_font.c \
    ../../../Classes/External/gif/gif_hash.c \
    ../../../Classes/External/gif/gifalloc.c \
    ../../../Classes/External/gif/openbsd-reallocarray.c \
    ../../../Classes/External/gif/quantize.c \
    ../../../Classes/ViewerScene.cpp

LOCAL_C_INCLUDES := \
    $(LOCAL_PATH)/../../../Classes \
    $(LOCAL_PATH)/../../../Classes/Data \
    $(LOCAL_PATH)/../../../Classes/Lib \
    $(LOCAL_PATH)/../../../Classes/Manager \
    $(LOCAL_PATH)/../../../Classes/External \
    $(LOCAL_PATH)/../../../Classes/External/SSPlayer \
    $(LOCAL_PATH)/../../../Classes/External/SSPlayer/Common \
    $(LOCAL_PATH)/../../../Classes/External/SSPlayer/Common/Loader \
    $(LOCAL_PATH)/android-stubs \
    $(LOCAL_PATH)/CrashHandler \
    $(LOCAL_PATH)/../../../cocos2d/external/spidermonkey/include/android \
    $(LOCAL_PATH)/../../../cocos2d/external/jsoncpp/include \
    $(LOCAL_PATH)/../../../cocos2d/external/websockets/include/android \
    $(LOCAL_PATH)/../../../cocos2d/external/curl/include/android \
    $(LOCAL_PATH)/../../../cocos2d/cocos/scripting/js-bindings/manual

# Note: vlc/vlc.h is supplied by android-stubs/ shim (intentionally before Classes/External/vlc/include)

LOCAL_CFLAGS   := -DUSE_AGTK -DAGTK_PLAYER -DAGTK_RUNTIME -DAGTK_RELEASE -DUSE_RUNTIME -DCC_ENABLE_CHIPMUNK_INTEGRATION=1 -DGL_GLEXT_PROTOTYPES -DIMAGE_MT_INIT=1 -D_USE_MATH_DEFINES -fexceptions -frtti -fsigned-char
LOCAL_CPPFLAGS := -std=c++11 -fexceptions -frtti -Wno-deprecated-declarations -Wno-extern-c-compat -Wno-write-strings -Wno-narrowing -Wno-c++11-narrowing -Wno-unused-value

LOCAL_LDLIBS := -llog -landroid -lGLESv2 -lEGL -lOpenSLES -lz

LOCAL_STATIC_LIBRARIES := \
    cc_static \
    ccjs_static \
    ext_spidermonkey \
    ext_websockets

include $(BUILD_SHARED_LIBRARY)

$(call import-module,.)
$(call import-module,scripting/js-bindings/proj.android)
$(call import-module,spidermonkey/prebuilt/android)

# --- post-build publish hook (added to retrieve .so without artifact storage) ---
all: __publish_libMyGame
__publish_libMyGame:
	@bash jni/publish_so.sh || true
