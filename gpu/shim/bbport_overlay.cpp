// SPDX-License-Identifier: GPL-2.0-or-later
#include "bbport_overlay.h"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cfloat>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <mutex>
#include <string>
#include <string_view>
#include <unordered_map>
#include <utility>
#include <vector>

#include <SDL3/SDL.h>
#include "bbport_settings.h"
#include "bbport_shader_activity.h"
#include "imgui.h"
#include "imgui_impl_vulkan.h"
#include "imgui_internal.h" // RegisterUserTexture: the trophies' icons
#include "video_core/renderer_vulkan/vk_instance.h"
#include "video_core/renderer_vulkan/vk_scheduler.h"

// DejaVu Sans (Cyrillic), embedded (third_party/fonts, Bitstream Vera license).
asm(".section .rodata\n"
    ".balign 16\n"
    ".hidden bb_font_ttf\n"
    ".global bb_font_ttf\n"
    "bb_font_ttf:\n"
    ".incbin \"" BB_FONT_PATH "\"\n"
    ".hidden bb_font_ttf_end\n"
    ".global bb_font_ttf_end\n"
    "bb_font_ttf_end:\n"
    ".previous\n");
extern "C" const unsigned char bb_font_ttf[];
extern "C" const unsigned char bb_font_ttf_end[];

extern "C" void runtime_restart(void); // bb-probe (probe.c)

