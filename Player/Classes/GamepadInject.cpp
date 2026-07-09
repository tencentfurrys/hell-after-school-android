// GamepadInject.cpp - v49 native input injection
// Implements the JNI symbol the modded GamepadOverlay Java has ALWAYS called
// (and which threw UnsatisfiedLinkError on arm64 because it was never built).
// Routes an injected cocos2d keycode into the SAME InputManager state the
// running scene polls every frame - identical to the real keyboard listener:
//   InputManager::getInstance()->getInputDataRaw()->registerKeyPressed(code, scancode)
#include "cocos2d.h"
#include "Manager/InputManager.h"
#include <jni.h>

using namespace cocos2d;

extern "C" {

JNIEXPORT void JNICALL
Java_org_cocos2dx_cpp_GamepadOverlay_nativeInjectCocos2dKey(JNIEnv* env, jclass clazz, jint keyCode, jboolean pressed)
{
    int kc = (int)keyCode;
    bool press = (pressed == JNI_TRUE);
    // InputManager mutation must happen on the cocos2d (GL) thread, same thread
    // the real EventKeyboard listener runs on.
    auto sched = Director::getInstance()->getScheduler();
    sched->performFunctionInCocosThread([kc, press]() {
        auto im = InputManager::getInstance();
        if (im == nullptr) return;
        auto raw = im->getInputDataRaw();
        if (raw == nullptr) return;
        if (press) {
            raw->registerKeyPressed(kc, kc);
        } else {
            raw->registerKeyReleased(kc, kc);
        }
    });
}

} // extern "C"
