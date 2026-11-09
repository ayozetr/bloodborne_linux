// SPDX-FileCopyrightText: Copyright 2026 bbport contributors
// SPDX-License-Identifier: GPL-2.0-or-later
#include "bbport_overlay.h"
#include "bbport_overlay_internal.h"
#include "bbport_atlas_menu.h"
#include "bbport_atlas_paths.h"
#include "bbport_map.h"
#include "bbport_map_art.h"
#include "shim/bb_env.h"

#include "bbport_toggles.h"

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cfloat>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <filesystem>
#include <fstream>
#include <unordered_map>
#include <mutex>
#include <string>
#include <string_view>
#include <vector>

#include <SDL3/SDL.h>
#include <fmt/format.h>
#include "bbport_guest_hooks.h"
#include "bbport_frame_rate.h"
#include "bbport_settings.h"
#include "imgui.h"
#include "imgui_impl_vulkan.h"
#include "imgui_internal.h" // RegisterUserTexture: the trophy icons
#include "vulkan/instance.h"
#include "render/compile_log.h"
#include "render/scheduler.h"

// DejaVu Sans (Cyrillic), embedded (third_party/fonts, Bitstream Vera license).
#ifdef _WIN32
#define BB_FONT_SECTION ".section .rdata,\"dr\"\n"
#define BB_FONT_HIDDEN(name) ""
#define BB_FONT_END ".text\n"
#else
#define BB_FONT_SECTION ".section .rodata\n"
#define BB_FONT_HIDDEN(name) ".hidden " name "\n"
#define BB_FONT_END ".previous\n"
#endif
asm(BB_FONT_SECTION
    ".balign 16\n"
    BB_FONT_HIDDEN("bb_font_ttf")
    ".global bb_font_ttf\n"
    "bb_font_ttf:\n"
    ".incbin \"" BB_FONT_PATH "\"\n"
    BB_FONT_HIDDEN("bb_font_ttf_end")
    ".global bb_font_ttf_end\n"
    "bb_font_ttf_end:\n"
    BB_FONT_END);
extern "C" const unsigned char bb_font_ttf[];
extern "C" const unsigned char bb_font_ttf_end[];

extern "C" void runtime_restart(void); // bb-probe (probe.c)


extern "C" int runtime_pad_button(const char* input); // bb-probe (runtime_pad/bindings.c)

namespace {
/// The SDL button the game's cross or circle is on (bbport.ini pad.cross / pad.circle: A and B
/// swapped on Nintendo-style controllers), the PS4's place without a binding.
u8 PadButton(const char* input, SDL_GamepadButton fallback) {
    const int button = runtime_pad_button(input);
    return static_cast<u8>(button >= 0 ? button : fallback);
}
} // namespace

