// Android stub for DllPluginManager — no-op since Android has no LoadLibrary.
// PGMMV uses .dll plugins on Windows for the in-engine editor; runtime games don't need them.
#include "Manager/DllPluginManager.h"

class DllPluginManagerAndroid : public DllPluginManager {
public:
    DllPluginManagerAndroid() {}
    virtual ~DllPluginManagerAndroid() {}
    virtual bool loadPlugins() override { return true; }
    virtual void unloadPlugins() override {}
    virtual void updatePlugins(float dt) override {}
};

// Provide the static _dllPluginManager definition + factory
DllPluginManager *DllPluginManager::_dllPluginManager = nullptr;

DllPluginManager *DllPluginManager::getInstance() {
    if (!_dllPluginManager) {
        _dllPluginManager = new DllPluginManagerAndroid();
    }
    return _dllPluginManager;
}

void DllPluginManager::purge() {
    if (_dllPluginManager) {
        delete _dllPluginManager;
        _dllPluginManager = nullptr;
    }
}

DllPluginManager::DllPluginManager() {}
DllPluginManager::~DllPluginManager() {}

// Android stubs for AGTK audio/vibration extensions
#include "audio/include/AudioEngine.h"
namespace cocos2d { namespace experimental {
bool AudioEngine::isAudioEngineImpl() { return _audioEngineImpl != nullptr; }
bool AudioEngine::checkChangeDevice() { return false; }
void AudioEngine::changeDevice() {}
}}

#include "platform/CCVibration.h"
namespace cocos2d {
void Vibration::playVibrationFile(int, int) {}
}
