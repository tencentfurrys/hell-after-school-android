#ifndef IMGUI_STUB_ANDROID_H
#define IMGUI_STUB_ANDROID_H
// Minimal ImGui stub for Android. Debug GUI (DebugManager) compiles but doesn't render.
#include <string>
#include <cstddef>
#include <cstdint>

struct ImVec2 {
    float x, y;
    ImVec2() : x(0), y(0) {}
    ImVec2(float _x, float _y) : x(_x), y(_y) {}
};
struct ImVec4 {
    float x, y, z, w;
    ImVec4() : x(0), y(0), z(0), w(0) {}
    ImVec4(float _x, float _y, float _z, float _w) : x(_x), y(_y), z(_z), w(_w) {}
};

typedef int ImGuiWindowFlags;
typedef int ImGuiCol;
typedef int ImGuiStyleVar;
typedef int ImGuiSetCond;
typedef int ImGuiTreeNodeFlags;
typedef int ImGuiSelectableFlags;
typedef int ImGuiInputTextFlags;
typedef int ImGuiComboFlags;
typedef int ImGuiColorEditFlags;

enum {
    ImGuiWindowFlags_HorizontalScrollbar = 1,
    ImGuiWindowFlags_AlwaysAutoResize = 2,
    ImGuiWindowFlags_NoResize = 4,
    ImGuiWindowFlags_NoTitleBar = 8,
    ImGuiWindowFlags_NoMove = 16,
    ImGuiWindowFlags_NoScrollbar = 32,
    ImGuiWindowFlags_NoCollapse = 64,
    ImGuiWindowFlags_NoSavedSettings = 128,
    ImGuiWindowFlags_ShowBorders = 256,
    ImGuiWindowFlags_NoBringToFrontOnFocus = 512,
    ImGuiWindowFlags_MenuBar = 1024,
    ImGuiSetCond_Appearing = 1,
    ImGuiSetCond_Always = 2,
    ImGuiSetCond_Once = 4,
    ImGuiSetCond_FirstUseEver = 8,
    ImGuiTreeNodeFlags_DefaultOpen = 1,
    ImGuiTreeNodeFlags_OpenOnArrow = 2,
    ImGuiTreeNodeFlags_Leaf = 4,
    ImGuiTreeNodeFlags_Selected = 8,
    ImGuiSelectableFlags_DontClosePopups = 1,
    ImGuiSelectableFlags_SpanAllColumns = 2,
    ImGuiInputTextFlags_CharsDecimal = 1,
    ImGuiInputTextFlags_CharsHexadecimal = 2,
    ImGuiInputTextFlags_CharsNoBlank = 4,
    ImGuiInputTextFlags_AutoSelectAll = 8,
    ImGuiInputTextFlags_EnterReturnsTrue = 16,
    ImGuiInputTextFlags_AlwaysInsertMode = 32,
    ImGuiInputTextFlags_ReadOnly = 64,
    ImGuiCol_Text = 0, ImGuiCol_Border = 1, ImGuiCol_FrameBg = 2,
    ImGuiCol_WindowBg = 3, ImGuiCol_Button = 4, ImGuiCol_ButtonHovered = 5,
    ImGuiCol_ButtonActive = 6, ImGuiCol_Header = 7, ImGuiCol_HeaderHovered = 8,
    ImGuiCol_HeaderActive = 9, ImGuiCol_TitleBg = 10, ImGuiCol_TitleBgActive = 11,
    ImGuiCol_TitleBgCollapsed = 12, ImGuiCol_MenuBarBg = 13, ImGuiCol_ScrollbarBg = 14,
    ImGuiCol_ScrollbarGrab = 15, ImGuiCol_ScrollbarGrabHovered = 16, ImGuiCol_ScrollbarGrabActive = 17,
    ImGuiCol_CheckMark = 18, ImGuiCol_SliderGrab = 19, ImGuiCol_SliderGrabActive = 20,
    ImGuiCol_ChildWindowBg = 21,
    ImGuiCol_PopupBg = 22, ImGuiCol_Separator = 23,
    ImGuiCol_BorderShadow = 24, ImGuiCol_TextDisabled = 25,
    ImGuiCol_ResizeGrip = 26, ImGuiCol_ResizeGripHovered = 27, ImGuiCol_ResizeGripActive = 28,
    ImGuiCol_PlotLines = 29, ImGuiCol_PlotLinesHovered = 30,
    ImGuiCol_PlotHistogram = 31, ImGuiCol_PlotHistogramHovered = 32,
    ImGuiCol_TextSelectedBg = 33, ImGuiCol_ModalWindowDarkening = 34,
    ImGuiCol_COUNT = 35,
};

