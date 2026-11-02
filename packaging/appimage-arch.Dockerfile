# SPDX-FileCopyrightText: Copyright 2026 bbport contributors
# SPDX-License-Identifier: GPL-2.0-or-later
# Plain Arch Linux with what build.sh and packaging/appimage-sharun.sh need (see
# packaging/appimage-in-arch.sh). Arch's packages are built for any x86-64 processor.
FROM archlinux:base-devel
# The image leaves translations out of every package it installs: GTK's and libadwaita's (and
# X11's compose tables) go into the AppImage, so they are kept.
RUN sed -i -e '/^NoExtract *= *usr\/share\/locale/d' -e '/^NoExtract *= *!/d' /etc/pacman.conf
RUN pacman -Syu --noconfirm --needed git cmake ninja python python-gobject gtk4 libadwaita sdl3 \
        vulkan-headers vulkan-icd-loader vulkan-tools glslang spirv-headers spirv-cross ffmpeg boost fmt \
        robin-map xxhash zydis miniz protobuf nlohmann-json openssl miniupnpc python-pillow \
        ttf-dejavu vulkan-radeon vulkan-intel mesa rust curl wget file patchelf zsync squashfs-tools \
        python-cairo librsvg gdk-pixbuf2 alsa-plugins pipewire-alsa \
    && pacman -Scc --noconfirm
# Header-only libraries the Linux fork's build takes from the AUR, at the versions it was tested
# with: VulkanMemoryAllocator 3.5.0 and xbyak 7.43.
RUN git clone --quiet --depth 1 --branch v3.5.0 \
        https://github.com/GPUOpen-LibrariesAndSDKs/VulkanMemoryAllocator /tmp/vma \
    && install -m644 /tmp/vma/include/vk_mem_alloc.h /usr/include/ \
    && git clone --quiet --depth 1 --branch v7.43 https://github.com/herumi/xbyak /tmp/xbyak \
    && install -d /usr/include/xbyak && install -m644 /tmp/xbyak/xbyak/*.h /usr/include/xbyak/ \
    && rm -rf /tmp/vma /tmp/xbyak
RUN install -d -m777 /home/builder
