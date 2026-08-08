package org.cocos2dx.cpp;

import android.graphics.SurfaceTexture;
import android.media.MediaPlayer;
import android.view.Surface;
import android.util.Log;
import java.util.concurrent.ConcurrentHashMap;

// [Android MP4 cutscene] Decodes a cutscene MP4 with MediaPlayer into a
// SurfaceTexture-backed OES texture that VideoSprite samples on the GL thread.
public class HASVideoDecoder {
	private static final String TAG = "HAS_Video";
	private static final ConcurrentHashMap<Integer, Holder> sMap = new ConcurrentHashMap<Integer, Holder>();
	private static int sNext = 1;

	static class Holder {
		SurfaceTexture st;
		Surface surface;
		MediaPlayer mp;
		boolean prepared = false;
		boolean ended = false;
		boolean shouldPlay = false;
		boolean loop = false;
		float pendingVol = 1.0f;
	}

	public static synchronized int nativeCreate(String path, int oesTexId, boolean loop) {
		try {
			final Holder h = new Holder();
			h.loop = loop;
			h.st = new SurfaceTexture(oesTexId);
			h.surface = new Surface(h.st);
			h.mp = new MediaPlayer();
			h.mp.setSurface(h.surface);
			h.mp.setDataSource(path);
			h.mp.setLooping(loop);
			h.mp.setOnPreparedListener(new MediaPlayer.OnPreparedListener() {
				public void onPrepared(MediaPlayer m) {
					h.prepared = true;
					try { m.setVolume(h.pendingVol, h.pendingVol); } catch (Throwable t) {}
					if (h.shouldPlay) { try { m.start(); } catch (Throwable t) {} }
				}
			});
			h.mp.setOnCompletionListener(new MediaPlayer.OnCompletionListener() {
				public void onCompletion(MediaPlayer m) { if (!h.loop) h.ended = true; }
			});
			h.mp.setOnErrorListener(new MediaPlayer.OnErrorListener() {
				public boolean onError(MediaPlayer m, int a, int b) {
					Log.e(TAG, "MediaPlayer error " + a + "/" + b);
					h.ended = true;
					return true;
				}
			});
			h.mp.prepareAsync();
			int id = sNext++;
			sMap.put(Integer.valueOf(id), h);
			Log.i(TAG, "created " + id + " path=" + path + " tex=" + oesTexId + " loop=" + loop);
			return id;
		} catch (Throwable t) {
			Log.e(TAG, "nativeCreate failed", t);
			return -1;
		}
	}

	public static void nativePlay(int id, float vol) {
		Holder h = get(id); if (h == null) return;
		h.pendingVol = clamp(vol);
		h.shouldPlay = true;
		h.ended = false;
		try { if (h.prepared) { h.mp.setVolume(h.pendingVol, h.pendingVol); h.mp.start(); } } catch (Throwable t) {}
	}

	public static void nativePause(int id) {
		Holder h = get(id); if (h == null) return;
		h.shouldPlay = false;
		try { if (h.prepared && h.mp.isPlaying()) h.mp.pause(); } catch (Throwable t) {}
	}

	public static void nativeResume(int id) {
		Holder h = get(id); if (h == null) return;
		h.shouldPlay = true;
		try { if (h.prepared) h.mp.start(); } catch (Throwable t) {}
	}

	public static void nativeStop(int id) {
		Holder h = get(id); if (h == null) return;
		h.shouldPlay = false;
		h.ended = true;
		try { if (h.prepared) h.mp.pause(); } catch (Throwable t) {}
	}

	public static void nativeSetVolume(int id, float vol) {
		Holder h = get(id); if (h == null) return;
		h.pendingVol = clamp(vol);
		try { if (h.prepared) h.mp.setVolume(h.pendingVol, h.pendingVol); } catch (Throwable t) {}
	}

	public static boolean nativeIsEnd(int id) {
		Holder h = get(id);
		return h == null ? true : h.ended;
	}

	// GL thread: pull latest frame into the OES texture, return transform matrix (float[16]) or null.
	public static float[] nativeUpdateTexImage(int id) {
		Holder h = get(id);
		if (h == null || h.st == null) return null;
		try {
			h.st.updateTexImage();
			float[] m = new float[16];
			h.st.getTransformMatrix(m);
			return m;
		} catch (Throwable t) {
			return null;
		}
	}

	public static void nativeRelease(int id) {
		Holder h = sMap.remove(Integer.valueOf(id));
		if (h == null) return;
		try { if (h.mp \!= null) { h.mp.setOnPreparedListener(null); h.mp.reset(); h.mp.release(); } } catch (Throwable t) {}
		try { if (h.surface \!= null) h.surface.release(); } catch (Throwable t) {}
		try { if (h.st \!= null) h.st.release(); } catch (Throwable t) {}
	}

	private static Holder get(int id) { return sMap.get(Integer.valueOf(id)); }
	private static float clamp(float v) { return v < 0.0f ? 0.0f : (v > 1.0f ? 1.0f : v); }
}
