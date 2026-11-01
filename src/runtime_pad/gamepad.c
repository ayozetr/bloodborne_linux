// SPDX-FileCopyrightText: Copyright 2026 bbport contributors
// SPDX-License-Identifier: GPL-2.0-or-later
/* runtime_pad.c part: which SDL gamepad drives the game (BB_GAMEPAD), the test virtual pad; the guest libc heap report.
 * #included by runtime_pad.c in order (one translation unit: it shares that file's
 * statics); not compiled on its own. */

/* BB_GAMEPAD (the launcher's controller choice): its SDL GUID, part of its name, or its device
 * path (/dev/input/eventN, or the hidraw path; the only way to tell two pads of the same model
 * apart, as local co-op needs). Issue #15: wheels and other controllers connected for good came
 * first. */
#include "../../gpu/shim/bb_env.h"
static const char *preferred_gamepad(void) {
    static const char *want; static int read;
    if (!read) { want=bb_env("BB_GAMEPAD"); if (want && !*want) want=NULL; read=1; }
    return want;
}
/* BB_GAMEPAD_STRICT=1 (local co-op, one game per player): only the chosen gamepad, never the
 * first one or the one in use instead - that one is another player's. Without a chosen one, no
 * gamepad at all. */
static int gamepad_strict(void) {
    static int strict=-1;
    if (strict<0) { const char *v=bb_env("BB_GAMEPAD_STRICT"); strict=v && v[0]=='1'; }
    return strict;
}
static int is_preferred(SDL_JoystickID id, const char *want) {
    char guid[33];
    SDL_GUIDToString(SDL_GetGamepadGUIDForID(id),guid,sizeof guid);
    const char *name=SDL_GetGamepadNameForID(id);
    const char *path=SDL_GetGamepadPathForID(id);
    return !strcasecmp(guid,want) || (path && !strcmp(path,want)) || (name && strcasestr(name,want));
}
/* Several gamepads at once (also one pad behind a 2.4 GHz receiver that shows as two) and none
 * chosen: the one being used takes over, checked five times a second. Used means a button held
 * or an axis well away from where it rested when it was opened: a wheel's pedals rest at one end
 * of their axis (issue #15). From Awaken's BloodBorneButPc, by way of the Linux fork. */
#define MAX_OTHER_PADS 4
static struct { SDL_Gamepad *pad; SDL_JoystickID id; int16_t rest[SDL_GAMEPAD_AXIS_COUNT]; } other_pads[MAX_OTHER_PADS];
static int pad_in_use(int slot) {
    SDL_Gamepad *p=other_pads[slot].pad;
    for (int b=0;b<SDL_GAMEPAD_BUTTON_COUNT;++b) if (SDL_GetGamepadButton(p,(SDL_GamepadButton)b)) return 1;
    for (int a=0;a<SDL_GAMEPAD_AXIS_COUNT;++a) {
        const int moved=SDL_GetGamepadAxis(p,(SDL_GamepadAxis)a)-other_pads[slot].rest[a];
        if (moved>20000 || moved<-20000) return 1;
    }
    return 0;
}
/* BB_PAD_LIGHTBAR=RRGGBB (the Linux fork's launcher: Controls, "Controller light bar colour"):
 * every pad with a light bar (DualShock 4, DualSense) shows that colour; unset, SDL's own. */
static void set_lightbar(SDL_Gamepad *pad) {
    static int read, on; static Uint8 rgb[3];
    if (!read) {
        read=1;
        const char *v=bb_env("BB_PAD_LIGHTBAR");
        if (v && *v=='#') ++v;
        if (v && strlen(v)==6 && strspn(v,"0123456789abcdefABCDEF")==6) {
            const unsigned long c=strtoul(v,NULL,16);
            rgb[0]=(Uint8)(c>>16); rgb[1]=(Uint8)(c>>8); rgb[2]=(Uint8)c; on=1;
        }
    }
    if (on && pad)
        printf("Runtime: light bar #%02x%02x%02x on %s%s\n",rgb[0],rgb[1],rgb[2],SDL_GetGamepadName(pad),
               SDL_SetGamepadLED(pad,rgb[0],rgb[1],rgb[2]) ? "" : " (it has none, or SDL cannot set it)");
}
static void follow_active_pad(uint64_t now) {
    static uint64_t last;
    if (now-last<200000) return;
    last=now;
    for (int s=0;s<MAX_OTHER_PADS;++s)
        if (other_pads[s].pad && !SDL_GamepadConnected(other_pads[s].pad)) {
            SDL_CloseGamepad(other_pads[s].pad); other_pads[s].pad=NULL;
        }
    int count=0;
    SDL_JoystickID *ids=SDL_GetGamepads(&count);
    for (int i=0; ids && count>1 && i<count; ++i) {
        if (gamepad && SDL_GetGamepadID(gamepad)==ids[i]) continue;
        int slot=-1, free_slot=-1;
        for (int s=0;s<MAX_OTHER_PADS;++s) {
            if (other_pads[s].pad && other_pads[s].id==ids[i]) slot=s;
            else if (!other_pads[s].pad && free_slot<0) free_slot=s;
        }
        if (slot<0 && free_slot>=0 && (other_pads[free_slot].pad=SDL_OpenGamepad(ids[i]))) {
            other_pads[free_slot].id=ids[i];
            set_lightbar(other_pads[free_slot].pad);
            for (int a=0;a<SDL_GAMEPAD_AXIS_COUNT;++a)
                other_pads[free_slot].rest[a]=SDL_GetGamepadAxis(other_pads[free_slot].pad,(SDL_GamepadAxis)a);
            slot=free_slot; /* rests now: not taken over in this check */
        } else if (slot>=0 && pad_in_use(slot)) {
            SDL_Gamepad *previous=gamepad;
            gamepad=other_pads[slot].pad;
            other_pads[slot].pad=previous;
            other_pads[slot].id=previous ? SDL_GetGamepadID(previous) : 0;
            for (int a=0;previous && a<SDL_GAMEPAD_AXIS_COUNT;++a)
                other_pads[slot].rest[a]=SDL_GetGamepadAxis(previous,(SDL_GamepadAxis)a);
            cal_reset(); /* a new pad has its own neutral */
            printf("Runtime: gamepad in use: %s\n",SDL_GetGamepadName(gamepad));
            break;
        }
    }
    SDL_free(ids);
}
/* BB_TEST_VPAD=1 (tests): a virtual gamepad without a touch surface (an Xbox-like pad) whose
 * buttons the pad file presses ("vpad:back"), so scripted runs go through the real gamepad path
 * (bindings, Back as the touchpad). BB_GAMEPAD=bbport picks it. */
