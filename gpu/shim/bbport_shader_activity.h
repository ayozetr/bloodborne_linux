// SPDX-License-Identifier: GPL-2.0-or-later
// bbport: whether shaders or pipelines are being compiled, for the overlay's notice. The pipeline
// cache counts every compilation (CompileTimer); the notice stays a moment after the last one
// ends, so a burst of short compilations does not make it flicker. From SrShadowy/bloodborne_pc
// (gpu/shim/bbport_shader_tracker).
#pragma once

#include <atomic>
#include <chrono>
#include <cstdint>

namespace BbShaderActivity {

inline std::atomic<std::uint32_t> active{0};
inline std::atomic<std::int64_t> last_end_ms{0};

inline std::int64_t NowMs() {
    return std::chrono::duration_cast<std::chrono::milliseconds>(
               std::chrono::steady_clock::now().time_since_epoch())
        .count();
}

inline void Begin() {
    active.fetch_add(1, std::memory_order_relaxed);
}

inline void End() {
    last_end_ms.store(NowMs(), std::memory_order_relaxed);
    active.fetch_sub(1, std::memory_order_release);
}

/// Milliseconds since the last compilation ended: 0 while one runs, -1 when none ever ran.
inline std::int64_t IdleMs() {
    if (active.load(std::memory_order_acquire) > 0) {
        return 0;
    }
    const std::int64_t end = last_end_ms.load(std::memory_order_relaxed);
    return end == 0 ? -1 : NowMs() - end;
}

} // namespace BbShaderActivity