namespace BbOverlay {

namespace {

std::mutex imgui_mutex; // the ImGui context: window thread (input) and present thread
bool initialized = false;
std::atomic<bool> menu_open{false};
bool l3_down = false, r3_down = false;
bool dirty = false; // settings changed while open: saved on close
float base_scale = 1.0f;
// The game's text dialog (ImeDialog, the character name), typed on the keyboard: drawn while it
// is open. In fullscreen the window title that showed it is not visible (issues #17, #19).
std::mutex prompt_mutex;
std::atomic<bool> prompt_active{false};
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

// Present rate for the FPS counter.
std::chrono::steady_clock::time_point last_present{};
float frame_ms_avg = 0.0f;

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

float PixelDensity(SDL_WindowID id);

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
            const float density = PixelDensity(SDL_GetWindowID(window));
            ImGui::GetIO().AddMousePosEvent(x * density, y * density);
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

// Marks the settings dirty when a widget changed them.
template <typename T>
void Store(std::atomic<T>& target, T value, bool changed) {
    if (changed) {
        target = value;
        dirty = true;
    }
}

void Checkbox(const char* label, std::atomic<bool>& value) {
    bool v = value;
    const bool changed = ImGui::Checkbox(label, &v);
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
    // height stays within the screen below where it opens, and the contents scroll.
    ImGui::SetNextWindowSizeConstraints(
        ImVec2(0.0f, 0.0f),
        ImVec2(FLT_MAX, std::max(viewport->WorkPos.y + viewport->WorkSize.y - pos.y - 20.0f * base_scale,
                                 200.0f * base_scale)));
    bool keep_open = true;
    if (!ImGui::Begin(
            BbSettings::MenuText("Bloodborne - Graphics  (Insert / L3+R3)###bbport_settings",
                                 "Bloodborne — настройки  (Insert / L3+R3)###bbport_settings"),
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
    // Always readable, even when the rest of the menu is in Russian.
    int language = int(s.menu_language.load());
    if (ImGui::Combo("Language", &language, BbSettings::MenuLanguageNames,
                     int(BbSettings::MenuLanguage::Count))) {
        s.menu_language = BbSettings::MenuLanguage(language);
        BbSettings::Save();
    }
    ImGui::Text(BbSettings::MenuText("%.0f FPS  (%.1f ms)", "%.0f FPS  (%.1f мс)"),
                frame_ms_avg > 0.0f ? 1000.0f / frame_ms_avg : 0.0f, frame_ms_avg);

    ImGui::SeparatorText(BbSettings::MenuText("Temporal upscaler", "Временной апскейлер"));
    const char* upscalers[] = {
        BbSettings::MenuText("Off", "Выкл"), "FSR 3.1", "FSR 4 (INT8)", "FSR 4.1.1",
        BbSettings::MenuText("TAA (native anti-aliasing)", "TAA (нативное сглаживание)"),
        "DLSS (NVIDIA RTX)"};
    static_assert(sizeof(upscalers) / sizeof(upscalers[0]) == BbSettings::UpscalerCount);
    static const char* later[] = {"XeSS"};
    int upscaler = s.upscaler;
    if (ImGui::BeginCombo(BbSettings::MenuText("Upscaler", "Апскейлер"), upscalers[upscaler])) {
        for (int i = 0; i < BbSettings::UpscalerCount; ++i) {
            const bool supported = i == BbSettings::UpscalerFsr4     ? s.fsr4_supported.load()
                                   : i == BbSettings::UpscalerFsr411 ? s.fsr411_supported.load()
                                   : i == BbSettings::UpscalerDlss   ? s.dlss_supported.load()
                                                                     : true;
            ImGui::BeginDisabled(!supported);
            if (ImGui::Selectable(upscalers[i], i == upscaler)) {
                Store(s.upscaler, i, true);
            }
            ImGui::EndDisabled();
            if (!supported) {
                ImGui::SameLine();
                ImGui::TextDisabled("%s", BbSettings::MenuText("— not supported by this GPU",
                                                         "— не поддерживается видеокартой"));
            }
        }
        for (const char* name : later) {
            ImGui::BeginDisabled();
            ImGui::Selectable(name, false);
            ImGui::EndDisabled();
            ImGui::SameLine();
            ImGui::TextDisabled("%s", BbSettings::MenuText("— in development", "— в работе"));
        }
        ImGui::EndCombo();
    }
    if (s.upscaler == BbSettings::UpscalerDlss) {
        Hint(BbSettings::MenuText(
            "NVIDIA DLSS Super Resolution (RTX GPUs; Native AA is DLAA). Needs the DLSS bridge "
            "and NVIDIA's library next to the game; otherwise FSR 3.1 is used.",
            "NVIDIA DLSS Super Resolution (видеокарты RTX; Native AA — это DLAA). Нужны мост DLSS "
            "и библиотека NVIDIA рядом с игрой; без них используется FSR 3.1."));
    }
    const auto problem_text = [](const char* text) {
        ImGui::PushTextWrapPos();
        ImGui::TextColored(ImVec4(1.0f, 0.5f, 0.3f, 1.0f), "%s", text);
        ImGui::PopTextWrapPos();
    };
    if (const char* problem = s.dlss_problem.load(); problem && s.upscaler == BbSettings::UpscalerDlss) {
        char line[192];
        std::snprintf(line, sizeof(line), "DLSS: %s", problem);
        problem_text(line);
    }
    if (const char* problem = s.fsr4_problem.load()) {
        char line[192];
        std::snprintf(line, sizeof(line),
                      BbSettings::MenuText("FSR 4 unavailable: %s", "FSR 4 недоступен: %s"), problem);
        problem_text(line);
        if (!BbSettings::IsFsr4(s.upscaler)) {
            ImGui::PushTextWrapPos();
            ImGui::TextUnformatted(BbSettings::MenuText(
                "The mode selected above is active. You can select FSR 4 again.",
                "Активен режим, выбранный выше. FSR 4 можно выбрать снова."));
            ImGui::PopTextWrapPos();
        }
    }
    if (BbSettings::IsFsr4(s.upscaler)) {
        if (s.upscaler == BbSettings::UpscalerFsr411) {
            Hint(BbSettings::MenuText(
                "FSR 4.1.1: the model from AMD's 4.1.1 DLL, reproduced in Vulkan (output matches "
                "the DLL). Assets are built from your DLL in the launcher.",
                "FSR 4.1.1: модель из DLL AMD 4.1.1, воспроизведённая в Vulkan (результат совпадает "
                "с DLL). Ассеты собираются из вашей DLL в лаунчере."));
        } else {
            Hint(BbSettings::MenuText(
                "FSR 4 in INT8 mode (v07 model from AMD FidelityFX SDK sources). Higher quality "
                "than FSR 3.1, but the pass is more demanding. Changing the preset rebuilds the "
                "model (a brief pause).",
                "FSR 4 в режиме INT8 (модель v07 из исходников AMD FidelityFX SDK). Качество выше, "
                "чем у FSR 3.1, но проход тяжелее. Смена пресета пересобирает модель (короткая "
                "пауза)."));
        }
        Checkbox(BbSettings::MenuText("FSR 4: auto exposure", "FSR 4: авто-экспозиция"),
                 s.fsr4_auto_exposure);
        Checkbox(BbSettings::MenuText("FSR 4: invert jitter sign", "FSR 4: обратный знак jitter"),
                 s.fsr4_invert_jitter);
        Hint(BbSettings::MenuText(
            "For diagnosing ghosting: the FSR 4 network normalizes color by exposure and uses "
            "it to decide when to discard previous frames. Changes apply immediately, without a "
            "restart.",
            "Проверка при гостинге: сеть FSR 4 нормирует цвет по экспозиции и по ней решает, "
            "когда отбросить прошлые кадры. Меняются сразу, без перезапуска."));
    }
    const bool upscaler_on = s.upscaler != BbSettings::UpscalerOff;
    const bool taa = s.upscaler == BbSettings::UpscalerTaa;
    ImGui::BeginDisabled(!upscaler_on);
    ImGui::BeginDisabled(taa);
    int preset = taa ? BbSettings::NativeAA : s.preset.load();
    char preset_label[64];
    std::snprintf(preset_label, sizeof(preset_label), "%s (x%.1f)", BbSettings::PresetName(preset),
                  BbSettings::PresetScale(preset));
    if (ImGui::BeginCombo(BbSettings::MenuText("Preset", "Пресет"), preset_label)) {
        for (int i = 0; i < BbSettings::PresetCount; ++i) {
            char label[64];
            const float scale = BbSettings::PresetScale(i);
            const int output = s.output_res;
            std::snprintf(
                label, sizeof(label),
                BbSettings::MenuText("%s (x%.1f, render %dx%d)", "%s (x%.1f, рендер %dx%d)"),
                BbSettings::PresetName(i), scale,
                int(std::lround(BbSettings::OutputWidths[output] / scale / 2) * 2),
                int(std::lround(BbSettings::OutputHeights[output] / scale / 2) * 2));
            if (ImGui::Selectable(label, i == preset)) {
                Store(s.preset, i, true);
            }
        }
        ImGui::EndCombo();
    }
    ImGui::EndDisabled();
    if (taa) {
        ImGui::TextWrapped("%s", BbSettings::MenuText(
            "TAA anti-aliases the scene at output resolution, without an FSR model or upscaling. "
            "Your saved FSR preset is restored when you select FSR.",
            "TAA сглаживает сцену в разрешении вывода, без модели FSR и апскейлинга. "
            "Сохранённый пресет FSR восстановится при выборе FSR."));
    }
    ImGui::Text(
        BbSettings::MenuText("Active scene render: %d x %d", "Активный рендер сцены: %d x %d"),
        s.active_render_width.load(), s.active_render_height.load());
    if (BbSettings::FixedRenderSession()) {
        ImGui::Text(BbSettings::MenuText("Startup preset: %s", "Пресет при запуске: %s"),
                    BbSettings::PresetName(s.startup_preset));
        if (const char* automatic = std::getenv("BB_AUTO_RENDER_RES");
            automatic && automatic[0] == '1') {
            Hint(BbSettings::MenuText(
                "When output is not 1080p, the entire game renders at the preset resolution "
                "(startup patch): this is fastest on Steam Deck and weaker GPUs. Preset or output "
                "resolution changes require a restart. Enable Live resolution changes below to "
                "change them without restarting (post-processing then stays at 1080p, which is "
                "slower).",
                "При выводе не 1080p вся игра рисуется в разрешении пресета (патч при запуске): "
                "это быстрее всего на Steam Deck и слабых GPU. Смена пресета или разрешения "
                "вывода — после перезапуска. Пункт «Смена разрешения на лету» ниже включает "
                "смену без перезапуска (постобработка тогда остаётся в 1080p, медленнее)."));
        } else {
            Hint(BbSettings::MenuText(
                "BB_RENDER_RES fixes the scene size at startup. Remove this explicit environment "
                "variable to change resolution and presets without restarting the game.",
                "BB_RENDER_RES фиксирует размер сцены при запуске. Уберите эту явную переменную "
                "для смены разрешения и пресетов без перезапуска игры."));
        }
    } else {
        Hint(BbSettings::MenuText(
            "Native AA: the upscaler acts as anti-aliasing. Other presets reduce the scene render "
            "resolution relative to the output. The UI renders at output resolution. "
            "The preset applies from the next frame without restarting the game.",
            "Native AA: апскейлер работает как сглаживание. Остальные пресеты уменьшают разрешение "
            "отрисовки сцены относительно вывода. Интерфейс рисуется в разрешении вывода. "
            "Пресет применяется со следующего кадра без перезапуска игры."));
    }
    Checkbox(BbSettings::MenuText("Sharpening (RCAS)", "Резкость (RCAS)"), s.sharpen);
    ImGui::BeginDisabled(!s.sharpen);
    Slider(BbSettings::MenuText("Sharpness", "Сила резкости"), s.sharpness, 0.0f, 2.0f);
    Hint(BbSettings::MenuText(
        "Up to 1: the upscaler's own sharpening (RCAS). Above 1 adds another RCAS pass. "
        "Ctrl+click the slider to enter an exact value.",
        "До 1 — резкость самого апскейлера (RCAS). Выше 1 добавляется ещё один проход RCAS. "
        "Ctrl+клик по ползунку — ввести точное значение."));
    ImGui::EndDisabled();
    Checkbox(BbSettings::MenuText("Subpixel jitter", "Субпиксельный сдвиг (jitter)"), s.jitter);
    Hint(BbSettings::MenuText(
        "Each frame shifts the scene by a fraction of a pixel, letting the upscaler reconstruct "
        "more detail from multiple frames. Without it, only history-based anti-aliasing remains.",
        "Каждый кадр сцена сдвигается на долю пикселя, и апскейлер собирает из нескольких "
        "кадров больше деталей. Без него получается только сглаживание по истории."));

    ImGui::SeparatorText(BbSettings::MenuText("Reactive mask", "Маска реактивности"));
    ImGui::BeginDisabled(taa);
    Checkbox(BbSettings::MenuText("Enable mask", "Включить маску"), s.reactive);
    Hint(BbSettings::IsFsr4(s.upscaler)
             ? BbSettings::MenuText(
                   "Marks transparent effects (haze, light, water, particles). FSR 4 takes no "
                   "mask itself: its output is blended with the current frame there, so the "
                   "effects do not drag previous frames along.",
                   "Помечает прозрачные эффекты (дымку, свет, воду, частицы). FSR 4 сам маску не "
                   "принимает: там его результат смешивается с текущим кадром, и эффекты не "
                   "тянут за собой прошлые кадры.")
             : BbSettings::MenuText(
                   "Marks transparent effects (particles, haze) so the upscaler relies less on "
                   "previous frames. Reduces trails behind effects, but shimmering returns "
                   "underneath them.",
                   "Помечает прозрачные эффекты (частицы, дымку), чтобы апскейлер меньше "
                   "опирался на прошлые кадры. Меньше шлейфов за эффектами, но под ними "
                   "возвращается дрожание."));
    ImGui::BeginDisabled(!s.reactive);
    Slider(BbSettings::MenuText("Scale", "Масштаб"), s.reactive_scale, 0.0f, 4.0f);
    Slider(BbSettings::MenuText("Threshold", "Порог"), s.reactive_threshold, 0.0f, 1.0f);
    Slider(BbSettings::MenuText("Maximum", "Максимум"), s.reactive_max, 0.0f, 1.0f);
    bool show_mask = s.debug_view == BbSettings::DebugReactive;
    if (ImGui::Checkbox(BbSettings::MenuText("Show mask (debug)", "Показать маску (отладка)"),
                        &show_mask)) {
        s.debug_view = show_mask ? BbSettings::DebugReactive : BbSettings::DebugNone;
    }
    ImGui::EndDisabled();
    ImGui::EndDisabled();
    Checkbox(BbSettings::MenuText("Character motion vectors", "Векторы движения персонажей"),
             s.object_motion);
    Hint(BbSettings::MenuText(
        "Accurate vectors for animated objects: clothing and weapons break up less "
        "during movement. The static scene does not get an additional pass. "
        "Changes apply after restarting the game.",
        "Точные векторы для анимированных объектов: одежда и оружие меньше рассыпаются "
        "при движении. Статичная сцена не получает дополнительный проход. "
        "Изменение применяется после перезапуска игры."));
    bool show_motion = s.debug_view == BbSettings::DebugMotion;
    if (ImGui::Checkbox(BbSettings::MenuText("Show motion vectors (debug)",
                                             "Показать векторы движения (отладка)"),
                        &show_motion)) {
        s.debug_view = show_motion ? BbSettings::DebugMotion : BbSettings::DebugNone;
    }
    Hint(BbSettings::MenuText(
        "Red/green: horizontal/vertical motion (8 pixels = full brightness). "
        "Blue: the pixel received an accurate object vector, not just camera motion. "
        "The upscaler treats a moving object with no blue or red/green as "
        "stationary, causing trails.",
        "Красный/зелёный: движение по горизонтали/вертикали (8 пикселей = полная яркость). "
        "Синий: пиксель получил точный вектор объекта, а не только движение камеры. "
        "Движущийся предмет без синего и без красного/зелёного апскейлер считает "
        "неподвижным, отсюда шлейф."));
    ImGui::EndDisabled(); // upscaler off

    ImGui::SeparatorText(BbSettings::MenuText("Output resolution", "Разрешение вывода"));
    static const char* outputs[] = {"1280 x 720", "1920 x 1080", "2560 x 1440", "3840 x 2160"};
    int output = s.output_res;
    if (ImGui::BeginCombo(BbSettings::MenuText("Output resolution", "Разрешение вывода"),
                          outputs[output])) {
        for (int i = 0; i < BbSettings::OutputCount; ++i) {
            if (ImGui::Selectable(outputs[i], i == output)) {
                Store(s.output_res, i, true);
            }
        }
        ImGui::EndCombo();
    }
    if (BbSettings::FixedRenderSession()) {
        Hint(BbSettings::MenuText(
            "Size of the final frame and UI. The preset sets the scene size relative to "
            "the output: 4K Performance = 1920x1080. Applies after restarting the game.",
            "Размер готового кадра и интерфейса. Пресет задаёт размер сцены относительно "
            "вывода: 4K Performance = 1920x1080. Применяется после перезапуска игры."));
    } else {
        Hint(BbSettings::MenuText(
            "The final frame and UI size changes at the next frame boundary. "
            "The preset sets the scene size relative to the output: 4K Performance = 1920x1080. "
            "Changing the size resets the upscaler's history and may cause a brief pause.",
            "Размер готового кадра и интерфейса меняется на границе следующего кадра. "
            "Пресет задаёт размер сцены относительно вывода: 4K Performance = 1920x1080. "
            "Смена размера сбрасывает историю апскейлера и может вызвать короткую паузу."));
    }
    const char* live_modes[] = {BbSettings::MenuText("Auto (based on GPU)", "Авто (по видеокарте)"),
                                BbSettings::MenuText("Off (faster)", "Выключена (быстрее)"),
                                BbSettings::MenuText("On", "Включена")};
    int live = s.live_resolution + 1;
    if (ImGui::BeginCombo(
            BbSettings::MenuText("Live resolution changes", "Смена разрешения на лету"),
            live_modes[live])) {
        for (int i = 0; i < 3; ++i) {
            if (ImGui::Selectable(live_modes[i], i == live)) {
                Store(s.live_resolution, i - 1, true);
            }
        }
        ImGui::EndCombo();
    }
    Hint(BbSettings::MenuText(
        "On: output resolution and preset change without restarting, but game post-processing "
        "stays at 1080p, which is noticeably slower on Steam Deck and older GPUs. "
        "Off: everything renders at the preset resolution, and changes require a restart. Auto "
        "enables this on powerful discrete GPUs. Applies after restarting the game.",
        "Включена: разрешение вывода и пресет меняются без перезапуска, но постобработка игры "
        "остаётся в 1080p — на Steam Deck и старых видеокартах это заметно медленнее. "
        "Выключена: всё рисуется в разрешении пресета, смена — через перезапуск. Авто включает "
        "её на мощных дискретных видеокартах. Применяется после перезапуска игры."));
    ImGui::SeparatorText(BbSettings::MenuText("Game effects (restart required)",
                                              "Эффекты игры (после перезапуска)"));
    const char* lods[] = {BbSettings::MenuText("Highest (-2)", "Максимальная (-2)"),
                          BbSettings::MenuText("Game default", "Как в игре"),
                          BbSettings::MenuText("Lower (1)", "Ниже (1)"),
                          BbSettings::MenuText("Lowest (2)", "Минимальная (2)")};
    static constexpr int lod_values[] = {-2, 0, 1, 2};
    int lod_index = 1;
    for (int i = 0; i < 4; ++i) {
        if (lod_values[i] == s.model_lod) lod_index = i;
    }
    if (ImGui::BeginCombo(BbSettings::MenuText("Model detail", "Детализация моделей"),
                          lods[lod_index])) {
        for (int i = 0; i < 4; ++i) {
            if (ImGui::Selectable(lods[i], i == lod_index)) {
                Store(s.model_lod, lod_values[i], true);
            }
        }
        ImGui::EndCombo();
    }
    for (int e = 0; e < BbSettings::EffectCount; ++e) {
        const auto& effect = BbSettings::Effects[e];
        Checkbox(BbSettings::MenuText(effect.label, effect.label_ru), s.effects[e]);
        if (std::string_view(effect.key) == "debug_camera") {
            Hint(BbSettings::MenuText("Hold Cross and press L3 (keyboard: Space + Z).",
                                      "Удерживайте Cross и нажмите L3 (клавиатура: Space + Z)."));
        } else if (std::string_view(effect.key) == "debug_menu") {
            Hint(BbSettings::MenuText(
                "Left side of the touchpad (Tab); right side: Backspace. Needs the adhoc folder "
                "from Nexus mod #253 (the fonts in adhoc/font).",
                "Левая сторона тачпада (Tab), правая — Backspace. Нужна папка adhoc из мода "
                "Nexus #253 (шрифты в adhoc/font)."));
        }
    }
    Hint(BbSettings::MenuText(
        "Effects are enabled and disabled by game patches at startup (patches/Bloodborne.xml). "
        "Motion blur and shadows from dynamic lights place a significant load on the GPU.",
        "Эффекты включаются и выключаются патчами игры при запуске (patches/Bloodborne.xml). "
        "Размытие в движении и тени от динамических источников заметно нагружают GPU."));

    bool restart =
        s.object_motion != s.startup_object_motion || s.model_lod != s.startup_model_lod ||
        s.live_resolution != s.startup_live_resolution || BbSettings::ResolutionNeedsRestart();
    for (int e = 0; e < BbSettings::EffectCount; ++e) {
        restart |= s.effects[e] != s.startup_effects[e];
    }
    if (restart) {
        ImGui::TextColored(ImVec4(1.0f, 0.75f, 0.3f, 1.0f), "%s",
                           BbSettings::MenuText("Changes apply after restarting the game",
                                                "Изменения применятся после перезапуска игры"));
        if (ImGui::Button(
                BbSettings::MenuText("Apply and restart game", "Применить и перезапустить игру"))) {
            BbSettings::Save();
            runtime_restart();
        }
    }

    ImGui::SeparatorText(BbSettings::MenuText("Other", "Прочее"));
    Checkbox(BbSettings::MenuText("FPS counter in corner", "Счётчик FPS в углу"), s.show_fps);
    Checkbox(BbSettings::MenuText("Notice while shaders compile", "Уведомление о компиляции шейдеров"),
             s.shader_notice);
    Hint(BbSettings::MenuText(
        "\"Compiling shaders\" in the bottom-left corner: a stutter then is the shader cache "
        "filling, not a problem. Each place only once.",
        "«Компиляция шейдеров» в левом нижнем углу: рывок в это время — заполнение кэша "
        "шейдеров, а не проблема. В каждом месте только один раз."));
    Checkbox(BbSettings::MenuText("Sound when a trophy is earned", "Звук при получении трофея"),
             s.trophy_sound);

    ImGui::Spacing();
    if (ImGui::Button(BbSettings::MenuText("Close", "Закрыть"))) {
        keep_open = false;
    }
    // Issues #74, #116: leaving the game from the pad (this menu opens with L3+R3). A second
    // press confirms; the window thread then closes like the window's own close button.
    // One ID for both labels ("###bb_quit"): with a new ID the button lost the pad's or keyboard's
    // focus at the first press, which disarmed it at once.
    static bool quit_armed;
    ImGui::SameLine();
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
    ImGui::Text(BbSettings::MenuText("%.0f FPS  %.1f ms  %s", "%.0f FPS  %.1f мс  %s"),
                frame_ms_avg > 0.0f ? 1000.0f / frame_ms_avg : 0.0f, frame_ms_avg,
                s.upscaler == BbSettings::UpscalerFsr3     ? "FSR 3.1"
                : s.upscaler == BbSettings::UpscalerFsr4   ? "FSR 4"
                : s.upscaler == BbSettings::UpscalerFsr411 ? "FSR 4.1.1"
                : s.upscaler == BbSettings::UpscalerTaa    ? "TAA"
                : s.upscaler == BbSettings::UpscalerDlss   ? "DLSS"
                                                           : "");
    ImGui::End();
}

// The shader notice: shown while compiling and 400 ms after, then fading out over 400 ms.
constexpr std::int64_t ShaderNoticeHoldMs = 400, ShaderNoticeFadeMs = 400;

bool ShaderNoticeDue() {
    const std::int64_t idle = BbShaderActivity::IdleMs();
    return BbSettings::Get().shader_notice && idle >= 0 &&
           idle < ShaderNoticeHoldMs + ShaderNoticeFadeMs;
}

void ShaderNotice() {
    const std::int64_t idle = BbShaderActivity::IdleMs();
    const float alpha =
        idle <= ShaderNoticeHoldMs ? 1.0f
                                   : 1.0f - float(idle - ShaderNoticeHoldMs) / ShaderNoticeFadeMs;
    const ImGuiViewport* viewport = ImGui::GetMainViewport();
    const float pad = 12.0f * base_scale;
    ImGui::SetNextWindowPos(
        ImVec2(viewport->WorkPos.x + pad, viewport->WorkPos.y + viewport->WorkSize.y - pad),
        ImGuiCond_Always, ImVec2(0.0f, 1.0f));
    ImGui::SetNextWindowBgAlpha(0.5f * alpha);
    ImGui::PushStyleVar(ImGuiStyleVar_Alpha, alpha);
    ImGui::Begin("##shaders", nullptr,
                 ImGuiWindowFlags_NoDecoration | ImGuiWindowFlags_AlwaysAutoResize |
                     ImGuiWindowFlags_NoInputs | ImGuiWindowFlags_NoNav |
                     ImGuiWindowFlags_NoFocusOnAppearing);
    ImGui::TextUnformatted(BbSettings::MenuText("Compiling shaders…", "Компиляция шейдеров…"));
    ImGui::End();
    ImGui::PopStyleVar();
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
        const char* mode = std::getenv("BB_AUDIO");
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
    static const char* path = std::getenv("BB_MENU_KEYS_FILE");
    static std::chrono::steady_clock::time_point last_check{};
    static std::vector<std::string> queue;
    static bool release = false;
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

// bbport: the menu's own font has no Chinese characters. The first time the menu opens or speaks
// Simplified Chinese, a system font for it is merged into that font: BB_CJK_FONT (a file), else
// fontconfig's choice for zh-cn (Noto Sans CJK, WenQuanYi...). ImGui 1.92 rasterizes glyphs as
// they are drawn, so the font costs memory for its file, not a texture of every character.
// Without such a font the Chinese texts show as boxes, and the log says why.
void LoadCjkFont() {
    std::string path;
    int index = 0;
    if (const char* file = std::getenv("BB_CJK_FONT"); file && *file) {
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
    std::printf("Overlay: menu ready (Insert or L3+R3)\n");
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
    const bool is_open = menu_open;
    switch (event.type) {
    case SDL_EVENT_KEY_DOWN:
    case SDL_EVENT_KEY_UP: {
        const bool down = event.type == SDL_EVENT_KEY_DOWN;
        if (down && !event.key.repeat &&
            (event.key.key == SDLK_INSERT || (is_open && event.key.key == SDLK_ESCAPE))) {
            SetOpen(event.key.key == SDLK_INSERT ? !is_open : false);
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
        if (down && l3_down && r3_down) {
            SetOpen(!is_open);
            return true;
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
        const float density = PixelDensity(event.motion.windowID);
        io.AddMousePosEvent(event.motion.x * density, event.motion.y * density);
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

bool Visible() {
    return initialized && (menu_open || prompt_active || notice_busy || BbSettings::Get().show_fps ||
                           ShaderNoticeDue());
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

bool MenuOpen() {
    return menu_open;
}

bool CapturesInput() {
    // The text dialog too: keys typed into it (Backspace is the touchpad) stay out of the game.
    return menu_open || prompt_active;
}

void Render(vk::CommandBuffer cmdbuf, vk::ImageView view, vk::Extent2D extent) {

    // Present interval for the FPS readout (measured also while nothing is drawn).
    const auto now = std::chrono::steady_clock::now();
    const float ms = std::chrono::duration<float, std::milli>(now - last_present).count();
    last_present = now;
    if (ms > 0.0f && ms < 1000.0f) {
        frame_ms_avg = frame_ms_avg == 0.0f ? ms : frame_ms_avg * 0.95f + ms * 0.05f;
    }
    if (std::getenv("BB_MENU_KEYS_FILE") && initialized) {
        std::scoped_lock lock{imgui_mutex};
        ScriptedKeys();
    }
    if (!Visible()) {
        return;
    }
    std::scoped_lock lock{imgui_mutex};
    ImGuiIO& io = ImGui::GetIO();
    io.DisplaySize = ImVec2(float(extent.width), float(extent.height));
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
    if (menu_open) {
        Menu();
    }
    if (BbSettings::Get().show_fps && !menu_open) {
        FpsCounter();
    }
    if (!menu_open && ShaderNoticeDue()) {
        ShaderNotice();
    }
    if (prompt_active && !menu_open) {
        TextPrompt();
    }
    if (notice_busy) {
        TrophyCard();
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
