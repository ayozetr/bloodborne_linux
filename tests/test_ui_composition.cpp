// SPDX-License-Identifier: GPL-2.0-or-later
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <sys/wait.h>
#include <unistd.h>
#include "gpu/shadps4/video_core/renderer_vulkan/ui_composition.h"

int main() {
    using namespace Vulkan::UiComposition;
    // Ultrawide: a 2580x1080 HUD canvas (BB_UI_RES, run.sh) scales uniformly to 3440x1440. Read
    // once per process: checked in a child, the rest with the game's own 1920x1080 canvas.
    if (const pid_t child = fork(); child == 0) {
        setenv("BB_UI_RES", "2580x1080", 1);
        const auto wide = Scale(960, 540, 3440, 1440, true);
        _exit(Canvas()[0] == 2580 && Canvas()[1] == 1080 && NativeViewport(2580, -1080) &&
                      !NativeViewport(1920, -1080) && std::abs(wide[0] - 4.0f / 3.0f) < 1e-5f &&
                      std::abs(wide[1] - 4.0f / 3.0f) < 1e-5f
                  ? 0 : 1);
    } else {
        int status = 0;
        assert(child > 0 && waitpid(child, &status, 0) == child && WIFEXITED(status) &&
               WEXITSTATUS(status) == 0);
    }
    unsetenv("BB_UI_RES");
    // Title/loading menus have no depth/camera. UI must still go to the native target.
    assert(Choose(true, true, false, true) == Background::Copy);
    assert(Choose(true, true, false, false) == Background::Copy);
    // In-game HUD: first reconstruct the scene, then draw the native UI over it.
    assert(Choose(true, true, true, true) == Background::Temporal);
    // Runtime FSR disable/failure must not change UI resolution.
    assert(Choose(true, true, true, false) == Background::Copy);
    assert(Choose(true, false, true, true) == Background::None);
    assert(Choose(false, true, true, true) == Background::None);
    assert(NativeViewport(1920, -1080));
    assert(!NativeViewport(960, -540));
    assert(MovieShader(0x34e8a281) && MovieShader(0x24042a9b));
    assert(!MovieShader(0x0b0acf50)); // fullscreen post/tonemap also has a native viewport
    assert(!MovieShader(0x6c62a79f)); // shadow geometry
    const auto display = Scale(960, 540, 1920, 1080, false);
    assert(display[0] == 2 && display[1] == 2);
    const auto ui = Scale(960, 540, 1920, 1080, true);
    assert(ui[0] == 1 && ui[1] == 1); // don't double an already native UI viewport
    const auto larger = Scale(960, 540, 3840, 2160, true);
    assert(larger[0] == 2 && larger[1] == 2);
    std::puts("UI composition: PASS (menu without camera, HUD, FSR off, viewport scaling, "
              "ultrawide canvas)");
}
