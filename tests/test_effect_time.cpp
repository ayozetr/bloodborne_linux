// SPDX-License-Identifier: GPL-2.0-or-later
#include "bbport_effect_time.h"
#include <cassert>
#include <cmath>
#include <cstring>
#include <limits>
#include <sys/mman.h>

namespace {
BbFrameRate::EffectTime clock_step;
float input, output;
int advances, calls, skipped;
void Advance() {
    ++advances;
    output = clock_step.Advance(input);
}
float Called(float dt) {
    ++calls;
    return dt;
}
float Skipped() {
    ++skipped;
    return -1.0f;
}

float Invoke(const void* entry, bool zero_time) {
    return reinterpret_cast<float (*)(int)>(const_cast<void*>(entry))(int(zero_time));
}
} // namespace
int main() {
    for (int rate : {30, 60, 90, 120, 144, 240, 480}) {
        BbFrameRate::EffectTime clock;
        double elapsed = 0.0, simulated = 0.0;
        for (int frame = 0; frame < rate * 120; ++frame) {
            const float dt = 1.0f / rate;
            const float step = clock.Advance(dt);
            elapsed += std::min(double(dt), 1.0 / 30.0);
            simulated += step;
            assert(step == 0.0f || std::abs(step * 60.0f - std::round(step * 60.0f)) < 1e-5f);
            assert(std::abs(simulated - elapsed) < 1.0 / 60.0 + 1e-4);
        }
    }
    BbFrameRate::EffectTime clock;
    assert(clock.Advance(std::numeric_limits<float>::infinity()) == 0.0f);
    assert(clock.Advance(std::numeric_limits<float>::quiet_NaN()) == 0.0f);
    assert(clock.Advance(-1.0f) == 0.0f);
    const auto stub = BbFrameRate::EffectTimeStub(reinterpret_cast<const void*>(&Advance), &output,
                                                  reinterpret_cast<uintptr_t>(&Called),
                                                  reinterpret_cast<uintptr_t>(&Skipped));
    assert(!stub.overflow);
    void* code = mmap(nullptr, 4096, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    assert(code != MAP_FAILED);
    std::memcpy(code, stub.code.data(), stub.size);
    BbGuestCode::Emitter entry;
    entry.Bytes({0x0f, 0x57, 0xc0, 0x85, 0xff}); // xorps xmm0,xmm0; test edi,edi
    entry.JmpAbs(reinterpret_cast<uintptr_t>(code));
    void* call_entry = static_cast<char*>(code) + 1024;
    std::memcpy(call_entry, entry.code.data(), entry.size);
    assert(mprotect(code, 4096, PROT_READ | PROT_EXEC) == 0);
    input = 1.0f / 144.0f;
    assert(Invoke(call_entry, false) == -1.0f); // No complete effect step yet.
    assert(Invoke(call_entry, false) == -1.0f);
    assert(std::abs(Invoke(call_entry, false) - 1.0f / 60.0f) < 1e-7f);
    assert(advances == 3 && calls == 1 && skipped == 2);
    assert(Invoke(call_entry, true) == 0.0f); // Original zero-time flag bypasses our accumulator.
    assert(advances == 3 && calls == 2 && skipped == 2);
    munmap(code, 4096);
}