typedef void* ImTextureID;
typedef unsigned int ImU32;
typedef int ImGuiKey;
struct ImFont;
typedef unsigned short ImWchar;
struct ImFontConfig {
    int OversampleH, OversampleV;
    bool MergeMode;
    ImWchar* GlyphRanges;
    float GlyphExtraSpacing;
    bool PixelSnapH;
    ImFontConfig() : OversampleH(0), OversampleV(0), MergeMode(false), GlyphRanges(nullptr), GlyphExtraSpacing(0), PixelSnapH(false) {}
};
struct ImFontAtlas {
    ImFont* AddFontFromFileTTF(const char*, float, const ImFontConfig* =nullptr, const ImWchar* =nullptr) { return nullptr; }
    ImFont* AddFontDefault(const ImFontConfig* =nullptr) { return nullptr; }
    void GetTexDataAsRGBA32(unsigned char**, int*, int*, int* =nullptr) {}
    const ImWchar* GetGlyphRangesDefault() { return nullptr; }
    const ImWchar* GetGlyphRangesJapanese() { return nullptr; }
    const ImWchar* GetGlyphRangesChinese() { return nullptr; }
    const ImWchar* GetGlyphRangesChineseFull() { return nullptr; }
    const ImWchar* GetGlyphRangesKorean() { return nullptr; }
    const ImWchar* GetGlyphRangesCyrillic() { return nullptr; }
    bool Build() { return true; }
    void Clear() {}
};
struct ImGuiIO {
    ImVec2 DisplaySize; float DeltaTime; bool WantCaptureMouse; bool WantCaptureKeyboard; bool WantTextInput;
    ImFontAtlas* Fonts;
    ImGuiIO() : DeltaTime(0), WantCaptureMouse(false), WantCaptureKeyboard(false), WantTextInput(false), Fonts(nullptr) {}
};
struct ImGuiStyle {
    ImVec4 Colors[35];
    float Alpha;
    float WindowFillAlphaDefault;
    float WindowRounding;
    float FrameRounding;
    ImVec2 ItemSpacing;
    ImVec2 ItemInnerSpacing;
    ImVec2 WindowPadding;
    ImGuiStyle() : Alpha(1), WindowFillAlphaDefault(1), WindowRounding(0), FrameRounding(0) {}
};
enum {
    ImGuiStyleVar_Alpha = 100,
    ImGuiStyleVar_WindowPadding = 101,
    ImGuiStyleVar_WindowRounding = 102,
    ImGuiStyleVar_FrameRounding = 103,
    ImGuiStyleVar_ItemSpacing = 104,
    ImGuiStyleVar_ItemInnerSpacing = 105,
    ImGuiStyleVar_FramePadding = 106,
    ImGuiStyleVar_IndentSpacing = 107,
};
struct ImDrawList;

