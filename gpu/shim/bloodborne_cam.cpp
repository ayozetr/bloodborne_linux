// SPDX-License-Identifier: GPL-2.0-or-later
// See bloodborne_cam.h.
#include "bloodborne_cam.h"

#include <cstdio>
#include <cstdlib>
#include <ctime>
#include <cstring>
#include <sys/mman.h>
#include <unistd.h>

// The direct mouse camera's hook: the game's camera update jumps here with the camera in r13,
// just before it loads the camera's pitch. The stub stamps the camera live, applies the mouse
// motion gathered since the last update (bbcam_apply) and runs the two loads it replaced.
// Turning the camera here, once per update, gives every frame exactly the motion since the one
// before; written from the window thread at any moment, a steady pan was split unevenly between
// frames and juddered by a pixel now and then. The game's registers are kept: its red zone is
// skipped, and what the System V ABI lets bbcam_apply change (rax, rcx, rdx, rsi, rdi, r8-r11,
// ymm0-15 whole, as the game's code is AVX, and the flags) is saved. Guest threads keep the
// port's fs (their TLS is gs), so port code runs there as in the other guest hooks. From
// Supermedo/bloodborne_pc d3a7584 (Ethan Murphy), written for Linux.
// `used`: only the asm below reads them, which link-time optimization does not see.
extern "C" {
__attribute__((used, visibility("hidden"))) std::uint64_t bbcam_apply_return = 0;
__attribute__((used, visibility("hidden"))) void bbcam_apply(std::uint64_t camera);
extern char bbcam_apply_stub[];
}
__asm__(".text\n"
        ".globl bbcam_apply_stub\n.hidden bbcam_apply_stub\nbbcam_apply_stub:\n"
        "  test %r13, %r13\n  jz 1f\n"
        "  movl $0x3F333333, 0x130(%r13)\n" // 0.7f: the camera is live
        "  lea -128(%rsp), %rsp\n  pushfq\n"
        "  push %rax\n  push %rcx\n  push %rdx\n  push %rsi\n  push %rdi\n"
        "  push %r8\n  push %r9\n  push %r10\n  push %r11\n  push %rbx\n"
        "  mov %rsp, %rbx\n  and $-32, %rsp\n  sub $512, %rsp\n"
        "  vmovdqu %ymm0, 0(%rsp)\n  vmovdqu %ymm1, 32(%rsp)\n  vmovdqu %ymm2, 64(%rsp)\n"
        "  vmovdqu %ymm3, 96(%rsp)\n  vmovdqu %ymm4, 128(%rsp)\n  vmovdqu %ymm5, 160(%rsp)\n"
        "  vmovdqu %ymm6, 192(%rsp)\n  vmovdqu %ymm7, 224(%rsp)\n  vmovdqu %ymm8, 256(%rsp)\n"
        "  vmovdqu %ymm9, 288(%rsp)\n  vmovdqu %ymm10, 320(%rsp)\n  vmovdqu %ymm11, 352(%rsp)\n"
        "  vmovdqu %ymm12, 384(%rsp)\n  vmovdqu %ymm13, 416(%rsp)\n  vmovdqu %ymm14, 448(%rsp)\n"
        "  vmovdqu %ymm15, 480(%rsp)\n"
        "  mov %r13, %rdi\n  call bbcam_apply\n"
        "  vmovdqu 0(%rsp), %ymm0\n  vmovdqu 32(%rsp), %ymm1\n  vmovdqu 64(%rsp), %ymm2\n"
        "  vmovdqu 96(%rsp), %ymm3\n  vmovdqu 128(%rsp), %ymm4\n  vmovdqu 160(%rsp), %ymm5\n"
        "  vmovdqu 192(%rsp), %ymm6\n  vmovdqu 224(%rsp), %ymm7\n  vmovdqu 256(%rsp), %ymm8\n"
        "  vmovdqu 288(%rsp), %ymm9\n  vmovdqu 320(%rsp), %ymm10\n  vmovdqu 352(%rsp), %ymm11\n"
        "  vmovdqu 384(%rsp), %ymm12\n  vmovdqu 416(%rsp), %ymm13\n  vmovdqu 448(%rsp), %ymm14\n"
        "  vmovdqu 480(%rsp), %ymm15\n"
        "  mov %rbx, %rsp\n"
        "  pop %rbx\n  pop %r11\n  pop %r10\n  pop %r9\n  pop %r8\n"
        "  pop %rdi\n  pop %rsi\n  pop %rdx\n  pop %rcx\n  pop %rax\n"
        "  popfq\n  lea 128(%rsp), %rsp\n"
        "  vmovss 0x140(%r13), %xmm0\n  vmovss 0x150(%r13), %xmm1\n" // the replaced loads
        "1:\n  jmp *bbcam_apply_return(%rip)\n");

