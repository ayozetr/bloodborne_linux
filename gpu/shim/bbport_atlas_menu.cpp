// SPDX-License-Identifier: GPL-2.0-or-later
#include "bbport_atlas_i18n.h" // bbport: the tile in the game's language
#include "bbport_atlas_menu.h"
#include "bbport_atlas_menu_state.h"
#include "bbport_map.h"
#include "bbport_map_art.h"
#include "../../src/runtime_map.h"
#include "../../src/runtime_menu_sound.h"
#include "imgui.h"
#include <SDL3/SDL.h>
#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>

namespace BbAtlasMenu {
namespace {
BbAtlasMenuState state;
std::atomic<bool> visible{false},focused{false},controller{false},suppressed{false};
std::atomic<float> fade{0}; // bbport: the tile fades in with the menu instead of appearing late
std::atomic<SDL_JoystickID> last_controller{0};
bool mouse_held=false,mouse_up_owned=false,hovered=false;
uint32_t map_previous=0;
uint64_t closing_since=0; // bbport: when Back closed the menu (it fades out, see Refresh)
bool closing_until_hidden=false; // bbport: a lamp travel: the tile stays hidden through the load
ImVec2 tile_min{},tile_max{};
BbMapMenu menu{};
bool Query() {
    BbMapLocation loc{};
    const bool state_ok=runtime_map_menu_state(&menu);
    const bool location_ok=runtime_map_location(&loc);
    // bbport: BB_ATLAS_DEBUG=1 logs why the tile is shown or not whenever that changes.
    static const bool debug=[]{const char* d=std::getenv("BB_ATLAS_DEBUG");return d&&d[0]=='1';}();
    if(debug){
        static int last=-1;
        const int now=(suppressed?1:0)|(BbMap::Enabled()?2:0)|(state_ok?4:0)|(menu.top_level?8:0)|(location_ok?16:0);
        if(now!=last){last=now;std::printf("Atlas debug: tile query suppressed=%d enabled=%d state=%d top=%d location=%d selected=%d\n",
            now&1,(now>>1)&1,(now>>2)&1,(now>>3)&1,(now>>4)&1,menu.selected);std::fflush(stdout);}
    }
    return !suppressed && BbMap::Enabled() && state_ok && menu.top_level && location_ok;
}
void Refresh() {
    // bbport: the tile shows as soon as the menu does and fades in over the settle time; input
    // still waits for it (Route).
    // The game stops reporting its menu a frame before the menu leaves the screen: the tile is
    // kept that long (as it was, without input) so that it does not vanish first.
    // Closed with Back, the game fades its menu out while still reporting it: the tile fades out
    // with it from the press (closing_since) instead of staying alone on the screen.
    static uint64_t last_shown=0;
    const uint64_t now=SDL_GetTicks();const bool shown=Query();
    state.Settled(shown,now);
    if(shown)last_shown=now;
    else {closing_since=0;closing_until_hidden=false;}
    // Back did not close the menu after all: the tile fades in again.
    if(closing_since&&!closing_until_hidden&&now-closing_since>600){closing_since=0;state.visible_since=now;}
    const bool lingering=!shown&&last_shown&&now-last_shown<50;
    const float out=closing_since?std::max(0.0f,1-float(now-closing_since)/150.0f):1.0f;
    visible=(shown||lingering)&&out>0&&!BbMap::IsOpen();focused=state.focused;
    if(shown)fade=std::min({1.0f,float(now-state.visible_since)/170.0f,out});
    else if(!lingering)fade=0.0f;
}
bool Hit(float x,float y){return x>=tile_min.x&&y>=tile_min.y&&x<tile_max.x&&y<tile_max.y;}
}
bool Visible(){return visible;}
// The load's black screen covers the game's menu at once: no fade-out, or it shows over the black.
void HideUntilMenuCloses(){closing_since=SDL_GetTicks()-1000;closing_until_hidden=true;visible=false;fade=0;}
bool Interacting(){return visible || BbMap::IsOpen() || runtime_map_menu_open();}
bool UsesControllerGlyphs(){const char* qa=std::getenv("BB_ATLAS_QA_DEVICE");return std::getenv("BB_ATLAS_QA")&&qa?std::strcmp(qa,"controller")==0:bool(controller);}
bool UsesPlayStationGlyphs(){const auto type=SDL_GetGamepadTypeForID(last_controller.load());return type==SDL_GAMEPAD_TYPE_PS3||type==SDL_GAMEPAD_TYPE_PS4||type==SDL_GAMEPAD_TYPE_PS5;}
bool Focused(){return focused;}
void Suppress(bool value){suppressed=value;if(value){visible=false;state.Reset();}}
void Reset(){state.Reset();focused=false;visible=false;hovered=false;mouse_held=false;map_previous=0;}
void Tick(){Refresh();if(BbMap::IsOpen()&&!runtime_map_menu_open()&&state.focused){BbMap::Close();Reset();}}
uint32_t RoutePad(uint32_t buttons,uint8_t lx,uint8_t ly,uint8_t rx,uint8_t ry) {
    const bool in_menu=Query();
    const bool was_open=BbMap::IsOpen();
    const uint32_t rising=buttons&~map_previous;
    auto result=state.Route(in_menu,menu.selected,was_open,buttons,runtime_map_confirm_button(),SDL_GetTicks());
    if(result.move)runtime_audio_menu_event(0);
    if(result.open){runtime_audio_menu_event(1);BbMap::OpenFromMenu();}
    const uint32_t back=runtime_map_confirm_button()==BbAtlasMenuState::Cross?BbAtlasMenuState::Circle:BbAtlasMenuState::Cross;
    // Only a Back pressed on the menu as it stands closes it: coming back from System, the game
    // reports its menu again at the very press that leaves System, and the tile then hid itself.
    const uint64_t pressed_at=SDL_GetTicks();
    const bool settled=state.visible_since&&pressed_at-state.visible_since>=180;
    if(!was_open&&in_menu&&settled&&!result.open&&(rising&back)&&(result.buttons&back)&&!closing_since)closing_since=pressed_at;
    if(!was_open&&in_menu&&BbMap::ShortcutMode()==1&&(rising&0x4u)){runtime_audio_menu_event(1);BbMap::OpenFromMenu();state.blocked|=buttons;result.buttons=0;}
    if(was_open) {
        if(result.close)BbMap::Back();
        else BbMap::MappedPad(rising,lx,ly,rx,ry,buttons);
        result.buttons=0;
    }
    map_previous=buttons;
    (void)rx;(void)ry;
    Refresh();return result.buttons;
}
bool HandleMouse(const SDL_Event& e) {
    // bbport: losing the window's focus (Alt+Tab, local co-op) only drops the mouse; the tile and
    // its selection stay, as the game's own selection does.
    if(e.type==SDL_EVENT_WINDOW_FOCUS_LOST){hovered=false;mouse_held=false;mouse_up_owned=false;return false;}
    if(e.type==SDL_EVENT_GAMEPAD_REMOVED){BbMap::Close();Reset();return false;}
    if(e.type==SDL_EVENT_GAMEPAD_BUTTON_DOWN || (e.type==SDL_EVENT_GAMEPAD_AXIS_MOTION&&std::abs(int(e.gaxis.value))>6000)){controller=true;last_controller=e.type==SDL_EVENT_GAMEPAD_BUTTON_DOWN?e.gbutton.which:e.gaxis.which;}
    if(e.type==SDL_EVENT_KEY_DOWN || e.type==SDL_EVENT_MOUSE_MOTION || e.type==SDL_EVENT_MOUSE_BUTTON_DOWN)controller=false;
    if(e.type==SDL_EVENT_MOUSE_BUTTON_UP&&e.button.button==SDL_BUTTON_LEFT&&mouse_up_owned){
        mouse_up_owned=false;const bool pressed=mouse_held;mouse_held=false;
        SDL_Window* window=SDL_GetWindowFromID(e.button.windowID);const float d=window?SDL_GetWindowPixelDensity(window):1;
        if(pressed&&Visible()&&Hit(e.button.x*d,e.button.y*d)){runtime_audio_menu_event(1);BbMap::OpenFromMenu();}return true;
    }
    if(!Visible())return false;
    if(e.type==SDL_EVENT_MOUSE_MOTION) {
        SDL_Window* window=SDL_GetWindowFromID(e.motion.windowID);const float d=window?SDL_GetWindowPixelDensity(window):1;
        const bool hit=Hit(e.motion.x*d,e.motion.y*d);
        if(hit&&!hovered&&!state.focused)runtime_audio_menu_event(0);
        hovered=hit;
        ImGui::GetIO().AddMousePosEvent(e.motion.x*d,e.motion.y*d);
        return true;
    }
    if(e.type==SDL_EVENT_MOUSE_BUTTON_DOWN && e.button.button==SDL_BUTTON_LEFT){
        SDL_Window* window=SDL_GetWindowFromID(e.button.windowID);const float d=window?SDL_GetWindowPixelDensity(window):1;
        if(Hit(e.button.x*d,e.button.y*d)){mouse_held=true;mouse_up_owned=true;if(!state.focused&&!hovered)runtime_audio_menu_event(0);state.focused=true;state.anchor=menu.selected;focused=true;return true;}
    }
    return false;
}
void Draw() {
    if(!Visible())return;
    const auto* vp=ImGui::GetMainViewport();const float s=std::min(vp->Size.x/1280.0f,vp->Size.y/720.0f);
    // bbport: while the menu opens it fades in and slides right by 10 units at a steady pace
    // (15 px at 1080p in ~170 ms, measured frame by frame); the tile and its label follow it.
    const float ease=fade.load();
    // The game's tiles become opaque more slowly than they slide (measured frame by frame).
    const float opacity=std::pow(ease,1.4f);
    const ImVec2 offset(vp->Pos.x+(vp->Size.x-1280*s)*.5f-10*s*(1-ease),vp->Pos.y+(vp->Size.y-720*s)*.5f);
    auto p=[&](float x,float y){return ImVec2(offset.x+x*s,offset.y+y*s);};
    tile_min=p(474,280);tile_max=p(530,336);
    auto* draw=ImGui::GetForegroundDrawList();
    const bool active=state.focused||hovered;
    if(active){
        // Cover only the native contextual text and focus rim. The native
        // selection remains intact, so Left/Back needs no memory patch.
        // bbport: the cover is only as wide as the game's own label ("System" in the game's
        // language) and fades out on every side, and it stops above the menu's divider line, so
        // that the background shows around the label as it does around the game's (it was a
        // flat box over the line).
        const char* label=BbAtlasText::Game("Map");
        ImFont* font=BbMap::TitleFont(); /* bbport: the port's font where the game's has no glyphs */const float size=16*s; /* bbport: the game's label size (measured on its "a" against ours) */const auto extent=font->CalcTextSizeA(size,1000,0,label);
        const float native=font->CalcTextSizeA(size,1000,0,BbAtlasText::Game("System")).x/s;
        // The game spaces its letters wider than ImGui does: its "System" is ~20 % wider.
        const float left=269-std::max(native*1.2f,extent.x/s)-6,right=274,top=323,bottom=341.5f,feather=16;
        // It fades with the tile (it stayed opaque while the tile faded out).
        const ImU32 plate=IM_COL32(30,33,33,int(255*opacity)),clear=IM_COL32(30,33,33,0);
        draw->AddRectFilled(p(left,top),p(right,bottom),plate);
        draw->AddRectFilledMultiColor(p(left-feather,top),p(left,bottom),clear,plate,plate,clear);
        draw->AddRectFilledMultiColor(p(right,top),p(right+6,bottom),plate,clear,clear,plate);
        draw->AddRectFilledMultiColor(p(left,top-4),p(right,top),clear,clear,plate,plate);
        draw->AddRectFilledMultiColor(p(left-feather,top-4),p(left,top),clear,clear,plate,clear);
        draw->AddRectFilledMultiColor(p(right,top-4),p(right+6,top),clear,clear,clear,plate);
        // The game's label colour, weight and place (measured against "System" pixel by pixel:
        // its strokes are lighter than ImGui's, hence the translucency).
        draw->AddText(font,size,ImVec2(offset.x+269*s-extent.x,offset.y+324*s),IM_COL32(160,140,104,int(215*opacity)),label);
        if(state.anchor==2||state.anchor==0){
            const float x=state.anchor==2?414.f:294.f;
            draw->AddRect(p(x,280),p(x+56,336),IM_COL32(38,34,28,int(255*opacity)),0,0,5.5f*s);
            draw->AddRectFilled(p(x+2,282),p(x+54,334),IM_COL32(20,18,15,int(64*opacity)));
            draw->AddRect(p(x,280),p(x+56,336),IM_COL32(131,123,103,int(255*opacity)),0,0,.8f*s);
        }
    }
    const int alpha=int(255*opacity);
    BbMapArt::DrawMenuIcon(draw,ImVec2((tile_min.x+tile_max.x)*.5f,(tile_min.y+tile_max.y)*.5f),56*s,mouse_held?IM_COL32(180,170,145,alpha):IM_COL32(255,255,255,alpha));
    draw->AddRect(tile_min,tile_max,active?IM_COL32(235,233,220,alpha):IM_COL32(131,123,103,alpha),0,0,(active?1.7f:.8f)*s);
    if(hovered)ImGui::SetTooltip("%s",BbAtlasText::Game("Map"));
}
}
