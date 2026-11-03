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
# Libraries the Linux fork's build takes from the AUR, at the versions it was tested with:
# VulkanMemoryAllocator 3.5.0 and magic_enum 0.9.8 (installed with their CMake files, which
# gpu/CMakeLists.txt asks for) and xbyak 7.43's headers.
RUN git clone --quiet --depth 1 --branch v3.5.0 \
        https://github.com/GPUOpen-LibrariesAndSDKs/VulkanMemoryAllocator /tmp/vma \
    && cmake -S /tmp/vma -B /tmp/vma/build -DCMAKE_INSTALL_PREFIX=/usr >/dev/null \
    && cmake --install /tmp/vma/build >/dev/null \
    && git clone --quiet --depth 1 --branch v0.9.8 https://github.com/Neargye/magic_enum /tmp/me \
    && cmake -S /tmp/me -B /tmp/me/build -DCMAKE_INSTALL_PREFIX=/usr -DMAGIC_ENUM_OPT_BUILD_EXAMPLES=OFF \
        -DMAGIC_ENUM_OPT_BUILD_TESTS=OFF >/dev/null \
    && cmake --install /tmp/me/build >/dev/null \
    && git clone --quiet --depth 1 --branch v7.43 https://github.com/herumi/xbyak /tmp/xbyak \
    && install -d /usr/include/xbyak && install -m644 /tmp/xbyak/xbyak/*.h /usr/include/xbyak/ \
    && rm -rf /tmp/vma /tmp/me /tmp/xbyak
RUN install -d -m777 /home/builder
