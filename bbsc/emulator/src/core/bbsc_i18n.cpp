// SPDX-License-Identifier: GPL-2.0-or-later
// bbport: BBSC's own texts in the game's language, see bbsc_i18n.h.

#include "core/bbsc_i18n.h"

#include <cstdlib>
#include <mutex>
#include <unordered_map>

namespace Core::Bbsc {
namespace {

// The languages of bbsc/translations, in the column order of bbsc_translations.inc.
enum Language { Spanish, French, German, Italian, Portuguese, Russian, LanguageCount };

struct Translation {
    const char16_t* english;
    const char16_t* text[LanguageCount];
};

constexpr Translation Translations[] = {
#include "core/bbsc_translations.inc"
};

constexpr std::u16string_view BossTag = u"<?npcNameId@";
constexpr std::u16string_view BossPlaceholder = u"{boss}";

// The PS4 system language codes of the game (BB_LANGUAGE): -1 for English and the others.
int GameLanguage() {
    static const int language = [] {
        const char* value = std::getenv("BB_LANGUAGE");
        switch (value != nullptr ? std::atoi(value) : 1) {
        case 3:  // Spanish (Spain)
        case 20: // Spanish (Latin America)
            return int{Spanish};
        case 2:  // French
        case 22: // French (Canada)
            return int{French};
        case 4:
            return int{German};
        case 5:
            return int{Italian};
        case 7:  // Portuguese (Portugal)
        case 17: // Portuguese (Brazil)
            return int{Portuguese};
        case 8:
            return int{Russian};
        default:
            return -1;
        }
    }();
    return language;
}

const char16_t* Lookup(std::u16string_view english, int language) {
    for (const Translation& entry : Translations) {
        if (english == entry.english) {
            return entry.text[language];
        }
    }
    return nullptr;
}

std::u16string Replace(std::u16string text, std::u16string_view from, std::u16string_view to) {
    for (size_t at = text.find(from); at != std::u16string::npos; at = text.find(from, at)) {
        text.replace(at, from.size(), to);
        at += to.size();
    }
    return text;
}

} // namespace

const char16_t* Text(const char16_t* english) {
    const int language = GameLanguage();
    if (english == nullptr || language < 0) {
        return english;
    }
    if (const char16_t* text = Lookup(english, language)) {
        return text;
    }
    // A text naming one boss: its {boss} form's translation, with the same tag. Made once per
    // text and kept (the game keeps pointing at it).
    const std::u16string_view view{english};
    const size_t tag = view.find(BossTag);
    const size_t tag_end = tag != std::u16string_view::npos ? view.find(u"?>", tag) : tag;
    if (tag_end == std::u16string_view::npos) {
        return english;
    }
    static std::mutex mutex;
    static std::unordered_map<std::u16string_view, std::u16string> made;
    std::scoped_lock lock{mutex};
    if (const auto found = made.find(view); found != made.end()) {
        return found->second.c_str();
    }
    const std::u16string_view boss = view.substr(tag, tag_end + 2 - tag);
    std::u16string form{view};
    form.replace(tag, boss.size(), BossPlaceholder);
    const char16_t* text = Lookup(form, language);
    if (text == nullptr) {
        return english;
    }
    return made.emplace(view, Replace(text, BossPlaceholder, boss)).first->second.c_str();
}

std::u16string TextWith(const char16_t* english_template, std::u16string_view boss) {
    const int language = GameLanguage();
    const char16_t* text = language >= 0 ? Lookup(english_template, language) : nullptr;
    return Replace(text != nullptr ? text : english_template, BossPlaceholder, boss);
}

} // namespace Core::Bbsc
