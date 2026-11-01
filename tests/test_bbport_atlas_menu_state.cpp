#include "../gpu/shim/bbport_atlas_menu_state.h"
#include <cassert>
#include <cstdio>

int main() {
    BbAtlasMenuState state;
    constexpr auto left=BbAtlasMenuState::Left;
    constexpr auto right=BbAtlasMenuState::Right;
    constexpr auto cross=BbAtlasMenuState::Cross;

    assert(state.Route(true,0,false,0,cross,100).buttons==0);
    assert(state.Route(true,0,false,0,cross,280).buttons==0);
    auto move=state.Route(true,0,false,left,cross,281);
    assert(state.focused && state.anchor==0 && move.move && !(move.buttons&left));
    state.Route(true,0,false,0,cross,282);
    move=state.Route(true,0,false,right,cross,283);
    assert(!state.focused && move.move && !(move.buttons&right)); // reveal first

    state.Route(true,0,false,0,cross,284);
    state.Route(true,0,false,left,cross,285);
    state.Route(true,0,false,0,cross,286);
    move=state.Route(true,0,false,left,cross,287);
    assert(!state.focused && !move.move && (move.buttons&left)); // native 0 -> 2

    state.Route(true,2,false,0,cross,288);
    move=state.Route(true,2,false,right,cross,289);
    assert(state.focused && state.anchor==2 && move.move && !(move.buttons&right));
    state.Route(true,2,false,0,cross,290);
    move=state.Route(true,2,false,left,cross,291);
    assert(!state.focused && move.move && !(move.buttons&left)); // reveal System

    state.Route(true,2,false,0,cross,292);
    state.Route(true,2,false,right,cross,293);
    state.Route(true,2,false,0,cross,294);
    move=state.Route(true,2,false,right,cross,295);
    assert(!state.focused && !move.move && (move.buttons&right)); // native 2 -> 0

    state.Route(true,0,false,0,cross,296);
    state.Route(true,0,false,left,cross,297);
    state.Route(true,0,false,0,cross,298);
    move=state.Route(true,0,false,cross,cross,299);
    assert(move.open && !(move.buttons&cross));

    // bbport: Up from below the Map tile (native 9 -> 2) focuses the Map tile; from below System
    // (8 -> 2) it stays on System.
    BbAtlasMenuState up;
    constexpr auto up_button=BbAtlasMenuState::Up;
    up.Route(true,9,false,0,cross,100);
    up.Route(true,9,false,0,cross,300);
    move=up.Route(true,9,false,up_button,cross,301);
    assert(!up.focused && (move.buttons&up_button)); // the game moves its selection
    up.Route(true,2,false,up_button,cross,302);
    assert(up.focused && up.anchor==2);
    up.Route(true,2,false,0,cross,303);
    move=up.Route(true,2,false,cross,cross,304);
    assert(move.open);
    BbAtlasMenuState system;
    system.Route(true,8,false,0,cross,100);
    system.Route(true,8,false,0,cross,300);
    system.Route(true,8,false,up_button,cross,301);
    system.Route(true,2,false,up_button,cross,302);
    assert(!system.focused);

    // bbport: Down from the Map tile: the game goes 2 -> 8, then Right is pulsed until 9.
    constexpr auto down=BbAtlasMenuState::Down;
    BbAtlasMenuState below;
    below.Route(true,2,false,0,cross,100);
    below.Route(true,2,false,0,cross,300);
    below.Route(true,2,false,right,cross,301);
    below.Route(true,2,false,0,cross,302);
    assert(below.focused);
    move=below.Route(true,2,false,down,cross,303);
    assert(!below.focused && (move.buttons&down)); // the game moves its selection down
    move=below.Route(true,8,false,down,cross,304);
    assert(move.buttons&right);
    move=below.Route(true,8,false,0,cross,305);
    assert(!(move.buttons&right));
    move=below.Route(true,8,false,0,cross,306);
    assert(move.buttons&right);
    move=below.Route(true,9,false,0,cross,307);
    assert(!(move.buttons&right) && !below.step_right_until);
    move=below.Route(true,9,false,0,cross,308);
    assert(!(move.buttons&right));
    // From System, Down stays the game's own.
    BbAtlasMenuState plain;
    plain.Route(true,2,false,0,cross,100);
    plain.Route(true,2,false,0,cross,300);
    plain.Route(true,2,false,down,cross,301);
    move=plain.Route(true,8,false,0,cross,302);
    assert(!(move.buttons&right));

    std::puts("BBPORT_ATLAS_MENU_STATE_PASS");
}
