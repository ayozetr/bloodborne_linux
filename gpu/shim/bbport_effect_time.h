// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include "bbport_guest_code.h"
#include <algorithm>
#include <cmath>

namespace BbFrameRate {
/// Particle lifetimes require whole 60 Hz steps. Keep the remainder, rather
/// than making the effects run faster than the simulation at 90/144 FPS
/// (community a9f292a7).
class EffectTime {
  public:
    float Advance(float dt) {
        if (!std::isfinite(dt) || dt <= 0.0f)
            return 0.0f;
        constexpr double step = 1.0 / 60.0;
        remainder += std::min(double(dt), 1.0 / 30.0);
        const auto steps = std::floor(remainder / step);
        remainder -= steps * step;
        return float(steps * step);
    }

  private:
    double remainder = 0.0;
};

/// Replaces the original flag branch + constant load, using our allocated stub
/// page. Keep the game's zero-time flag and skip the effect update on
/// substep-only frames.
inline BbGuestCode::Emitter EffectTimeStub(const void* advance, const float* dt, std::uint64_t call,
                                           std::uint64_t after_call) {
    BbGuestCode::Emitter e;
    e.Bytes({0x74, 0x0e}); // Original jne: a zero-time frame still calls with its
                           // original xmm0.
    e.JmpAbs(call);
    e.SaveVolatile();
    e.SaveXmm();
    e.CallAbs(advance);
    e.RestoreXmm();
    e.RestoreVolatile();
    e.Bytes({0x50, 0x48, 0xb8}); // push rax; movabs rax, dt
    e.U64(reinterpret_cast<std::uint64_t>(dt));
    e.Bytes({0xc5, 0xfa, 0x10, 0x00, 0x58});                   // vmovss xmm0,[rax]; pop rax
    e.Bytes({0x51, 0xc5, 0xf9, 0x7e, 0xc1, 0x85, 0xc9, 0x59}); // test float bits, preserve rcx
    e.Bytes({0x74, 0x0e});
    e.JmpAbs(call);
    e.JmpAbs(after_call);
    return e;
}
} // namespace BbFrameRate
