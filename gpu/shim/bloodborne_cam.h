// SPDX-License-Identifier: GPL-2.0-or-later
// Direct mouse camera: hooks the game's camera update so mouse motion writes the camera's
// yaw/pitch itself (1:1, no stick deadzone or turn curve), like a native PC game. Game 1.09.
// From Supermedo/bloodborne_pc edd20a5 (João Pedro Valadares), itself from the bbmouse mouse
// camera of Supermedo/bloodborne_pc#3 (mcrib884) and shadlixps4's Bloodborne mouse camera;
// on Linux the game is at its fixed image base, so no memory scan is needed.
//
// Window capture (relative mode, F1, the menu) stays with window.cpp; this class only patches the
// game's code and applies motion. While the player is locked on, motion goes to the mouse-to-stick
// path instead (IsLockedOn), so a flick still switches targets.

#pragma once

#include <atomic>
#include <cstddef>
#include <cstdint>

namespace BbCamera {

/// bbport.ini mouse_camera=direct and the sensitivity (1.0 = 900 mouse counts per radian). Any
/// thread; the window thread applies it.
void Configure(bool direct, float sensitivity);
bool Configured();

/// Window thread: installs (true) or removes (false) the camera hook. Returns whether the hook is
/// active afterwards (false when the game's camera code is not the expected 1.09 code).
bool SetEnabled(bool enabled);
bool Enabled();
/// True while the game reports a lock-on target (motion is not applied then).
bool LockedOn();

/// Window thread: gathers relative mouse motion; the game's camera update applies it (once per
/// update, so every frame turns by the motion since the one before).
void OnMouseMotion(float xrel, float yrel);

/// Window thread, every event poll. BB_CAM_TRACE=<file> (diagnostics, not with the direct mouse
/// camera): records the camera object and writes "ms yaw pitch" (radians) to the file whenever
/// the camera turns, to measure how the game turns it for a given stick input.
void TraceTick();

} // namespace BbCamera