namespace ImGui {
    inline bool Begin(const char*, bool* =nullptr, ImGuiWindowFlags=0) { return false; }
    inline bool Begin(const char*, bool*, const ImVec2&, float, ImGuiWindowFlags) { return false; }
    inline void End() {}
    inline bool BeginChild(const char*, const ImVec2& =ImVec2(0,0), bool=false, ImGuiWindowFlags=0) { return false; }
    inline bool BeginChild(unsigned int, const ImVec2& =ImVec2(0,0), bool=false, ImGuiWindowFlags=0) { return false; }
    inline void EndChild() {}
    inline bool Button(const char*, const ImVec2& =ImVec2(0,0)) { return false; }
    inline bool SmallButton(const char*) { return false; }
    inline void SameLine(float=0, float=-1) {}
    inline void NewLine() {}
    inline void Separator() {}
    inline void Spacing() {}
    inline void Text(const char*, ...) {}
    inline void TextUnformatted(const char*, const char* =nullptr) {}
    inline void TextColored(const ImVec4&, const char*, ...) {}
    inline void TextDisabled(const char*, ...) {}
    inline void TextWrapped(const char*, ...) {}
    inline void LabelText(const char*, const char*, ...) {}
    inline void BulletText(const char*, ...) {}
    inline bool Checkbox(const char*, bool*) { return false; }
    inline bool CheckboxFlags(const char*, unsigned int*, unsigned int) { return false; }
    inline bool RadioButton(const char*, bool) { return false; }
    inline bool RadioButton(const char*, int*, int) { return false; }
    inline bool InputText(const char*, char*, size_t, ImGuiInputTextFlags=0, int(*)(void*)=nullptr, void* =nullptr) { return false; }
    inline bool InputTextMultiline(const char*, char*, size_t, const ImVec2& =ImVec2(0,0), ImGuiInputTextFlags=0, int(*)(void*)=nullptr, void* =nullptr) { return false; }
    inline bool InputFloat(const char*, float*, float=0, float=0, int=-1, ImGuiInputTextFlags=0) { return false; }
    inline bool InputInt(const char*, int*, int=1, int=100, ImGuiInputTextFlags=0) { return false; }
    inline bool SliderFloat(const char*, float*, float, float, const char* ="%.3f", float=1.0f) { return false; }
    inline bool SliderInt(const char*, int*, int, int, const char* ="%d") { return false; }
    inline bool DragFloat(const char*, float*, float=1.0f, float=0, float=0, const char* ="%.3f", float=1.0f) { return false; }
    inline bool DragInt(const char*, int*, float=1.0f, int=0, int=0, const char* ="%d") { return false; }
    inline bool ColorEdit3(const char*, float[3]) { return false; }
    inline bool ColorEdit4(const char*, float[4], bool=true) { return false; }
    inline bool Combo(const char*, int*, const char* const[], int, int=-1) { return false; }
    inline bool Combo(const char*, int*, const char*, int=-1) { return false; }
    inline bool BeginCombo(const char*, const char*, ImGuiComboFlags=0) { return false; }
    inline void EndCombo() {}
    inline bool Selectable(const char*, bool=false, ImGuiSelectableFlags=0, const ImVec2& =ImVec2(0,0)) { return false; }
    inline bool Selectable(const char*, bool*, ImGuiSelectableFlags=0, const ImVec2& =ImVec2(0,0)) { return false; }
    inline bool MenuItem(const char*, const char* =nullptr, bool=false, bool=true) { return false; }
    inline bool MenuItem(const char*, const char*, bool*, bool=true) { return false; }
    inline bool BeginMenu(const char*, bool=true) { return false; }
    inline void EndMenu() {}
    inline bool BeginMenuBar() { return false; }
    inline void EndMenuBar() {}
    inline bool BeginMainMenuBar() { return false; }
    inline void EndMainMenuBar() {}
    inline bool BeginPopup(const char*) { return false; }
    inline bool BeginPopupModal(const char*, bool* =nullptr, ImGuiWindowFlags=0) { return false; }
    inline void EndPopup() {}
    inline void OpenPopup(const char*) {}
    inline void CloseCurrentPopup() {}
    inline bool TreeNode(const char*) { return false; }
    inline bool TreeNode(const char*, const char*, ...) { return false; }
    inline bool TreeNodeEx(const char*, ImGuiTreeNodeFlags=0) { return false; }
    inline bool TreeNodeEx(const char*, ImGuiTreeNodeFlags, const char*, ...) { return false; }
    inline void TreePop() {}
    inline void SetNextWindowPos(const ImVec2&, ImGuiSetCond=0) {}
    inline void SetNextWindowSize(const ImVec2&, ImGuiSetCond=0) {}
    inline void SetNextWindowContentSize(const ImVec2&) {}
    inline void SetWindowFontScale(float) {}
    inline ImVec2 GetWindowSize() { return ImVec2(0,0); }
    inline ImVec2 GetWindowPos() { return ImVec2(0,0); }
    inline ImVec2 GetCursorScreenPos() { return ImVec2(0,0); }
    inline ImVec2 GetCursorPos() { return ImVec2(0,0); }
    inline void SetCursorPos(const ImVec2&) {}
    inline void SetCursorPosX(float) {}
    inline void SetCursorPosY(float) {}
    inline float GetCursorPosX() { return 0; }
    inline float GetCursorPosY() { return 0; }
    inline void PushItemWidth(float) {}
    inline void PopItemWidth() {}
    inline float CalcItemWidth() { return 0; }
    inline void PushTextWrapPos(float=0) {}
    inline void PopTextWrapPos() {}
    inline void PushID(const char*) {}
    inline void PushID(int) {}
    inline void PushID(const void*) {}
    inline void PopID() {}
    inline unsigned int GetID(const char*) { return 0; }
    inline void Indent(float=0) {}
    inline void Unindent(float=0) {}
    inline void Columns(int=1, const char* =nullptr, bool=true) {}
    inline void NextColumn() {}
    inline int GetColumnIndex() { return 0; }
    inline float GetColumnOffset(int=-1) { return 0; }
    inline void SetColumnOffset(int, float) {}
    inline float GetColumnWidth(int=-1) { return 0; }
    inline int GetColumnsCount() { return 0; }
    inline bool IsItemActive() { return false; }
    inline bool IsItemHovered() { return false; }
    inline bool IsItemClicked(int=0) { return false; }
    inline bool IsItemVisible() { return false; }
    inline bool IsWindowFocused() { return false; }
    inline bool IsWindowHovered() { return false; }
    inline bool IsMouseClicked(int, bool=false) { return false; }
    inline bool IsMouseDown(int) { return false; }
    inline bool IsKeyPressed(int, bool=true) { return false; }
    inline bool IsKeyDown(int) { return false; }
    inline ImVec2 GetItemRectMin() { return ImVec2(0,0); }
    inline ImVec2 GetItemRectMax() { return ImVec2(0,0); }
    inline ImVec2 GetItemRectSize() { return ImVec2(0,0); }
    inline float GetFrameHeight() { return 0; }
    inline float GetTextLineHeight() { return 0; }
    inline float GetTextLineHeightWithSpacing() { return 0; }
    inline float GetScrollY() { return 0; }
    inline float GetScrollMaxY() { return 0; }
    inline void SetScrollY(float) {}
    inline void SetScrollHere(float=0.5f) {}
    inline void SetScrollFromPosY(float, float=0.5f) {}
    inline void PushStyleColor(ImGuiCol, const ImVec4&) {}
    inline void PushStyleColor(ImGuiCol, ImU32) {}
    inline void PopStyleColor(int=1) {}
    inline void PushStyleVar(ImGuiStyleVar, float) {}
    inline void PushStyleVar(ImGuiStyleVar, const ImVec2&) {}
    inline void PopStyleVar(int=1) {}
    inline ImGuiStyle& GetStyle() { static ImGuiStyle s = {}; return s; }
    inline ImGuiIO& GetIO() { static ImGuiIO io = {}; return io; }
    inline ImDrawList* GetWindowDrawList() { return nullptr; }
    inline void SetWindowFocus() {}
    inline void SetWindowFocus(const char*) {}
    inline bool IsAnyItemActive() { return false; }
    inline void Image(ImTextureID, const ImVec2&, const ImVec2& =ImVec2(0,0), const ImVec2& =ImVec2(1,1), const ImVec4& =ImVec4(1,1,1,1), const ImVec4& =ImVec4(0,0,0,0)) {}
    inline bool ImageButton(ImTextureID, const ImVec2&, const ImVec2& =ImVec2(0,0), const ImVec2& =ImVec2(1,1), int=-1, const ImVec4& =ImVec4(0,0,0,0), const ImVec4& =ImVec4(1,1,1,1)) { return false; }
    inline void ProgressBar(float, const ImVec2& =ImVec2(-1,0), const char* =nullptr) {}
    inline bool CollapsingHeader(const char*, ImGuiTreeNodeFlags=0) { return false; }
    inline bool CollapsingHeader(const char*, bool*, ImGuiTreeNodeFlags=0) { return false; }
    inline void BeginTooltip() {}
    inline void EndTooltip() {}
    inline void SetTooltip(const char*, ...) {}
    inline ImU32 GetColorU32(ImGuiCol, float=1.0f) { return 0; }
    inline ImU32 GetColorU32(const ImVec4&) { return 0; }
    inline bool IsItemDeactivatedAfterEdit() { return false; }
    inline bool ListBox(const char*, int*, const char* const[], int, int=-1) { return false; }
    inline bool ListBoxHeader(const char*, int, int=-1) { return false; }
    inline bool ListBoxHeader(const char*, const ImVec2& =ImVec2(0,0)) { return false; }
    inline void ListBoxFooter() {}
    inline void Bullet() {}
    inline void Dummy(const ImVec2&) {}
    inline ImVec2 GetMousePos() { return ImVec2(0,0); }
    inline void BeginGroup() {}
    inline void EndGroup() {}
    inline bool InputDouble(const char*, double*, double=0, double=0, const char* ="%.6f", ImGuiInputTextFlags=0) { return false; }
    inline bool InputDouble(const char*, double*, double, double, int) { return false; }
    inline void ForcedClosePopup() {}
    inline ImVec2 GetContentRegionAvail() { return ImVec2(0,0); }
    inline ImVec2 GetContentRegionMax() { return ImVec2(0,0); }
    inline float GetContentRegionAvailWidth() { return 0; }
    inline float GetWindowContentRegionWidth() { return 0; }
}
static const ImWchar* glyphRangesJapanese = nullptr;
#endif
