/* bbport: the pad with Hunter's Atlas on (BB_ATLAS_ENABLED=1): what the map and its tile take
 * from the pad, neutral input while they hold it, and buttons still held afterwards kept from the
 * game until released (src/runtime_pad.c, sample_atlas). tests/test_pad.c covers it off. */
#define _GNU_SOURCE
#include <assert.h>
#include <unistd.h>
#include "../src/runtime_pad.c"

static int capture;          /* the overlay or the map holds the input */
static uint32_t atlas_takes; /* buttons the tile or the map uses */
int bbgpu_overlay_captures_input(void) { return capture; }
uint32_t bbgpu_atlas_route_pad(uint32_t buttons, uint8_t lx, uint8_t ly, uint8_t rx, uint8_t ry) {
    (void)lx; (void)ly; (void)rx; (void)ry; return buttons & ~atlas_takes;
}
void bbgpu_mouse_take(double *dx, double *dy, int *up, int *down) { *dx=*dy=0; *up=*down=0; }
int bbgpu_mouse_captured(void) { return 0; }
void bbgpu_mouse_look_enable(int enabled) { (void)enabled; }
void bbgpu_mouse_camera_configure(int direct, float sensitivity) { (void)direct; (void)sensitivity; }
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
    char path[]="/tmp/bbport-pad-atlas-XXXXXX";
    int fd=mkstemp(path);
    assert(fd>=0);
    close(fd);
    setenv("BB_PAD_FILE",path,1);
    setenv("BB_ATLAS_ENABLED","1",1);
    unsetenv("BB_CONFIG");
    setenv("SDL_VIDEODRIVER","dummy",1);
    SDL_SetHint(SDL_HINT_GAMECONTROLLER_IGNORE_DEVICES_EXCEPT,"0x0000/0x0000"); /* no real pad */
    assert(SDL_Init(SDL_INIT_VIDEO|SDL_INIT_GAMEPAD));
    assert(atlas_on());
    PadData d;
    /* Nothing open: the game gets the pad. */
    inject(path,"cross square");
    sample(&d);
    assert((d.buttons & (BTN_CROSS|BTN_SQUARE))==(BTN_CROSS|BTN_SQUARE));
    /* The tile takes Cross (its focus confirm): the game gets the rest. */
    atlas_takes=BTN_CROSS;
    sample(&d);
    assert(!(d.buttons & BTN_CROSS) && (d.buttons & BTN_SQUARE));
    atlas_takes=0;
    /* The map open: neutral input, whatever is held. */
    capture=1;
    inject(path,"cross square lx=0 ly=255");
    sample(&d);
    assert(!d.buttons && d.left_x==128 && d.left_y==128 && !d.l2 && !d.r2);
    /* Closed with Cross and the stick still held: hidden from the game until released. */
    capture=0;
    sample(&d);
    assert(!(d.buttons & (BTN_CROSS|BTN_SQUARE)) && d.left_x==128 && d.left_y==128);
    inject(path,"square");
    sample(&d);
    assert(!d.buttons); /* Square was held throughout: still hidden */
    inject(path,"");
    sample(&d);
    assert(!d.buttons);
    /* Pressed again after the release: the game gets it. */
    inject(path,"cross");
    sample(&d);
    assert(d.buttons & BTN_CROSS);
    unlink(path);
    SDL_Quit();
    puts("PASS: Hunter's Atlas pad routing: tile takes, neutral while open, held buttons hidden after");
    return 0;
}
