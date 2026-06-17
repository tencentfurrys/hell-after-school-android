#pragma once
#include "imgui.h"
#include "cocos2d.h"
namespace cocos2d {
class ImGuiLayer : public cocos2d::Layer {
public:
    static ImGuiLayer* create() {
        auto layer = new (std::nothrow) ImGuiLayer();
        if (layer && layer->init()) {
            layer->autorelease();
            return layer;
        }
        CC_SAFE_DELETE(layer);
        return nullptr;
    }
};
}
