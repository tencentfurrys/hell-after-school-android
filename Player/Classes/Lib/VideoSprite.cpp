#include "VideoSprite.h"
#include "renderer/ccGLStateCache.h"
#include "AudioEngine.h"
#include "Manager/AudioManager.h"
#if CC_TARGET_PLATFORM == CC_PLATFORM_ANDROID
#include "platform/android/jni/JniHelper.h"
#include "platform/CCFileUtils.h"
#include <jni.h>
#include <vector>
#include <cstdio>
#ifndef GL_TEXTURE_EXTERNAL_OES
#define GL_TEXTURE_EXTERNAL_OES 0x8D65
#endif
#endif

USING_NS_CC;
using namespace experimental;

NS_AGTK_BEGIN
#if CC_TARGET_PLATFORM == CC_PLATFORM_ANDROID
static const char* kHASVideoClass = "org/cocos2dx/cpp/HASVideoDecoder";
#endif

/**
 * @class VideoSprite
 */
VideoSprite::VideoSprite() : cocos2d::Sprite()
{
	_vlc = nullptr;
	_vlcPlayer = nullptr;
	_filename = nullptr;
	_buffer = nullptr;
	_texWidth = 0;
	_texHeight = 0;
	_endReached = false;
	_state = kStateIdle;
	_volume = nullptr;
	_pause = false;
#if CC_TARGET_PLATFORM == CC_PLATFORM_ANDROID
	_androidHandle = -1;
	_oesTexture = 0;
	_oesFbo = 0;
	_oesProgram = 0;
	_oesAttrPos = _oesAttrTex = _oesUniTexMat = _oesUniSampler = -1;
	for (int i = 0; i < 16; i++) _oesTexMatrix[i] = (i % 5 == 0) ? 1.0f : 0.0f;
#endif
}

VideoSprite::~VideoSprite()
{
#if CC_TARGET_PLATFORM == CC_PLATFORM_ANDROID
	if (_androidHandle >= 0) {
		cocos2d::JniHelper::callStaticVoidMethod(kHASVideoClass, "nativeRelease", _androidHandle);
		_androidHandle = -1;
	}
	if (_oesFbo) { glDeleteFramebuffers(1, &_oesFbo); _oesFbo = 0; }
	if (_oesTexture) { glDeleteTextures(1, &_oesTexture); _oesTexture = 0; }
	if (_oesProgram) { glDeleteProgram(_oesProgram); _oesProgram = 0; }
#endif
	CC_SAFE_RELEASE_NULL(_filename);
	if (_vlcPlayer) {
		libvlc_media_player_stop(_vlcPlayer);
		libvlc_media_player_release(_vlcPlayer);
	}
	if (_vlc) {
		libvlc_release(_vlc);
	}
	if (_buffer) {
		free(_buffer);
	}
	CC_SAFE_RELEASE_NULL(_volume);
}

VideoSprite *VideoSprite::createWithFilename(std::string filename, cocos2d::Size size, bool bLoop)
{
	auto p = new (std::nothrow) VideoSprite();
	if (p && p->initWithFilename(filename, size, bLoop)) {
		p->autorelease();
		return p;
	}
	CC_SAFE_DELETE(p);
	return nullptr;
}

