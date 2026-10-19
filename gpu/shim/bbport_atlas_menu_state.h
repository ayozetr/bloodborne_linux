// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <cstdint>

// Logical PS4 buttons after input.ini mapping. No native menu mutation.
class BbAtlasMenuState {
public:
    enum : uint32_t { Right=0x20,Up=0x10,Down=0x40,Left=0x80,Cross=0x4000,Circle=0x2000 };
    struct Result {uint32_t buttons;bool open=false,close=false,move=false;};
    bool focused=false;
    int anchor=2;
    int last_index=-1; // bbport: the native selection at the previous call
    // bbport: Down from the Map tile. The game moves from System (2) to the tile below it (8);
    // Right is then pulsed (pressed one call, released the next) until it reaches 9, below Map.
    uint64_t step_right_until=0;
    bool step_right_pressed=false;
    uint32_t previous=0,blocked=0;
    uint64_t visible_since=0;
    bool was_visible=false;
    void Reset(){focused=false;anchor=2;blocked|=previous;was_visible=false;visible_since=0;last_index=-1;
                 step_right_until=0;step_right_pressed=false;}
    bool Settled(bool visible,uint64_t now) {
        if(!visible){was_visible=false;visible_since=0;return false;}
        if(!was_visible){was_visible=true;visible_since=now;}
        return now-visible_since>=180;
    }
    Result Route(bool visible,int index,bool map_open,uint32_t buttons,uint32_t confirm,uint64_t now) {
        blocked&=buttons;
        const uint32_t rising=buttons&~previous;previous=buttons;
        const int from=last_index;last_index=index;
        const bool ready=Settled(visible,now);
        Result out{buttons&~blocked};
        if(map_open){
            blocked|=buttons;
            if(rising&(confirm==Cross?Circle:Cross)){out.close=true;blocked|=buttons;}
            out.buttons=0;return out;
        }
        if(!ready){focused=false;step_right_until=0;return out;}
        if(step_right_until){
            if(index==9||now>step_right_until||(index!=2&&index!=8)){step_right_until=0;step_right_pressed=false;}
            else if(index==8){
                step_right_pressed=!step_right_pressed;
                out.buttons=(buttons&~blocked&~Right)|(step_right_pressed?Right:0u);return out;
            }
        }
        if(focused&&index!=anchor)focused=false;
        // bbport: Up from the row below lands on System (the game knows of no tile above columns
        // 4-6); from below the Map tile, the Map tile takes the focus instead. The game has
        // already played its cursor sound.
        if(!focused&&index==2&&from>=9&&from<=11){focused=true;anchor=2;}
        if(!focused&&((index==2&&(rising&Right))||(index==0&&(rising&Left)))){
            focused=true;anchor=index;blocked|=index==2?Right:Left;out.move=true;
        }
        else if(focused){
            if(rising&confirm){out.open=true;blocked|=buttons;}
            else if(rising&(Left|Right)){
                const uint32_t edge=rising&(Left|Right);
                // Revealing the underlying tile uses the local cursor sound.
                // Moving to the opposite end uses the game's own native wrap.
                const bool reveal=(anchor==2&&edge==Left)||(anchor==0&&edge==Right);
                focused=false;
                if(reveal){blocked|=edge;out.move=true;}
            }
            // bbport: Down goes to the tile below Map (see step_right_until).
            else if(anchor==2&&(rising&Down)){focused=false;step_right_until=now+400;step_right_pressed=false;}
            // Up/down and Back retain the game's own menu behavior.
            else if(rising&(Up|Down|(confirm==Cross?Circle:Cross)))focused=false;
        }
        out.buttons=buttons&~blocked;return out;
    }
};
