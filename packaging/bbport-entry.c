// Entry point of the packaged port (the AppImage's): a static program that removes the host's
// library injection from the environment, then runs the real wrapper (TARGET).
//
// Steam starts every non-Steam game with LD_PRELOAD=.../gameoverlayrenderer.so (any
// compatibility tool, Steam Deck included). Loaded into this package's own glibc, the overlay
// cannot find its libGL.so.1 and the first dynamic program, the wrapper's bash, exits at once:
// "error while loading shared libraries: libGL.so.1". Being static, this program is not affected.
// LD_LIBRARY_PATH, GTK_PATH and the like name host libraries just as incompatible with the
// package; Steam's Vulkan layers (overlay, fossilize) are host libraries too.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#ifndef TARGET
#error "TARGET: the wrapper to run"
#endif

static void drop(const char* name) {
    const char* value = getenv(name);
    if (!value || !*value) {
        unsetenv(name);
        return;
    }
    // Kept for diagnostics (the launcher's log shows the environment problems).
    char saved[128];
    snprintf(saved, sizeof saved, "BB_HOST_%s", name);
    setenv(saved, value, 1);
    unsetenv(name);
}

// deadinside28#172: in Steam's Game Mode a non-Steam game runs in pressure-vessel, which points
// Vulkan at its own driver and layer manifests. They are not the user's choice, and with them the
// package's Mesa was never registered and the window had no VK_KHR_surface. Dropped like the
// variables above; the host's gamescope WSI layer, a host library too, is turned off with them.
static int drop_pressure_vessel(void) {
    static const char* const vulkan[] = {
        "VK_DRIVER_FILES", "VK_ICD_FILENAMES", "VK_ADD_DRIVER_FILES", "VK_IMPLICIT_LAYER_PATH",
        "VK_LAYER_PATH", "VK_ADD_LAYER_PATH",
    };
    int dropped = 0;
    for (size_t i = 0; i < sizeof vulkan / sizeof vulkan[0]; ++i) {
        const char* value = getenv(vulkan[i]);
        if (value && strstr(value, "/pressure-vessel/")) {
            drop(vulkan[i]);
            dropped = 1;
        }
    }
    return dropped;
}

int main(int argc, char** argv) {
    (void)argc;
    static const char* const host_only[] = {
        "LD_PRELOAD", "LD_LIBRARY_PATH", "LD_AUDIT", "GTK_PATH", "GTK_MODULES", "GTK_EXE_PREFIX",
        "GIO_EXTRA_MODULES", "GDK_PIXBUF_MODULEDIR", "PYTHONHOME", "PYTHONPATH",
    };
    for (size_t i = 0; i < sizeof host_only / sizeof host_only[0]; ++i) {
        drop(host_only[i]);
    }
    if (drop_pressure_vessel()) {
        setenv("DISABLE_GAMESCOPE_WSI", "1", 1);
    }
    setenv("DISABLE_VK_LAYER_VALVE_steam_overlay_1", "1", 1);
    setenv("DISABLE_VK_LAYER_VALVE_steam_fossilize_1", "1", 1);
    argv[0] = (char*)TARGET;
    execv(TARGET, argv);
    perror("bbport: " TARGET);
    return 127;
}
