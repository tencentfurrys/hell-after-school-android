#!/usr/bin/env python3
# v31 engine patcher — runs on the CI runner against the REAL unredacted source.
# Adds readable observability to GameManager.cpp:
#   1) #include <dlfcn.h> and <android/log.h>
#   2) actionLog() also emits each composed line to logcat (tag EngineAction),
#      which the app's Java logger captures into hell_runtime.log; and, if
#      libmenushim exports menushim_action_log(), appends to engine_action.log.
#   3) always-on markers through the boot/render chain (AGTK_DEBUG_ACTION_LOG is
#      compiled out in release, so we call actionLog(1,...) directly)
import sys, io

PATH = sys.argv[1] if len(sys.argv) > 1 else "Player/Classes/Manager/GameManager.cpp"

with io.open(PATH, "r", encoding="utf-8", errors="surrogateescape", newline="") as f:
    s = f.read()

nl = "\r\n" if "\r\n" in s else "\n"

def must(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        print("PATCH-FAIL [%s]: anchor count=%d (expected 1)" % (label, n)); sys.exit(1)
    s = s.replace(old, new, 1)
    print("PATCH-OK [%s]" % label)

# 1) includes
must('#include "DebugManager.h"',
     '#include "DebugManager.h"' + nl +
     "#include <dlfcn.h>        // v31 observability" + nl +
     "#include <android/log.h>  // v31 observability",
     "includes")

# 2) surface actionLog output to readable channels
mirror = (
    "\t\tfileUtils->addStringToFile(tmp, filePath);" + nl +
    "\t\t{ // v31: action_log.txt is not in the diag zip, so also surface readable copies" + nl +
    "\t\t\t__android_log_print(ANDROID_LOG_INFO, \"EngineAction\", \"%s\", tmp.c_str()); // -> hell_runtime.log" + nl +
    "\t\t\tstatic void(*s_mlog)(const char*) = nullptr; static bool s_tried = false;" + nl +
    "\t\t\tif (!s_tried) { s_tried = true; void* h = dlopen(\"libmenushim.so\", RTLD_NOLOAD | RTLD_GLOBAL);" + nl +
    "\t\t\t\tif (h) s_mlog = (void(*)(const char*))dlsym(h, \"menushim_action_log\"); }" + nl +
    "\t\t\tif (s_mlog) s_mlog(tmp.c_str()); // -> <diagDir>/engine_action.log" + nl +
    "\t\t}"
)
must("\t\tfileUtils->addStringToFile(tmp, filePath);", mirror, "actionLog-mirror")

# 3) boot/render-chain markers (always-on)
must("\tauto scene = Scene::createWithPhysics();",
     "\tGameManager::getInstance()->actionLog(1, \"# v31 createCanvas: enter (bLoading=%d)\", (int)bLoading);" + nl +
     "\tauto scene = Scene::createWithPhysics();" + nl +
     "\tGameManager::getInstance()->actionLog(1, \"# v31 createCanvas: after createWithPhysics scene=%p\", (void*)scene);",
     "marker-createWithPhysics")

must("\t\tlayer = GameScene::create(id);",
     "\t\tGameManager::getInstance()->actionLog(1, \"# v31 createCanvas: pre GameScene::create id=%d\", id);" + nl +
     "\t\tlayer = GameScene::create(id);" + nl +
     "\t\tGameManager::getInstance()->actionLog(1, \"# v31 createCanvas: post GameScene::create layer=%p\", (void*)layer);",
     "marker-gamescene")

must("\t\t\t\tscene->addChild(renderTexture);",
     "\t\t\t\tGameManager::getInstance()->actionLog(1, \"# v31 createCanvas: pre addChild renderTexture=%p\", (void*)renderTexture);" + nl +
     "\t\t\t\tscene->addChild(renderTexture);" + nl +
     "\t\t\t\tGameManager::getInstance()->actionLog(1, \"# v31 createCanvas: post addChild renderTexture\");",
     "marker-rendertexture")

must("\tdirector->runWithScene(scene);",
     "\tGameManager::getInstance()->actionLog(1, \"# v31 startCanvas: pre runWithScene scene=%p\", (void*)scene);" + nl +
     "\tdirector->runWithScene(scene);" + nl +
     "\tGameManager::getInstance()->actionLog(1, \"# v31 startCanvas: post runWithScene (returned)\");",
     "marker-runwithscene")

with io.open(PATH, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
    f.write(s)
print("v31 engine patch applied OK")
