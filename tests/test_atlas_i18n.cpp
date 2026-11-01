// SPDX-License-Identifier: GPL-2.0-or-later
// bbport: Hunter's Atlas's texts in the port's menu languages (gpu/shim/bbport_atlas_i18n.h).
#include "bbport_atlas_i18n.h"

#include <cassert>
#include <cstdio>
#include <cstring>

int main() {
    using L = BbSettings::MenuLanguage;
    using BbAtlasText::In;
    // English, and texts the table does not have, stay as they are.
    assert(!std::strcmp(In(L::English, "Map"), "Map"));
    assert(!std::strcmp(In(L::Spanish, "Not a text of the map"), "Not a text of the map"));
    // Every column in MenuLanguage order, Russian first.
    assert(!std::strcmp(In(L::Russian, "Map"), "Карта"));
    assert(!std::strcmp(In(L::Spanish, "Map"), "Mapa"));
    assert(!std::strcmp(In(L::Italian, "Map"), "Mappa"));
    assert(!std::strcmp(In(L::French, "Map"), "Carte"));
    assert(!std::strcmp(In(L::German, "Map"), "Karte"));
    assert(!std::strcmp(In(L::PortugueseBrazil, "Map"), "Mapa"));
    assert(!std::strcmp(In(L::ChineseSimplified, "Map"), "地图"));
    assert(!std::strcmp(In(L::Count, "Map"), "Map"));
    // A text built around a name, and a text the map compares after translating it.
    assert(!std::strcmp(In(L::Spanish, "Travel to "), "¿Viajar a "));
    assert(!std::strcmp(In(L::French, "Pointer"), "Pointeur"));
    std::puts("ATLAS_I18N_PASS");
    return 0;
}
