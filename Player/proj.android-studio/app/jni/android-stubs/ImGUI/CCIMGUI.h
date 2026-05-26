#pragma once
#include "imgui.h"
#include "cocos2d.h"
namespace cocos2d {
class CCIMGUI {
public:
    static CCIMGUI* getInstance() { static CCIMGUI s; return &s; }
    void setFontName(const std::string&) {}
    void addImGUI(std::function<void()>, const std::string&) {}
    void removeImGUI(const std::string&) {}
    bool exist(const std::string&) { return false; }
    ImFont* addFontFile(const std::string&, float, const unsigned short* =nullptr, const unsigned short* =nullptr) { return nullptr; }
    void enableFont(ImFont*) {}
    void disableFont() {}
};
}
