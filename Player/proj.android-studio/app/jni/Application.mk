APP_STL := c++_static

APP_CPPFLAGS := -frtti -fexceptions -DCC_ENABLE_CHIPMUNK_INTEGRATION=1 -DUSE_AGTK -DAGTK_RUNTIME -DAGTK_RELEASE -DUSE_RUNTIME -DCC_TEXTURE_ATLAS_USE_VAO=0 -std=c++11 -fsigned-char
APP_LDFLAGS  := -latomic -Wl,-Bsymbolic -Wl,-z,notext -Wl,-z,max-page-size=16384 -Wl,-z,common-page-size=16384

# Galaxy J3 Orbit is 32-bit ARMv7; arm64-v8a for everything else modern.
APP_ABI := armeabi-v7a arm64-v8a
APP_PLATFORM := android-26

ifeq ($(NDK_DEBUG),1)
  APP_CPPFLAGS += -DCOCOS2D_DEBUG=1
  APP_OPTIM := debug
else
  APP_CPPFLAGS += -DNDEBUG
  APP_OPTIM := release
endif
