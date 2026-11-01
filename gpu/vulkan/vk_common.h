// SPDX-FileCopyrightText: Copyright 2026 bbport contributors
// SPDX-License-Identifier: GPL-2.0-or-later
// bbport vulkan: how the port uses Vulkan-Hpp: functions loaded at run time, aggregate structs
// (designated initializers), results returned instead of exceptions; VMA with dynamic functions.
#pragma once

#define VK_ENABLE_BETA_EXTENSIONS
#define VK_NO_PROTOTYPES
#define VULKAN_HPP_DISPATCH_LOADER_DYNAMIC 1
#define VULKAN_HPP_NO_CONSTRUCTORS
#define VULKAN_HPP_NO_STRUCT_SETTERS
#define VULKAN_HPP_HAS_SPACESHIP_OPERATOR
#define VULKAN_HPP_NO_EXCEPTIONS
// Results are checked by the callers.
#define VULKAN_HPP_ASSERT_ON_RESULT

// bbport (0xCydral, Linux fork): vulkan.hpp adds fields to DispatchLoaderBase when NDEBUG is
// undefined, so the layout of vk::detail::DispatchLoaderDynamic depends on it. libbbgpu is built
// with NDEBUG while the renderer tests build without it (their asserts must run); the inline
// init() copies the linker keeps would then read the dispatcher at offsets another translation
// unit did not write (a call through a null vkGetInstanceProcAddr). Included with NDEBUG
// everywhere.
#ifndef NDEBUG
#define NDEBUG
#define BB_VK_COMMON_RESTORE_ASSERTS
#endif
#include <vulkan/vulkan.hpp>
#ifdef BB_VK_COMMON_RESTORE_ASSERTS
#undef BB_VK_COMMON_RESTORE_ASSERTS
#undef NDEBUG
#include <cassert> // vulkan.hpp's own include of it just turned assert() off
#endif

#define VMA_STATIC_VULKAN_FUNCTIONS 0
#define VMA_DYNAMIC_VULKAN_FUNCTIONS 1
