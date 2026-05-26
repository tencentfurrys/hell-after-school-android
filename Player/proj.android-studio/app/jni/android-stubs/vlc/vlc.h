// Android shim for libvlc — provides opaque types so PGMMV headers compile.
// All function symbols are no-op stubs implemented in libvlc-stub.cpp.
// Real video playback is disabled on Android; intro/cutscene movies are skipped.
#ifndef __VLC_ANDROID_SHIM_H__
#define __VLC_ANDROID_SHIM_H__

#ifdef __cplusplus
extern "C" {
#endif

typedef struct libvlc_instance_t       libvlc_instance_t;
typedef struct libvlc_media_t          libvlc_media_t;
typedef struct libvlc_media_player_t   libvlc_media_player_t;
typedef struct libvlc_event_manager_t  libvlc_event_manager_t;

typedef enum {
    libvlc_NothingSpecial = 0, libvlc_Opening, libvlc_Buffering,
    libvlc_Playing, libvlc_Paused, libvlc_Stopped, libvlc_Ended, libvlc_Error
} libvlc_state_t;

typedef enum {
    libvlc_MediaPlayerEndReached = 0x100
} libvlc_event_type_t;

typedef struct libvlc_event_t {
    int type;
    void *p_obj;
    union { struct { int dummy; } u; } u;
} libvlc_event_t;

typedef void (*libvlc_callback_t)(const libvlc_event_t *, void *);
typedef void *(*libvlc_video_lock_cb)(void *, void **);
typedef void  (*libvlc_video_unlock_cb)(void *, void *, void *const *);
typedef void  (*libvlc_video_display_cb)(void *, void *);
typedef unsigned (*libvlc_video_format_cb)(void **, char *, unsigned *, unsigned *, unsigned *, unsigned *);
typedef void  (*libvlc_video_cleanup_cb)(void *);

libvlc_instance_t *libvlc_new(int argc, const char *const *argv);
void libvlc_release(libvlc_instance_t *);
libvlc_media_t *libvlc_media_new_path(libvlc_instance_t *, const char *);
void libvlc_media_release(libvlc_media_t *);
void libvlc_media_add_option(libvlc_media_t *, const char *);
libvlc_media_player_t *libvlc_media_player_new_from_media(libvlc_media_t *);
void libvlc_media_player_release(libvlc_media_player_t *);
int  libvlc_media_player_play(libvlc_media_player_t *);
void libvlc_media_player_stop(libvlc_media_player_t *);
void libvlc_media_player_set_pause(libvlc_media_player_t *, int);
libvlc_state_t libvlc_media_player_get_state(libvlc_media_player_t *);
libvlc_event_manager_t *libvlc_media_player_event_manager(libvlc_media_player_t *);
int  libvlc_event_attach(libvlc_event_manager_t *, libvlc_event_type_t, libvlc_callback_t, void *);
void libvlc_video_set_callbacks(libvlc_media_player_t *, libvlc_video_lock_cb, libvlc_video_unlock_cb, libvlc_video_display_cb, void *);
void libvlc_video_set_format(libvlc_media_player_t *, const char *, unsigned, unsigned, unsigned);
void libvlc_video_set_format_callbacks(libvlc_media_player_t *, libvlc_video_format_cb, libvlc_video_cleanup_cb);
void libvlc_audio_set_volume(libvlc_media_player_t *, int);
int  libvlc_audio_get_volume(libvlc_media_player_t *);

#ifdef __cplusplus
}
#endif
#endif