bool VideoSprite::initWithFilename(std::string filename, cocos2d::Size size, bool bLoop)
{
#if CC_TARGET_PLATFORM == CC_PLATFORM_ANDROID
	// --- Android: decode the real MP4 via MediaPlayer + SurfaceTexture (OES) ---
	if (size.width == 0 && size.height == 0) {
		size = cocos2d::Director::getInstance()->getWinSize();
	}
	unsigned int width = (unsigned int)size.width;
	unsigned int height = (unsigned int)size.height;
	unsigned int length = width * height * 4;
	_buffer = (unsigned char *)malloc(length);
	CC_ASSERT(_buffer);
	memset(_buffer, 0, length);
	cocos2d::Texture2D *texture = new cocos2d::Texture2D();
	texture->initWithData(_buffer, length, cocos2d::Texture2D::PixelFormat::RGBA8888, width, height, size);
	if (!initWithTexture(texture)) {
		return false;
	}
	this->setTexWidth(width);
	this->setTexHeight(height);
	this->setFilename(cocos2d::__String::create(filename));
	_volume = agtk::ValueTimer<float>::create(0.0f);
	CC_SAFE_RETAIN(_volume);
	setupOESAndroid();
	std::string realPath = resolveMovieToCacheAndroid(filename);
	_androidHandle = cocos2d::JniHelper::callStaticIntMethod(kHASVideoClass, "nativeCreate", realPath, (int)_oesTexture, bLoop);
	CCLOG("[HAS video] nativeCreate tex=%u -> handle %d", _oesTexture, _androidHandle);
	return true;
#else
	_vlc = libvlc_new(0, NULL);
// #AGTK-NX
#if (CC_TARGET_PLATFORM == CC_PLATFORM_NX)
#else
	{
		std::string from = "/";
		std::string to = "\\";
		std::string::size_type pos = filename.find(from);
		while (pos != std::string::npos) {
			filename.replace(pos, from.size(), to);
			pos = filename.find(from, pos + to.size());
		}
	}
#endif
	//
	libvlc_media_t *media = libvlc_media_new_path(_vlc, filename.c_str());
	if (media == nullptr) {
		CC_ASSERT(0);
		return false;
	}
	_vlcPlayer = libvlc_media_player_new_from_media(media);
	if (bLoop) {//ループ有り。
		libvlc_media_add_option(media, "input-repeat=-1");
	}
	libvlc_media_release(media);

	libvlc_video_set_callbacks(_vlcPlayer, VideoSprite::lock, VideoSprite::unlock, VideoSprite::display, this);
	libvlc_event_attach(
		libvlc_media_player_event_manager(_vlcPlayer),
		libvlc_MediaPlayerEndReached,
		endReached,
		(void *)this);

	if (size.width == 0 && size.height == 0) {
		size = cocos2d::Director::getInstance()->getWinSize();
	}
	unsigned int width = size.width;
	unsigned int height = size.height;
	unsigned int length = width * height * 4;
	_buffer = (unsigned char *)malloc(length);
	CC_ASSERT(_buffer);
	memset(_buffer, 0, length);
	cocos2d::Texture2D *texture = new cocos2d::Texture2D();
	texture->initWithData(_buffer, length, cocos2d::Texture2D::PixelFormat::RGBA8888, width, height, size);
	if (!initWithTexture(texture)) {
		return false;
	}
	libvlc_video_set_format(_vlcPlayer, "RGBA", width, height, width << 2);

	this->setTexWidth(width);
	this->setTexHeight(height);
	this->setFilename(cocos2d::__String::create(filename));

	_volume = agtk::ValueTimer<float>::create(0.0f);
	CC_SAFE_RETAIN(_volume);

	//scheduleUpdate();
	return true;
#endif
}

void *VideoSprite::lock(void *data, void **p_pixels)
{
	auto p = static_cast<VideoSprite *>(data);
	*p_pixels = p->_buffer;
	return NULL;
}

void VideoSprite::unlock(void *data, void *id, void *const *p_pixels)
{
	CC_ASSERT(id == NULL);
}

void VideoSprite::display(void *data, void *id)
{
}

void VideoSprite::endReached(const struct libvlc_event_t *event, void *data)
{
	if (libvlc_MediaPlayerEndReached == event->type) {
		auto p = static_cast<VideoSprite *>(data);
		p->_endReached = true;
		p->setState(kStateStop);
		CCLOG("END!");
	}
}

unsigned VideoSprite::videoSetup(void **opaque, char *chroma, unsigned *width, unsigned *height, unsigned *pitches, unsigned *lines)
{
	CC_ASSERT(0);
	auto p = static_cast<VideoSprite *>(*opaque);
	return 0;
}

const char *VideoSprite::getFilename()
{
	CC_ASSERT(_filename);
	return _filename->getCString();
}

