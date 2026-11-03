// SPDX-FileCopyrightText: Copyright 2026 bbport contributors
// SPDX-License-Identifier: GPL-2.0-or-later
#define _GNU_SOURCE
#include <assert.h>
#include <unistd.h>
#include "../src/runtime_pad.c"

static int capture;
int bbgpu_overlay_captures_input(void) { return capture; }
uint32_t bbgpu_atlas_route_pad(uint32_t buttons, uint8_t lx, uint8_t ly, uint8_t rx, uint8_t ry) {
    (void)lx; (void)ly; (void)rx; (void)ry; return buttons; /* Hunter's Atlas off here */
}
void bbgpu_mouse_take(double *dx, double *dy, int *up, int *down) { *dx=*dy=0; *up=*down=0; }
int bbgpu_mouse_captured(void) { return 0; }
void bbgpu_mouse_look_enable(int enabled) { (void)enabled; }
void bbgpu_mouse_capture(void) {}
int bbgpu_camera_look(float yaw, float pitch) { (void)yaw; (void)pitch; return 0; }
void bbgpu_filter_pad(uint32_t *buttons, const uint8_t *sticks) { (void)buttons; (void)sticks; }
int bbgpu_pointer_wanted(void) { return 0; }
/* The game's image is not mapped here: the mouse's auto-rotation hold leaves its code alone. */
int runtime_memory_low_info(uintptr_t address, int *prot, uintptr_t *end) { (void)address; (void)prot; (void)end; return 0; }
int bbgpu_video_active(void) { return 0; }
int bbgpu_world_active(void) { return 1; }
unsigned long long bbgpu_world_us(void) { return 0; }
int bbgpu_video_skip(void) { return 0; }
int bbgpu_free_camera(void) { return 0; }
void runtime_re_watch_tick(const void *pad_buffer, uint64_t reads) { (void)pad_buffer; (void)reads; }
uintptr_t runtime_libc_base;
uintptr_t runtime_lookup(const RuntimeExport *table, size_t count, const char *name) {
    (void)table; (void)count; (void)name;
    return 0;
}

static void inject(const char *path, const char *tokens) {
    FILE *f=fopen(path,"w");
    assert(f);
    fputs(tokens,f);
    fclose(f);
    usleep(25000);
}

