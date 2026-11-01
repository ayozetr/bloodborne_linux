// SPDX-License-Identifier: GPL-2.0-or-later
// bbport: Hunter's Atlas's texts in the languages of the port's menus (Atlas has English and a
// Russian tile label). The map and its quick-menu tile follow the game's language, like the
// port's pages in the game's System menu (BbGameMenu::Language); the map's section of the
// port's own menu (Insert) follows that menu's language. English when a text is missing.
#pragma once

#include <array>
#include <string_view>
#include <unordered_map>

#include "bbport_game_menu.h"
#include "bbport_settings.h"

namespace BbAtlasText {

/// English -> Russian, Spanish, Italian, French, German, Brazilian Portuguese, Simplified Chinese
/// (BbSettings::MenuLanguage order from Russian on).
inline const char* In(BbSettings::MenuLanguage language, const char* english) {
    using Row = std::array<const char*, 7>;
    static const std::unordered_map<std::string_view, Row> table{
        // The quick-menu tile and the map.
        {"Map", {"Карта", "Mapa", "Mappa", "Carte", "Karte", "Mapa", "地图"}},
        // The game's own label of the tile left of the Map tile, which the Map tile's label covers.
        {"System", {"Система", "Sistema", "Sistema", "Système", "System", "Sistema", "系统"}},
        {"Lamps", {"Фонари", "Faroles", "Lanterne", "Lanternes", "Laternen", "Lanternas", "提灯"}},
        {"Pointer", {"Указатель", "Puntero", "Puntatore", "Pointeur", "Zeiger", "Ponteiro", "指针"}},
        {"Pan", {"Сдвиг", "Desplazar", "Sposta", "Déplacer", "Verschieben", "Mover", "平移"}},
        {"Zoom", {"Масштаб", "Zoom", "Zoom", "Zoom", "Zoom", "Zoom", "缩放"}},
        {"Recenter", {"Центрировать", "Centrar", "Centra", "Recentrer", "Zentrieren", "Centralizar", "回到中心"}},
        {"Travel", {"Перейти", "Viajar", "Viaggia", "Voyager", "Reisen", "Viajar", "前往"}},
        {"Back", {"Назад", "Volver", "Indietro", "Retour", "Zurück", "Voltar", "返回"}},
        {"Cancel", {"Отмена", "Cancelar", "Annulla", "Annuler", "Abbrechen", "Cancelar", "取消"}},
        {"Floor", {"Этаж", "Planta", "Piano", "Étage", "Ebene", "Andar", "楼层"}},
        {"Other levels", {"Другие уровни", "Otros niveles", "Altri livelli", "Autres niveaux", "Andere Ebenen",
                          "Outros níveis", "其他楼层"}},
        {"Interior", {"Помещение", "Interior", "Interno", "Intérieur", "Innenraum", "Interior", "室内"}},
        {"High", {"Выше", "Alto", "Alto", "Haut", "Hoch", "Alto", "高"}},
        {"Low", {"Ниже", "Bajo", "Basso", "Bas", "Tief", "Baixo", "低"}},
        {"Pickups", {"Предметы", "Objetos", "Oggetti", "Objets", "Gegenstände", "Itens", "可拾取物品"}},
        {"Blood vials", {"Флаконы крови", "Viales de sangre", "Fiale di sangue", "Fioles de sang", "Blutphiolen",
                         "Frascos de sangue", "采血瓶"}},
        {"Insight", {"Озарение", "Perspicacia", "Intuizione", "Perspicacité", "Einsicht", "Discernimento", "洞察"}},
        {"Equipment", {"Снаряжение", "Equipo", "Equipaggiamento", "Équipement", "Ausrüstung", "Equipamento", "装备"}},
        {"Coldblood", {"Холодная кровь", "Sangre fría", "Sangue freddo", "Sang-froid", "Kaltblut", "Sangue-frio",
                       "冷血"}},
        {"Cross", {"Крест", "Cruz", "Croce", "Croix", "Kreuz", "Xis", "叉"}},
        {"Circle", {"Круг", "Círculo", "Cerchio", "Rond", "Kreis", "Círculo", "圆"}},
        {"Triangle", {"Треугольник", "Triángulo", "Triangolo", "Triangle", "Dreieck", "Triângulo", "三角"}},
        {"Click", {"Щелчок", "Clic", "Clic", "Clic", "Klick", "Clique", "点击"}},
        {"Drag", {"Перетаскивание", "Arrastrar", "Trascina", "Glisser", "Ziehen", "Arrastar", "拖动"}},
        {"Near ", {"Рядом: ", "Cerca de ", "Vicino a ", "Près de ", "Nahe ", "Perto de ", "靠近 "}},
        {"Travel to lamp", {"Перейти к фонарю", "Viajar al farol", "Viaggia alla lanterna", "Voyager vers la lanterne",
                            "Zur Laterne reisen", "Viajar para a lanterna", "前往提灯"}},
        // "Travel to " + the lamp + "?"
        {"Travel to ", {"Перейти к: ", "¿Viajar a ", "Viaggiare a ", "Voyager vers ", "Reisen nach ", "Viajar para ",
                        "前往 "}},
        {"Select to travel", {"Выберите, чтобы перейти", "Selecciona para viajar", "Seleziona per viaggiare",
                              "Sélectionner pour voyager", "Zum Reisen auswählen", "Selecione para viajar",
                              "选择以前往"}},
        {"Locked or currently unavailable", {"Закрыт или сейчас недоступен", "Bloqueado o no disponible ahora",
                                             "Bloccata o non disponibile ora", "Verrouillée ou indisponible pour l'instant",
                                             "Gesperrt oder gerade nicht verfügbar",
                                             "Bloqueada ou indisponível no momento", "未解锁或当前不可用"}},
        {"Map fast travel is disabled in the launcher",
         {"Быстрое перемещение по карте выключено в лаунчере",
          "El viaje rápido del mapa está desactivado en el launcher",
          "Il viaggio rapido della mappa è disattivato nel launcher",
          "Le voyage rapide de la carte est désactivé dans le lanceur",
          "Die Schnellreise der Karte ist im Launcher ausgeschaltet",
          "A viagem rápida do mapa está desativada no launcher", "地图快速传送已在启动器中关闭"}},
        {"This lamp is currently unavailable.",
         {"Этот фонарь сейчас недоступен.", "Este farol no está disponible ahora.",
          "Questa lanterna non è disponibile ora.", "Cette lanterne est indisponible pour l'instant.",
          "Diese Laterne ist gerade nicht verfügbar.", "Esta lanterna está indisponível no momento.",
          "此提灯当前不可用。"}},
        {"The destination changed or the game cannot travel now.",
         {"Пункт назначения изменился или сейчас перемещение невозможно.",
          "El destino ha cambiado o el juego no puede viajar ahora.",
          "La destinazione è cambiata o il gioco non può viaggiare ora.",
          "La destination a changé ou le jeu ne peut pas voyager maintenant.",
          "Das Ziel hat sich geändert oder das Spiel kann gerade nicht reisen.",
          "O destino mudou ou o jogo não pode viajar agora.", "目的地已变更，或游戏当前无法传送。"}},
        {"Travel was rejected or did not complete. No second request was sent.",
         {"Перемещение отклонено или не завершилось. Повторный запрос не отправлялся.",
          "El viaje fue rechazado o no terminó. No se envió una segunda petición.",
          "Il viaggio è stato rifiutato o non è terminato. Non è stata inviata una seconda richiesta.",
          "Le voyage a été refusé ou ne s'est pas terminé. Aucune seconde demande n'a été envoyée.",
          "Die Reise wurde abgelehnt oder nicht abgeschlossen. Es wurde keine zweite Anfrage gesendet.",
          "A viagem foi recusada ou não terminou. Nenhum segundo pedido foi enviado.",
          "传送被拒绝或未完成。未发送第二次请求。"}},
        {"No available lamps for this character.",
         {"У этого персонажа нет доступных фонарей.", "Este personaje no tiene faroles disponibles.",
          "Questo personaggio non ha lanterne disponibili.", "Ce personnage n'a aucune lanterne disponible.",
          "Dieser Charakter hat keine verfügbaren Laternen.", "Este personagem não tem lanternas disponíveis.",
          "此角色没有可用的提灯。"}},
        {"Awaiting your location", {"Ожидание вашего местоположения", "Esperando tu ubicación",
                                    "In attesa della tua posizione", "En attente de votre position",
                                    "Warte auf deine Position", "Aguardando sua localização", "正在等待你的位置"}},
        {"Location unavailable", {"Местоположение недоступно", "Ubicación no disponible", "Posizione non disponibile",
                                  "Position indisponible", "Position nicht verfügbar", "Localização indisponível",
                                  "位置不可用"}},
        {"Map data is not available for this location",
         {"Для этого места нет данных карты", "No hay datos del mapa para este lugar",
          "Non ci sono dati della mappa per questo luogo", "Aucune donnée de carte pour cet endroit",
          "Für diesen Ort gibt es keine Kartendaten", "Não há dados de mapa para este local", "此位置没有地图数据"}},
        {"Your position is unavailable while loading or outside a supported area",
         {"Ваше местоположение недоступно во время загрузки или вне поддерживаемой зоны",
          "Tu posición no está disponible durante una carga o fuera de una zona compatible",
          "La tua posizione non è disponibile durante un caricamento o fuori da una zona supportata",
          "Votre position est indisponible pendant un chargement ou hors d'une zone prise en charge",
          "Deine Position ist während des Ladens oder außerhalb eines unterstützten Gebiets nicht verfügbar",
          "Sua posição fica indisponível durante o carregamento ou fora de uma área compatível",
          "加载中或位于不支持的区域时无法显示你的位置"}},
        {"Move the left stick to point at a lamp.",
         {"Наведите левый стик на фонарь.", "Mueve el stick izquierdo para señalar un farol.",
          "Muovi la levetta sinistra per indicare una lanterna.", "Déplacez le stick gauche pour viser une lanterne.",
          "Bewege den linken Stick auf eine Laterne.", "Mova o analógico esquerdo para apontar uma lanterna.",
          "移动左摇杆指向提灯。"}},
        {"Move the right stick to pan.",
         {"Двигайте правый стик, чтобы сдвинуть карту.", "Mueve el stick derecho para desplazar el mapa.",
          "Muovi la levetta destra per spostare la mappa.", "Déplacez le stick droit pour faire défiler la carte.",
          "Bewege den rechten Stick, um die Karte zu verschieben.", "Mova o analógico direito para mover o mapa.",
          "移动右摇杆平移地图。"}},
        {"Drag the map to pan.", {"Перетащите карту, чтобы сдвинуть её.", "Arrastra el mapa para desplazarlo.",
                                  "Trascina la mappa per spostarla.", "Faites glisser la carte pour la déplacer.",
                                  "Ziehe die Karte, um sie zu verschieben.", "Arraste o mapa para movê-lo.",
                                  "拖动地图以平移。"}},
        // The map's section in the port's own menu (Insert).
        {"Navigation map", {"Карта", "Mapa de navegación", "Mappa di navigazione", "Carte de navigation",
                            "Navigationskarte", "Mapa de navegação", "导航地图"}},
        {"Enable full-screen map", {"Включить полноэкранную карту", "Activar el mapa a pantalla completa",
                                    "Attiva la mappa a schermo intero", "Activer la carte en plein écran",
                                    "Vollbildkarte aktivieren", "Ativar o mapa em tela cheia", "启用全屏地图"}},
        {"Enable or disable Hunter's Atlas in the launcher.",
         {"Включайте и выключайте Hunter's Atlas в лаунчере.", "Activa o desactiva Hunter's Atlas en el launcher.",
          "Attiva o disattiva Hunter's Atlas nel launcher.", "Activez ou désactivez Hunter's Atlas dans le lanceur.",
          "Hunter's Atlas im Launcher ein- oder ausschalten.", "Ative ou desative o Hunter's Atlas no launcher.",
          "在启动器中开启或关闭 Hunter's Atlas。"}},
        {"Map key", {"Клавиша карты", "Tecla del mapa", "Tasto della mappa", "Touche de la carte", "Kartentaste",
                     "Tecla do mapa", "地图按键"}},
        {"Map controller shortcut", {"Сочетание на геймпаде", "Atajo del mando", "Scorciatoia del controller",
                                     "Raccourci manette", "Controller-Kürzel", "Atalho do controle", "手柄快捷键"}},
        {"Open map", {"Открыть карту", "Abrir el mapa", "Apri la mappa", "Ouvrir la carte", "Karte öffnen",
                      "Abrir o mapa", "打开地图"}},
        {"Disabled", {"Выключено", "Desactivado", "Disattivato", "Désactivé", "Aus", "Desativado", "关闭"}},
        {"Open game menu, then click right stick (R3)",
         {"Откройте меню игры, затем нажмите правый стик (R3)", "Abre el menú del juego y pulsa el stick derecho (R3)",
          "Apri il menu di gioco, poi premi la levetta destra (R3)",
          "Ouvrez le menu du jeu, puis cliquez sur le stick droit (R3)",
          "Spielmenü öffnen, dann rechten Stick drücken (R3)",
          "Abra o menu do jogo e pressione o analógico direito (R3)", "打开游戏菜单，然后按下右摇杆（R3）"}},
        {"Hold LB / L1 + RB / R1 + Menu / Options for about 650 ms",
         {"Удерживайте LB / L1 + RB / R1 + Menu / Options около 650 мс",
          "Mantén LB / L1 + RB / R1 + Menú / Options unos 650 ms",
          "Tieni premuti LB / L1 + RB / R1 + Menu / Options per circa 650 ms",
          "Maintenez LB / L1 + RB / R1 + Menu / Options environ 650 ms",
          "LB / L1 + RB / R1 + Menü / Options etwa 650 ms halten",
          "Segure LB / L1 + RB / R1 + Menu / Options por cerca de 650 ms",
          "按住 LB / L1 + RB / R1 + Menu / Options 约 650 毫秒"}},
    };
    const int index = int(language) - int(BbSettings::MenuLanguage::Russian);
    if (index < 0 || index >= int(Row().size())) {
        return english;
    }
    const auto it = table.find(english);
    return it == table.end() ? english : it->second[size_t(index)];
}

/// The map and the tile: the game's language.
inline const char* Game(const char* english) {
    return In(BbGameMenu::Language(), english);
}

/// The map's section in the port's menu: that menu's language.
inline const char* Menu(const char* english) {
    return In(BbSettings::Get().menu_language.load(), english);
}

/// Whether the game's language needs the port's font: the map's font (made from the game's own
/// menu font) keeps Latin and Cyrillic, every text above but the Chinese, and no CJK glyphs.
inline bool NeedsPortFont() {
    return BbGameMenu::Language() == BbSettings::MenuLanguage::ChineseSimplified;
}

} // namespace BbAtlasText
