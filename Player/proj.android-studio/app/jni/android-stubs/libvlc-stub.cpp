// No-op implementations of every libvlc symbol the PGMMV player uses.
// Compiled into the Android build instead of linking real libvlc.
// Effect: any libvlc_* call from VideoSprite.cpp returns benign defaults;
// the engine sees video as "ended" immediately and moves on.

#include "vlc/vlc.h"
#include <cstddef>
#include <cstdlib>

extern "C" {

// Provide dummy struct definitions so sizeof/alignment work if needed.
struct libvlc_instance_t      { int _; };
struct libvlc_media_t         { int _; };
struct libvlc_media_player_t  { int _; };
struct libvlc_event_manager_t { int _; };

static libvlc_instance_t      g_inst    = {0};
static libvlc_media_t         g_media   = {0};
static libvlc_media_player_t  g_player  = {0};
static libvlc_event_manager_t g_evtmgr  = {0};

libvlc_instance_t *libvlc_new(int, const char *const *) { return &g_inst; }
void libvlc_release(libvlc_instance_t *) {}
libvlc_media_t *libvlc_media_new_path(libvlc_instance_t *, const char *) { return &g_media; }
void libvlc_media_release(libvlc_media_t *) {}
void libvlc_media_add_option(libvlc_media_t *, const char *) {}
libvlc_media_player_t *libvlc_media_player_new_from_media(libvlc_media_t *) { return &g_player; }
void libvlc_media_player_release(libvlc_media_player_t *) {}
int  libvlc_media_player_play(libvlc_media_player_t *) { return 0; }
void libvlc_media_player_stop(libvlc_media_player_t *) {}
void libvlc_media_player_set_pause(libvlc_media_player_t *, int) {}
libvlc_state_t libvlc_media_player_get_state(libvlc_media_player_t *) { return libvlc_Ended; }
libvlc_event_manager_t *libvlc_media_player_event_manager(libvlc_media_player_t *) { return &g_evtmgr; }
int  libvlc_event_attach(libvlc_event_manager_t *, libvlc_event_type_t, libvlc_callback_t, void *) { return 0; }
void libvlc_video_set_callbacks(libvlc_media_player_t *, libvlc_video_lock_cb, libvlc_video_unlock_cb, libvlc_video_display_cb, void *) {}
void libvlc_video_set_format(libvlc_media_player_t *, const char *, unsigned, unsigned, unsigned) {}
void libvlc_video_set_format_callbacks(libvlc_media_player_t *, libvlc_video_format_cb, libvlc_video_cleanup_cb) {}
void libvlc_audio_set_volume(libvlc_media_player_t *, int) {}
int  libvlc_audio_get_volume(libvlc_media_player_t *) { return 100; }

}
