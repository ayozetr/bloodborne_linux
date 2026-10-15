# SPDX-License-Identifier: GPL-2.0-or-later
# bbport: libbbsc.so, BBSC (Bloodborne Seamless Co-op, CLS_AMG) for the Linux port. The mod's
# own build (emulator/mod/build-mod.cmd) makes bbsc.dll for Windows; this one builds the same
# game logic (emulator/src/core/bloodborne_re.cpp with BBSC_MOD) with the mod's network files and
# the Linux counterparts of its platform files (emulator/mod/linux/). bb-probe loads it into the
# game's process (BB_BBSC_LIB) and calls bbsc_start().
cmake_minimum_required(VERSION 3.20)
project(bbsc CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

find_path(XBYAK_INCLUDE xbyak/xbyak.h REQUIRED)
find_path(FMT_INCLUDE fmt/format.h REQUIRED)

add_library(bbsc SHARED
    emulator/src/core/bloodborne_re.cpp
    emulator/src/core/bbsc_memscan.cpp
    emulator/mod/bbsc_relay.cpp
    emulator/mod/bbsc_channel.cpp
    emulator/mod/bbsc_http.cpp
    emulator/mod/linux/bbsc_mod_linux.cpp
    emulator/mod/linux/bbsc_hooks_linux.cpp)
target_compile_definitions(bbsc PRIVATE BBSC_MOD FMT_HEADER_ONLY)
target_include_directories(bbsc PRIVATE emulator/mod emulator/mod/shim emulator/src
                           ${XBYAK_INCLUDE} ${FMT_INCLUDE})
# Only bbsc_start is for bb-probe; the game's runtime symbols it calls (runtime_memory_vma_info)
# come from bb-probe itself, which exports them.
set_target_properties(bbsc PROPERTIES CXX_VISIBILITY_PRESET hidden VISIBILITY_INLINES_HIDDEN ON)
target_link_options(bbsc PRIVATE -Wl,-z,undefs)
find_package(Threads REQUIRED)
target_link_libraries(bbsc PRIVATE Threads::Threads)

# BBSC turns itself off without its license, notice and supporters list next to it (as the
# Windows mod folder has them).
add_custom_command(TARGET bbsc POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different ${CMAKE_CURRENT_SOURCE_DIR}/LICENSE
            $<TARGET_FILE_DIR:bbsc>/LICENSE.txt
    COMMAND ${CMAKE_COMMAND} -E copy_if_different ${CMAKE_CURRENT_SOURCE_DIR}/NOTICE.md
            $<TARGET_FILE_DIR:bbsc>/NOTICE.txt
    COMMAND ${CMAKE_COMMAND} -E copy_if_different ${CMAKE_CURRENT_SOURCE_DIR}/SUPPORTERS.txt
            $<TARGET_FILE_DIR:bbsc>/SUPPORTERS.txt)