namespace BbOverlay {

namespace {

using namespace detail;

std::mutex imgui_mutex; // the ImGui context: window thread (input) and present thread
bool initialized = false;
std::atomic<bool> menu_open{false};
bool l3_down = false, r3_down = false;
// Issue #304: L3+R3 opens the menu only when held (menu_pad_hold_ms, 800 by default), not when both
// sticks are pressed in a fight (lock-on and camera reset); closing is immediate. 0 leaves L3+R3 to
// the game (ayozetr/bloodborne_linux#38: PvP). The hold starts at `l3r3_since` (steady clock ns,
// 0: not held) and is checked at each present (Visible); `open_requested` opens it in Render,
// under the ImGui lock.
long long OpenHoldMs() {
    return BbSettings::Get().menu_pad_hold_ms.load(std::memory_order_relaxed);
}
std::atomic<long long> l3r3_since{0};
std::atomic<bool> open_requested{false};
long long NowNs() {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(
               std::chrono::steady_clock::now().time_since_epoch())
        .count();
}
// The game's text dialog (ImeDialog, the character name), typed on the keyboard: drawn while it
// is open. In fullscreen the window title that showed it is not visible (issues #17, #19).
std::mutex prompt_mutex;
std::atomic<bool> prompt_active{false};
/// A module's line over the game (bbgpu_overlay_banner: BBSC's "joining the host" during its
/// loads, where the game itself shows a black screen).
std::mutex banner_mutex;
std::string banner_text;
std::atomic<bool> banner_active{false};
std::string prompt_title, prompt_text;
// bbport: an on-screen keyboard in the text dialog, for a controller (Steam Deck, the sofa): the
// name could only be typed on a physical keyboard. From SrShadowy/bloodborne_pc. Its state is
// kept under imgui_mutex (HandleEvent, Render); the edits go to the window thread, which owns the
// text (TakeTextEdits), so the render thread never changes the window.
struct OnScreenKeyboard {
    int row = 1, col = 0;
    bool caps = true;
    u64 last_stick_ms = 0;
} osk;
std::vector<TextEdit> text_edits; // under prompt_mutex
constexpr const char* OskKeys[4][2][12] = {
    {{"1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "_"},
     {"1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "_"}},
    {{"Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"}, {"q", "w", "e", "r", "t", "y", "u", "i", "o", "p"}},
    {{"A", "S", "D", "F", "G", "H", "J", "K", "L", "'"}, {"a", "s", "d", "f", "g", "h", "j", "k", "l", "'"}},
    {{"Z", "X", "C", "V", "B", "N", "M", ",", ".", "/"}, {"z", "x", "c", "v", "b", "n", "m", ",", ".", "/"}},
};
// The letters of the menu's language that the English rows lack (the game takes them in a name:
// ñ typed on a physical keyboard worked, not on this one), a row of their own above the actions.
struct OskExtraRow {
    int count;
    const char* keys[2][12];
};
constexpr OskExtraRow OskExtras[] = {
    {0, {}},                                                                      // English
    {0, {}},                                                                      // Russian
    {9, {{"Ñ", "Á", "É", "Í", "Ó", "Ú", "Ü", "¿", "¡"},
         {"ñ", "á", "é", "í", "ó", "ú", "ü", "¿", "¡"}}},                         // Spanish
    {6, {{"À", "È", "É", "Ì", "Ò", "Ù"}, {"à", "è", "é", "ì", "ò", "ù"}}},       // Italian
    {12, {{"À", "Â", "Ç", "É", "È", "Ê", "Ë", "Î", "Ï", "Ô", "Ù", "Û"},
          {"à", "â", "ç", "é", "è", "ê", "ë", "î", "ï", "ô", "ù", "û"}}},          // French
    {4, {{"Ä", "Ö", "Ü", "ß"}, {"ä", "ö", "ü", "ß"}}},                           // German
    {12, {{"Á", "Â", "Ã", "À", "Ç", "É", "Ê", "Í", "Ó", "Ô", "Õ", "Ú"},
          {"á", "â", "ã", "à", "ç", "é", "ê", "í", "ó", "ô", "õ", "ú"}}},         // Portuguese
    {0, {}},                                                                      // Chinese
};
static_assert(std::size(OskExtras) == size_t(BbSettings::MenuLanguage::Count));
enum OskAction { OskCaps, OskSpace, OskBackspace, OskClear, OskConfirm, OskCancel, OskActions };
/// Trophies to announce, oldest first; the front one is on screen (as shadPS4's trophy_ui.cpp:
/// slides in from the right, stays, fades out over the last second).
struct TrophyToast {
    char grade;
    std::string name;
    float elapsed = 0.0f;
    std::filesystem::path icon;
};
// The trophy icons (TROPnnn.PNG, 240x240), decoded once and handed to the Vulkan backend as user
// textures (it uploads them with the font atlas); kept for the session (40 at most). null: none.
std::unordered_map<std::string, ImTextureData*> trophy_icons;
std::mutex trophy_mutex;
std::deque<TrophyToast> trophy_queue;
std::atomic<bool> trophy_active{false};
// bbport (the Linux fork): its own trophy notices take the place of the toast above.
// Trophy notices (bbgpu_trophy_notice): one card at a time in the top-left corner, in the style
// of the PS4's, with the trophy's icon (a cup in its grade's colour when it has none).
struct Notice {
    int id = 0;
    char grade = '-';
    std::string name;
    std::vector<u8> icon; // RGBA
    int icon_size = 0;
};
std::mutex notice_mutex;
std::deque<Notice> notices;
std::atomic<bool> notice_busy{false}; // queued or on screen
bool notice_shown = false;            // the present thread's (imgui_mutex)
Notice notice;
std::chrono::steady_clock::time_point notice_start;
std::unordered_map<int, ImTextureData*> notice_icons; // kept: one per trophy, 64 KiB each
constexpr float NoticeIn = 0.35f, NoticeHold = 5.0f, NoticeOut = 0.6f;
constexpr float TrophySeconds = 6.0f, TrophySlide = 0.4f;

// Present rate for the FPS counter.
std::chrono::steady_clock::time_point last_present{};
float frame_ms_avg = 0.0f;

float PixelDensity(SDL_WindowID id);

// Hunter's Atlas (MikeTat1988): the in-game map, only with BB_ATLAS_ENABLED=1 (the launcher's
// switch). Off, none of its code runs: no files read, no tile, no input routed.
bool AtlasOn() {
    static const bool on = [] {
        const char* env = bb_env("BB_ATLAS_ENABLED");
        return env && env[0] && std::strcmp(env, "0") != 0;
    }();
    return on;
}

/// The size the menu is drawn at (the swapchain's, Draw), for the mouse's position in it.
std::atomic<u32> display_width{0}, display_height{0};

/// A mouse position in the window to the menu's pixels. The swapchain may be another size than the
/// window, which shows it scaled: on Windows a window of 1920x1080 on a 2560x1080 monitor kept the
/// monitor's size, the mouse's x was a quarter short of the drawn menu and clicks missed the
/// checkboxes while rows still lit up (2026-10-27). Without a size yet: the pixel density.
ImVec2 ToDisplay(SDL_WindowID id, float x, float y) {
    SDL_Window* window = SDL_GetWindowFromID(id);
    int w = 0, h = 0;
    const u32 dw = display_width.load(std::memory_order_relaxed), dh = display_height.load(std::memory_order_relaxed);
    if (window && dw && dh && SDL_GetWindowSize(window, &w, &h) && w > 0 && h > 0) {
        return {x * float(dw) / float(w), y * float(dh) / float(h)};
    }
    const float density = PixelDensity(id);
    return {x * density, y * density};
}

void SetOpen(bool value) {
    if (menu_open.exchange(value) == value) {
        return;
    }
    // The system cursor shows over the menu (window.cpp); ImGui learns where it is now, not at
    // the next motion: mouse motion is not passed on while the menu is closed.
    if (value) {
        if (SDL_Window* window = SDL_GetMouseFocus()) {
            float x = 0.0f, y = 0.0f;
            SDL_GetMouseState(&x, &y);
            const ImVec2 at = ToDisplay(SDL_GetWindowID(window), x, y);
            ImGui::GetIO().AddMousePosEvent(at.x, at.y);
        }
    }
    if (!value && dirty) {
        dirty = false;
        BbSettings::Save();
    }
}

ImGuiKey KeyFromSdl(SDL_Keycode key) {
    switch (key) {
    case SDLK_TAB: return ImGuiKey_Tab;
    case SDLK_LEFT: return ImGuiKey_LeftArrow;
    case SDLK_RIGHT: return ImGuiKey_RightArrow;
    case SDLK_UP: return ImGuiKey_UpArrow;
    case SDLK_DOWN: return ImGuiKey_DownArrow;
    case SDLK_PAGEUP: return ImGuiKey_PageUp;
    case SDLK_PAGEDOWN: return ImGuiKey_PageDown;
    case SDLK_HOME: return ImGuiKey_Home;
    case SDLK_END: return ImGuiKey_End;
    case SDLK_DELETE: return ImGuiKey_Delete;
    case SDLK_BACKSPACE: return ImGuiKey_Backspace;
    case SDLK_SPACE: return ImGuiKey_Space;
    case SDLK_RETURN: return ImGuiKey_Enter;
    case SDLK_KP_ENTER: return ImGuiKey_KeypadEnter;
    case SDLK_ESCAPE: return ImGuiKey_Escape;
    case SDLK_LCTRL: return ImGuiKey_LeftCtrl;
    case SDLK_RCTRL: return ImGuiKey_RightCtrl;
    case SDLK_LSHIFT: return ImGuiKey_LeftShift;
    case SDLK_RSHIFT: return ImGuiKey_RightShift;
    case SDLK_LALT: return ImGuiKey_LeftAlt;
    case SDLK_RALT: return ImGuiKey_RightAlt;
    default: return ImGuiKey_None;
    }
}

ImGuiKey KeyFromGamepad(u8 button) {
    // The menu's accept and back follow the game's cross and circle.
    if (button == PadButton("cross", SDL_GAMEPAD_BUTTON_SOUTH)) {
        return ImGuiKey_GamepadFaceDown;
    }
    if (button == PadButton("circle", SDL_GAMEPAD_BUTTON_EAST)) {
        return ImGuiKey_GamepadFaceRight;
    }
    switch (button) {
    case SDL_GAMEPAD_BUTTON_SOUTH: return ImGuiKey_GamepadFaceDown;
    case SDL_GAMEPAD_BUTTON_EAST: return ImGuiKey_GamepadFaceRight;
    case SDL_GAMEPAD_BUTTON_WEST: return ImGuiKey_GamepadFaceLeft;
    case SDL_GAMEPAD_BUTTON_NORTH: return ImGuiKey_GamepadFaceUp;
    case SDL_GAMEPAD_BUTTON_DPAD_UP: return ImGuiKey_GamepadDpadUp;
    case SDL_GAMEPAD_BUTTON_DPAD_DOWN: return ImGuiKey_GamepadDpadDown;
    case SDL_GAMEPAD_BUTTON_DPAD_LEFT: return ImGuiKey_GamepadDpadLeft;
    case SDL_GAMEPAD_BUTTON_DPAD_RIGHT: return ImGuiKey_GamepadDpadRight;
    case SDL_GAMEPAD_BUTTON_LEFT_SHOULDER: return ImGuiKey_GamepadL1;
    case SDL_GAMEPAD_BUTTON_RIGHT_SHOULDER: return ImGuiKey_GamepadR1;
    case SDL_GAMEPAD_BUTTON_START: return ImGuiKey_GamepadStart;
    case SDL_GAMEPAD_BUTTON_BACK: return ImGuiKey_GamepadBack;
    default: return ImGuiKey_None;
    }
}

float PixelDensity(SDL_WindowID id) {
    SDL_Window* window = SDL_GetWindowFromID(id);
    const float density = window ? SDL_GetWindowPixelDensity(window) : 1.0f;
    return density > 0.0f ? density : 1.0f;
}

/// The FPS readout: the frames shown and their interval; with frame generation the multiplier
/// in between ("240 FPS  FG 4x  4.2 ms"), from the generated frames shown per game frame.
std::string FpsText() {
    const auto& s = BbSettings::Get();
    const float shown = frame_ms_avg > 0.0f ? 1000.0f / frame_ms_avg : 0.0f;
    const int generated = s.frame_generation.load(std::memory_order_relaxed) != BbSettings::FrameGenOff
                              ? s.frame_gen_now.load(std::memory_order_relaxed)
                              : 0;
    char text[192];
    if (generated > 0) {
        std::snprintf(text, sizeof(text),
                      BbSettings::MenuText("%.0f FPS  FG %dx  %.1f ms", "%.0f FPS  FG %dx  %.1f мс"),
                      shown, generated + 1, frame_ms_avg);
    } else {
        std::snprintf(text, sizeof(text), BbSettings::MenuText("%.0f FPS  %.1f ms", "%.0f FPS  %.1f мс"),
                      shown, frame_ms_avg);
    }
    // Other programs took video memory from the game (BufferCache::VramPromotionsPaused): how much
    // less the budget is than the most it was this session. It read "VRAM -552 MB", which looked
    // like a negative figure.
    if (const u32 lost = BbStats::vram_budget_lost_mb.load(std::memory_order_relaxed); lost >= 150) {
        const size_t used = std::strlen(text);
        std::snprintf(text + used, sizeof(text) - used,
                      BbSettings::MenuText("  VRAM: %u MB taken by other apps", "  VRAM: %u МБ заняты другими программами"),
                      lost);
    }
    return text;
}

// bbport: the menu's own font has no Chinese characters. The first time the menu opens or speaks
// Simplified Chinese, a system font for it is merged into that font: BB_CJK_FONT (a file), else
// fontconfig's choice for zh-cn (Noto Sans CJK, WenQuanYi...). ImGui 1.92 rasterizes glyphs as
// they are drawn, so the font costs memory for its file, not a texture of every character.
// Without such a font the Chinese texts show as boxes, and the log says why.
void LoadCjkFont() {
    std::string path;
    int index = 0;
    if (const char* file = bb_env("BB_CJK_FONT"); file && *file) {
        path = file;
    } else if (FILE* pipe = popen("fc-match -f '%{file}|%{index}|%{lang}' 'sans-serif:lang=zh-cn' "
                                  "2>/dev/null",
                                  "r")) {
        std::string out;
        char buffer[4096];
        for (size_t n; (n = std::fread(buffer, 1, sizeof(buffer), pipe)) > 0;) {
            out.append(buffer, n);
        }
        pclose(pipe);
        // file|index|lang|lang|...: fontconfig answers with some font even when none has
        // Chinese, so its languages must list zh-cn.
        const size_t first = out.find('|');
        const size_t second = first == std::string::npos ? first : out.find('|', first + 1);
        if (second != std::string::npos && (out + "|").find("|zh-cn|", second) != std::string::npos) {
            path = out.substr(0, first);
            index = std::atoi(out.c_str() + first + 1);
        }
    }
    if (path.empty()) {
        std::printf("Overlay: no font with Chinese characters found (install Noto Sans CJK or "
                    "WenQuanYi, or set BB_CJK_FONT to a font file)\n");
        return;
    }
    ImGuiIO& io = ImGui::GetIO();
    ImFontConfig config;
    config.MergeMode = true;
    config.FontNo = index;
    config.DstFont = io.Fonts->Fonts[0];
    if (io.Fonts->AddFontFromFileTTF(path.c_str(), 18.0f, &config)) {
        std::printf("Overlay: Chinese characters from %s\n", path.c_str());
    } else {
        std::printf("Overlay: could not load the font %s\n", path.c_str());
    }
}

} // namespace

namespace detail {

/// BB_OVERLAY_TRACE=1 (diagnostics): the menu's mouse buttons as SDL gives them and as ImGui
/// takes them (Windows: items highlight but clicks do not change them).
bool OverlayTrace() {
    static const bool on = bb_env_on("BB_OVERLAY_TRACE");
    return on;
}

void Checkbox(const char* label, std::atomic<bool>& value) {
    bool v = value;
    const bool changed = ImGui::Checkbox(label, &v);
    if (changed && OverlayTrace()) {
        std::printf("Overlay trace: checkbox \"%s\" -> %d (id %#x)\n", label, int(v), unsigned(ImGui::GetItemID()));
    }
    Store(value, v, changed);
}

void Slider(const char* label, std::atomic<float>& value, float lo, float hi) {
    float v = value;
    const bool changed = ImGui::SliderFloat(label, &v, lo, hi, "%.2f");
    Store(value, v, changed);
}

void Hint(const char* text) {
    ImGui::SameLine();
    ImGui::TextDisabled("(?)");
    if (ImGui::BeginItemTooltip()) {
        ImGui::PushTextWrapPos(ImGui::GetFontSize() * 30.0f);
        ImGui::TextUnformatted(text);
        ImGui::PopTextWrapPos();
        ImGui::EndTooltip();
    }
}

} // namespace detail

namespace {

// The settings menu as in 0.3 and 0.4: one window (moved with the mouse, its place kept in
// bbport.ini), sections one under the other, ImGui's own widgets and keyboard/gamepad navigation.
void Menu() {
    auto& s = BbSettings::Get();
    const ImGuiViewport* viewport = ImGui::GetMainViewport();
    // Where it was moved last (bbport.ini menu_pos, a fraction of the screen), kept on screen.
    ImVec2 pos(viewport->WorkPos.x + 40.0f * base_scale, viewport->WorkPos.y + 40.0f * base_scale);
    if (s.menu_x >= 0.0f && s.menu_y >= 0.0f) {
        const float margin = 80.0f * base_scale;
        pos.x = viewport->WorkPos.x +
                std::clamp(s.menu_x * viewport->WorkSize.x, 0.0f, std::max(viewport->WorkSize.x - margin, 0.0f));
        pos.y = viewport->WorkPos.y +
                std::clamp(s.menu_y * viewport->WorkSize.y, 0.0f, std::max(viewport->WorkSize.y - margin, 0.0f));
    }
    ImGui::SetNextWindowPos(pos, ImGuiCond_Appearing);
    ImGui::SetNextWindowSize(ImVec2(620.0f * base_scale, 0.0f), ImGuiCond_Appearing);
    // A menu taller than the screen would leave its last row (Close, Quit game) off screen: its
    // height stays within the screen below where it opens, and the contents scroll. From the
    // Linux fork.
    ImGui::SetNextWindowSizeConstraints(
        ImVec2(0.0f, 0.0f),
        ImVec2(FLT_MAX, std::max(viewport->WorkPos.y + viewport->WorkSize.y - pos.y - 20.0f * base_scale,
                                 200.0f * base_scale)));
    bool keep_open = true;
    if (!ImGui::Begin(
            BbSettings::MenuText("Bloodborne - Graphics  (Insert / hold L3+R3)###bbport_settings",
                                 "Bloodborne — настройки  (Insert / удерживать L3+R3)###bbport_settings"),
            &keep_open, ImGuiWindowFlags_NoCollapse)) {
        ImGui::End();
        return;
    }
    // Moved: remembered (saved with the settings when the menu closes).
    if (!ImGui::IsWindowAppearing() && viewport->WorkSize.x > 0.0f && viewport->WorkSize.y > 0.0f) {
        const ImVec2 at = ImGui::GetWindowPos();
        const float fx = (at.x - viewport->WorkPos.x) / viewport->WorkSize.x;
        const float fy = (at.y - viewport->WorkPos.y) / viewport->WorkSize.y;
        if (std::abs(at.x - pos.x) >= 1.0f || std::abs(at.y - pos.y) >= 1.0f) {
            s.menu_x = fx;
            s.menu_y = fy;
            dirty = true;
        }
    }
    // Always readable, whatever language the rest of the menu is in.
    int language = int(s.menu_language.load());
    if (ImGui::Combo("Language", &language, BbSettings::MenuLanguageNames,
                     int(BbSettings::MenuLanguage::Count))) {
        s.menu_language = BbSettings::MenuLanguage(language);
        s.menu_language_chosen = true;
        BbSettings::Save();
    }
    ImGui::TextUnformatted(FpsText().c_str());

    const bool taa = UpscalerSection(s);
    ReactiveMaskSection(s, taa);
    OutputSection(s);
    GameEffectsSection(s);
    FrameRateLimitSection(s);
    ImGui::SeparatorText(BbSettings::MenuText("Camera (right stick)", "Камера (правый стик)"));
    Slider(BbSettings::MenuText("Horizontal speed", "Скорость по горизонтали"), s.camera_speed[1], 0.25f, 2.0f);
    Slider(BbSettings::MenuText("Vertical speed", "Скорость по вертикали"), s.camera_speed[0], 0.25f, 2.0f);

    if (AtlasOn()) {
        BbMap::Settings();
    }
    ImGui::SeparatorText(BbSettings::MenuText("Other", "Прочее"));
    Checkbox(BbSettings::MenuText("FPS counter in corner", "Счётчик FPS в углу"), s.show_fps);
    Checkbox(BbSettings::MenuText("Mute in the background", "Без звука в фоне"), s.mute_unfocused);
    Checkbox(BbSettings::MenuText("Sound when a trophy is earned", "Звук при получении трофея"),
             s.trophy_sound);
    ShadersSection();

    ImGui::Spacing();
    if (ImGui::Button(BbSettings::MenuText("Close", "Закрыть"))) {
        keep_open = false;
    }
    // Issues #74, #116: leaving the game from the pad (this menu opens with L3+R3). A second
    // press confirms; the window thread then closes like the window's own close button.
    static bool quit_armed;
    ImGui::SameLine();
    // One ImGui ID for both labels ("###bb_quit"): with the label as its ID the button changed at
    // the first press, lost the pad's or keyboard's focus and disarmed at once, so quitting worked
    // only with the mouse over it (parsifal295, in the Linux fork).
    const std::string quit_label =
        std::string(quit_armed ? BbSettings::MenuText("Press again to quit", "Нажмите ещё раз для выхода")
                               : BbSettings::MenuText("Quit game", "Выйти из игры")) +
        "###bb_quit";
    if (ImGui::Button(quit_label.c_str())) {
        if (quit_armed) {
            SDL_Event quit{};
            quit.type = SDL_EVENT_QUIT;
            SDL_PushEvent(&quit);
        }
        quit_armed = !quit_armed;
    }
    if (quit_armed && !ImGui::IsItemFocused() && !ImGui::IsItemHovered()) {
        quit_armed = false;
    }
    ImGui::TextDisabled("%s", BbSettings::MenuText("Settings are saved to bbport.ini",
                                             "Настройки сохраняются в bbport.ini"));
    ImGui::End();
    if (!keep_open) {
        SetOpen(false);
    }
}

void FpsCounter() {
    const ImGuiViewport* viewport = ImGui::GetMainViewport();
    const float pad = 12.0f * base_scale;
    ImGui::SetNextWindowPos(
        ImVec2(viewport->WorkPos.x + viewport->WorkSize.x - pad, viewport->WorkPos.y + pad),
        ImGuiCond_Always, ImVec2(1.0f, 0.0f));
    ImGui::SetNextWindowBgAlpha(0.5f);
    ImGui::Begin("##fps", nullptr,
                 ImGuiWindowFlags_NoDecoration | ImGuiWindowFlags_AlwaysAutoResize |
                     ImGuiWindowFlags_NoInputs | ImGuiWindowFlags_NoNav |
                     ImGuiWindowFlags_NoFocusOnAppearing);
    const auto& s = BbSettings::Get();
    ImGui::Text("%s  %s", FpsText().c_str(),
                s.upscaler == BbSettings::UpscalerFsr3     ? "FSR 3.1"
                : s.upscaler == BbSettings::UpscalerFsr4   ? "FSR 4"
                : s.upscaler == BbSettings::UpscalerFsr411 ? "FSR 4.1.1"
                : s.upscaler == BbSettings::UpscalerTaa    ? "TAA"
                : s.upscaler == BbSettings::UpscalerDlss   ? "DLSS"
                : s.upscaler == BbSettings::UpscalerFsr1   ? "FSR 1"
                : s.upscaler == BbSettings::UpscalerFsrAmd ? "FSR 4 (AMD)"
                                                           : "");
    ImGui::End();
}

/// "Compiling shaders": pipelines made in the background (the cache's preload, imported recipes)
/// as done / queued, the recipe import, and the game's own compiles of the last 1.5 s (idea from
/// the SrShadowy fork's precompile splash; here a line in the corner while it lasts).
/// BB_SHADER_PROGRESS=0 hides it.
struct ShaderProgress {
    u32 done = 0, total = 0, recent = 0;
    bool importing = false;
};
ShaderProgress CurrentShaderProgress() {
    static const bool enabled = !bb_env_off("BB_SHADER_PROGRESS");
    ShaderProgress p;
    if (!enabled) {
        return p;
    }
    p.total = g_bb_background_pipelines_total.load(std::memory_order_relaxed);
    p.done = g_bb_background_pipelines_done.load(std::memory_order_relaxed);
    // An import longer than 3 minutes is not shown (a stuck child must not keep the line up).
    static const long long start = NowNs();
    p.importing = g_bb_shader_import_active.load(std::memory_order_relaxed) &&
                  NowNs() - start < 180'000'000'000ll;
    static u32 last_compiles = 0;
    static long long last_change = 0;
    static u32 window_start_compiles = 0;
    const u32 compiles = g_bb_compiles_total.load(std::memory_order_relaxed);
    const long long now = NowNs();
    if (compiles != last_compiles) {
        if (now - last_change > 1'500'000'000ll) {
            window_start_compiles = last_compiles;
        }
        last_compiles = compiles;
        last_change = now;
    }
    if (last_change != 0 && now - last_change <= 1'500'000'000ll) {
        p.recent = compiles - window_start_compiles;
    }
    return p;
}
bool ShaderProgressShown() {
    const ShaderProgress p = CurrentShaderProgress();
    const bool shown = p.done < p.total || p.importing || p.recent != 0;
    static bool was_shown = false;
    if (shown != was_shown) {
        was_shown = shown;
        std::printf("Overlay: \"Compiling shaders\" %s (%u of %u in the background%s, %u just now)\n",
                    shown ? "shown" : "hidden", p.done, p.total,
                    p.importing ? ", recipes importing" : "", p.recent);
    }
    return shown;
}
void ShaderProgressLine() {
    const ShaderProgress p = CurrentShaderProgress();
    std::string text;
    if (p.done < p.total) {
        text = fmt::format("{} {} / {}",
                           BbSettings::MenuText("Compiling shaders", "Компиляция шейдеров"), p.done,
                           p.total);
    } else if (p.importing) {
        text = BbSettings::MenuText("Preparing shaders...", "Подготовка шейдеров...");
    } else if (p.recent != 0) {
        text = fmt::format("{} ({})",
                           BbSettings::MenuText("Compiling shaders", "Компиляция шейдеров"),
                           p.recent);
    } else {
        return;
    }
    const ImGuiViewport* viewport = ImGui::GetMainViewport();
    const float pad = 12.0f * base_scale;
    ImGui::SetNextWindowPos(ImVec2(viewport->WorkPos.x + pad,
                                   viewport->WorkPos.y + viewport->WorkSize.y - pad),
                            ImGuiCond_Always, ImVec2(0.0f, 1.0f));
    ImGui::SetNextWindowBgAlpha(0.5f);
    ImGui::Begin("##shader_progress", nullptr,
                 ImGuiWindowFlags_NoDecoration | ImGuiWindowFlags_AlwaysAutoResize |
                     ImGuiWindowFlags_NoInputs | ImGuiWindowFlags_NoNav |
                     ImGuiWindowFlags_NoFocusOnAppearing);
    ImGui::TextUnformatted(text.c_str());
    ImGui::End();
}

// A trophy icon as an ImGui texture (present thread, under imgui_mutex); null when it cannot be
// read or SDL is older than 3.4 (no PNG loader).
ImTextureData* TrophyIcon(const std::filesystem::path& path) {
    if (path.empty()) {
        return nullptr;
    }
    const auto [it, added] = trophy_icons.try_emplace(path.string(), nullptr);
    if (!added) {
        return it->second;
    }
#if SDL_VERSION_ATLEAST(3, 4, 0)
    // UTF-8 for SDL (on Windows path::c_str() is wide, string() the ANSI code page).
    const std::u8string utf8 = path.u8string();
    const char* name = reinterpret_cast<const char*>(utf8.c_str());
    SDL_Surface* loaded = SDL_LoadPNG(name);
    SDL_Surface* rgba = loaded ? SDL_ConvertSurface(loaded, SDL_PIXELFORMAT_RGBA32) : nullptr;
    SDL_DestroySurface(loaded);
    if (!rgba) {
        std::printf("Overlay: trophy icon %s not loaded: %s\n", name, SDL_GetError());
        return nullptr;
    }
    auto* tex = IM_NEW(ImTextureData)();
    tex->Create(ImTextureFormat_RGBA32, rgba->w, rgba->h);
    for (int y = 0; y < rgba->h; ++y) {
        std::memcpy(tex->GetPixelsAt(0, y), static_cast<const unsigned char*>(rgba->pixels) + y * rgba->pitch,
                    std::size_t(rgba->w) * 4);
    }
    SDL_DestroySurface(rgba);
    ImGui::RegisterUserTexture(tex);
    it->second = tex;
#endif
    return it->second;
}

// The front trophy of the queue: a dark panel at the top centre (the game's HUD has its health at
// the top left, its echoes and insight at the top right), sliding down, with a badge in the
// grade's colour, "Trophy earned" and the name.
void TrophyWindow(float dt) {
    TrophyToast toast;
    {
        std::scoped_lock lock{trophy_mutex};
        if (trophy_queue.empty()) {
            trophy_active = false;
            return;
        }
        auto& front = trophy_queue.front();
        if (front.elapsed <= 0.0f && front.elapsed + dt > 0.0f) {
            std::printf("Overlay: trophy shown: %s\n", front.name.c_str());
        }
        front.elapsed += dt;
        if (front.elapsed > TrophySeconds) {
            trophy_queue.pop_front();
            trophy_active = !trophy_queue.empty();
            return;
        }
        toast = front;
    }
    if (toast.elapsed < 0.0f) {
        return; // a delayed one (BB_TROPHY_TEST)
    }
    const ImGuiViewport* viewport = ImGui::GetMainViewport();
    const float s = base_scale;
    const ImVec2 size{380.0f * s, 76.0f * s};
    const float slide = std::min(toast.elapsed / TrophySlide, 1.0f);
    const float eased = 1.0f - (1.0f - slide) * (1.0f - slide);
    const float x = viewport->WorkPos.x + (viewport->WorkSize.x - size.x) * 0.5f;
    const float y = viewport->WorkPos.y - size.y + (size.y + 24.0f * s) * eased;
    const float alpha = std::clamp(std::min(slide, TrophySeconds - toast.elapsed), 0.0f, 1.0f);
    auto* draw = ImGui::GetForegroundDrawList();
    const auto a = [alpha](int r, int g, int b, int base) { return IM_COL32(r, g, b, int(base * alpha)); };
    draw->AddRectFilled({x, y}, {x + size.x, y + size.y}, a(12, 10, 8, 220), 8.0f * s);
    draw->AddRect({x, y}, {x + size.x, y + size.y}, a(150, 130, 100, 200), 8.0f * s, 0, 1.5f * s);
    // The badge: the grade's colour (platinum, gold, silver, bronze; grey unknown) and its letter.
    const ImU32 badge = toast.grade == 'P'   ? a(200, 215, 235, 255)
                        : toast.grade == 'G' ? a(222, 180, 60, 255)
                        : toast.grade == 'S' ? a(185, 190, 196, 255)
                        : toast.grade == 'B' ? a(176, 112, 64, 255)
                                             : a(120, 120, 120, 255);
    const ImVec2 centre{x + 38.0f * s, y + size.y * 0.5f};
    const char letter[2] = {toast.grade == '?' ? 'T' : toast.grade, 0};
    const ImVec2 letter_size = ImGui::CalcTextSize(letter);
    if (ImTextureData* icon = TrophyIcon(toast.icon)) {
        // The game's icon, the grade as a small badge on its corner.
        const float half = 26.0f * s;
        draw->AddImageRounded(icon->GetTexRef(), {centre.x - half, centre.y - half}, {centre.x + half, centre.y + half},
                              {0, 0}, {1, 1}, a(255, 255, 255, 255), 4.0f * s);
        const ImVec2 dot{centre.x + half - 2.0f * s, centre.y + half - 2.0f * s};
        draw->AddCircleFilled(dot, 9.0f * s, badge);
        draw->AddCircle(dot, 9.0f * s, a(30, 25, 20, 255), 0, 1.5f * s);
    } else {
        draw->AddCircleFilled(centre, 24.0f * s, badge);
        draw->AddCircle(centre, 24.0f * s, a(30, 25, 20, 255), 0, 2.0f * s);
        draw->AddText({centre.x - letter_size.x * 0.5f, centre.y - letter_size.y * 0.5f}, a(30, 25, 20, 255), letter);
    }
    const float text_x = x + 76.0f * s, wrap = size.x - 88.0f * s;
    // In the game's language, as the name (BB_LANGUAGE, the PS4 number: 8 Russian).
    static const bool russian = [] {
        const char* env = bb_env("BB_LANGUAGE");
        return env && std::atoi(env) == 8;
    }();
    draw->AddText({text_x, y + 12.0f * s}, a(200, 185, 150, 255), russian ? "Получен трофей" : "Trophy earned");
    draw->AddText(nullptr, 0.0f, {text_x, y + 12.0f * s + ImGui::GetTextLineHeightWithSpacing()},
                  a(240, 232, 215, 255), toast.name.c_str(), nullptr, wrap);
}

ImU32 GradeColour(char grade, float alpha) {
    const int a = int(255.0f * alpha);
    switch (grade) {
    case 'P':
        return IM_COL32(170, 200, 228, a);
    case 'G':
        return IM_COL32(226, 186, 72, a);
    case 'S':
        return IM_COL32(196, 200, 206, a);
    case 'B':
        return IM_COL32(186, 118, 68, a);
    default:
        return IM_COL32(200, 200, 200, a);
    }
}

// A small cup: bowl, handles, stem and base, `size` high from `top`.
void DrawCup(ImDrawList* draw, ImVec2 top, float size, ImU32 colour) {
    const float w = size * 0.8f, x = top.x, y = top.y;
    draw->PathLineTo(ImVec2(x, y));
    draw->PathLineTo(ImVec2(x + w, y));
    draw->PathBezierCubicCurveTo(ImVec2(x + w, y + size * 0.45f), ImVec2(x + w * 0.65f, y + size * 0.6f),
                                 ImVec2(x + w * 0.5f, y + size * 0.6f));
    draw->PathBezierCubicCurveTo(ImVec2(x + w * 0.35f, y + size * 0.6f), ImVec2(x, y + size * 0.45f),
                                 ImVec2(x, y));
    draw->PathFillConvex(colour);
    const float handle = size * 0.12f;
    draw->AddCircle(ImVec2(x - handle * 0.4f, y + size * 0.2f), handle, colour, 12, size * 0.07f);
    draw->AddCircle(ImVec2(x + w + handle * 0.4f, y + size * 0.2f), handle, colour, 12, size * 0.07f);
    draw->AddRectFilled(ImVec2(x + w * 0.44f, y + size * 0.58f), ImVec2(x + w * 0.56f, y + size * 0.82f),
                        colour);
    draw->AddRectFilled(ImVec2(x + w * 0.22f, y + size * 0.82f), ImVec2(x + w * 0.78f, y + size * 0.95f),
                        colour, size * 0.04f);
}

ImTextureData* NoticeIcon(const Notice& n) {
    if (n.icon_size <= 0) {
        return nullptr;
    }
    auto& texture = notice_icons[n.id];
    if (texture == nullptr) {
        texture = new ImTextureData();
        texture->Create(ImTextureFormat_RGBA32, n.icon_size, n.icon_size);
        std::memcpy(texture->GetPixels(), n.icon.data(), n.icon.size());
        ImGui::RegisterUserTexture(texture);
    }
    return texture;
}

// The trophy chime: a short bell of our own (no audio from the console), two notes and a third
// for the platinum, on its own SDL stream beside the game's. From GerasimosKan's trophies
// (deadinside28/bloodborne_pc#127). BB_AUDIO=none keeps it silent like the game.
void TrophyChime(bool platinum) {
    static SDL_AudioStream* stream = []() -> SDL_AudioStream* {
        const char* mode = bb_env("BB_AUDIO");
        if ((mode && !std::strcmp(mode, "none")) || !SDL_InitSubSystem(SDL_INIT_AUDIO)) {
            return nullptr;
        }
        const SDL_AudioSpec spec{SDL_AUDIO_F32, 1, 48000};
        SDL_AudioStream* s =
            SDL_OpenAudioDeviceStream(SDL_AUDIO_DEVICE_DEFAULT_PLAYBACK, &spec, nullptr, nullptr);
        if (s) {
            SDL_ResumeAudioStreamDevice(s);
        }
        return s;
    }();
    if (!stream) {
        return;
    }
    constexpr int rate = 48000;
    constexpr float two_pi = 6.2831853f, step = 0.09f;
    std::vector<float> pcm(rate * 6 / 5);
    const float notes[] = {1318.5f, 1975.5f, 2637.0f}; // E6, B6, E7
    for (int k = 0; k < (platinum ? 3 : 2); ++k) {
        for (std::size_t i = std::size_t(k * step * rate); i < pcm.size(); ++i) {
            const float t = float(i) / rate - k * step, f = notes[k];
            const float envelope = std::min(t / 0.004f, 1.0f) * std::exp(-t * 5.0f);
            // A bell: the fundamental and a quickly fading inharmonic partial.
            pcm[i] += 0.12f * envelope *
                      (std::sin(two_pi * f * t) +
                       0.35f * std::exp(-t * 8.0f) * std::sin(two_pi * 2.76f * f * t));
        }
    }
    SDL_PutAudioStreamData(stream, pcm.data(), int(pcm.size() * sizeof(float)));
}

void TrophyCard() {
    const auto now = std::chrono::steady_clock::now();
    if (!notice_shown) {
        std::scoped_lock lock{notice_mutex};
        if (notices.empty()) {
            notice_busy = false;
            return;
        }
        notice = std::move(notices.front());
        notices.pop_front();
        notice_shown = true;
        notice_start = now;
        if (BbSettings::Get().trophy_sound) {
            TrophyChime(notice.grade == 'P');
        }
    }
    const float t = std::chrono::duration<float>(now - notice_start).count();
    if (t > NoticeIn + NoticeHold + NoticeOut) {
        notice_shown = false;
        return;
    }
    const float in = std::min(t / NoticeIn, 1.0f);
    const float alpha = t < NoticeIn + NoticeHold ? in : 1.0f - (t - NoticeIn - NoticeHold) / NoticeOut;
    const float ease = 1.0f - (1.0f - in) * (1.0f - in);
    const float s = base_scale;
    const ImGuiViewport* viewport = ImGui::GetMainViewport();
    ImDrawList* draw = ImGui::GetForegroundDrawList();
    ImFont* font = ImGui::GetFont();
    const float text_size = ImGui::GetFontSize();
    const float pad = 12.0f * s, icon = 72.0f * s, width = 470.0f * s;
    const float text_x = pad + icon + 16.0f * s, text_w = width - text_x - pad;
    const char* earned = BbSettings::MenuText("You have earned a trophy.", "Вы получили трофей.");
    const ImVec2 name_size =
        font->CalcTextSizeA(text_size * 1.05f, FLT_MAX, text_w, notice.name.c_str());
    const float height = std::max(icon + 2.0f * pad, pad * 2.0f + text_size * 1.6f + name_size.y);
    const ImVec2 p0(viewport->WorkPos.x + 36.0f * s - (1.0f - ease) * 48.0f * s,
                    viewport->WorkPos.y + 36.0f * s);
    const ImVec2 p1(p0.x + width, p0.y + height);
    draw->AddRectFilled(ImVec2(p0.x + 3.0f * s, p0.y + 4.0f * s), ImVec2(p1.x + 3.0f * s, p1.y + 4.0f * s),
                        IM_COL32(0, 0, 0, int(90 * alpha)), 8.0f * s);
    draw->AddRectFilled(p0, p1, IM_COL32(24, 24, 30, int(232 * alpha)), 8.0f * s);
    draw->AddRect(p0, p1, IM_COL32(255, 255, 255, int(28 * alpha)), 8.0f * s);
    const ImVec2 icon0(p0.x + pad, p0.y + (height - icon) * 0.5f);
    if (ImTextureData* texture = NoticeIcon(notice)) {
        draw->AddImageRounded(texture->GetTexRef(), icon0, ImVec2(icon0.x + icon, icon0.y + icon),
                              ImVec2(0, 0), ImVec2(1, 1), IM_COL32(255, 255, 255, int(255 * alpha)),
                              4.0f * s);
    } else {
        draw->AddRectFilled(icon0, ImVec2(icon0.x + icon, icon0.y + icon),
                            IM_COL32(50, 50, 58, int(255 * alpha)), 4.0f * s);
        DrawCup(draw, ImVec2(icon0.x + icon * 0.28f, icon0.y + icon * 0.22f), icon * 0.56f,
                GradeColour(notice.grade, alpha));
    }
    const ImVec2 line1(p0.x + text_x, p0.y + pad + 2.0f * s);
    draw->AddText(font, text_size * 0.92f, line1, IM_COL32(205, 205, 212, int(255 * alpha)), earned);
    draw->AddText(font, text_size * 1.05f, ImVec2(line1.x, line1.y + text_size * 1.45f),
                  IM_COL32(255, 255, 255, int(255 * alpha)), notice.name.c_str(), nullptr, text_w);
}

const OskExtraRow& OskExtra() {
    return OskExtras[size_t(BbSettings::Get().menu_language.load())];
}

/// The rows of characters: the four English ones, and the language's own when it has any.
int OskKeyRows() {
    return OskExtra().count ? 5 : 4;
}

int OskRowLength(int row) {
    return row == 0 ? 12 : row < 4 ? 10 : row < OskKeyRows() ? OskExtra().count : OskActions;
}

const char* OskKey(int row, int col) {
    return row < 4 ? OskKeys[row][osk.caps ? 0 : 1][col] : OskExtra().keys[osk.caps ? 0 : 1][col];
}

const char* OskActionLabel(int action) {
    switch (action) {
    case OskCaps: return BbSettings::MenuText("Caps", "Регистр");
    case OskSpace: return BbSettings::MenuText("Space", "Пробел");
    case OskBackspace: return BbSettings::MenuText("Delete", "Стереть");
    case OskClear: return BbSettings::MenuText("Clear", "Очистить");
    case OskConfirm: return BbSettings::MenuText("OK", "OK");
    default: return BbSettings::MenuText("Cancel", "Отмена");
    }
}

void OskEdit(TextEdit::Kind kind, std::string text = {}) {
    std::scoped_lock lock{prompt_mutex};
    text_edits.push_back({kind, std::move(text)});
}

void OskPress(int row, int col) {
    if (row < OskKeyRows()) {
        OskEdit(TextEdit::Append, OskKey(row, col));
        return;
    }
    switch (col) {
    case OskCaps: osk.caps = !osk.caps; break;
    case OskSpace: OskEdit(TextEdit::Append, " "); break;
    case OskBackspace: OskEdit(TextEdit::Backspace); break;
    case OskClear: OskEdit(TextEdit::Clear); break;
    case OskConfirm: OskEdit(TextEdit::Confirm); break;
    default: OskEdit(TextEdit::Cancel); break;
    }
}

void OskMove(int d_row, int d_col) {
    const int rows = OskKeyRows() + 1;
    osk.row = (osk.row + d_row + rows) % rows;
    const int length = OskRowLength(osk.row);
    osk.col = d_col ? (osk.col + d_col + length) % length : std::min(osk.col, length - 1);
}

/// Window thread, the text dialog open and the menu closed: a controller types on the keyboard.
bool OskEvent(const SDL_Event& event) {
    if (event.type == SDL_EVENT_GAMEPAD_BUTTON_DOWN) {
        // Types and cancels on the game's cross and circle, wherever bbport.ini puts them.
        if (event.gbutton.button == PadButton("cross", SDL_GAMEPAD_BUTTON_SOUTH)) {
            OskPress(osk.row, osk.col);
            return true;
        }
        if (event.gbutton.button == PadButton("circle", SDL_GAMEPAD_BUTTON_EAST)) {
            OskEdit(TextEdit::Cancel);
            return true;
        }
        switch (event.gbutton.button) {
        case SDL_GAMEPAD_BUTTON_DPAD_UP: OskMove(-1, 0); return true;
        case SDL_GAMEPAD_BUTTON_DPAD_DOWN: OskMove(1, 0); return true;
        case SDL_GAMEPAD_BUTTON_DPAD_LEFT: OskMove(0, -1); return true;
        case SDL_GAMEPAD_BUTTON_DPAD_RIGHT: OskMove(0, 1); return true;
        case SDL_GAMEPAD_BUTTON_SOUTH: OskPress(osk.row, osk.col); return true;
        case SDL_GAMEPAD_BUTTON_WEST: OskEdit(TextEdit::Backspace); return true;
        case SDL_GAMEPAD_BUTTON_NORTH: OskEdit(TextEdit::Append, " "); return true;
        case SDL_GAMEPAD_BUTTON_EAST: OskEdit(TextEdit::Cancel); return true;
        case SDL_GAMEPAD_BUTTON_START: OskEdit(TextEdit::Confirm); return true;
        case SDL_GAMEPAD_BUTTON_LEFT_SHOULDER:
        case SDL_GAMEPAD_BUTTON_RIGHT_SHOULDER: osk.caps = !osk.caps; return true;
        default: return false;
        }
    }
    if (event.type == SDL_EVENT_GAMEPAD_AXIS_MOTION &&
        (event.gaxis.axis == SDL_GAMEPAD_AXIS_LEFTX || event.gaxis.axis == SDL_GAMEPAD_AXIS_LEFTY)) {
        constexpr int Deadzone = 18000;
        const u64 now = SDL_GetTicks();
        const int value = event.gaxis.value;
        if (now - osk.last_stick_ms < 180 || (value < Deadzone && value > -Deadzone)) {
            return true;
        }
        osk.last_stick_ms = now;
        const int step = value > 0 ? 1 : -1;
        event.gaxis.axis == SDL_GAMEPAD_AXIS_LEFTX ? OskMove(0, step) : OskMove(step, 0);
        return true;
    }
    return false;
}

void TextPrompt() {
    std::string title, text;
    {
        std::scoped_lock lock{prompt_mutex};
        title = prompt_title;
        text = prompt_text;
    }
    const float s = ImGui::GetStyle().FontScaleMain;
    const ImGuiViewport* viewport = ImGui::GetMainViewport();
    ImGui::SetNextWindowPos(ImVec2(viewport->WorkPos.x + viewport->WorkSize.x * 0.5f,
                                   viewport->WorkPos.y + viewport->WorkSize.y * 0.5f),
                            ImGuiCond_Always, ImVec2(0.5f, 0.5f));
    ImGui::SetNextWindowBgAlpha(0.94f);
    ImGui::Begin("##textprompt", nullptr,
                 ImGuiWindowFlags_NoDecoration | ImGuiWindowFlags_AlwaysAutoResize |
                     ImGuiWindowFlags_NoInputs | ImGuiWindowFlags_NoNav |
                     ImGuiWindowFlags_NoFocusOnAppearing);
    ImGui::TextUnformatted(title.c_str());
    ImGui::Separator();
    ImGui::Text("%s_", text.c_str());
    ImGui::Separator();
    // The keys: the selected one in the menu's accent colour. Drawn only (NoInputs): the
    // controller moves the selection, a physical keyboard types as before.
    const ImVec2 key(40.0f * s, 34.0f * s);
    const ImGuiStyle& style = ImGui::GetStyle();
    const auto key_button = [&](const char* label, float width, bool selected) {
        ImGui::PushStyleColor(ImGuiCol_Button, selected ? style.Colors[ImGuiCol_ButtonActive]
                                                        : style.Colors[ImGuiCol_FrameBg]);
        ImGui::Button(label, ImVec2(width, key.y));
        ImGui::PopStyleColor();
    };
    osk.row = std::min(osk.row, OskKeyRows()); // the language changed: its row went
    for (int row = 0; row < OskKeyRows(); ++row) {
        for (int col = 0; col < OskRowLength(row); ++col) {
            if (col) {
                ImGui::SameLine();
            }
            ImGui::PushID(row * 16 + col);
            key_button(OskKey(row, col), key.x, osk.row == row && osk.col == col);
            ImGui::PopID();
        }
    }
    for (int action = 0; action < OskActions; ++action) {
        if (action) {
            ImGui::SameLine();
        }
        const char* label = OskActionLabel(action);
        const bool caps_on = action == OskCaps && osk.caps;
        key_button(label, std::max(key.x * 1.4f, ImGui::CalcTextSize(label).x + 18.0f * s),
                   (osk.row == OskKeyRows() && osk.col == action) || caps_on);
    }
    ImGui::Separator();
    ImGui::TextUnformatted(BbSettings::MenuText(
        "Controller: D-pad or left stick moves, Cross types, Square deletes, Triangle is a space, "
        "L1/R1 caps, Options = OK, Circle = cancel",
        "Геймпад: крестовина или левый стик — выбор, Cross — ввод, Square — стереть, Triangle — "
        "пробел, L1/R1 — регистр, Options — OK, Circle — отмена"));
    ImGui::TextUnformatted(BbSettings::MenuText(
        "Keyboard: type, Backspace = delete, Enter = OK, Esc = cancel",
        "Клавиатура: ввод, Backspace — стереть, Enter — OK, Esc — отмена"));
    ImGui::End();
}

/// BB_MENU_KEYS_FILE=<file> (scripted tests): tokens toggle up down left right enter back l1 r1,
/// consumed when the file appears (it is removed), one key press per frame.
void ScriptedKeys() {
    static const char* path = bb_env("BB_MENU_KEYS_FILE");
    static std::chrono::steady_clock::time_point last_check{};
    static std::vector<std::string> queue;
    static bool release = false, mouse_release = false;
    static ImGuiKey held = ImGuiKey_None;
    if (!path) {
        return;
    }
    ImGuiIO& io = ImGui::GetIO();
    if (release) {
        io.AddKeyEvent(held, false);
        release = false;
        return;
    }
    if (mouse_release) {
        io.AddMouseButtonEvent(0, false);
        mouse_release = false;
        return;
    }
    const auto now = std::chrono::steady_clock::now();
    if (queue.empty() && now - last_check > std::chrono::milliseconds(100)) {
        last_check = now;
        if (FILE* f = std::fopen(path, "r")) {
            char token[32];
            while (std::fscanf(f, "%31s", token) == 1) {
                queue.emplace_back(token);
            }
            std::fclose(f);
            std::remove(path);
        }
    }
    if (queue.empty()) {
        return;
    }
    const std::string token = queue.front();
    queue.erase(queue.begin());
    if (token == "toggle") {
        SetOpen(!menu_open);
        return;
    }
    // "click X Y": the left button pressed at display pixel X, Y and released the frame after.
    if (token == "click" && queue.size() >= 2) {
        const float x = std::strtof(queue[0].c_str(), nullptr), y = std::strtof(queue[1].c_str(), nullptr);
        queue.erase(queue.begin(), queue.begin() + 2);
        io.AddMousePosEvent(x, y);
        io.AddMouseButtonEvent(0, true);
        mouse_release = true;
        return;
    }
    held = token == "up" ? ImGuiKey_GamepadDpadUp : token == "down" ? ImGuiKey_GamepadDpadDown
         : token == "left" ? ImGuiKey_GamepadDpadLeft : token == "right" ? ImGuiKey_GamepadDpadRight
         : token == "enter" ? ImGuiKey_GamepadFaceDown : token == "l1" ? ImGuiKey_GamepadL1
         : token == "r1" ? ImGuiKey_GamepadR1 : token == "kdown" ? ImGuiKey_DownArrow
         : token == "kup" ? ImGuiKey_UpArrow : ImGuiKey_None;
    if (token == "back") {
        SetOpen(false);
        return;
    }
    if (held != ImGuiKey_None) {
        io.AddKeyEvent(held, true);
        release = true;
    }
}

} // namespace

void SetTextPrompt(bool active, const std::string& prompt, const std::string& text) {
    {
        std::scoped_lock lock{prompt_mutex};
        prompt_title = prompt;
        prompt_text = text;
        if (!active) {
            text_edits.clear();
        }
    }
    if (active && !prompt_active.exchange(true)) {
        std::scoped_lock lock{imgui_mutex};
        osk = OnScreenKeyboard{};
    }
    prompt_active = active;
}

std::vector<TextEdit> TakeTextEdits() {
    std::scoped_lock lock{prompt_mutex};
    return std::exchange(text_edits, {});
}

void Init(const Vulkan::Instance& instance, vk::Format format, u32 image_count) {
    std::scoped_lock lock{imgui_mutex};
    if (initialized) {
        return;
    }
    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGuiIO& io = ImGui::GetIO();
    io.IniFilename = nullptr; // window positions are not kept
    io.ConfigFlags |= ImGuiConfigFlags_NavEnableKeyboard | ImGuiConfigFlags_NavEnableGamepad;
    io.BackendFlags |= ImGuiBackendFlags_HasGamepad;
    io.BackendPlatformName = "bbport";

    ImGui::StyleColorsDark();
    ImGuiStyle& style = ImGui::GetStyle();
    style.WindowRounding = 6.0f;
    style.FrameRounding = 4.0f;
    style.GrabRounding = 4.0f;
    style.Colors[ImGuiCol_WindowBg].w = 0.92f;

    ImFontConfig font_config;
    font_config.FontDataOwnedByAtlas = false;
    io.Fonts->AddFontFromMemoryTTF(const_cast<unsigned char*>(bb_font_ttf),
                                   int(bb_font_ttf_end - bb_font_ttf), 18.0f, &font_config);
    // Hunter's Atlas: the map's serif title font, made from the player's own menu asset by the
    // map generator (the port's font above stays the default).
    if (AtlasOn()) {
        const auto map_font = BbAtlasPath("BB_MAP_FONT", BbAtlasPath("BB_MAP_DIR", "navigation-map/maps")
                                                              .parent_path() / "fonts/bloodborne-native.ttf");
        std::ifstream face_file(map_font, std::ios::binary | std::ios::ate);
        if (face_file) {
            const auto bytes = face_file.tellg();
            if (bytes > 0 && bytes < 16 * 1024 * 1024) {
                void* data = IM_ALLOC(size_t(bytes));
                face_file.seekg(0);
                face_file.read(static_cast<char*>(data), bytes);
                if (face_file) {
                    if (auto* face = io.Fonts->AddFontFromMemoryTTF(data, int(bytes), 24.0f)) {
                        BbMap::SetTitleFont(face);
                    }
                } else {
                    IM_FREE(data);
                }
            }
        }
    }

    const vk::Instance vk_instance = instance.GetInstance();
    ImGui_ImplVulkan_LoadFunctions(
        instance.ApiVersion(),
        [](const char* name, void* user) {
            return VULKAN_HPP_DEFAULT_DISPATCHER.vkGetInstanceProcAddr(
                *static_cast<const vk::Instance*>(user), name);
        },
        const_cast<vk::Instance*>(&vk_instance));

    const VkFormat color_format = static_cast<VkFormat>(format);
    ImGui_ImplVulkan_InitInfo info{};
    info.ApiVersion = instance.ApiVersion();
    info.Instance = vk_instance;
    info.PhysicalDevice = instance.GetPhysicalDevice();
    info.Device = instance.GetDevice();
    info.QueueFamily = instance.GetGraphicsQueueFamilyIndex();
    info.Queue = instance.GetGraphicsQueue();
    info.DescriptorPoolSize = 16;
    info.MinImageCount = std::max(image_count, 2u);
    info.ImageCount = std::max(image_count, 2u);
    info.UseDynamicRendering = true;
    info.PipelineInfoMain.PipelineRenderingCreateInfo = {
        .sType = VK_STRUCTURE_TYPE_PIPELINE_RENDERING_CREATE_INFO_KHR,
        .colorAttachmentCount = 1,
        .pColorAttachmentFormats = &color_format,
    };
    if (!ImGui_ImplVulkan_Init(&info)) {
        std::printf("Overlay: ImGui Vulkan backend init failed\n");
        ImGui::DestroyContext();
        return;
    }
    initialized = true;
    if (AtlasOn()) {
        BbMapArt::Init();
        BbMap::Init();
    }
    std::printf("Overlay: menu ready (Insert, or hold L3+R3)\n");
}

void UpdateTextInput(SDL_Window* window) {
    bool want = false;
    {
        std::scoped_lock lock{imgui_mutex};
        want = initialized && menu_open && ImGui::GetIO().WantTextInput;
    }
    if (want != SDL_TextInputActive(window)) {
        if (want) {
            SDL_StartTextInput(window);
        } else {
            SDL_StopTextInput(window);
        }
    }
}

bool HandleEvent(const SDL_Event& event) {
    std::scoped_lock lock{imgui_mutex};
    if (!initialized) {
        return false;
    }
    ImGuiIO& io = ImGui::GetIO();
    if (AtlasOn()) {
        BbAtlasMenu::Suppress(menu_open || prompt_active);
        if (!prompt_active && BbAtlasMenu::HandleMouse(event)) {
            return true;
        }
        if (!prompt_active && BbMap::HandleEvent(event)) {
            return true;
        }
    }
    // The map takes the keyboard, the mouse and the pad's ImGui navigation as the menu does.
    const bool map_open = AtlasOn() && BbMap::IsOpen();
    const bool is_open = menu_open || map_open;
    switch (event.type) {
    case SDL_EVENT_KEY_DOWN:
    case SDL_EVENT_KEY_UP: {
        const bool down = event.type == SDL_EVENT_KEY_DOWN;
        if (down && !event.key.repeat &&
            (event.key.key == SDLK_INSERT || (is_open && event.key.key == SDLK_ESCAPE))) {
            if (map_open) {
                BbMap::Close();
            }
            SetOpen(event.key.key == SDLK_INSERT ? !menu_open : false);
            return true;
        }
        if (!is_open) {
            return false;
        }
        io.AddKeyEvent(ImGuiMod_Ctrl, (event.key.mod & SDL_KMOD_CTRL) != 0);
        io.AddKeyEvent(ImGuiMod_Shift, (event.key.mod & SDL_KMOD_SHIFT) != 0);
        io.AddKeyEvent(ImGuiMod_Alt, (event.key.mod & SDL_KMOD_ALT) != 0);
        if (const ImGuiKey key = KeyFromSdl(event.key.key); key != ImGuiKey_None) {
            io.AddKeyEvent(key, down);
        }
        return true;
    }
    case SDL_EVENT_GAMEPAD_AXIS_MOTION:
        return !is_open && prompt_active && OskEvent(event);
    case SDL_EVENT_GAMEPAD_BUTTON_DOWN:
    case SDL_EVENT_GAMEPAD_BUTTON_UP: {
        const bool down = event.type == SDL_EVENT_GAMEPAD_BUTTON_DOWN;
        const u8 button = event.gbutton.button;
        if (button == SDL_GAMEPAD_BUTTON_LEFT_STICK) {
            l3_down = down;
        } else if (button == SDL_GAMEPAD_BUTTON_RIGHT_STICK) {
            r3_down = down;
        }
        if (l3_down && r3_down) {
            if (down && is_open) {
                SetOpen(false);
                return true;
            }
            if (down && l3r3_since.load() == 0 && OpenHoldMs() > 0) {
                l3r3_since = NowNs(); // the game sees the press too (a fight goes on)
            }
        } else {
            l3r3_since = 0;
        }
        if (!is_open) {
            return prompt_active && OskEvent(event);
        }
        if (const ImGuiKey key = KeyFromGamepad(button); key != ImGuiKey_None) {
            io.AddKeyEvent(key, down);
        }
        return true;
    }
    case SDL_EVENT_TEXT_INPUT: {
        // Typed characters (Ctrl+click on a slider, a text field): key events alone erase but
        // do not type. SDL sends them while text input is on (UpdateTextInput).
        if (!is_open) {
            return false;
        }
        io.AddInputCharactersUTF8(event.text.text);
        return true;
    }
    case SDL_EVENT_MOUSE_MOTION: {
        if (!is_open) {
            return false;
        }
        const ImVec2 at = ToDisplay(event.motion.windowID, event.motion.x, event.motion.y);
        io.AddMousePosEvent(at.x, at.y);
        return true;
    }
    case SDL_EVENT_MOUSE_BUTTON_DOWN:
    case SDL_EVENT_MOUSE_BUTTON_UP: {
        if (!is_open) {
            return false;
        }
        const int button = event.button.button == SDL_BUTTON_LEFT    ? 0
                           : event.button.button == SDL_BUTTON_RIGHT  ? 1
                           : event.button.button == SDL_BUTTON_MIDDLE ? 2
                                                                      : -1;
        if (button >= 0) {
            io.AddMouseButtonEvent(button, event.type == SDL_EVENT_MOUSE_BUTTON_DOWN);
        }
        if (OverlayTrace()) {
            std::printf("Overlay trace: SDL button %d %s at %.0f,%.0f (mouse id %u, clicks %d)\n",
                        int(event.button.button), event.type == SDL_EVENT_MOUSE_BUTTON_DOWN ? "down" : "up",
                        event.button.x, event.button.y, unsigned(event.button.which), int(event.button.clicks));
        }
        return true;
    }
    case SDL_EVENT_MOUSE_WHEEL:
        if (!is_open) {
            return false;
        }
        io.AddMouseWheelEvent(event.wheel.x, event.wheel.y);
        return true;
    default:
        return false;
    }
}

void SetBanner(const char* text) {
    {
        std::scoped_lock lock{banner_mutex};
        banner_text = text ? text : "";
    }
    banner_active = text != nullptr && text[0] != 0;
}

void ShowTrophy(char grade, const std::string& name, const std::filesystem::path& icon, float delay) {
    std::scoped_lock lock{trophy_mutex};
    trophy_queue.push_back({grade, name, -delay, icon});
    trophy_active = true;
}

void TrophyNotice(int id, char grade, std::string name, std::vector<u8> icon, int icon_size) {
    if (icon.size() != size_t(icon_size) * size_t(icon_size) * 4) {
        icon.clear();
        icon_size = 0;
    }
    std::scoped_lock lock{notice_mutex};
    notices.push_back(Notice{id, grade, std::move(name), std::move(icon), icon_size});
    notice_busy = true;
}

bool Visible() {
    // BB_OVERLAY_OPEN=1 (tests): the menu open from the start, its sections unfolded.
    static bool open_at_start = bb_env_on("BB_OVERLAY_OPEN");
    if (open_at_start && initialized) {
        open_at_start = false;
        open_requested = true;
    }
    if (const long long since = l3r3_since.load();
        since != 0 && !menu_open && NowNs() - since >= OpenHoldMs() * 1'000'000) {
        l3r3_since = 0;
        open_requested = true;
    }
    const bool shader_progress = ShaderProgressShown();
    return initialized && (menu_open || open_requested || prompt_active || banner_active ||
                           trophy_active || notice_busy || BbSettings::Get().show_fps || shader_progress ||
                           (AtlasOn() && (BbMap::IsOpen() || BbAtlasMenu::Visible())));
}

uint32_t RoutePad(uint32_t buttons, uint8_t lx, uint8_t ly, uint8_t rx, uint8_t ry) {
    if (!AtlasOn()) {
        return buttons;
    }
    std::scoped_lock lock{imgui_mutex};
    if (!initialized || menu_open || prompt_active) {
        return buttons;
    }
    return BbAtlasMenu::RoutePad(buttons, lx, ly, rx, ry);
}

bool MenuOpen() {
    // bbport (Linux fork): also while Hunter's Atlas's map or its quick-menu tile uses the pointer
    // (main's ReleasesMouse): the window lets the mouse go and shows the system cursor.
    return menu_open || (AtlasOn() && initialized && BbAtlasMenu::Interacting());
}

bool TextPromptOpen() {
    return prompt_active.load(std::memory_order_relaxed);
}

bool CapturesInput() {
    // The text dialog too: keys typed into it (Backspace is the touchpad) stay out of the game.
    // Hunter's Atlas: its open map and its controller shortcut while it is being held.
    return menu_open || prompt_active || (AtlasOn() && BbMap::CapturesInput());
}

void Render(vk::CommandBuffer cmdbuf, vk::ImageView view, vk::Extent2D extent) {

    // Present interval for the FPS readout (measured also while nothing is drawn).
    const auto now = std::chrono::steady_clock::now();
    const float ms = std::chrono::duration<float, std::milli>(now - last_present).count();
    last_present = now;
    if (ms > 0.0f && ms < 1000.0f) {
        frame_ms_avg = frame_ms_avg == 0.0f ? ms : frame_ms_avg * 0.95f + ms * 0.05f;
    }
    // BB_FPS_PRINT=1: the present rate every 5 s on stdout, without the cost of BB_FRAME_STATS
    // (its timers are in the draw path): to measure as players run the game.
    static const bool fps_print = bb_env_on("BB_FPS_PRINT");
    if (fps_print) {
        static auto window_start = now;
        static std::uint64_t presents = 0;
        ++presents;
        if (const double s = std::chrono::duration<double>(now - window_start).count(); s >= 5.0) {
            std::printf("Present rate: %.1f FPS over %.1f s\n", presents / s, s);
            std::fflush(stdout);
            window_start = now;
            presents = 0;
        }
    }
    if (bb_env("BB_MENU_KEYS_FILE") && initialized) {
        std::scoped_lock lock{imgui_mutex};
        ScriptedKeys();
    }
    // Hunter's Atlas follows every presented frame, also while nothing is drawn.
    if (AtlasOn() && initialized) {
        std::scoped_lock lock{imgui_mutex};
        BbMap::PollTestCommands();
        BbMap::Tick();
        BbAtlasMenu::Suppress(menu_open || prompt_active);
        BbAtlasMenu::Tick();
    }
    if (!Visible()) {
        return;
    }
    std::scoped_lock lock{imgui_mutex};
    if (open_requested.exchange(false)) {
        SetOpen(true);
    }
    ImGuiIO& io = ImGui::GetIO();
    io.DisplaySize =ImVec2(float(extent.width), float(extent.height));
    display_width.store(extent.width, std::memory_order_relaxed);
    display_height.store(extent.height, std::memory_order_relaxed);
    io.DeltaTime = ms > 0.0f && ms < 1000.0f ? ms / 1000.0f : 1.0f / 60.0f;
    // UI scale follows the display height (1080p = 1).
    const float scale = std::max(float(extent.height) / 1080.0f, 0.75f);
    if (std::abs(scale - base_scale) > 0.01f) {
        ImGuiStyle& style = ImGui::GetStyle();
        style.ScaleAllSizes(scale / base_scale);
        style.FontScaleMain = scale;
        base_scale = scale;
    }

    static bool cjk_font_tried = false;
    // Also when the menu opens in another language: its language list names Chinese in Chinese.
    if (!cjk_font_tried &&
        (menu_open || BbSettings::Get().menu_language == BbSettings::MenuLanguage::ChineseSimplified)) {
        cjk_font_tried = true;
        LoadCjkFont();
    }
    ImGui_ImplVulkan_NewFrame();
    ImGui::NewFrame();
    if (OverlayTrace() && menu_open && (io.MouseClicked[0] || io.MouseReleased[0])) {
        const ImGuiContext& g = *ImGui::GetCurrentContext();
        std::printf("Overlay trace: ImGui left %s at %.0f,%.0f, display %.0fx%.0f, hovered id %#x, active id %#x\n",
                    io.MouseClicked[0] ? "clicked" : "released", io.MousePos.x, io.MousePos.y,
                    io.DisplaySize.x, io.DisplaySize.y, unsigned(g.HoveredIdPreviousFrame), unsigned(g.ActiveId));
    }
    if (menu_open) {
        Menu();
        if (AtlasOn() && BbMap::IsOpen()) {
            SetOpen(false);
        }
    }
    const bool map_open = AtlasOn() && BbMap::IsOpen();
    if (map_open) {
        BbMap::Draw();
    }
    if (AtlasOn() && !menu_open && !prompt_active && !map_open) {
        BbAtlasMenu::Draw();
    }
    if (BbSettings::Get().show_fps && !menu_open && !map_open) {
        FpsCounter();
    }
    if (prompt_active && !menu_open) {
        TextPrompt();
    }
    if (notice_busy) {
        TrophyCard();
    }
    if (!menu_open) {
        ShaderProgressLine();
    }
    if (trophy_active) {
        TrophyWindow(io.DeltaTime);
    }
    if (banner_active) {
        std::string text;
        {
            std::scoped_lock banner_lock{banner_mutex};
            text = banner_text;
        }
        const ImVec2 size = ImGui::CalcTextSize(text.c_str());
        auto* draw = ImGui::GetForegroundDrawList();
        const ImVec2 at{(io.DisplaySize.x - size.x) * 0.5f, io.DisplaySize.y * 0.82f};
        draw->AddRectFilled({at.x - 24.0f, at.y - 12.0f}, {at.x + size.x + 24.0f, at.y + size.y + 12.0f},
                            IM_COL32(0, 0, 0, 170), 6.0f);
        draw->AddText(at, IM_COL32(230, 220, 200, 255), text.c_str());
    }
    ImGui::Render();

    const vk::RenderingAttachmentInfo attachment{
        .imageView = view,
        .imageLayout = vk::ImageLayout::eColorAttachmentOptimal,
        .loadOp = vk::AttachmentLoadOp::eLoad,
        .storeOp = vk::AttachmentStoreOp::eStore,
    };
    cmdbuf.beginRendering(vk::RenderingInfo{
        .renderArea = {{0, 0}, extent},
        .layerCount = 1,
        .colorAttachmentCount = 1,
        .pColorAttachments = &attachment,
    });
    {
        // Font atlas uploads submit to the graphics queue themselves.
        std::scoped_lock submit_lock{Vulkan::Scheduler::submit_mutex};
        ImGui_ImplVulkan_RenderDrawData(ImGui::GetDrawData(), cmdbuf);
    }
    cmdbuf.endRendering();
}

} // namespace BbOverlay

extern "C" void bbgpu_overlay_banner(const char* text) {
    BbOverlay::SetBanner(text);
}
