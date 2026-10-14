#define _GNU_SOURCE
#include <assert.h>
#include <unistd.h>
#include "../src/runtime_pad.c"

static int capture;
int bbgpu_overlay_captures_input(void) { return capture; }
void bbgpu_mouse_take(double *dx, double *dy, int *up, int *down) { *dx=*dy=0; *up=*down=0; }
int bbgpu_mouse_captured(void) { return 0; }
void bbgpu_mouse_look_enable(int enabled) { (void)enabled; }
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
                          "pad.r1=righttrigger\nkey.cross=X, Space\npad.bogus=a\n";
    assert(write(config_fd,controls,sizeof(controls)-1)==(ssize_t)(sizeof(controls)-1));
    close(config_fd);
    setenv("BB_CONFIG",config,1);
    setenv("SDL_VIDEODRIVER","dummy",1);
    /* Only the virtual test controller is a gamepad, whatever is plugged in. */
    SDL_SetHint(SDL_HINT_GAMECONTROLLER_IGNORE_DEVICES_EXCEPT,"0x1d50/0x6189");
    assert(SDL_Init(SDL_INIT_VIDEO|SDL_INIT_GAMEPAD));
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
    /* Buttons still held when a menu closes stay hidden until all are released (hold_after_capture). */
    assert(pad_read_state(1,&data)==0 && data.touch_count==1 && data.touches[0].x==480 &&
           data.buttons==0);
    assert(SDL_SetJoystickVirtualButton(joystick,SDL_GAMEPAD_BUTTON_TOUCHPAD,false));
    assert(SDL_SetJoystickVirtualTouchpad(joystick,0,0,false,0,0,0));
    SDL_UpdateJoysticks();
    SDL_UpdateGamepads();
    assert(pad_read_state(1,&data)==0 && data.buttons==0 && !hold_after_capture);
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
    /* Keyboard movement: opposite keys, the last pressed wins (or cancel out with
     * stick_socd=neutral); a diagonal stays within a round gate (unless stick_circular=0). */
    {
        bool keys[SDL_SCANCODE_COUNT]={0};
        const int a_key=bindings[IN_MOVE_LEFT].keys[0], d_key=bindings[IN_MOVE_RIGHT].keys[0];
        const int w_key=bindings[IN_MOVE_UP].keys[0];
        PadData m={0};
        m.left_x=m.left_y=128;
        keys[a_key]=1; apply_keyboard(&m,keys); assert(m.left_x==0);
        keys[d_key]=1; apply_keyboard(&m,keys); assert(m.left_x==255); /* D pressed last */
        keys[a_key]=0; apply_keyboard(&m,keys); assert(m.left_x==255);
        keys[a_key]=1; apply_keyboard(&m,keys); assert(m.left_x==0);   /* now A is the last */
        keys[a_key]=keys[d_key]=0;
        stick_socd_last=0;
        keys[a_key]=1; apply_keyboard(&m,keys);
        keys[d_key]=1; apply_keyboard(&m,keys); assert(m.left_x==128);
        stick_socd_last=1; keys[a_key]=keys[d_key]=0;
        keys[w_key]=keys[a_key]=1; apply_keyboard(&m,keys);
        assert(m.left_x==128-90 && m.left_y==128-90);
        stick_circular=0; apply_keyboard(&m,keys);
        assert(m.left_x==0 && m.left_y==0);
        stick_circular=1; keys[w_key]=keys[a_key]=0;
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
    puts("PASS: pad ABI, debug camera chord, left/right clicks, SDL touch coordinates, overlay capture, controls, mouse, keyboard movement, round gate");
}
