// SPDX-FileCopyrightText: Copyright 2026 bbport contributors
// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once

#include <cstdint>
#include <cstring>
#include <span>

namespace BbEffectFlags {

// Bloodborne 1.09: 0x22c4cb3 clears SSAO when the context's capability bit 3
// (+0x48) is absent. 0x22a3efb uses the target at +0x10d0 via 0xe669a0,
// then dereferences its result without a null check at 0x22a3f07.
// A live preference must not re-enable this pass on a context without its target.
inline bool SsaoEnabled(std::span<const std::uint8_t> context, bool requested) {
    constexpr std::size_t target = 0x10d0;
    if (!requested || context.size() < target + 0x1b9) {
        return false;
    }
    std::uint64_t capabilities = 0;
    std::memcpy(&capabilities, context.data() + 0x48, sizeof(capabilities));
    if (!(capabilities & 8)) {
        return false;
    }
    // The same selector as guest 0xe669a0. A target may not yet be initialized,
    // even when the context is configured to support SSAO.
    const bool alternate = context[target + 0x1b8] && context[target + 0x189];
    std::uint64_t resource = 0;
    std::memcpy(&resource, context.data() + target + (alternate ? 0xc0 : 0x68), sizeof(resource));
    return resource != 0;
}

// Setup (0x22c39f0) runs after the constructor whose tail reports the context, so these say
// only whether a live preference may turn a pass back on; a context without support keeps
// the switch the game left.

// 0x22c3d8f builds the half-size velocity maps (+0xce0, +0xd38; 0x2266420 keeps each resource
// at +0x18) and the motion blur object (+0x28b0) only with capability 0x420, and 0x22c3e62
// clears motion blur otherwise. 0x229ef1b and 0x22ab35b take [+0xcf8] and [+0xd50] unchecked.
inline bool MotionBlurSupported(std::span<const std::uint8_t> context) {
    if (context.size() < 0xd58) {
        return false;
    }
    std::uint64_t capabilities = 0;
    std::uint64_t velocity = 0;
    std::uint64_t velocity_other = 0;
    std::memcpy(&capabilities, context.data() + 0x48, sizeof(capabilities));
    std::memcpy(&velocity, context.data() + 0xcf8, sizeof(velocity));
    std::memcpy(&velocity_other, context.data() + 0xd50, sizeof(velocity_other));
    return (capabilities & 0x420) && velocity != 0 && velocity_other != 0;
}

// 0x22c4e36 builds the game's anti-aliasing (FXAA, +0x1bc8 via 0xe58b00) only with capability
// 0x10, and 0x22c4e75 clears it otherwise.
inline bool GameAaSupported(std::span<const std::uint8_t> context) {
    if (context.size() < 0x50) {
        return false;
    }
    std::uint64_t capabilities = 0;
    std::memcpy(&capabilities, context.data() + 0x48, sizeof(capabilities));
    return (capabilities & 0x10) != 0;
}

} // namespace BbEffectFlags
