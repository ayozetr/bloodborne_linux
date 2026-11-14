// SPDX-FileCopyrightText: Copyright 2026 bbport contributors
// SPDX-License-Identifier: GPL-2.0-or-later
#include "bbport_effect_flags.h"

#include <array>
#include <cassert>
#include <cstdio>

int main() {
    std::array<std::uint8_t, 0x29a0> context{};
    const auto put = [&](std::size_t offset, std::uint64_t value) {
        std::memcpy(context.data() + offset, &value, sizeof(value));
    };
    // A menu/auxiliary context must stay off despite the user's enabled preference.
    assert(!BbEffectFlags::SsaoEnabled(context, true));
    put(0x10d0 + 0x68, 0x1040000000ull);
    assert(!BbEffectFlags::SsaoEnabled(context, true));
    put(0x48, 8);
    assert(BbEffectFlags::SsaoEnabled(context, true));
    assert(!BbEffectFlags::SsaoEnabled(context, false));
    // Follow both selector flags exactly; do not use a nonselected target as fallback.
    context[0x10d0 + 0x1b8] = 1;
    assert(BbEffectFlags::SsaoEnabled(context, true));
    context[0x10d0 + 0x189] = 1;
    assert(!BbEffectFlags::SsaoEnabled(context, true));
    put(0x10d0 + 0xc0, 0x1041000000ull);
    assert(BbEffectFlags::SsaoEnabled(context, true));
    // Removing/reinitializing a target must disable the pass again.
    put(0x10d0 + 0xc0, 0);
    assert(!BbEffectFlags::SsaoEnabled(context, true));
    assert(!BbEffectFlags::SsaoEnabled(std::span(context).first(0x1288), true));
    std::puts("effect-flags: SSAO context capability and target selection OK");

    // Motion blur: only where setup built both velocity maps (capability 0x420).
    context = {};
    assert(!BbEffectFlags::MotionBlurSupported(context));
    put(0xcf8, 0x1042000000ull);
    put(0xd50, 0x1043000000ull);
    assert(!BbEffectFlags::MotionBlurSupported(context));
    put(0x48, 0x2207); // the game's 128x128 context: no 0x420
    assert(!BbEffectFlags::MotionBlurSupported(context));
    put(0x48, 0x20);
    assert(BbEffectFlags::MotionBlurSupported(context));
    put(0x48, 0x400);
    assert(BbEffectFlags::MotionBlurSupported(context));
    // Capability without the maps (setup not done, or released): not yet.
    put(0xd50, 0);
    assert(!BbEffectFlags::MotionBlurSupported(context));
    put(0xd50, 0x1043000000ull);
    put(0xcf8, 0);
    assert(!BbEffectFlags::MotionBlurSupported(context));
    assert(!BbEffectFlags::MotionBlurSupported(std::span(context).first(0xd50)));
    std::puts("effect-flags: motion blur context capability and velocity maps OK");

    // The game's anti-aliasing: capability 0x10 only.
    context = {};
    assert(!BbEffectFlags::GameAaSupported(context));
    put(0x48, 0x2207 & ~0x10ull);
    assert(!BbEffectFlags::GameAaSupported(context));
    put(0x48, 0x10);
    assert(BbEffectFlags::GameAaSupported(context));
    assert(!BbEffectFlags::GameAaSupported(std::span(context).first(0x48)));
    std::puts("effect-flags: game AA context capability OK");
}
