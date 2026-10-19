// SPDX-License-Identifier: GPL-2.0-or-later
// bbport: hooks in the game's code that write GPU memory (BB_GUEST_IN_PLACE). Where the game
// copies resource data into memory the GPU uses, the GPU side is told once the data is there, as a
// driver is told of a resource update; the write needs no page protection to be seen. Each site
// is checked byte for byte against the expected code (another game version: not installed).
#pragma once

#include <cstdint>

namespace BbGuestHooks {
/// [address, address + size) of GPU memory the game has just handed out again: its old contents
/// are dead and whatever writes it next may be code the GPU side does not hear of.
using RangeCallback = void (*)(std::uint64_t address, std::uint64_t size);

/// Installs the hooks once (GPU side, after the game is loaded).
void Install(RangeCallback on_gpu_range_allocated);

/// Fixes for bugs of the game's own, with every memory model (once, before the game's threads
/// run): failed render jobs give their pool slot back (Laurence's cinematic above 30 FPS hung),
/// and the blur kernel's sample count is kept valid (exception 0xa0020007). From upstream bbport
/// 0.6.
void InstallGameFixes();
} // namespace BbGuestHooks
