#pragma once
#include "imgui.h"
#include "cocos2d.h"
namespace cocos2d {
class ImGuiLayer : public cocos2d::Layer {
public:
    static ImGuiLayer* create() { return nullptr; }
};
}