int main(void) {
    char path[]="/tmp/bbport-pad-test-XXXXXX";
    int fd=mkstemp(path);
    assert(fd>=0);
    close(fd);
    setenv("BB_PAD_FILE",path,1);
    /* bbport.ini controls: buttons moved, a trigger as a button and a button as a trigger. */
    char config[]="/tmp/bbport-pad-config-XXXXXX";
    int config_fd=mkstemp(config);
    assert(config_fd>=0);
    const char controls[]="upscaler=fsr3\npad.cross=b\npad.circle=a\npad.r2=rightshoulder\n"
                          "pad.r1=righttrigger\nkey.cross=X, Space\npad.bogus=a\n"
                          "key.l3=Left Ctrl+C, Keypad +\n";
    assert(write(config_fd,controls,sizeof(controls)-1)==(ssize_t)(sizeof(controls)-1));
    close(config_fd);
    setenv("BB_CONFIG",config,1);
    setenv("SDL_VIDEODRIVER","dummy",1);
    /* Only the virtual test controller is a gamepad, whatever is plugged in. */
    SDL_SetHint(SDL_HINT_GAMECONTROLLER_IGNORE_DEVICES_EXCEPT,"0x1d50/0x6189");
    assert(SDL_Init(SDL_INIT_VIDEO|SDL_INIT_GAMEPAD));
    /* The keyboard defaults: Escape the menu, R2 a Shift chord on the left button. */
    bind_defaults();
    assert(bindings[IN_OPTIONS].keys[0]==SDL_SCANCODE_ESCAPE && bindings[IN_OPTIONS].mods[0]<0);
    assert(bindings[IN_R2].keys[0]==MOUSE_KEY+SDL_BUTTON_LEFT && bindings[IN_R2].mods[0]==SDL_SCANCODE_LSHIFT);
    assert(bindings[IN_R1].keys[0]==MOUSE_KEY+SDL_BUTTON_LEFT && bindings[IN_R1].mods[0]<0);
    /* A chord on the keyboard: C alone is R3, Ctrl+C is L3 and not R3 too. */
    load_bindings();
    assert(bindings[IN_L3].key_count==2 && bindings[IN_L3].keys[0]==SDL_SCANCODE_C &&
           bindings[IN_L3].mods[0]==SDL_SCANCODE_LCTRL && bindings[IN_L3].keys[1]==SDL_SCANCODE_KP_PLUS &&
           bindings[IN_L3].mods[1]<0);
    {
        bool keys[SDL_SCANCODE_COUNT]={0};
        keys[SDL_SCANCODE_C]=true;
        assert(key_down(keys,IN_R3) && !key_down(keys,IN_L3));
        keys[SDL_SCANCODE_LCTRL]=true;
        assert(key_down(keys,IN_L3) && !key_down(keys,IN_R3));
    }
    assert(pad_init()==0 && pad_open(1,0,0,NULL)==1);
    PadData data;
    inject(path,"cross l3 touchpad_left");
    assert(pad_read_state(1,&data)==0);
    assert((data.buttons & (BTN_CROSS|BTN_L3|BTN_TOUCHPAD))==(BTN_CROSS|BTN_L3|BTN_TOUCHPAD));
    /* A new touch gets a new id (1..127), as from a DualShock 4: the game ignores id 0. */
    assert(data.touch_count==1 && data.touches[0].x==480 && data.touches[0].y==471 && data.touches[0].id==1);
    inject(path,"touchpad_right");
    assert(pad_read_state(1,&data)==0 && data.touch_count==1 && data.touches[0].x==1440);
    inject(path,"");
    assert(pad_read_state(1,&data)==0 && data.buttons==0 && data.touch_count==0);

    SDL_VirtualJoystickTouchpadDesc touch={.nfingers=2};
    SDL_VirtualJoystickDesc desc;
    SDL_INIT_INTERFACE(&desc);
    desc.type=SDL_JOYSTICK_TYPE_GAMEPAD;
    desc.naxes=SDL_GAMEPAD_AXIS_COUNT;
    desc.nbuttons=SDL_GAMEPAD_BUTTON_COUNT;
    desc.button_mask=(1u<<SDL_GAMEPAD_BUTTON_COUNT)-1;
    desc.axis_mask=(1u<<SDL_GAMEPAD_AXIS_COUNT)-1;
    desc.name="bbport test controller";
    desc.vendor_id=0x1d50;
    desc.product_id=0x6189;
    desc.ntouchpads=1;
    desc.touchpads=&touch;
    SDL_JoystickID id=SDL_AttachVirtualJoystick(&desc);
    assert(id!=0);
    SDL_Joystick *joystick=SDL_OpenJoystick(id);
    assert(joystick);
    assert(SDL_SetJoystickVirtualTouchpad(joystick,0,0,true,0.75f,0.5f,1.0f));
    assert(SDL_SetJoystickVirtualTouchpad(joystick,0,1,true,0.25f,1.0f,1.0f));
    assert(SDL_SetJoystickVirtualButton(joystick,SDL_GAMEPAD_BUTTON_TOUCHPAD,true));
    SDL_UpdateJoysticks();
    SDL_UpdateGamepads();
    assert(pad_read_state(1,&data)==0);
    assert(gamepad && data.touch_count==2 && (data.buttons & BTN_TOUCHPAD));
    assert(data.touches[0].x==1439 && data.touches[0].y==471 && data.touches[0].id==2);
    assert(data.touches[1].x==480 && data.touches[1].y==942 && data.touches[1].id==3);
    capture=1;
    assert(pad_read_state(1,&data)==0 && data.touch_count==0 && data.buttons==0);
    capture=0;
    assert(SDL_SetJoystickVirtualTouchpad(joystick,0,0,false,0,0,0));
    assert(SDL_SetJoystickVirtualTouchpad(joystick,0,1,false,0,0,0));
    SDL_UpdateJoysticks();
    SDL_UpdateGamepads();
    assert(pad_read_state(1,&data)==0 && data.touch_count==1 && data.touches[0].x==480);
    assert(SDL_SetJoystickVirtualButton(joystick,SDL_GAMEPAD_BUTTON_TOUCHPAD,false));
    assert(SDL_SetJoystickVirtualButton(joystick,SDL_GAMEPAD_BUTTON_EAST,true));
    assert(SDL_SetJoystickVirtualButton(joystick,SDL_GAMEPAD_BUTTON_RIGHT_SHOULDER,true));
    assert(SDL_SetJoystickVirtualAxis(joystick,SDL_GAMEPAD_AXIS_RIGHT_TRIGGER,32767));
    SDL_UpdateJoysticks();
    SDL_UpdateGamepads();
    assert(pad_read_state(1,&data)==0);
    assert(data.buttons==(BTN_CROSS|BTN_R2|BTN_R1) && data.r2==255);
    assert(bindings[IN_CROSS].key_count==2 && bindings[IN_CROSS].keys[0]==SDL_SCANCODE_X &&
           bindings[IN_CROSS].keys[1]==SDL_SCANCODE_SPACE);
    SDL_CloseJoystick(joystick);
    if (gamepad) SDL_CloseGamepad(gamepad);
    gamepad=NULL;
    assert(SDL_DetachVirtualJoystick(id));
    SDL_Quit();
    unlink(path);
    unlink(config);
    /* Mouse: names, the look stick's speed-to-deflection at two frame rates, the wheel's presses. */
    assert(key_from_name("Mouse Left")==MOUSE_KEY+SDL_BUTTON_LEFT && key_from_name("wheel down")==MOUSE_WHEEL_DOWN);
    for (int rate=60;rate<=240;rate*=4) {
        PadData m; memset(&m,0,sizeof m);
        look_x=look_y=0; look_last_us=1;
        const uint64_t step=1000000/rate;
        for (int i=1;i<=rate;++i) { /* 500 pixels/s to the right for a second */
            m.right_x=m.right_y=128;
            apply_mouse_look(&m,500.0/rate,0,1+i*step,1);
        }
        assert(m.right_x>=128+16+50 && m.right_x<=128+16+62 && m.right_y==128);
        m.right_x=128;
        apply_mouse_look(&m,0,0,1+(rate+60)*step,1); /* still: back to the pad's stick */
        for (int i=0;i<20;++i) apply_mouse_look(&m,0,0,1+(rate+61+i)*step,1);
        assert(m.right_x==128);
    }
    mouse_wheel_step(1000000,0,2);
    assert(wheel_phase[1]==1 && mouse_key_down(MOUSE_WHEEL_DOWN));
    mouse_wheel_step(1070000,0,0);
    assert(!mouse_key_down(MOUSE_WHEEL_DOWN));
    mouse_wheel_step(1140000,0,0);
    assert(mouse_key_down(MOUSE_WHEEL_DOWN) && wheel_pending[1]==0);
    /* Issue #20: right after reconnecting, an 8BitDo Pro 2 (as an Xbox One controller) reported
       -32768 on all four axes before its first real report. That was taken as a biased neutral,
       and the sticks at rest then read as pushed all the way: the camera and the player spun. */
    {
        const int16_t railed[4]={-32768,-32768,-32768,-32768}, rest[4]={120,-80,40,-20};
        cal_reset();
        for (int i=0;i<30;++i) cal_sample(railed);
        assert(!cal_have_center); /* not a neutral: waits for a real report */
        for (int i=0;i<=PAD_CAL_QUIET_SAMPLES;++i) cal_sample(rest); /* the first one moved: not quiet */
        assert(cal_have_center && !cal_center[0] && !cal_center[1] && !cal_center[2] && !cal_center[3]);
        assert(stick_axis(0,0)==128 && stick_axis(3,0)==128);
        /* A clone's biased neutral (both sticks at a constant ~ +/-16380) is still taken. */
        const int16_t clone[4]={16380,-16380,16380,-16380};
        cal_reset();
        for (int i=0;i<=PAD_CAL_QUIET_SAMPLES;++i) cal_sample(clone);
        assert(cal_have_center && cal_center[0]==16380 && cal_center[1]==-16380);
        assert(stick_axis(0,16380)==128);
        /* Back to a genuine pad at rest for the checks below. */
        const int16_t quiet_rest[4]={5,5,5,5};
        cal_reset();
        for (int i=0;i<=PAD_CAL_QUIET_SAMPLES;++i) cal_sample(quiet_rest);
        assert(cal_have_center && !cal_center[0]);
    }
    /* Issue #7: a controller stick past the round gate comes back onto it, keeping its direction;
     * one axis all the way (0 or 255) stays as it is. */
    {
        uint8_t x=255, y=255; round_gate(1,&x,&y);
        assert(x==128+90 && y==128+90);
        x=0; y=128; round_gate(1,&x,&y); assert(x==0 && y==128);
        x=255; y=128; round_gate(1,&x,&y); assert(x==255 && y==128);
        x=255; y=200; round_gate(0,&x,&y);
        assert(x>=237 && x<=239 && y>=190 && y<=192); /* (127,72) scaled to reach 127 */
    }
    /* The round dead zone: inside it the centre; along one axis as the per-axis one; a push close
     * to an axis keeps its small part of the other one (per axis it was dropped). */
    {
        const int dz=pad_deadzone, outer=pad_deadzone_outer;
        pad_deadzone=10; pad_deadzone_outer=127;
        uint8_t x=0, y=0;
        stick_deadzone(6,6,&x,&y); assert(x==128 && y==128);       /* length 8.5: inside */
        stick_deadzone(0,-9,&x,&y); assert(x==128 && y==128);
        stick_deadzone(127,0,&x,&y); assert(x==255 && y==128);     /* full: full */
        stick_deadzone(-128,0,&x,&y); assert(x==0 && y==128);
        stick_deadzone(0,40,&x,&y); assert(x==128 && y==128+33);   /* 128*30/117 */
        stick_deadzone(8,100,&x,&y);                               /* per axis: x 128 */
        assert(x>128+5 && x<=128+8 && y>=128+98 && y<=128+101);
        stick_deadzone(127,127,&x,&y); assert(x==255 && y==255);   /* a square gate's corner */
        pad_deadzone=dz; pad_deadzone_outer=outer;
    }
    /* Stick options: swapped sticks, then the camera stick (now the left one) inverted; the
     * centre stays the centre. */
    {
        PadData m; memset(&m,0,sizeof m);
        m.left_x=10; m.left_y=20; m.right_x=128; m.right_y=0;
        apply_stick_options(&m);
        assert(m.left_x==10 && m.left_y==20 && m.right_x==128 && m.right_y==0);
        pad_swap_sticks=pad_invert_look_x=pad_invert_look_y=1;
        apply_stick_options(&m);
        assert(m.left_x==128 && m.left_y==0 && m.right_x==246 && m.right_y==236);
        m.right_x=128; m.right_y=0; pad_swap_sticks=0;
        apply_stick_options(&m);
        assert(m.right_x==128 && m.right_y==255);
        pad_invert_look_x=pad_invert_look_y=0;
    }
    /* Issue #7: a camera stick all the way out on a diagonal is pulled in under the game's fast
     * turn (~96%); straight sideways, straight up/down and anything short of the rim stay. */
    {
        PadData m; memset(&m,0,sizeof m);
        m.right_x=218; m.right_y=38; camera_diagonal(&m); assert(m.right_x==218 && m.right_y==38); /* off */
        pad_camera_diagonal=1;
        m.right_x=218; m.right_y=38; /* 45 degrees, all the way */
        camera_diagonal(&m);
        const float r=hypotf((float)m.right_x-128.0f,(float)m.right_y-128.0f)/127.0f;
        assert(r>0.91f && r<0.94f && m.right_x-128==128-m.right_y);
        m.right_x=255; m.right_y=128; camera_diagonal(&m); assert(m.right_x==255 && m.right_y==128);
        m.right_x=250; m.right_y=100; camera_diagonal(&m); assert(m.right_x==250 && m.right_y==100); /* 13 degrees */
        m.right_x=140; m.right_y=1; camera_diagonal(&m); assert(m.right_x==140 && m.right_y==1);   /* 85 degrees */
        m.right_x=200; m.right_y=56; camera_diagonal(&m); assert(m.right_x==200 && m.right_y==56); /* 80% */
        pad_camera_diagonal=0;
    }
    /* keyboard_layout=classic: the Linux fork's keys (Space Cross, Left Shift Circle, Enter
     * Options, arrows the camera, IJKL the d-pad); without it 0.7's (Space the dodge). */
    {
        char classic_path[]="/tmp/bbport-classic-XXXXXX";
        const int fd=mkstemp(classic_path);
        assert(fd>=0);
        const char text[]="keyboard_layout=classic\n";
        assert(write(fd,text,sizeof(text)-1)==(ssize_t)(sizeof(text)-1));
        close(fd);
        const char *saved=getenv("BB_CONFIG");
        char saved_copy[512]; snprintf(saved_copy,sizeof saved_copy,"%s",saved ? saved : "");
        setenv("BB_CONFIG",classic_path,1);
        load_bindings();
        assert(layout_classic && bindings[IN_CROSS].keys[0]==SDL_SCANCODE_SPACE);
        assert(bindings[IN_CIRCLE].keys[0]==SDL_SCANCODE_LSHIFT && bindings[IN_DODGE].key_count==0);
        assert(bindings[IN_OPTIONS].keys[0]==SDL_SCANCODE_RETURN && bindings[IN_UP].keys[0]==SDL_SCANCODE_I);
        assert(bindings[IN_LOOK_LEFT].keys[0]==SDL_SCANCODE_LEFT);
        unlink(classic_path);
        setenv("BB_CONFIG",saved_copy,1);
        load_bindings();
        assert(!layout_classic && bindings[IN_DODGE].keys[0]==SDL_SCANCODE_SPACE);
    }
    /* Keyboard movement: opposite keys, the last pressed wins (or cancel out with
     * stick_socd=neutral). */
    {
        assert(key_direction(0,1,0)==-1);
        assert(key_direction(0,1,1)==1);  /* D pressed last */
        assert(key_direction(0,0,1)==1);
        assert(key_direction(0,1,1)==-1); /* now A is the last */
        assert(key_direction(0,0,0)==0);
        stick_socd_last=0;
        assert(key_direction(0,1,1)==0);
        stick_socd_last=1;
    }
    /* The movement keys as the stick (cassioKenji's measurements): the square gate, at most 30
     * degrees a read toward the keys' direction, a half turn through forward, a release held
     * 60 ms. */
    {
        int x, y; uint64_t t=10000000;
        assert(key_move(0,-1,t,&x,&y) && x==0 && y==-127);              /* W */
        t+=16000; key_move(-1,-1,t,&x,&y);                               /* W+A: one step of 14.4 */
        assert(y==-127 && x<-25 && x>-40);
        for (int i=0;i<10;++i) { t+=16000; key_move(-1,-1,t,&x,&y); }
        assert(x==-127 && y==-127);                                      /* the square's corner */
        t+=200000; key_move(-1,-1,t,&x,&y); t+=200000; key_move(-1,0,t,&x,&y);
        assert(x==-127 && y>-127 && y<0);                                /* toward A: 30 degrees at most */
        for (int i=0;i<10;++i) { t+=16000; key_move(-1,0,t,&x,&y); }
        assert(x==-127 && y==0);
        t+=16000; key_move(1,0,t,&x,&y);                                 /* A -> D: through forward */
        assert(y<0);
        t+=20000; assert(key_move(0,0,t,&x,&y) && y<0);                  /* released: held */
        t+=100000; assert(!key_move(0,0,t,&x,&y));
        stick_circular=1;
        t+=16000; key_move(-1,-1,t,&x,&y);
        assert(x==-90 && y==-90);                                        /* round gate */
        stick_circular=0;
        t+=200000; key_move(0,0,t,&x,&y);
    }
    /* keyboard_movement=0.7 and the stick options are read from bbport.ini. */
    {
        char movement_path[]="/tmp/bbport-movement-XXXXXX";
        const int fd=mkstemp(movement_path);
        assert(fd>=0);
        const char text[]="keyboard_movement=0.7\nstick_socd=neutral\nstick_circular=1\n";
        assert(write(fd,text,sizeof(text)-1)==(ssize_t)(sizeof(text)-1));
        close(fd);
        const char *saved=getenv("BB_CONFIG");
        char saved_copy[512]; snprintf(saved_copy,sizeof saved_copy,"%s",saved ? saved : "");
        setenv("BB_CONFIG",movement_path,1);
        load_bindings();
        assert(key_movement_07 && !stick_socd_last && stick_circular);
        unlink(movement_path);
        setenv("BB_CONFIG",saved_copy,1);
        load_bindings();
        assert(!key_movement_07 && stick_socd_last && !stick_circular);
    }
    /* button_prompts=switch: another gamepad's prompts, with a Nintendo pad's art and labels. */
    {
        char prompts_path[]="/tmp/bbport-prompts-XXXXXX";
        const int fd=mkstemp(prompts_path);
        assert(fd>=0);
        const char text[]="button_prompts=switch\n";
        assert(write(fd,text,sizeof(text)-1)==(ssize_t)(sizeof(text)-1));
        close(fd);
        const char *saved=getenv("BB_CONFIG");
        char saved_copy[512]; snprintf(saved_copy,sizeof saved_copy,"%s",saved ? saved : "");
        setenv("BB_CONFIG",prompts_path,1);
        load_bindings();
        prompt_note(NULL,0,0);
        assert(runtime_pad_prompt_device()==1 && runtime_pad_prompt_nintendo());
        unlink(prompts_path);
        setenv("BB_CONFIG",saved_copy,1);
        load_bindings();
        assert(prompt_forced==-1);
    }
    puts("PASS: pad ABI, debug camera chord, left/right clicks, SDL touch coordinates, overlay capture, controls, mouse, stick neutral, round gate and dead zone, stick options, classic keyboard layout, keyboard movement, Switch prompts");
}
