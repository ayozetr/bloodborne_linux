// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <cstdlib>
#include "bb_env.h"
#include <filesystem>
#include <string>
inline std::filesystem::path BbAtlasPath(const char* name,std::filesystem::path fallback={}) {
#ifdef _WIN32
    const std::wstring wide_name(name,name+std::char_traits<char>::length(name));
    const wchar_t* value=_wgetenv(wide_name.c_str());
    return value&&*value?std::filesystem::path(value):fallback;
#else
    // bbport (Linux fork): through bb_env(), as every BB_* variable (gpu/shim/bb_env_vars.def).
    const char* value=bb_env(name);return value&&*value?std::filesystem::path(value):fallback;
#endif
}