void VideoSprite::play(float volume)
{
	_endReached = false;
	this->setState(kStatePlay);
	this->setVolume(volume);
	_pause = false;
#if CC_TARGET_PLATFORM == CC_PLATFORM_ANDROID
	if (_androidHandle >= 0) {
		float v = volume / 100.0f;
		if (v < 0.0f) v = 0.0f;
		if (v > 1.0f) v = 1.0f;
		cocos2d::JniHelper::callStaticVoidMethod(kHASVideoClass, "nativePlay", _androidHandle, v);
	}
#else
	CC_ASSERT(_vlc && _vlcPlayer);
	libvlc_media_player_play(_vlcPlayer);
#endif
}

void VideoSprite::stop()
{
#if CC_TARGET_PLATFORM == CC_PLATFORM_ANDROID
	if (_androidHandle >= 0) cocos2d::JniHelper::callStaticVoidMethod(kHASVideoClass, "nativeStop", _androidHandle);
#else
	CC_ASSERT(_vlcPlayer);
	libvlc_media_player_stop(_vlcPlayer);
#endif
}

void VideoSprite::pause()
{
	_pause = true;
#if CC_TARGET_PLATFORM == CC_PLATFORM_ANDROID
	if (_androidHandle >= 0) cocos2d::JniHelper::callStaticVoidMethod(kHASVideoClass, "nativePause", _androidHandle);
#else
	CC_ASSERT(_vlcPlayer);
	libvlc_media_player_set_pause(_vlcPlayer, true);
#endif
}

void VideoSprite::resume()
{
	_pause = false;
#if CC_TARGET_PLATFORM == CC_PLATFORM_ANDROID
	if (_androidHandle >= 0) cocos2d::JniHelper::callStaticVoidMethod(kHASVideoClass, "nativeResume", _androidHandle);
#else
	CC_ASSERT(_vlcPlayer);
	libvlc_media_player_set_pause(_vlcPlayer, false);
#endif
}

libvlc_state_t VideoSprite::getVlcState()
{
	auto state = libvlc_media_player_get_state(_vlcPlayer);
	CCLOG("%d", state);
	return state;
}

void VideoSprite::draw(cocos2d::Renderer *renderer, const cocos2d::Mat4 &transform, uint32_t flags)
{
	_insideBounds = (flags & FLAGS_TRANSFORM_DIRTY) ? renderer->checkVisibility(transform, _contentSize) : _insideBounds;
	if (_insideBounds) {
#if CC_TARGET_PLATFORM == CC_PLATFORM_ANDROID
		// _texture already holds the current video frame (blitted from the OES
		// SurfaceTexture in update()); do NOT re-upload the CPU buffer here.
#else
		if (_buffer) {
			cocos2d::GL::bindTexture2D(_texture->getName());
			glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, _texWidth, _texHeight, 0, GL_RGBA, GL_UNSIGNED_BYTE, (uint8_t *)_buffer);
		}
		else {
			cocos2d::GL::bindTexture2D((GLuint)0);
		}
#endif
		_trianglesCommand.init(_globalZOrder,
			_texture,
			getGLProgramState(),
			_blendFunc,
			_polyInfo.triangles,
			transform,
			flags);

		renderer->addCommand(&_trianglesCommand);
	}
}

void VideoSprite::update(float dt)
{
	_volume->update(dt);
	auto bgmVolume = AudioManager::getInstance()->getBgmVolume();
#if CC_TARGET_PLATFORM == CC_PLATFORM_ANDROID
	if (_androidHandle >= 0) {
		if (fetchFrameMatrixAndroid(_oesTexMatrix)) {
			blitVideoFrameAndroid();
		}
		float v = (_volume->getValue() * bgmVolume) / 10000.0f;
		if (v < 0.0f) v = 0.0f;
		if (v > 1.0f) v = 1.0f;
		cocos2d::JniHelper::callStaticVoidMethod(kHASVideoClass, "nativeSetVolume", _androidHandle, v);
		if (cocos2d::JniHelper::callStaticBooleanMethod(kHASVideoClass, "nativeIsEnd", _androidHandle)) {
			_endReached = true;
			this->setState(kStateStop);
		}
	}
#else
	libvlc_audio_set_volume(_vlcPlayer, _volume->getValue() * bgmVolume);
#endif
}

void VideoSprite::setVolume(float volume, float seconds)
{
	_volume->start(volume, seconds);
}

