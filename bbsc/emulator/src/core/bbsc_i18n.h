// SPDX-License-Identifier: GPL-2.0-or-later
// bbport: BBSC's own texts in the game's language. BBSC writes them in English; the translations
// (bbsc/translations/*.json, made into bbsc_translations.inc by gen_translations.py) are looked up
// by that English text, so BBSC's sources keep their English strings as they are.

#pragma once

#include <string>
#include <string_view>

namespace Core::Bbsc {

// `english` in the game's language (BB_LANGUAGE, the PS4 system language code), or `english`
// itself when there is no translation. A text naming one boss (<?npcNameId@N?>) uses the
// translation of its {boss} form. The pointer stays valid for the whole run.
const char16_t* Text(const char16_t* english);

// The translation of `english_template`, whose {boss} is replaced by `boss`.
std::u16string TextWith(const char16_t* english_template, std::u16string_view boss);

} // namespace Core::Bbsc