namespace BbCamera {
namespace {
using u8 = std::uint8_t;
using u64 = std::uint64_t;
constexpr u64 ImageBase = 0x800000000ull; // as bbport_guest_hooks.cpp

/// The camera update: `vmovss xmm0, [r13 + 0x140]; vmovss xmm1, [r13 + 0x150]` (pitch, smoothed
/// pitch), with r13 the camera object. Jumped over to bbcam_apply_stub (the direct camera), or for
/// BB_CAM_TRACE to a stub that records r13.
constexpr u64 CamMain = 0x143ceaa;
constexpr std::size_t CamMainLen = 18;
constexpr u8 CamMainCode[CamMainLen] = {0xc4, 0xc1, 0x7a, 0x10, 0x85, 0x40, 0x01, 0x00, 0x00,
                                        0xc4, 0xc1, 0x7a, 0x10, 0x8d, 0x50, 0x01, 0x00, 0x00};
/// The game's own writes of the camera angles (vmovss [r13 + ...]): NOPs while the mouse drives
/// them. The same four as the "Disable Camera Auto Rotation via Movement" game patch (Imedved,
/// Kyo), so they may already be NOPs.
constexpr std::size_t NopLen = 9;
struct NopSite {
    u64 offset;
    u8 code[NopLen];
};
constexpr NopSite NopSites[4] = {
    {0x143c6e8, {0xc4, 0xc1, 0x7a, 0x11, 0x85, 0x44, 0x01, 0x00, 0x00}},
    {0x143c984, {0xc4, 0xc1, 0x7a, 0x11, 0x8d, 0x30, 0x01, 0x00, 0x00}},
    {0x143dde6, {0xc4, 0xc1, 0x7a, 0x11, 0x85, 0x94, 0x02, 0x00, 0x00}},
    {0x143c870, {0xc4, 0xc1, 0x7a, 0x11, 0xad, 0x44, 0x01, 0x00, 0x00}},
};
constexpr u8 Nop9[NopLen] = {0x90, 0x90, 0x90, 0x90, 0x90, 0x90, 0x90, 0x90, 0x90};
/// The Monocular's camera: [[[base] + 0x68] + 0x84] != 0 while it is up, its angles at
/// [[[base] + 0x68] + 0x68] + 0x148 / 0x14c.
constexpr u64 MonocularBase = 0x553e8d0;
constexpr float CountsPerRadian = 900.0f;
constexpr float Pi = 3.14159265f, TwoPi = 6.28318531f;

std::atomic<bool> configured{false}, enabled{false}, locked_on{false};
std::atomic<float> scale{1.0f};
/// Mouse motion gathered by the window thread since the camera's last update, and when that was.
std::atomic<float> pending_x{0.0f}, pending_y{0.0f};
std::atomic<std::int64_t> last_apply_ms{0};
u8 nop_saved[4][NopLen] = {};
u8* stub = nullptr;
bool reported_missing = false;

u8* At(u64 offset) {
    return reinterpret_cast<u8*>(ImageBase + offset);
}

/// [address, address + size) is mapped (mincore fails on a hole), so reading it cannot fault.
/// At most two pages: what the camera reads at once.
bool Mapped(u64 address, std::size_t size) {
    const long page = sysconf(_SC_PAGESIZE);
    if (address == 0 || address + size < address) {
        return false;
    }
    const u64 first = address & ~u64(page - 1);
    const u64 last = (address + size - 1) & ~u64(page - 1);
    unsigned char vec[2];
    return last - first <= u64(page) &&
           mincore(reinterpret_cast<void*>(first), last - first + page, vec) == 0;
}

/// Writes `size` bytes of code at `offset`: all but the first byte, then the first, so a thread
/// meeting the site decodes either the old instruction start or the new one.
bool WriteCode(u64 offset, const u8* bytes, std::size_t size) {
    const long page = sysconf(_SC_PAGESIZE);
    const u64 address = ImageBase + offset;
    void* first = reinterpret_cast<void*>(address & ~u64(page - 1));
    const std::size_t span = address + size - reinterpret_cast<u64>(first);
    if (mprotect(first, span, PROT_READ | PROT_WRITE | PROT_EXEC) != 0) {
        return false;
    }
    u8* p = At(offset);
    for (std::size_t i = 1; i < size; ++i) {
        __atomic_store_n(p + i, bytes[i], __ATOMIC_SEQ_CST);
    }
    __atomic_store_n(p, bytes[0], __ATOMIC_SEQ_CST);
    mprotect(first, span, PROT_READ | PROT_EXEC);
    return true;
}

/// BB_CAM_TRACE's stub: it records the camera object (r13) at +0x38, stamps the object
/// (+0x130 = 0.7f: the camera is live; the game's own write there is one of the NOPs), runs the
/// two instructions the jump covers and jumps back. Built once, never freed (a thread may be in it).
bool BuildStub() {
    if (stub) {
        return true;
    }
    void* p = mmap(nullptr, 4096, PROT_READ | PROT_WRITE | PROT_EXEC, MAP_PRIVATE | MAP_ANONYMOUS,
                   -1, 0);
    if (p == MAP_FAILED) {
        return false;
    }
    u8* t = static_cast<u8*>(p);
    const u8 head[] = {
        0x49, 0x85, 0xed,                         // 0x00 test r13, r13
        0x74, 0x2b,                               // 0x03 jz 0x30
        0x4c, 0x89, 0x2d, 0x2c, 0x00, 0x00, 0x00, // 0x05 mov [rip + 0x2c], r13 (to 0x38)
        0x41, 0xc7, 0x85, 0x30, 0x01, 0x00, 0x00, // 0x0c mov dword [r13 + 0x130], 0x3f333333
        0x33, 0x33, 0x33, 0x3f,
    };
    std::memcpy(t, head, sizeof(head));                  // up to 0x17
    std::memcpy(t + 0x17, CamMainCode, CamMainLen);      // 0x17: the covered instructions
    const u8 back[] = {0xff, 0x25, 0x11, 0x00, 0x00, 0x00, 0x90}; // 0x29 jmp [rip + 0x11] (0x40)
    std::memcpy(t + 0x29, back, sizeof(back));
    const u8 skip[] = {0xff, 0x25, 0x0a, 0x00, 0x00, 0x00, 0x90, 0x90}; // 0x30 jmp [rip + 0x0a]
    std::memcpy(t + 0x30, skip, sizeof(skip));
    const u64 none = 0, ret = ImageBase + CamMain + CamMainLen;
    std::memcpy(t + 0x38, &none, 8); // the camera object
    std::memcpy(t + 0x40, &ret, 8);  // back into the game
    stub = t;
    return true;
}

u64 Object() {
    return stub ? __atomic_load_n(reinterpret_cast<u64*>(stub + 0x38), __ATOMIC_ACQUIRE) : 0;
}

template <typename T>
T Read(u64 address) {
    return *reinterpret_cast<const volatile T*>(address);
}
template <typename T>
void Write(u64 address, T value) {
    *reinterpret_cast<volatile T*>(address) = value;
}
std::int64_t NowMs() {
    timespec now{};
    clock_gettime(CLOCK_MONOTONIC, &now);
    return std::int64_t(now.tv_sec) * 1000 + now.tv_nsec / 1000000;
}
void AddFloat(std::atomic<float>& value, float add) {
    float old = value.load(std::memory_order_relaxed);
    while (!value.compare_exchange_weak(old, old + add, std::memory_order_relaxed)) {
    }
}
float WrapYaw(float yaw) {
    while (yaw > Pi) {
        yaw -= TwoPi;
    }
    while (yaw < -Pi) {
        yaw += TwoPi;
    }
    return yaw;
}
} // namespace

void Configure(bool direct, float sensitivity) {
    if (!(sensitivity > 0.0f) || sensitivity > 20.0f) {
        sensitivity = 1.0f;
    }
    scale.store(sensitivity, std::memory_order_relaxed);
    configured.store(direct, std::memory_order_relaxed);
}

bool Configured() {
    return configured.load(std::memory_order_relaxed);
}

bool Enabled() {
    return enabled.load(std::memory_order_acquire);
}

bool LockedOn() {
    return locked_on.load(std::memory_order_relaxed);
}

bool SetEnabled(bool on) {
    if (on == enabled.load(std::memory_order_relaxed)) {
        return on;
    }
    if (!on) {
        // Motion stops first, then the game's code comes back as it was.
        enabled.store(false, std::memory_order_release);
        locked_on.store(false, std::memory_order_relaxed);
        WriteCode(CamMain, CamMainCode, CamMainLen);
        for (int i = 0; i < 4; ++i) {
            WriteCode(NopSites[i].offset, nop_saved[i], NopLen);
        }
        std::printf("Mouse camera: direct mode off\n");
        return false;
    }
    // Only the 1.09 camera code (or its NOPs from the auto-rotation patch) is hooked.
    bool expected = Mapped(ImageBase + CamMain, CamMainLen) &&
                    std::memcmp(At(CamMain), CamMainCode, CamMainLen) == 0;
    for (int i = 0; expected && i < 4; ++i) {
        expected = Mapped(ImageBase + NopSites[i].offset, NopLen) &&
                   (std::memcmp(At(NopSites[i].offset), NopSites[i].code, NopLen) == 0 ||
                    std::memcmp(At(NopSites[i].offset), Nop9, NopLen) == 0);
    }
    if (!expected) {
        if (!reported_missing) {
            reported_missing = true;
            std::printf("Mouse camera: the game's camera code is not the 1.09 code; the mouse "
                        "stays on the stick\n");
        }
        return false;
    }
    for (int i = 0; i < 4; ++i) {
        std::memcpy(nop_saved[i], At(NopSites[i].offset), NopLen);
    }
    // jmp [rip + 0] to the stub, then NOPs up to the end of the two covered instructions.
    u8 jump[CamMainLen];
    std::memset(jump, 0x90, sizeof(jump));
    jump[0] = 0xff;
    jump[1] = 0x25;
    std::memset(jump + 2, 0, 4);
    bbcam_apply_return = ImageBase + CamMain + CamMainLen;
    pending_x.store(0.0f, std::memory_order_relaxed);
    pending_y.store(0.0f, std::memory_order_relaxed);
    const u64 target = reinterpret_cast<u64>(bbcam_apply_stub);
    std::memcpy(jump + 6, &target, 8);
    if (!WriteCode(CamMain, jump, CamMainLen)) {
        std::printf("Mouse camera: the game's code is not writable; the mouse stays on the stick\n");
        return false;
    }
    for (int i = 0; i < 4; ++i) {
        WriteCode(NopSites[i].offset, Nop9, NopLen);
    }
    locked_on.store(false, std::memory_order_relaxed);
    enabled.store(true, std::memory_order_release);
    std::printf("Mouse camera: direct mode on\n");
    return true;
}

void OnMouseMotion(float xrel, float yrel) {
    // Locked on, window.cpp sends the motion to the stick instead.
    if (!enabled.load(std::memory_order_acquire) || locked_on.load(std::memory_order_relaxed)) {
        return;
    }
    // While the camera is not updated (a loading screen), motion is not saved up for later.
    if (NowMs() - last_apply_ms.load(std::memory_order_relaxed) > 100) {
        pending_x.store(xrel, std::memory_order_relaxed);
        pending_y.store(yrel, std::memory_order_relaxed);
        return;
    }
    AddFloat(pending_x, xrel);
    AddFloat(pending_y, yrel);
}

namespace {
/// The game thread, in its camera update (bbcam_apply_stub): turns the camera `cam` by the motion
/// gathered since the last update. `cam` is the object the game is about to read.
void Apply(u64 cam) {
    last_apply_ms.store(NowMs(), std::memory_order_relaxed);
    if (!enabled.load(std::memory_order_acquire)) {
        return;
    }
    const float xrel = pending_x.exchange(0.0f, std::memory_order_relaxed);
    const float yrel = pending_y.exchange(0.0f, std::memory_order_relaxed);
    // Locked on: the game drives the camera (checked every update).
    const bool locked = Read<float>(cam + 0x154) == 1.0f;
    locked_on.store(locked, std::memory_order_relaxed);
    if (locked || (xrel == 0.0f && yrel == 0.0f)) {
        return;
    }
    const float s = scale.load(std::memory_order_relaxed);
    const float d_pitch = yrel / CountsPerRadian * s;
    const float d_yaw = xrel / CountsPerRadian * s;

    // The Monocular has its own angles, turned at half the speed.
    if (const u64 p1 = Read<u64>(ImageBase + MonocularBase); Mapped(p1 + 0x68, 8)) {
        const u64 p2 = Read<u64>(p1 + 0x68);
        if (Mapped(p2 + 0x68, 0x20) && Read<int>(p2 + 0x84) != 0) {
            if (const u64 p3 = Read<u64>(p2 + 0x68); Mapped(p3 + 0x148, 8)) {
                float pitch = Read<float>(p3 + 0x148) + d_pitch * 0.5f;
                pitch = pitch > 1.71f ? 1.71f : pitch < -1.94f ? -1.94f : pitch;
                Write<float>(p3 + 0x148, pitch);
                Write<float>(p3 + 0x14c, WrapYaw(Read<float>(p3 + 0x14c) + d_yaw * 0.5f));
                return;
            }
        }
    }

    float pitch = Read<float>(cam + 0x140) + d_pitch;
    float min_pitch = Read<float>(cam + 0x1f0), max_pitch = Read<float>(cam + 0x1ec);
    if (min_pitch >= max_pitch || min_pitch < -3.0f || max_pitch > 3.0f) {
        min_pitch = -1.94f;
        max_pitch = 1.71f;
    }
    pitch = pitch > max_pitch ? max_pitch : pitch < min_pitch ? min_pitch : pitch;
    const float yaw = WrapYaw(Read<float>(cam + 0x144) + d_yaw);
    // Target, smoothed and converging pitch; target and converging yaw.
    Write<float>(cam + 0x140, pitch);
    Write<float>(cam + 0x150, pitch);
    Write<float>(cam + 0x26c, pitch);
    Write<float>(cam + 0x144, yaw);
    Write<float>(cam + 0x270, yaw);
}
} // namespace

extern "C" __attribute__((used)) void bbcam_apply(std::uint64_t camera) {
    Apply(camera);
}


namespace {
/// CamMain jumps to the stub (which records the camera object), the game's camera code otherwise
/// untouched. For BB_CAM_TRACE.
bool InstallRecorder() {
    if (!Mapped(ImageBase + CamMain, CamMainLen) ||
        std::memcmp(At(CamMain), CamMainCode, CamMainLen) != 0 || !BuildStub()) {
        return false;
    }
    u8 jump[CamMainLen];
    std::memset(jump, 0x90, sizeof(jump));
    jump[0] = 0xff;
    jump[1] = 0x25;
    std::memset(jump + 2, 0, 4);
    const u64 target = reinterpret_cast<u64>(stub);
    std::memcpy(jump + 6, &target, 8);
    return WriteCode(CamMain, jump, CamMainLen);
}
} // namespace

void TraceTick() {
    static const char* path = std::getenv("BB_CAM_TRACE");
    static std::FILE* file = nullptr;
    static bool failed = false;
    static float last_yaw = 0.0f, last_pitch = 0.0f;
    if (path == nullptr || *path == '\0' || failed) {
        return;
    }
    if (configured.load(std::memory_order_relaxed)) {
        // The direct mouse camera owns the hook (bbport.ini is read after the window is up): the
        // camera code goes back as it was for it, and the trace stops.
        if (file != nullptr && !enabled.load(std::memory_order_acquire) &&
            Mapped(ImageBase + CamMain, CamMainLen) && At(CamMain)[0] == 0xff) {
            WriteCode(CamMain, CamMainCode, CamMainLen);
        }
        failed = file != nullptr;
        if (failed) {
            std::printf("Camera trace: off (mouse_camera=direct)\n");
        }
        return;
    }
    if (file == nullptr) {
        if (!Mapped(ImageBase + CamMain, CamMainLen)) {
            return; // the game is not loaded yet
        }
        if (!InstallRecorder() || (file = std::fopen(path, "w")) == nullptr) {
            failed = true;
            std::printf("Camera trace: could not start (%s)\n", path);
            return;
        }
        std::printf("Camera trace: yaw and pitch to %s\n", path);
    }
    // The window comes up before the game's image is loaded: loading it writes the camera code
    // over the jump, which then goes in again.
    if (std::memcmp(At(CamMain), CamMainCode, CamMainLen) == 0 && InstallRecorder()) {
        std::printf("Camera trace: camera code hooked\n");
    }
    const u64 cam = Object();
    if (cam == 0 || !Mapped(cam + 0x140, 8)) {
        return;
    }
    const float pitch = Read<float>(cam + 0x140), yaw = Read<float>(cam + 0x144);
    if (yaw == last_yaw && pitch == last_pitch) {
        return;
    }
    last_yaw = yaw;
    last_pitch = pitch;
    timespec now{};
    clock_gettime(CLOCK_MONOTONIC, &now);
    std::fprintf(file, "%.3f %.6f %.6f\n", now.tv_sec * 1000.0 + now.tv_nsec / 1e6, yaw, pitch);
    std::fflush(file);
}

} // namespace BbCamera
