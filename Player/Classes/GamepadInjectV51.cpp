// GamepadInject.cpp - v51 native input injection
// Implements the JNI symbol the modded GamepadOverlay Java has always called.
// Routes an injected cocos2d keycode into the SAME InputManager state the
// running scene polls every frame - identical to the real keyboard listener:
//   InputManager::getInstance()->getInputDataRaw()->registerKeyPressed(code, scancode)
//
// v51 fix: the overlay sends the LETTER on the button face as the cocos2d
// keycode. For most buttons the face key IS the game action (Jump=SPACE,
// W=switch, S, D, D-pad) so they work as-is. But three buttons have a face
// label that differs from their real action key:
//     X (overlay cc KEY_X)  = ATTACK           -> KEY_A
//     C (overlay cc KEY_C)  = DASH             -> KEY_LEFT_SHIFT
//     V (overlay cc KEY_V)  = COLLECTIBLES MENU-> KEY_LEFT_CTRL
// We remap ONLY those three, by cocos2d enum symbol (compiler resolves the
// exact ordinal from the real engine header - no hand-computed numbers).
#include "cocos2d.h"
#include "Manager/InputManager.h"
#include <jni.h>

using namespace cocos2d;

static int remapOverlayKey(int cc)
{
    typedef cocos2d::EventKeyboard::KeyCode KC;
    // Overlay face-key -> real game action key.
    if (cc == (int)KC::KEY_X) return (int)KC::KEY_A;           // attack
    if (cc == (int)KC::KEY_C) return (int)KC::KEY_LEFT_SHIFT;  // dash
    if (cc == (int)KC::KEY_V) return (int)KC::KEY_LEFT_CTRL;   // collectibles menu
    return cc;                                                 // everything else unchanged
}

extern "C" {

JNIEXPORT void JNICALL
Java_org_cocos2dx_cpp_GamepadOverlay_nativeInjectCocos2dKey(JNIEnv* env, jclass clazz, jint keyCode, jboolean pressed)
{
    int kc = remapOverlayKey((int)keyCode);
    bool press = (pressed == JNI_TRUE);
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