static SDL_Joystick *test_vpad;
static void test_vpad_attach(void) {
    static int done;
    if (done) return;
    done=1;
    const char *env=bb_env("BB_TEST_VPAD");
    if (!env || env[0]!='1') return;
    SDL_VirtualJoystickDesc desc;
    SDL_INIT_INTERFACE(&desc);
    desc.type=SDL_JOYSTICK_TYPE_GAMEPAD;
    desc.naxes=SDL_GAMEPAD_AXIS_COUNT;
    desc.nbuttons=SDL_GAMEPAD_BUTTON_MISC1;
    desc.name="bbport test pad";
    const SDL_JoystickID id=SDL_AttachVirtualJoystick(&desc);
    test_vpad=id ? SDL_OpenJoystick(id) : NULL;
    printf("Runtime: test gamepad %s\n",test_vpad ? "attached" : SDL_GetError());
}
/* The chosen gamepad, else the first while it is not connected (checked again every second, it
 * is taken as soon as it connects); without a chosen one, the one in use (follow_active_pad);
 * called under lock. */
static SDL_Gamepad *current_gamepad(void) {
    static int on_preferred; static uint64_t last_scan;
    if (!sdl_ready) sdl_ready = SDL_WasInit(SDL_INIT_GAMEPAD) ? 1 : SDL_InitSubSystem(SDL_INIT_GAMEPAD) ? 1 : -1;
    if (sdl_ready<0) return NULL;
    test_vpad_attach();
    if (gamepad && !SDL_GamepadConnected(gamepad)) { SDL_CloseGamepad(gamepad); gamepad=NULL; }
    const char *want=preferred_gamepad();
    const uint64_t now=now_us();
    if (!gamepad || (want && !on_preferred && now-last_scan>1000000)) {
        last_scan=now;
        int count=0, pick=-1;
        SDL_JoystickID *ids=SDL_GetGamepads(&count);
        for (int i=0; want && ids && i<count && pick<0; ++i) if (is_preferred(ids[i],want)) pick=i;
        if (pick<0 && !gamepad && ids && count>0 && !gamepad_strict()) pick=0;
        if (pick>=0 && (!gamepad || SDL_GetGamepadID(gamepad)!=ids[pick])) {
            if (gamepad) SDL_CloseGamepad(gamepad);
            gamepad=SDL_OpenGamepad(ids[pick]);
            cal_reset(); /* a new pad has its own neutral */
            on_preferred=want && gamepad && is_preferred(ids[pick],want);
            if (gamepad) {
                ++connected_count;
                set_lightbar(gamepad);
                const char *path=SDL_GetGamepadPath(gamepad);
                printf("Runtime: gamepad connected: %s%s (%s)\n",SDL_GetGamepadName(gamepad),
                       !want ? "" : on_preferred ? " (the chosen one)" : " (the chosen one is not connected)",
                       path ? path : "no path");
            }
        }
        SDL_free(ids);
    }
    if (!want && !gamepad_strict()) follow_active_pad(now);
    return gamepad;
}
/* bbport (frame stats): the game's libc heap, read every 5 s from a game thread (it reads the pad)
 * with libc.prx's malloc_stats (export stub at libc.prx+0x1f8c0; malloc_stats_fast returns 1 in this libc, the module at image +0x56e0000):
 * in use now and at most, and what it took from the system. A heap that keeps growing is a leak. */
typedef struct { uint16_t size, version; uint32_t reserved; uint64_t max_system, system, max_in_use, in_use; } MallocManagedSize;
static void report_guest_heap(void) {
    static int enabled=-1; static uint64_t last;
    if (enabled<0) enabled=bb_env("BB_FRAME_STATS")!=NULL;
    const uint64_t now=now_us();
    if (!enabled || now-last<5000000) return;
    last=now;
    /* Bloodborne's libc.prx (another game's libc has its exports elsewhere). */
    if (!runtime_libc_base) return;
    const uint8_t *stub=(const uint8_t *)(runtime_libc_base+0x1f8c0);
    if (runtime_libc_base!=0x800000000ull+0x56e0000 || stub[0]!=0xff || stub[1]!=0x25) return;
    ABI int (*stats)(MallocManagedSize *)=(ABI int (*)(MallocManagedSize *))(uintptr_t)stub;
    MallocManagedSize m={.size=sizeof(m),.version=1};
    const int result=stats(&m);
    if (result!=0) { static int told; if (!told++) printf("Guest heap: malloc_stats returned %#x\n",(unsigned)result); return; }
    {
        printf("Guest heap: %.1f MB in use (most %.1f), %.1f MB from the system (most %.1f)\n",
               m.in_use/1048576.0,m.max_in_use/1048576.0,m.system/1048576.0,m.max_system/1048576.0);
    }
}