float VideoSprite::getVolume()
{
	return _volume->getValue();
}
#if CC_TARGET_PLATFORM == CC_PLATFORM_ANDROID
//----------------------------------------------------------------------------------------------------
// [Android MP4 cutscene] real video decode support (MediaPlayer + SurfaceTexture -> OES)
//----------------------------------------------------------------------------------------------------
static GLuint hasCompileShader(GLenum type, const char *src)
{
	GLuint s = glCreateShader(type);
	glShaderSource(s, 1, &src, nullptr);
	glCompileShader(s);
	GLint ok = 0;
	glGetShaderiv(s, GL_COMPILE_STATUS, &ok);
	if (!ok) {
		char log[1024]; GLsizei n = 0; glGetShaderInfoLog(s, sizeof(log), &n, log);
		CCLOG("[HAS video] shader compile failed: %s", log);
		glDeleteShader(s); return 0;
	}
	return s;
}

void VideoSprite::setupOESAndroid()
{
	glGenTextures(1, &_oesTexture);
	glBindTexture(GL_TEXTURE_EXTERNAL_OES, _oesTexture);
	glTexParameteri(GL_TEXTURE_EXTERNAL_OES, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
	glTexParameteri(GL_TEXTURE_EXTERNAL_OES, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
	glTexParameteri(GL_TEXTURE_EXTERNAL_OES, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
	glTexParameteri(GL_TEXTURE_EXTERNAL_OES, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
	glBindTexture(GL_TEXTURE_EXTERNAL_OES, 0);
	const char *vs =
		"attribute vec2 a_pos;\n"
		"attribute vec2 a_tex;\n"
		"uniform mat4 u_texMat;\n"
		"varying vec2 v_tex;\n"
		"void main(){ gl_Position = vec4(a_pos, 0.0, 1.0); v_tex = (u_texMat * vec4(a_tex, 0.0, 1.0)).xy; }\n";
	const char *fs =
		"#extension GL_OES_EGL_image_external : require\n"
		"precision mediump float;\n"
		"varying vec2 v_tex;\n"
		"uniform samplerExternalOES u_tex;\n"
		"void main(){ gl_FragColor = texture2D(u_tex, v_tex); }\n";
	GLuint v = hasCompileShader(GL_VERTEX_SHADER, vs);
	GLuint f = hasCompileShader(GL_FRAGMENT_SHADER, fs);
	_oesProgram = glCreateProgram();
	glAttachShader(_oesProgram, v);
	glAttachShader(_oesProgram, f);
	glLinkProgram(_oesProgram);
	GLint ok = 0; glGetProgramiv(_oesProgram, GL_LINK_STATUS, &ok);
	if (!ok) { char log[1024]; GLsizei n = 0; glGetProgramInfoLog(_oesProgram, sizeof(log), &n, log); CCLOG("[HAS video] program link failed: %s", log); }
	if (v) glDeleteShader(v);
	if (f) glDeleteShader(f);
	_oesAttrPos    = glGetAttribLocation(_oesProgram, "a_pos");
	_oesAttrTex    = glGetAttribLocation(_oesProgram, "a_tex");
	_oesUniTexMat  = glGetUniformLocation(_oesProgram, "u_texMat");
	_oesUniSampler = glGetUniformLocation(_oesProgram, "u_tex");
	glGenFramebuffers(1, &_oesFbo);
}

bool VideoSprite::fetchFrameMatrixAndroid(float *out16)
{
	cocos2d::JniMethodInfo t;
	if (!cocos2d::JniHelper::getStaticMethodInfo(t, kHASVideoClass, "nativeUpdateTexImage", "(I)[F")) {
		return false;
	}
	jfloatArray arr = (jfloatArray)t.env->CallStaticObjectMethod(t.classID, t.methodID, _androidHandle);
	bool ok = false;
	if (arr) {
		t.env->GetFloatArrayRegion(arr, 0, 16, out16);
		t.env->DeleteLocalRef(arr);
		ok = true;
	}
	t.env->DeleteLocalRef(t.classID);
	return ok;
}

void VideoSprite::blitVideoFrameAndroid()
{
	if (_oesProgram == 0 || _oesFbo == 0) return;
	GLint prevFbo = 0; glGetIntegerv(GL_FRAMEBUFFER_BINDING, &prevFbo);
	GLint prevVp[4]; glGetIntegerv(GL_VIEWPORT, prevVp);
	glBindFramebuffer(GL_FRAMEBUFFER, _oesFbo);
	glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, _texture->getName(), 0);
	glViewport(0, 0, (GLsizei)_texWidth, (GLsizei)_texHeight);
	glDisable(GL_BLEND);
	glDisable(GL_DEPTH_TEST);
	glDisable(GL_SCISSOR_TEST);
	glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
	glClear(GL_COLOR_BUFFER_BIT);
	glUseProgram(_oesProgram);
	// Fullscreen quad; tex V-flipped so the frame lands right-side-up in the
	// cocos2d Texture2D. TODO(build): if cutscene is upside down, remove the V flip.
	static const GLfloat pos[8] = { -1.0f,-1.0f,  1.0f,-1.0f,  -1.0f,1.0f,  1.0f,1.0f };
	static const GLfloat tex[8] = {  0.0f, 1.0f,  1.0f, 1.0f,   0.0f,0.0f,  1.0f,0.0f };
	glEnableVertexAttribArray(_oesAttrPos);
	glVertexAttribPointer(_oesAttrPos, 2, GL_FLOAT, GL_FALSE, 0, pos);
	glEnableVertexAttribArray(_oesAttrTex);
	glVertexAttribPointer(_oesAttrTex, 2, GL_FLOAT, GL_FALSE, 0, tex);
	glUniformMatrix4fv(_oesUniTexMat, 1, GL_FALSE, _oesTexMatrix);
	glActiveTexture(GL_TEXTURE0);
	glBindTexture(GL_TEXTURE_EXTERNAL_OES, _oesTexture);
	glUniform1i(_oesUniSampler, 0);
	glDrawArrays(GL_TRIANGLE_STRIP, 0, 4);
	glBindTexture(GL_TEXTURE_EXTERNAL_OES, 0);
	glDisableVertexAttribArray(_oesAttrPos);
	glDisableVertexAttribArray(_oesAttrTex);
	glBindFramebuffer(GL_FRAMEBUFFER, (GLuint)prevFbo);
	glViewport(prevVp[0], prevVp[1], prevVp[2], prevVp[3]);
	cocos2d::GL::useProgram(0);
	cocos2d::GL::bindTexture2D(0);
}

std::string VideoSprite::resolveMovieToCacheAndroid(const std::string &filename)
{
	auto fu = cocos2d::FileUtils::getInstance();
	std::string base = filename;
	size_t sp = base.find_last_of('/');
	if (sp != std::string::npos) base = base.substr(sp + 1);
	std::vector<std::string> cands;
	cands.push_back(filename);
	cands.push_back("Resources/" + filename);
	cands.push_back("movies/" + base);
	cands.push_back("Resources/movies/" + base);
	cocos2d::Data data;
	for (auto &cnd : cands) {
		std::string fp = fu->fullPathForFilename(cnd);
		if (!fp.empty()) {
			data = fu->getDataFromFile(fp);
			if (!data.isNull()) { CCLOG("[HAS video] movie resolved via %s", cnd.c_str()); break; }
		}
	}
	if (data.isNull()) data = fu->getDataFromFile(filename);
	std::string dir = fu->getWritablePath() + "movie_cache/";
	if (!fu->isDirectoryExist(dir)) fu->createDirectory(dir);
	std::string outPath = dir + base;
	if (!data.isNull()) {
		FILE *fp = fopen(fu->getSuitableFOpen(outPath).c_str(), "wb");
		if (fp) { fwrite(data.getBytes(), 1, data.getSize(), fp); fclose(fp); }
		else CCLOG("[HAS video] failed to write cache: %s", outPath.c_str());
	} else {
		CCLOG("[HAS video] WARNING could not read movie asset %s", filename.c_str());
	}
	return outPath;
}
#endif


// #AGTK-NX
#if (CC_TARGET_PLATFORM == CC_PLATFORM_NX)
#endif
NS_AGTK_END
