// SPDX-License-Identifier: GPL-2.0-or-later
#include "bbport_guest_hooks.h"
#include "bbport_heap_sites.h"
#include "bbport_toggles.h"
#include "bbport_guest_code_hooks.h"

#include <array>
#include <atomic>
#include <chrono>
#include <pthread.h>
#include <csignal>
#include <cstdint>
#include <cstdlib>
#include <cstdio>
#include <cstring>
#include <sys/mman.h>
#include <sys/uio.h>
#include <ucontext.h>
#include <unistd.h>

extern "C" void runtime_memory_note_write(uintptr_t address, uint64_t size);

namespace BbGuestHooks {
namespace {
using u64 = std::uint64_t;
using u8 = std::uint8_t;
constexpr u64 ImageBase = 0x800000000ull;

/// The return of the game's GPU memory range allocator 0x26aa070 (rdi allocator, rsi size,
/// rdx alignment; it returns a node: [node + 8] the start, [[node + 0x18] + 8] the end, the next
/// node's start): `add rsp, 0x18` in its epilogue, reached by its own branches only.
constexpr u64 AllocReturn = 0x26aa255;
constexpr unsigned char AllocReturnCode[4] = {0x48, 0x83, 0xc4, 0x18};
RangeCallback on_range_allocated = nullptr;

/// The game's other GPU memory heap (TLSF-like, headers in the memory: free at 0x20858a0, alloc at
/// 0x2085a60), reached through a pointer at 0x54b9f38 set at startup. Its only three callers
/// (wrappers that record {address, size} in a map) pass r8 = rbp - 0x50 for the size handed out and
/// follow the call with `mov rbx, rax` (rax: the address).
constexpr std::array<u64, 3> HeapAllocReturns = {0x11e6629, 0x11e6736, 0x11e6846};
constexpr unsigned char HeapAllocReturnCode[3] = {0x48, 0x89, 0xc3};

/// BB_FRAME_STATS: the range allocator's collector (0x26aa860, `push rbp`; rdi the allocator): its
/// live range count [+0xc8] and byte count [+0xd0] are noted for the frame stats.
constexpr u64 CollectorEntry = 0x26aa860;
constexpr unsigned char CollectorEntryCode[1] = {0x55};

/// BB_HEAP_SITES=1: the game's deferred object release (0xbb5f10) skips the destruction when the
/// registry check (0xbf0790) fails: `js 0xbb5fc7` there, its result counted (eax).
constexpr u64 ReleaseCheck = 0xbb5fb0;
constexpr unsigned char ReleaseCheckCode[2] = {0x78, 0x15};

/// `call memcpy` (0x261a1b0: rdi destination, rsi source, rdx size) in the resource loaders:
/// 0x216d420 and 0x2171d60 copy texture and buffer data into GPU memory (most of the write
/// faults while areas stream in).
struct CallSite {
    u64 offset;
    unsigned char code[5];
};
constexpr std::array<CallSite, 2> MemcpySites = {{
    {0x216d5ea, {0xe8, 0xc1, 0xcb, 0x4a, 0x00}},
    {0x2171fea, {0xe8, 0xc1, 0x81, 0x4a, 0x00}},
}};
std::array<std::atomic<u64>, MemcpySites.size()> hits{};

/// The game's memcpy at those sites: the GPU side is told before (its write traps lift: no fault
/// per page) and after the copy (the data now there), as for file reads.
void* LoaderCopy(void* dst, const void* src, std::size_t size) {
    runtime_memory_note_write(reinterpret_cast<u64>(dst), size);
    std::memcpy(dst, src, size);
    runtime_memory_note_write(reinterpret_cast<u64>(dst), size);
    return dst;
}

/// bbport: native detours (default; BB_GUEST_HOOK_TRAPS=1: int3 traps). Each hooked site jumps to
/// a stub next to the image that calls the handler and runs the instructions the jump covers;
/// the copy call sites call LoaderCopy through a trampoline there. An int3 trap costs a signal
/// (a few microseconds in the kernel) per call; a detour costs a call. The int3 written first
/// stays the fallback while the jump's bytes go in: OnTrap sends a thread that meets it to the stub.
struct NativeSite {
    u64 offset;
    std::atomic<u64> stub{0};
};
std::array<NativeSite, 4> native_sites{{{AllocReturn}, {HeapAllocReturns[0]}, {HeapAllocReturns[1]},
                                        {HeapAllocReturns[2]}}};
u8* stub_page = nullptr;
std::size_t stub_used = 0;
constexpr std::size_t StubPageSize = 4096;

/// A page within +-2 GiB of the image (below its base: the image grows upwards).
u8* MapStubPage() {
    for (u64 k = 1; k <= 64; ++k) {
        const u64 hint = ImageBase - k * (16ull << 20);
        void* p = mmap(reinterpret_cast<void*>(hint), StubPageSize, PROT_READ | PROT_WRITE | PROT_EXEC,
                       MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED_NOREPLACE, -1, 0);
        if (p != MAP_FAILED) {
            return static_cast<u8*>(p);
        }
    }
    return nullptr;
}

struct Emitter {
    std::array<u8, 256> code{};
    std::size_t size = 0;
    void Bytes(std::initializer_list<u8> bytes) {
        for (const u8 b : bytes) {
            code[size++] = b;
        }
    }
    void U32(std::uint32_t v) {
        std::memcpy(&code[size], &v, 4);
        size += 4;
    }
    void U64(u64 v) {
        std::memcpy(&code[size], &v, 8);
        size += 8;
    }
    /// Saves the caller-saved registers (the handler may change them), aligns the stack.
    void SaveVolatile() {
        Bytes({0x50, 0x51, 0x52, 0x56, 0x57, 0x41, 0x50, 0x41, 0x51, 0x41, 0x52, 0x41, 0x53});
        Bytes({0x41, 0x54});             // push r12 (holds the unaligned stack pointer)
        Bytes({0x49, 0x89, 0xe4});       // mov r12, rsp
        Bytes({0x48, 0x83, 0xe4, 0xf0}); // and rsp, -16
    }
    void JmpAbs(u64 to) {
        Bytes({0xff, 0x25, 0x00, 0x00, 0x00, 0x00}); // jmp [rip]
        U64(to);
    }
    void CallAbs(const void* fn) {
        Bytes({0x48, 0xb8}); // movabs rax, fn
        U64(reinterpret_cast<u64>(fn));
        Bytes({0xff, 0xd0}); // call rax
    }
    void RestoreVolatile() {
        Bytes({0x4c, 0x89, 0xe4}); // mov rsp, r12
        Bytes({0x41, 0x5c});       // pop r12
        Bytes({0x41, 0x5b, 0x41, 0x5a, 0x41, 0x59, 0x41, 0x58, 0x5f, 0x5e, 0x5a, 0x59, 0x58});
    }
};

/// Copies `e` into the stub page; returns its address there, or 0.
u64 PlaceStub(const Emitter& e) {
    if (!stub_page || stub_used + e.size > StubPageSize) {
        return 0;
    }
    u8* at = stub_page + stub_used;
    std::memcpy(at, e.code.data(), e.size);
    stub_used += (e.size + 15) & ~std::size_t(15);
    return reinterpret_cast<u64>(at);
}

bool Rel32To(u64 from_next, u64 to, std::uint32_t& rel) {
    const std::int64_t d = std::int64_t(to) - std::int64_t(from_next);
    if (d < INT32_MIN || d > INT32_MAX) {
        return false;
    }
    rel = std::uint32_t(std::int32_t(d));
    return true;
}

/// Replaces bytes [1, 5) at `address` (byte 0 is the trap already there), then byte 0.
void WriteJumpOverTrap(u64 address, u8 opcode, std::uint32_t rel) {
    const long page_size = sysconf(_SC_PAGESIZE);
    void* page = reinterpret_cast<void*>(address & ~u64(page_size - 1));
    const std::size_t span = (address + 5) - reinterpret_cast<u64>(page);
    mprotect(page, span, PROT_READ | PROT_WRITE | PROT_EXEC);
    auto* p = reinterpret_cast<u8*>(address);
    for (int i = 0; i < 4; ++i) {
        __atomic_store_n(p + 1 + i, u8(rel >> (8 * i)), __ATOMIC_SEQ_CST);
    }
    __atomic_store_n(p, opcode, __ATOMIC_SEQ_CST);
    mprotect(page, span, PROT_READ | PROT_EXEC);
}

void AllocHook(u64 node) {
    if (!node) {
        return;
    }
    const u64 start = *reinterpret_cast<const u64*>(node + 8);
    const u64 next = *reinterpret_cast<const u64*>(node + 0x18);
    const u64 end = next ? *reinterpret_cast<const u64*>(next + 8) : start;
    if (end > start && end - start < (u64(1) << 32)) {
        on_range_allocated(start, end - start);
    }
}

void HeapHook(u64 address, u64 size) {
    if (address != 0 && size != 0 && size < (u64(1) << 32)) {
        on_range_allocated(address, size);
    }
}

/// The detour of a site whose int3 is in place (Patch). False: left as a trap.
bool InstallDetour(NativeSite& site) {
    const u64 address = ImageBase + site.offset;
    Emitter e;
    u64 back = 0;
    if (site.offset == AllocReturn) {
        // `add rsp, 0x18; pop rbx` (5 bytes) in the allocator's epilogue; rax: the node.
        if (reinterpret_cast<const u8*>(address)[4] != 0x5b) {
            return false;
        }
        e.SaveVolatile();
        e.Bytes({0x48, 0x89, 0xc7}); // mov rdi, rax (unchanged by the saving)
        e.CallAbs(reinterpret_cast<const void*>(&AllocHook));
        e.RestoreVolatile();
        e.Bytes({0x48, 0x83, 0xc4, 0x18}); // add rsp, 0x18
        e.Bytes({0x5b});                   // pop rbx
        back = address + 5;
    } else {
        // `mov rbx, rax; test rbx, rbx` (6 bytes) after the heap call; [rbp - 0x50]: the size.
        const auto* code = reinterpret_cast<const u8*>(address);
        if (code[3] != 0x48 || code[4] != 0x85 || code[5] != 0xdb) {
            return false;
        }
        e.Bytes({0x48, 0x89, 0xc3});                               // mov rbx, rax
        e.Bytes({0x48, 0x8d, 0xa4, 0x24, 0x80, 0xff, 0xff, 0xff}); // lea rsp, [rsp - 128]
        e.SaveVolatile();
        e.Bytes({0x48, 0x89, 0xdf});       // mov rdi, rbx
        e.Bytes({0x48, 0x8b, 0x75, 0xb0}); // mov rsi, [rbp - 0x50]
        e.CallAbs(reinterpret_cast<const void*>(&HeapHook));
        e.RestoreVolatile();
        e.Bytes({0x48, 0x8d, 0xa4, 0x24, 0x80, 0x00, 0x00, 0x00}); // lea rsp, [rsp + 128]
        e.Bytes({0x48, 0x85, 0xdb});                               // test rbx, rbx
        back = address + 6;
    }
    // jmp back
    const u64 jmp_at = reinterpret_cast<u64>(stub_page + stub_used) + e.size;
    std::uint32_t rel_back = 0;
    if (!Rel32To(jmp_at + 5, back, rel_back)) {
        return false;
    }
    e.Bytes({0xe9});
    e.U32(rel_back);
    const u64 stub = PlaceStub(e);
    std::uint32_t rel = 0;
    if (!stub || !Rel32To(address + 5, stub, rel)) {
        return false;
    }
    site.stub.store(stub, std::memory_order_release); // a thread at the trap now goes there
    WriteJumpOverTrap(address, 0xe9, rel);
    return true;
}

/// The copy call sites: the call's target becomes a trampoline to LoaderCopy.
bool InstallCallDetour(u64 offset) {
    Emitter e;
    e.Bytes({0xff, 0x25, 0x00, 0x00, 0x00, 0x00}); // jmp [rip]
    e.U64(reinterpret_cast<u64>(&LoaderCopy));
    const u64 stub = PlaceStub(e);
    const u64 address = ImageBase + offset;
    std::uint32_t rel = 0;
    if (!stub || !Rel32To(address + 5, stub, rel)) {
        return false;
    }
    WriteJumpOverTrap(address, 0xe8, rel);
    return true;
}
struct sigaction previous_action {};

void OnTrap(int sig, siginfo_t* info, void* context) {
    auto* g = static_cast<ucontext_t*>(context)->uc_mcontext.gregs;
    const u64 rip = u64(g[REG_RIP]) - 1; // past the int3
    for (const auto& site : native_sites) {
        if (rip == ImageBase + site.offset) {
            if (const u64 stub = site.stub.load(std::memory_order_acquire)) {
                g[REG_RIP] = greg_t(stub); // the detour is going in: its stub runs the site
                return;
            }
        }
    }
    if (rip == ImageBase + ReleaseCheck) {
        const auto result = static_cast<std::int32_t>(g[REG_RAX] & 0xffffffff);
        BbHeapSites::NoteReleaseCheck(std::uint32_t(result));
        g[REG_RIP] = greg_t(ImageBase + (result < 0 ? 0xbb5fc7 : ReleaseCheck + 2));
        return;
    }
    if (rip == ImageBase + CollectorEntry) {
        const u64 allocator = u64(g[REG_RDI]);
        for (std::size_t i = 0; i < BbStats::range_allocators.size(); ++i) {
            u64 expected = 0;
            if (BbStats::range_allocators[i].load(std::memory_order_relaxed) == allocator ||
                BbStats::range_allocators[i].compare_exchange_strong(expected, allocator)) {
                BbStats::range_live[i].store(*reinterpret_cast<const u64*>(allocator + 0xc8),
                                             std::memory_order_relaxed);
                BbStats::range_bytes[i].store(*reinterpret_cast<const u64*>(allocator + 0xd0),
                                              std::memory_order_relaxed);
                break;
            }
        }
        g[REG_RSP] -= 8; // push rbp
        *reinterpret_cast<u64*>(g[REG_RSP]) = u64(g[REG_RBP]);
        g[REG_RIP] = greg_t(ImageBase + CollectorEntry + 1);
        return;
    }
    for (const u64 site : HeapAllocReturns) {
        if (rip != ImageBase + site) {
            continue;
        }
        const u64 address = u64(g[REG_RAX]);
        const u64 size = *reinterpret_cast<const u64*>(u64(g[REG_RBP]) - 0x50);
        if (address != 0 && size != 0 && size < (u64(1) << 32)) {
            on_range_allocated(address, size);
        }
        g[REG_RBX] = g[REG_RAX];
        g[REG_RIP] = greg_t(ImageBase + site + sizeof(HeapAllocReturnCode));
        return;
    }
    if (rip == ImageBase + AllocReturn) {
        if (const u64 node = u64(g[REG_RAX])) {
            const u64 start = *reinterpret_cast<const u64*>(node + 8);
            const u64 next = *reinterpret_cast<const u64*>(node + 0x18);
            const u64 end = next ? *reinterpret_cast<const u64*>(next + 8) : start;
            if (end > start && end - start < (u64(1) << 32)) {
                on_range_allocated(start, end - start);
            }
        }
        g[REG_RSP] += 0x18;
        g[REG_RIP] = greg_t(ImageBase + AllocReturn + sizeof(AllocReturnCode));
        return;
    }
    for (std::size_t i = 0; i < MemcpySites.size(); ++i) {
        const auto& site = MemcpySites[i];
        if (rip != ImageBase + site.offset) {
            continue;
        }
        hits[i].fetch_add(1, std::memory_order_relaxed);
        // The call, to LoaderCopy instead of the game's memcpy: push the return address, jump.
        const u64 ret = ImageBase + site.offset + 5;
        g[REG_RSP] -= 8;
        *reinterpret_cast<u64*>(g[REG_RSP]) = ret;
        g[REG_RIP] = greg_t(reinterpret_cast<u64>(&LoaderCopy));
        return;
    }
    if (previous_action.sa_flags & SA_SIGINFO) {
        if (previous_action.sa_sigaction) {
            previous_action.sa_sigaction(sig, info, context);
            return;
        }
    } else if (previous_action.sa_handler != SIG_DFL && previous_action.sa_handler != SIG_IGN &&
               previous_action.sa_handler) {
        previous_action.sa_handler(sig);
        return;
    }
    signal(SIGTRAP, SIG_DFL);
    raise(SIGTRAP);
}

bool Patch(u64 address, const unsigned char* expected, std::size_t size) {
    unsigned char bytes[16]{};
    iovec local{bytes, size}, remote{reinterpret_cast<void*>(address), size};
    if (process_vm_readv(getpid(), &local, 1, &remote, 1, 0) != ssize_t(size) ||
        std::memcmp(bytes, expected, size) != 0) {
        return false;
    }
    const long page_size = sysconf(_SC_PAGESIZE);
    void* page = reinterpret_cast<void*>(address & ~u64(page_size - 1));
    const std::size_t span = (address + size) - reinterpret_cast<u64>(page);
    if (mprotect(page, span, PROT_READ | PROT_WRITE | PROT_EXEC) != 0) {
        return false;
    }
    __atomic_store_n(reinterpret_cast<unsigned char*>(address), static_cast<unsigned char>(0xcc),
                     __ATOMIC_SEQ_CST);
    mprotect(page, span, PROT_READ | PROT_EXEC);
    return true;
}

/// Render jobs (the cutscene and area streaming jobs: FD4 job runners) take a slot from a pool of
/// the game's at their start (held at [runner + 0x120]) and give it back when they end well. A job
/// that ends with a failure (result 1) left it held: above 30 FPS Laurence's cinematic fails
/// enough of them to empty the pool, and the game then waits for a slot for good (a hang).
std::atomic<u64> job_slots_released{0};
using GiveBack = void (*)(u64 queue, u64 item); // 0x1056990, the pool's own give-back

void NoteJobSlotReleased(const char* how) {
    const u64 n = job_slots_released.fetch_add(1) + 1;
    if (n <= 5 || (n & (n - 1)) == 0) {
        std::printf("Guest hooks: a render job %s gave its slot back (%llu so far)\n", how,
                    static_cast<unsigned long long>(n));
    }
}

/// At the shared exit of the job's run (0x1068092): r14 the runner, the pool in r12, r15d the
/// result.
void JobSlotFix(u64 runner, u64 queue, std::uint32_t result) {
    if (result != 1) {
        return;
    }
    u64& held = *reinterpret_cast<u64*>(runner + 0x120);
    const u64 item = held;
    if (!item) {
        return;
    }
    reinterpret_cast<GiveBack>(ImageBase + 0x1056990)(queue, item);
    held = 0;
    NoteJobSlotReleased("that failed");
}

/// The runner destroyed or reset (`mov qword [rbx + 0x120], 0` at 0x106798a and 0x1067a5c) with a
/// slot still held (a job cancelled in the middle): the slot goes back first, to the pool the
/// game's own 0x1057350 returns (the global at 0x54b8788).
void JobSlotDrop(u64 runner) {
    u64& held = *reinterpret_cast<u64*>(runner + 0x120);
    const u64 item = held;
    const u64 queue = *reinterpret_cast<const u64*>(ImageBase + 0x54b8788);
    if (!item || !queue) {
        return;
    }
    reinterpret_cast<GiveBack>(ImageBase + 0x1056990)(queue, item);
    held = 0;
    NoteJobSlotReleased("destroyed with its slot");
}

/// Runs `code` (the instructions the jump covers) after the stub's own part, then goes back. The
/// jump is written as plain bytes: InstallGameFixes runs while the image is still being prepared
/// (writable, no game thread yet), and the loader sets each segment's protection afterwards.
bool PlaceJumpTo(Emitter& e, u64 address, const u8* code, std::size_t size) {
    for (std::size_t i = 0; i < size; ++i) {
        e.Bytes({code[i]});
    }
    e.Bytes({0xff, 0x25, 0x00, 0x00, 0x00, 0x00}); // jmp [rip]
    e.U64(address + size);
    const u64 stub = PlaceStub(e);
    std::uint32_t rel = 0;
    if (!stub || !Rel32To(address + 5, stub, rel)) {
        return false;
    }
    auto* p = reinterpret_cast<u8*>(address);
    p[0] = 0xe9; // jmp rel32
    std::memcpy(p + 1, &rel, 4);
    return true;
}

bool InstallJobSlotDropHook(u64 offset) {
    static constexpr std::array<u8, 11> code = {0x48, 0xc7, 0x83, 0x20, 0x01, 0x00,
                                                0x00, 0x00, 0x00, 0x00, 0x00};
    const u64 address = ImageBase + offset;
    if (std::memcmp(reinterpret_cast<const void*>(address), code.data(), code.size())) {
        return false;
    }
    Emitter e;
    e.SaveVolatile();
    e.Bytes({0x48, 0x89, 0xdf}); // mov rdi, rbx (the runner)
    e.CallAbs(reinterpret_cast<const void*>(&JobSlotDrop));
    e.RestoreVolatile();
    return PlaceJumpTo(e, address, code.data(), code.size());
}

/// BB_JOB_SLOT_FIX=0: not installed.
bool InstallJobSlotFix() {
    if (const char* env = std::getenv("BB_JOB_SLOT_FIX"); env && env[0] == '0') {
        return false;
    }
    // mov rax, [rbx]; cmp rax, [rbp - 0x30]: the stack check every exit of that function ends in.
    static constexpr std::array<u8, 7> code = {0x48, 0x8b, 0x03, 0x48, 0x3b, 0x45, 0xd0};
    const u64 address = ImageBase + 0x1068092;
    if (std::memcmp(reinterpret_cast<const void*>(address), code.data(), code.size()) ||
        std::memcmp(reinterpret_cast<const void*>(ImageBase + 0x106798a),
                    "\x48\xc7\x83\x20\x01\x00\x00\x00\x00\x00\x00", 11) ||
        std::memcmp(reinterpret_cast<const void*>(ImageBase + 0x1067a5c),
                    "\x48\xc7\x83\x20\x01\x00\x00\x00\x00\x00\x00", 11)) {
        return false; // all three or none
    }
    Emitter e;
    e.SaveVolatile();
    e.Bytes({0x4c, 0x89, 0xf7});       // mov rdi, r14 (the runner)
    // SaveVolatile keeps its stack anchor in r12 and the game's r12 (the pool) at [r12].
    e.Bytes({0x49, 0x8b, 0x34, 0x24}); // mov rsi, [r12]
    e.Bytes({0x44, 0x89, 0xfa});       // mov edx, r15d (the result)
    e.CallAbs(reinterpret_cast<const void*>(&JobSlotFix));
    e.RestoreVolatile();
    if (!PlaceJumpTo(e, address, code.data(), code.size())) {
        return false;
    }
    return InstallJobSlotDropHook(0x106798a) & InstallJobSlotDropHook(0x1067a5c);
}

/// Yebis's blur-kernel sample parameters (GPUTexUtil_GetRecursiveSampleParameters, 0xbbc3e0): its
/// first argument, the base sample count, must be at least 3 (the game's own assertion, raised as
/// exception 0xa0020007: upstream issue #207). Game data now and then gives 2; the count is raised
/// to 3 at the entry. BB_KERNEL_CLAMP=0: not installed.
bool InstallKernelSampleClamp() {
    if (const char* env = std::getenv("BB_KERNEL_CLAMP"); env && env[0] == '0') {
        return false;
    }
    // push rbp; mov rbp, rsp; push r15
    static constexpr std::array<u8, 6> entry = {0x55, 0x48, 0x89, 0xe5, 0x41, 0x57};
    const u64 address = ImageBase + 0xbbc3e0;
    if (std::memcmp(reinterpret_cast<const void*>(address), entry.data(), entry.size())) {
        return false;
    }
    Emitter e;
    e.Bytes({0x83, 0xff, 0x03});             // cmp edi, 3
    e.Bytes({0x7d, 0x05});                   // jge over
    e.Bytes({0xbf, 0x03, 0x00, 0x00, 0x00}); // mov edi, 3
    return PlaceJumpTo(e, address, entry.data(), entry.size());
}

/// The GX occlusion queries (upstream 0.7, its #336 and PR #343 by whp199: a guest fault at
/// 0x2169edc on GXRenderThread, address 0, after 1 h 40 min in the Hunter's Dream). A query (0x30
/// bytes, made by its pool, 0xec6820 and 0xec68d0, with 0x2288d00) gets its handle, its first
/// field, from 0xe2f080(this, 1) -> 0x21674f0, which allocates a 0x18-byte handle (the device's
/// allocator at +0xdc10) and its data (+0xdc18). On a failure it returns 8 or 9 and the handle
/// stays null; the pool does not look. The render command 0x2285e10 then begins the query
/// (0xe2f130: inner state [this + 8] 0 -> 2, then 0x2169ec0(device, device + 0xb730, handle),
/// which reads the handle: the fault) and ends it (0xe2f160: state 1, 0x216a070, which reads it
/// too). The guard: at the begin, a query whose creation failed (GxQueryCreated keeps their
/// addresses) is created again; one still without a handle is not begun, and its end is skipped.
/// Its state stays 0, so the result getter (0xe2f190) gives its stored result, 0 (nothing
/// visible). A null handle the creation did not leave (a query released while the render thread
/// holds it) is only skipped: creating one would write into a freed object. The pool creates on
/// the main thread, the retry runs on GXRenderThread: both allocators (0x1fc5f30, 0x1fc5ed0) hold
/// their lock (+0x468) around the game's TLSF heap (0x2085a60), and the rest of the creation
/// touches only the query. The cause (the device's heap full late in a long session) is a guess;
/// each failed creation is logged once a minute.
/// BB_GX_QUERY_GUARD=0: not installed.
/// BB_RE_GX_QUERY=1: the first creations and guard events are logged with their thread.
/// BB_GX_QUERY_FAIL=N (diagnostics): every N-th creation (retries too) fails as with a full heap
/// (the game's release 0xe2f020 takes the new handle back), so the guard's paths run in any
/// session. The pool makes 8192 at startup and hands out the last made first: N = 2 reaches a scene.
constexpr u64 GxQueryBeginSite = 0xe2f134; // cmp dword [rdi + 8], 0; jne 0xe2f157 (begun already)
constexpr u64 GxQueryReturn = 0xe2f157;    // mov al, 1; pop rbp; ret
constexpr unsigned char GxQueryBeginCode[6] = {0x83, 0x7f, 0x08, 0x00, 0x75, 0x1d};
constexpr u64 GxQueryEndSite = 0xe2f164;   // mov dword [rdi + 8], 1
constexpr u64 GxQueryEndReturn = 0xe2f181; // mov al, 1; pop rbp; ret
constexpr unsigned char GxQueryEndCode[7] = {0xc7, 0x47, 0x08, 0x01, 0x00, 0x00, 0x00};
constexpr u64 GxQueryCreate = 0xe2f080;
constexpr u64 GxQueryRelease = 0xe2f020;
/// The creation's common exit (`mov rcx, [r15]; cmp rcx, [rbp - 0x20]`, the stack check): eax the
/// result, r14 where the handle goes (the query), rbx null when the handle's allocation failed.
constexpr u64 GxQueryCreateExit = 0x21675b0;
constexpr std::array<u8, 7> GxQueryCreateExitCode = {0x49, 0x8b, 0x0f, 0x48, 0x3b, 0x4d, 0xe0};
std::array<std::atomic<u64>, 256> gx_query_failed{}; ///< queries whose creation failed (0: free)
std::atomic<u64> gx_query_failures{0}, gx_query_recreated{0}, gx_query_skipped{0};
std::atomic<long long> gx_query_failure_told{0}, gx_query_guard_told{0};

/// True the first time and then at most once a minute (`last`: steady clock, ms).
bool OncePerMinute(std::atomic<long long>& last) {
    const long long now = std::chrono::duration_cast<std::chrono::milliseconds>(
                              std::chrono::steady_clock::now().time_since_epoch())
                              .count();
    long long seen = last.load(std::memory_order_relaxed);
    return (seen == 0 || now - seen >= 60000) && last.compare_exchange_strong(seen, now);
}

std::array<char, 32> ThreadName() {
    std::array<char, 32> name{};
    if (pthread_getname_np(pthread_self(), name.data(), name.size()) != 0 || !name[0]) {
        name = {"?"};
    }
    return name;
}

/// BB_RE_GX_QUERY=1: true for the first 16 events counted in `traced`.
bool GxQueryTrace(std::atomic<int>& traced) {
    static const bool trace = [] {
        const char* env = std::getenv("BB_RE_GX_QUERY");
        return env && env[0] == '1';
    }();
    return trace && traced.fetch_add(1) < 16;
}

void __attribute__((sysv_abi)) GxQueryCreated(u64, const BbGuestCode::RegisterSnapshot* r) {
    auto status = std::uint32_t(r->rax);
    const u64 query = r->r14;
    static const long fail_every = [] {
        const char* env = std::getenv("BB_GX_QUERY_FAIL");
        return env ? std::strtol(env, nullptr, 10) : 0l;
    }();
    static std::atomic<u64> creations{0};
    const bool simulated =
        status == 0 && fail_every > 0 && (creations.fetch_add(1) + 1) % u64(fail_every) == 0;
    if (simulated) {
        using Release = void(__attribute__((sysv_abi)) *)(u64 query);
        reinterpret_cast<Release>(ImageBase + GxQueryRelease)(query);
        const_cast<BbGuestCode::RegisterSnapshot*>(r)->rax = status = 9;
    }
    static std::atomic<int> traced{0};
    if (GxQueryTrace(traced)) {
        std::printf("GX query: %#llx created, result %u%s (thread %s)\n",
                    static_cast<unsigned long long>(query), status,
                    simulated ? " (BB_GX_QUERY_FAIL)" : "", ThreadName().data());
    }
    if (status == 0) {
        for (auto& slot : gx_query_failed) {
            u64 expected = query;
            if (slot.load(std::memory_order_relaxed) == query) {
                slot.compare_exchange_strong(expected, 0);
            }
        }
        return;
    }
    bool known = false;
    for (const auto& slot : gx_query_failed) {
        known = known || slot.load(std::memory_order_relaxed) == query;
    }
    for (auto& slot : gx_query_failed) {
        u64 expected = 0;
        if (known || slot.compare_exchange_strong(expected, query)) {
            break;
        }
    }
    const u64 n = gx_query_failures.fetch_add(1) + 1;
    if (!OncePerMinute(gx_query_failure_told)) {
        return;
    }
    std::printf("Guest hooks: a GX occlusion query could not be created (error %u: %s), %llu so far "
                "(thread %s); the query guard creates it again before it begins\n",
                status,
                simulated     ? "BB_GX_QUERY_FAIL"
                : status == 9 ? (r->rbx ? "no memory for its data" : "no memory for its handle")
                              : "the device or its data not ready",
                static_cast<unsigned long long>(n), ThreadName().data());
}

/// The begin's stub calls this for a query without a handle (rdi). A query whose creation failed
/// is created again (the game's own 0xe2f080, as the pool does); the stub then looks again.
void GxQueryWithoutHandle(u64 query) {
    bool failed = false;
    for (const auto& slot : gx_query_failed) {
        failed = failed || slot.load(std::memory_order_relaxed) == query;
    }
    if (failed) {
        using Create = bool(__attribute__((sysv_abi)) *)(u64 query, std::uint32_t kind);
        reinterpret_cast<Create>(ImageBase + GxQueryCreate)(query, 1); // GxQueryCreated keeps or forgets it
    }
    const bool created = *reinterpret_cast<const volatile u64*>(query) != 0;
    const u64 recreated = gx_query_recreated.fetch_add(created) + created;
    const u64 skipped = gx_query_skipped.fetch_add(!created) + !created;
    static std::atomic<int> traced{0};
    if (!OncePerMinute(gx_query_guard_told) && !GxQueryTrace(traced)) {
        return;
    }
    std::printf("Guest hooks: GX occlusion query %#llx had no handle at its begin (%s): %llu created "
                "again, %llu not begun (no fault; nothing visible) so far (thread %s)\n",
                static_cast<unsigned long long>(query),
                failed ? "its creation had failed" : "no failed creation seen: released?",
                static_cast<unsigned long long>(recreated), static_cast<unsigned long long>(skipped),
                ThreadName().data());
}

/// Written as plain bytes, as PlaceJumpTo: the image is still writable (InstallGameFixes).
bool PlaceJump(u64 address, u64 stub) {
    std::uint32_t rel = 0;
    if (!stub || !Rel32To(address + 5, stub, rel)) {
        return false;
    }
    auto* p = reinterpret_cast<u8*>(address);
    p[0] = 0xe9; // jmp rel32
    std::memcpy(p + 1, &rel, 4);
    return true;
}

bool InstallGxQueryGuard() {
    if (const char* env = std::getenv("BB_GX_QUERY_GUARD"); env && env[0] == '0') {
        return false;
    }
    const u64 begin = ImageBase + GxQueryBeginSite;
    const u64 end = ImageBase + GxQueryEndSite;
    if (std::memcmp(reinterpret_cast<const void*>(begin), GxQueryBeginCode, sizeof(GxQueryBeginCode)) ||
        std::memcmp(reinterpret_cast<const void*>(end), GxQueryEndCode, sizeof(GxQueryEndCode))) {
        return false;
    }
    // The begin: the game's state check, then the handle's.
    Emitter b;
    b.Bytes({0x83, 0x7f, 0x08, 0x00}); // cmp dword [rdi + 8], 0
    b.Bytes({0x75, 0x00});             // jne done (begun or ended already)
    const std::size_t to_done = b.size;
    b.Bytes({0x48, 0x83, 0x3f, 0x00}); // cmp qword [rdi], 0
    b.Bytes({0x74, 0x00});             // je none
    const std::size_t to_none = b.size;
    const std::size_t body = b.size;
    b.JmpAbs(begin + sizeof(GxQueryBeginCode)); // body: state 2, the begin
    const std::size_t done = b.size;
    b.JmpAbs(ImageBase + GxQueryReturn);
    b.code[to_done - 1] = u8(done - to_done);
    b.code[to_none - 1] = u8(b.size - to_none);
    b.SaveVolatile(); // none: rdi (the query) and rsi kept
    b.CallAbs(reinterpret_cast<const void*>(&GxQueryWithoutHandle));
    b.RestoreVolatile();
    b.Bytes({0x48, 0x83, 0x3f, 0x00});        // cmp qword [rdi], 0: created again?
    b.Bytes({0x75, u8(body - (b.size + 2))}); // jne body
    b.Bytes({0xeb, u8(done - (b.size + 2))}); // jmp done: not begun, the state stays 0
    // The end: only a query with a handle (begun) is ended.
    Emitter e;
    e.Bytes({0x48, 0x83, 0x3f, 0x00}); // cmp qword [rdi], 0
    e.Bytes({0x74, 0x00});             // je none
    const std::size_t to_skip = e.size;
    for (const u8 c : GxQueryEndCode) {
        e.Bytes({c}); // mov dword [rdi + 8], 1
    }
    e.JmpAbs(end + sizeof(GxQueryEndCode));
    e.code[to_skip - 1] = u8(e.size - to_skip);
    e.JmpAbs(ImageBase + GxQueryEndReturn); // none: not ended, the state stays 0
    const u64 begin_stub = PlaceStub(b);
    const u64 end_stub = PlaceStub(e);
    std::uint32_t rel = 0;
    if (!begin_stub || !end_stub || !Rel32To(begin + 5, begin_stub, rel) ||
        !Rel32To(end + 5, end_stub, rel)) {
        return false;
    }
    // Without the creation observer a query without a handle is only skipped.
    const bool observer = BbGuestCode::InstallHook(reinterpret_cast<void*>(ImageBase + GxQueryCreateExit),
                                                   GxQueryCreateExitCode, 0, GxQueryCreated);
    if (!observer) {
        std::printf("Guest hooks: GX occlusion query creations not observed: a query without a "
                    "handle is only skipped\n");
    }
    return PlaceJump(begin, begin_stub) && PlaceJump(end, end_stub);
}
} // namespace

void Install(RangeCallback on_gpu_range_allocated) {
    static std::atomic<bool> installed{false};
    if (installed.exchange(true)) {
        return;
    }
    struct sigaction action {};
    action.sa_sigaction = OnTrap;
    action.sa_flags = SA_SIGINFO | SA_NODEFER;
    sigemptyset(&action.sa_mask);
    sigaction(SIGTRAP, &action, &previous_action);
    int patched = 0;
    for (const auto& site : MemcpySites) {
        patched += Patch(ImageBase + site.offset, site.code, sizeof(site.code));
    }
    std::printf("Guest hooks: %d of %zu resource copy sites tell the GPU side of their writes\n",
                patched, MemcpySites.size());
    on_range_allocated = on_gpu_range_allocated;
    const bool allocator = Patch(ImageBase + AllocReturn, AllocReturnCode, sizeof(AllocReturnCode));
    // BB_HEAP_HOOKS=0 (bisecting): the heap's ranges are not reported.
    const char* heap_env = std::getenv("BB_HEAP_HOOKS");
    const bool heap_hooks = !heap_env || heap_env[0] != '0';
    if (BbStats::enabled) {
        Patch(ImageBase + CollectorEntry, CollectorEntryCode, sizeof(CollectorEntryCode));
    }
    int heap_sites = 0;
    for (const u64 site : HeapAllocReturns) {
        if (!heap_hooks) {
            break;
        }
        heap_sites += Patch(ImageBase + site, HeapAllocReturnCode, sizeof(HeapAllocReturnCode));
    }
    std::printf("Guest hooks: GPU heap allocations seen at %d of %zu call sites\n", heap_sites,
                HeapAllocReturns.size());
    std::printf("Guest hooks: GPU memory allocator %s\n", allocator ? "tells the GPU side of new ranges" : "not found");
    // Native detours over the traps just placed (BB_GUEST_HOOK_TRAPS=1 keeps the traps).
    const char* traps_env = std::getenv("BB_GUEST_HOOK_TRAPS");
    if (!(traps_env && traps_env[0] == '1') && (stub_page = MapStubPage()) != nullptr) {
        int detours = 0;
        for (const auto& site : MemcpySites) {
            if (reinterpret_cast<const u8*>(ImageBase + site.offset)[0] == 0xcc) {
                detours += InstallCallDetour(site.offset);
            }
        }
        for (auto& site : native_sites) {
            if (reinterpret_cast<const u8*>(ImageBase + site.offset)[0] == 0xcc) {
                detours += InstallDetour(site);
            }
        }
        mprotect(stub_page, StubPageSize, PROT_READ | PROT_EXEC);
        std::printf("Guest hooks: %d native detours (no traps; BB_GUEST_HOOK_TRAPS=1: int3)\n",
                    detours);
    }
    BbHeapSites::Install();
    if (const char* env = std::getenv("BB_HEAP_SITES"); env && env[0] == '1') {
        Patch(ImageBase + ReleaseCheck, ReleaseCheckCode, sizeof(ReleaseCheckCode));
    }
}

void InstallGameFixes() {
    // bbgpu_patch_image: after the relocations and the patches, before the segments get their
    // protection (installed earlier, at the GPU's start, the jump made a code page read-only
    // while the loader still had relocations to write there: a fault at start).
    static std::atomic<bool> installed{false};
    if (installed.exchange(true)) {
        return;
    }
    // A page of its own: Install's (new memory model only) is read-only once it is done.
    stub_page = MapStubPage();
    stub_used = 0;
    if (!stub_page) {
        std::printf("Guest hooks: no page near the game for the fixes of its own bugs\n");
        return;
    }
    std::printf("Guest hooks: render job slot leak fix %s\n",
                InstallJobSlotFix() ? "on" : "not installed");
    std::printf("Guest hooks: blur-kernel sample count clamp %s\n",
                InstallKernelSampleClamp() ? "on" : "not installed");
    std::printf("Guest hooks: GX occlusion query guard %s\n",
                InstallGxQueryGuard() ? "on" : "not installed");
    mprotect(stub_page, StubPageSize, PROT_READ | PROT_EXEC);
}
} // namespace BbGuestHooks
