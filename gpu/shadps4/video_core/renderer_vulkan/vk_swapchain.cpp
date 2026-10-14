// SPDX-FileCopyrightText: Copyright 2024-2026 shadPS4 Emulator Project
// SPDX-License-Identifier: GPL-2.0-or-later

#include <algorithm>
#include <atomic>
#include <cstdio>
#include <limits>
#include "common/assert.h"
#include "common/logging/log.h"
#include "core/emulator_settings.h"
#include "imgui/renderer/imgui_core.h"
#include "sdl_window.h"
#include "video_core/renderer_vulkan/vk_instance.h"
#include "video_core/renderer_vulkan/vk_platform.h"
#include "video_core/renderer_vulkan/vk_scheduler.h"
#include "video_core/renderer_vulkan/vk_swapchain.h"

namespace Vulkan {

/// bbport (from Awaken's BloodBorneButPc): display events (a lost surface, a failed swapchain)
/// are reported a few times and the presenter skips frames until a new swapchain works; they
/// ended the game (exit 23).
static void NoteDisplayEvent(const char* what, vk::Result result) {
    static std::atomic<u32> notes{0};
    if (notes.fetch_add(1, std::memory_order_relaxed) < 16) {
        std::printf("Display: %s: %s\n", what, vk::to_string(result).c_str());
    }
}

static constexpr vk::SurfaceFormatKHR SURFACE_FORMAT_HDR = {
    .format = vk::Format::eA2B10G10R10UnormPack32,
    .colorSpace = vk::ColorSpaceKHR::eHdr10St2084EXT,
};

Swapchain::Swapchain(const Instance& instance_, const Frontend::WindowSDL& window_)
    : instance{instance_}, window{window_}, surface{CreateSurface(instance.GetInstance(), window)} {
    FindPresentFormat();
    FindPresentMode();

    Create(window.GetWidth(), window.GetHeight());
    ImGui::Core::Initialize(instance, window, image_count, surface_format.format);
}

Swapchain::~Swapchain() {
    Destroy();
    instance.GetInstance().destroySurfaceKHR(surface);
}

void Swapchain::Create(u32 width_, u32 height_) {
    width = width_;
    height = height_;
    needs_recreation = false;

    // bbport: a lost surface (VK_ERROR_SURFACE_LOST_KHR: a display or driver reset) is made again
    // on the same window before a swapchain can be created on it.
    if (surface_lost) {
        RecreateSurface();
    }

    // bbport: a minimised window has a 0x0 surface (issue #31); no swapchain can have that extent.
    // The old one stays (presents are skipped) until the window is back.
    if (!SetSurfaceProperties()) {
        needs_recreation = true;
        return;
    }
    if (extent.width == 0 || extent.height == 0) {
        zero_extent = true;
        needs_recreation = true;
        return;
    }
    zero_extent = false;

    // bbport: the old swapchain is retired through oldSwapchain instead of destroyed first.
    // NVIDIA's Wayland WSI keeps a wp_tearing_control per swapchain; a fresh swapchain on the
    // same surface was rejected ("Surface already has a tearing controller", SurfaceLost).
    const vk::SwapchainKHR old_swapchain = swapchain;
    swapchain = nullptr;
    Destroy();

    const std::array queue_family_indices = {
        instance.GetGraphicsQueueFamilyIndex(),
        instance.GetPresentQueueFamilyIndex(),
    };

    const bool exclusive = queue_family_indices[0] == queue_family_indices[1];
    const u32 queue_family_indices_count = exclusive ? 1u : 2u;
    const vk::SharingMode sharing_mode =
        exclusive ? vk::SharingMode::eExclusive : vk::SharingMode::eConcurrent;
    const auto format = needs_hdr ? SURFACE_FORMAT_HDR : surface_format;
    const vk::SwapchainCreateInfoKHR swapchain_info = {
        .surface = surface,
        .minImageCount = image_count,
        .imageFormat = format.format,
        .imageColorSpace = format.colorSpace,
        .imageExtent = extent,
        .imageArrayLayers = 1,
        .imageUsage = vk::ImageUsageFlagBits::eColorAttachment |
                      vk::ImageUsageFlagBits::eTransferSrc | vk::ImageUsageFlagBits::eTransferDst,
        .imageSharingMode = sharing_mode,
        .queueFamilyIndexCount = queue_family_indices_count,
        .pQueueFamilyIndices = queue_family_indices.data(),
        .preTransform = transform,
        .compositeAlpha = composite_alpha,
        .presentMode = present_mode,
        .clipped = true,
        .oldSwapchain = old_swapchain,
    };

    auto [swapchain_result, chain] = instance.GetDevice().createSwapchainKHR(swapchain_info);
    // The old swapchain is retired by the call even when it fails.
    if (old_swapchain) {
        instance.GetDevice().destroySwapchainKHR(old_swapchain);
    }
    if (swapchain_result != vk::Result::eSuccess) {
        // bbport: no swapchain now (IsPresentable is false): presents are skipped and the next
        // one tries again (this was an assertion, exit 23).
        NoteDisplayEvent("creating the swapchain failed", swapchain_result);
        surface_lost = swapchain_result == vk::Result::eErrorSurfaceLostKHR;
        needs_recreation = true;
        return;
    }
    swapchain = chain;

    SetupImages();
    RefreshSemaphores();
    // The new chain may have fewer images (AwesomeObserver b3164c1): start the indices over.
    frame_index = image_index = 0;
}

void Swapchain::Recreate(u32 width_, u32 height_) {
    LOG_DEBUG(Render_Vulkan, "Recreate the swapchain: width={} height={} HDR={}", width_, height_,
              needs_hdr);
    Create(width_, height_);
}

void Swapchain::SetHDR(bool hdr) {
    if (needs_hdr == hdr) {
        return;
    }

    WaitIdle();

    needs_hdr = hdr;
    Recreate(width, height);
    ImGui::Core::OnSurfaceFormatChange(needs_hdr ? SURFACE_FORMAT_HDR.format
                                                 : surface_format.format);
}

bool Swapchain::AcquireNextImage() {
    if (!swapchain) {
        needs_recreation = true; // the last Create failed
        return false;
    }
    vk::Device device = instance.GetDevice();
    // bbport: in 10 s slices, saying so once when the compositor holds every image that long
    // (issue #5: a frozen game with nothing in the log).
    vk::Result result;
    bool told = false;
    while ((result = device.acquireNextImageKHR(swapchain, 10'000'000'000ULL,
                                                image_acquired[frame_index], VK_NULL_HANDLE,
                                                &image_index)) == vk::Result::eTimeout ||
           result == vk::Result::eNotReady) {
        if (!told) {
            told = true;
            std::printf("Swapchain: no image from the compositor in 10 s (it holds all %zu)\n",
                        images.size());
            std::fflush(stdout);
        }
    }
    if (told) {
        std::printf("Swapchain: the compositor gave an image back\n");
        std::fflush(stdout);
    }

    switch (result) {
    case vk::Result::eSuccess:
        break;
    case vk::Result::eSuboptimalKHR:
        // A suboptimal acquire still owns an image and signals the semaphore: present it in the
        // normal submission, then recreate (Present() returns false). Dropping it left the
        // semaphore signalled and never waited on. From AwesomeObserver b3164c1 (E. Doronin).
        needs_recreation = true;
        return true;
    case vk::Result::eErrorSurfaceLostKHR:
        NoteDisplayEvent("acquiring a swapchain image", result);
        surface_lost = true;
        needs_recreation = true;
        break;
    case vk::Result::eErrorOutOfDateKHR:
    case vk::Result::eErrorUnknown:
        needs_recreation = true;
        break;
    default:
        // bbport: e.g. a lost exclusive fullscreen: recreated like out-of-date (this was
        // UNREACHABLE, exit 23).
        NoteDisplayEvent("acquiring a swapchain image", result);
        needs_recreation = true;
        break;
    }

    return !needs_recreation;
}

bool Swapchain::Present() {
    const vk::PresentInfoKHR present_info = {
        .waitSemaphoreCount = 1,
        .pWaitSemaphores = &present_ready[image_index],
        .swapchainCount = 1,
        .pSwapchains = &swapchain,
        .pImageIndices = &image_index,
    };

    auto result = instance.GetPresentQueue().presentKHR(present_info);
    if (result == vk::Result::eErrorOutOfDateKHR || result == vk::Result::eSuboptimalKHR) {
        needs_recreation = true;
    } else if (result != vk::Result::eSuccess && result != vk::Result::eErrorDeviceLost) {
        // bbport: a lost surface (display or driver reset) or another display event: recreated
        // like out-of-date (this was an assertion, exit 23). A lost device still stops below.
        NoteDisplayEvent("presenting", result);
        surface_lost = result == vk::Result::eErrorSurfaceLostKHR;
        needs_recreation = true;
    } else {
        ASSERT_MSG(result == vk::Result::eSuccess, "Swapchain presentation failed: {}",
                   vk::to_string(result));
    }

    frame_index = (frame_index + 1) % image_count;

    return !needs_recreation;
}

void Swapchain::FindPresentFormat() {
    const auto [formats_result, formats] =
        instance.GetPhysicalDevice().getSurfaceFormatsKHR(surface);
    ASSERT_MSG(formats_result == vk::Result::eSuccess, "Failed to query surface formats: {}",
               vk::to_string(formats_result));

    // Check if the device supports HDR formats. Here we care of Rec.2020 PQ only as it is expected
    // game output. Other variants as e.g. linear Rec.2020 will require additional color space
    // rotation
    supports_hdr =
        std::find_if(formats.begin(), formats.end(), [](const vk::SurfaceFormatKHR& format) {
            return format == SURFACE_FORMAT_HDR;
        }) != formats.end();
    // Also make sure that user allowed us to use HDR
    supports_hdr &= EmulatorSettings.IsHdrAllowed();

    // If there is a single undefined surface format, the device doesn't care, so we'll just use
    // RGBA sRGB.
    if (formats[0].format == vk::Format::eUndefined) {
        surface_format.format = vk::Format::eR8G8B8A8Unorm;
        surface_format.colorSpace = vk::ColorSpaceKHR::eSrgbNonlinear;
        return;
    }

    // Try to find a suitable format.
    for (const vk::SurfaceFormatKHR& sformat : formats) {
        vk::Format format = sformat.format;
        if (format != vk::Format::eR8G8B8A8Unorm && format != vk::Format::eB8G8R8A8Unorm) {
            continue;
        }

        surface_format.format = format;
        surface_format.colorSpace = sformat.colorSpace;
        return;
    }

    UNREACHABLE_MSG("Unable to find required swapchain format!");
}

void Swapchain::FindPresentMode() {
    const auto [modes_result, modes] =
        instance.GetPhysicalDevice().getSurfacePresentModesKHR(surface);
    if (modes_result != vk::Result::eSuccess) {
        LOG_ERROR(Render, "Failed to query available present modes, falling back to Fifo as "
                          "guaranteed supported option.");
        present_mode = vk::PresentModeKHR::eFifo;
        return;
    }

    const auto requested_mode = EmulatorSettings.GetPresentMode();
    if (requested_mode == "Mailbox") {
        present_mode = vk::PresentModeKHR::eMailbox;
    } else if (requested_mode == "Fifo") {
        present_mode = vk::PresentModeKHR::eFifo;
    } else if (requested_mode == "Immediate") {
        present_mode = vk::PresentModeKHR::eImmediate;
    } else {
        LOG_ERROR(Render_Vulkan, "Unknown present mode {}, defaulting to Mailbox.",
                  EmulatorSettings.GetPresentMode());
        present_mode = vk::PresentModeKHR::eMailbox;
    }

    if (std::ranges::find(modes, present_mode) == modes.cend()) {
        // FIFO is guaranteed to be supported by the Vulkan spec.
        constexpr auto fallback = vk::PresentModeKHR::eFifo;
        LOG_WARNING(Render, "Requested present mode {} is not supported, falling back to {}.",
                    vk::to_string(present_mode), vk::to_string(fallback));
        present_mode = fallback;
    }
}

bool Swapchain::SetSurfaceProperties() {
    const auto [capabilities_result, capabilities] =
        instance.GetPhysicalDevice().getSurfaceCapabilitiesKHR(surface);
    if (capabilities_result != vk::Result::eSuccess) {
        // bbport: e.g. a lost surface: no swapchain until it is back (this was an assertion).
        NoteDisplayEvent("querying the surface", capabilities_result);
        surface_lost = capabilities_result == vk::Result::eErrorSurfaceLostKHR;
        return false;
    }

    extent = capabilities.currentExtent;
    if (capabilities.currentExtent.width == std::numeric_limits<u32>::max()) {
        extent.width = std::max(capabilities.minImageExtent.width,
                                std::min(capabilities.maxImageExtent.width, width));
        extent.height = std::max(capabilities.minImageExtent.height,
                                 std::min(capabilities.maxImageExtent.height, height));
    }

    // Select number of images in swap chain, we prefer one buffer in the background to work on
    image_count = capabilities.minImageCount + 1;
    if (capabilities.maxImageCount > 0) {
        image_count = std::min(image_count, capabilities.maxImageCount);
    }

    // Prefer identity transform if possible
    transform = vk::SurfaceTransformFlagBitsKHR::eIdentity;
    if (!(capabilities.supportedTransforms & transform)) {
        transform = capabilities.currentTransform;
    }

    // Opaque is not supported everywhere.
    composite_alpha = vk::CompositeAlphaFlagBitsKHR::eOpaque;
    if (!(capabilities.supportedCompositeAlpha & vk::CompositeAlphaFlagBitsKHR::eOpaque)) {
        composite_alpha = vk::CompositeAlphaFlagBitsKHR::eInherit;
    }
    return true;
}

void Swapchain::WaitIdle() {
    // bbport: vkDeviceWaitIdle needs every queue of the device externally synchronized: the
    // recording threads submit to the same queue under this lock (Scheduler::submit_mutex).
    std::scoped_lock submit_lock{Scheduler::submit_mutex};
    const auto wait_result = instance.GetDevice().waitIdle();
    if (wait_result != vk::Result::eSuccess) {
        LOG_WARNING(Render_Vulkan, "Failed to wait for device to become idle: {}",
                    vk::to_string(wait_result));
    }
}

void Swapchain::RecreateSurface() {
    Destroy(); // a swapchain goes before its surface
    instance.GetInstance().destroySurfaceKHR(surface);
    surface = CreateSurface(instance.GetInstance(), window);
    surface_lost = false;
    std::printf("Display: the window's surface was lost; created again\n");
}

void Swapchain::Destroy() {
    vk::Device device = instance.GetDevice();
    WaitIdle();

    for (auto& image_view : images_view) {
        device.destroyImageView(image_view);
    }
    images_view.clear();
    images.clear();

    if (swapchain) {
        device.destroySwapchainKHR(swapchain);
        swapchain = nullptr; // bbport: a failed Create leaves none (IsPresentable)
    }

    for (const auto& sem : image_acquired) {
        device.destroySemaphore(sem);
    }
    for (const auto& sem : present_ready) {
        device.destroySemaphore(sem);
    }

    image_acquired.clear();
    present_ready.clear();
}

void Swapchain::RefreshSemaphores() {
    const vk::Device device = instance.GetDevice();
    image_acquired.resize(image_count);
    present_ready.resize(image_count);

    for (vk::Semaphore& semaphore : image_acquired) {
        auto [semaphore_result, sem] = device.createSemaphore({});
        ASSERT_MSG(semaphore_result == vk::Result::eSuccess,
                   "Failed to create image acquired semaphore: {}",
                   vk::to_string(semaphore_result));
        semaphore = sem;
    }
    for (vk::Semaphore& semaphore : present_ready) {
        auto [semaphore_result, sem] = device.createSemaphore({});
        ASSERT_MSG(semaphore_result == vk::Result::eSuccess,
                   "Failed to create present ready semaphore: {}", vk::to_string(semaphore_result));
        semaphore = sem;
    }

    for (u32 i = 0; i < image_count; ++i) {
        SetObjectName(device, image_acquired[i], "Swapchain Semaphore: image_acquired {}", i);
        SetObjectName(device, present_ready[i], "Swapchain Semaphore: present_ready {}", i);
    }
}

void Swapchain::SetupImages() {
    vk::Device device = instance.GetDevice();
    auto [images_result, imgs] = device.getSwapchainImagesKHR(swapchain);
    ASSERT_MSG(images_result == vk::Result::eSuccess, "Failed to create swapchain images: {}",
               vk::to_string(images_result));
    images = std::move(imgs);
    image_count = static_cast<u32>(images.size());
    images_view.resize(image_count);
    for (u32 i = 0; i < image_count; ++i) {
        if (images_view[i]) {
            device.destroyImageView(images_view[i]);
        }
        auto [im_view_result, im_view] = device.createImageView(vk::ImageViewCreateInfo{
            .image = images[i],
            .viewType = vk::ImageViewType::e2D,
            .format = needs_hdr ? SURFACE_FORMAT_HDR.format : surface_format.format,
            .subresourceRange =
                {
                    .aspectMask = vk::ImageAspectFlagBits::eColor,
                    .levelCount = 1,
                    .layerCount = 1,
                },
        });
        ASSERT_MSG(im_view_result == vk::Result::eSuccess, "Failed to create image view: {}",
                   vk::to_string(im_view_result));
        images_view[i] = im_view;
    }

    for (u32 i = 0; i < image_count; ++i) {
        SetObjectName(device, images[i], "Swapchain Image {}", i);
        SetObjectName(device, images_view[i], "Swapchain ImageView {}", i);
    }
}

} // namespace Vulkan
