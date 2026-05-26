#pragma once
#include "imgui.h"
#include "cocos2d.h"
namespace cocos2d {
class IMGUIGLViewImpl : public GLView {
public:
    bool isFocusInIme() const { return false; }
    void setImeOpenStatus(bool) {}
    void onFocusInIme() {}
    void onFocusOutIme() {}
    bool isFullScreen() const { return false; }
    void setFullScreen() {}
    void setFullScreen(bool) {}
    void setFullScreen(bool, float, float) {}
    void restoreScreen() {}
    void focusWindow() {}
    void minimizeWindow() {}
    void maximizeWindow() {}
};
}
