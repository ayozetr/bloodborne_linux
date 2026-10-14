# SPDX-License-Identifier: GPL-2.0-or-later
"""Launcher translations. The Russian text is the key; other languages are looked up by it.

ui_language in the launcher settings: one of LANGUAGES or "" (the system locale; English when
the launcher has no translation for it).
"""
import os

EN = {
    "Папка DLC": "DLC folder",
    "Выбрать папку DLC": "Choose the DLC folder",
    "Не использовать DLC": "Don't use DLC",
    "Найдено DLC: {}": "DLC found: {}",
    "Не используется": "Not used",
    "Нет DLC этой игры в папке": "No DLC of this game in the folder",
    # Window, pages, buttons
    "Запустить": "Play",
    "Остановить": "Stop",
    "Настройки": "Settings",
    "Журнал": "Log",
    "Не удалось запустить: {}": "Could not start: {}",
    "Копировать": "Copy",
    "Экспорт журнала…": "Export log…",
    "Экспорт журнала": "Export log",
    "Журнал скопирован": "Log copied",
    "Журнал сохранён: {}": "Log saved: {}",
    "Не удалось сохранить журнал: {}": "Could not save the log: {}",
    "\n— игра завершилась (код {}) —\n": "\n— the game exited (code {}) —\n",
    # Launcher language
    "Язык лаунчера": "Launcher language",
    "Как в системе": "System",
    "Применится после перезапуска лаунчера, пока игра запущена":
        "Applies after restarting the launcher while the game is running",
    # Game
    "Игра": "Game",
    "Папка игры ({})": "Game folder ({})",
    "Папка игры": "Game folder",
    "Выбрать папку с eboot.bin": "Choose the folder with eboot.bin",
    "Открыть в файловом менеджере": "Open in the file manager",
    "Папка сохранений": "Saves folder",
    "Выбрать папку сохранений": "Choose the saves folder",
    "Вернуть папку по умолчанию": "Back to the default folder",
    "Язык системы": "System language",
    "По умолчанию: {}": "Default: {}",
    "Найдены сохранения": "Saves found",
    "Сохранений пока нет: игра создаст их здесь": "No saves yet: the game will create them here",
    "не выбрана": "not chosen",
    "Найден eboot.bin": "eboot.bin found",
    "Нет eboot.bin в папке": "No eboot.bin in the folder",
    "Управление": "Controls",
    "Клавиатура": "Keyboard",
    "Геймпад": "Gamepad",
    "Назначение кнопок; применяется при запуске игры": "Button assignments; applied when the game starts",
    "Назначить": "Assign",
    "Сбросить": "Reset",
    "{} (по умолчанию)": "{} (default)",
    "не назначено": "not assigned",
    "Нажмите клавишу или кнопку… (Esc — отмена)": "Press a key or a button… (Esc cancels)",
    "Крест": "Cross",
    "Круг": "Circle",
    "Квадрат": "Square",
    "Треугольник": "Triangle",
    "Тачпад, левая половина (жесты)": "Touchpad, left half (gestures)",
    "Тачпад, правая половина (личные вещи)": "Touchpad, right half (key items)",
    "Крестовина вверх": "D-pad up",
    "Крестовина вниз": "D-pad down",
    "Крестовина влево": "D-pad left",
    "Крестовина вправо": "D-pad right",
    "Движение вперёд": "Move forward",
    "Движение назад": "Move back",
    "Движение влево": "Move left",
    "Движение вправо": "Move right",
    "Камера вверх": "Camera up",
    "Камера вниз": "Camera down",
    "Камера влево": "Camera left",
    "Камера вправо": "Camera right",
    "Контроллер": "Controller",
    "Выбранный берётся, как только подключится": "The chosen one is used as soon as it connects",
    "Первый подключённый": "First connected",
    "{} (не подключён)": "{} (not connected)",
    "Монитор": "Monitor",
    "Пропускать выбор «по сети / вне сети»": "Skip the \u201cplay online / offline\u201d choice",
    "Игра сразу открывает главное меню в режиме вне сети (патч игры)":
        "The game opens the main menu offline at once (a game patch)",
    "Основной": "Primary",
    ", основной": ", primary",
    "Нужно обновление 1.09: скопируйте файлы дампа обновления 1.09 в папку игры с заменой (найдена версия {})":
        "The 1.09 update is needed: copy the dumped 1.09 update into the game folder, replacing files (found version {})",
    "eboot.bin не от версии 1.09: скопируйте eboot.bin из дампа обновления 1.09 в папку игры с заменой":
        "eboot.bin is not from 1.09: copy eboot.bin from the dumped 1.09 update into the game folder, replacing it",
    "eboot.bin с вшитым патчем 60 FPS от Lance McDonald: из-за него игра падает в меню жестов. Скопируйте чистый eboot.bin из дампа обновления 1.09 в папку игры с заменой":
        "This eboot.bin has Lance McDonald's 60 fps patch baked in, which crashes the game in the gestures menu: copy a clean eboot.bin from the dumped 1.09 update into the game folder, replacing it",
    "Это не магазинное издание Bloodborne (найдено {}): нужен Bloodborne любого региона с обновлением 1.09":
        "Not a retail release of Bloodborne (found {}): Bloodborne from any region with update 1.09 is needed",
    "eboot.bin не читается как расшифрованный исполняемый файл PS4: сделайте дамп заново":
        "eboot.bin cannot be read as a decrypted PS4 executable: dump the game again",
    "Файлы игры повреждены при распаковке: шейдеры не распаковываются, игра зависнет на загрузке. Распакуйте игру и обновление 1.09 заново исправленным инструментом (issue #81)":
        "The game files were damaged when extracted: the shaders do not unpack and the game would hang while loading. Extract the game and the 1.09 update again with a fixed tool (issue #81)",
    "Bloodborne {}, версия 1.09": "Bloodborne {}, version 1.09",
    "Папка игры (с eboot.bin)": "Game folder (with eboot.bin)",
    # Languages
    "Английский": "English",
    "Русский": "Russian",
    "Японский": "Japanese",
    "Французский": "French",
    "Испанский": "Spanish",
    "Немецкий": "German",
    "Итальянский": "Italian",
    # Mods
    "Моды": "Mods",
    "Распакуйте каждый мод в отдельную папку (с dvdroot_ps4 или сразу с chr/, parts/ и т. п.). "
    "При совпадении файлов побеждает мод ниже в списке. Применяется при запуске.":
        "Extract each mod into its own folder (with dvdroot_ps4, or chr/, parts/, ... directly). "
        "When files collide, the mod lower in the list wins. Applied at start.",
    "Загружать моды": "Load mods",
    "Папка модов": "Mods folder",
    "Выбрать папку модов": "Choose the mods folder",
    "Открыть папку модов": "Open the mods folder",
    "Обновить список": "Refresh the list",
    "Загрузить раньше": "Load earlier",
    "Загрузить позже": "Load later",
    "Модов нет": "No mods",
    # Patches
    "Сторонние патчи": "Third-party patches",
    "XML-патчи в формате shadPS4 для версии 01.09 из папки патчей. Применяются при запуске.":
        "shadPS4-format XML patches for version 01.09 from the patches folder. Applied at start.",
    "Папка патчей": "Patches folder",
    "Выбрать папку патчей": "Choose the patches folder",
    "Открыть папку патчей": "Open the patches folder",
    "Патчей нет": "No patches",
    "Автор: {}": "Author: {}",
    # Screen
    "Экран": "Display",
    "Разрешение вывода": "Output resolution",
    "Апскейлер дорисовывает кадр; Steam Deck — 720p": "The upscaler fills the frame; Steam Deck: 720p",
    "Полноэкранный режим": "Fullscreen",
    "Смена разрешения на лету": "Live resolution changes",
    "Без перезапуска, но медленнее на Steam Deck и старых GPU":
        "No restart needed, but slower on the Steam Deck and older GPUs",
    "Авто (по видеокарте)": "Auto (by GPU)",
    "Выключена (быстрее)": "Off (faster)",
    "Включена": "On",
    "Режим показа кадров": "Present mode",
    "Разрешить HDR": "Allow HDR",
    # Upscaler
    "Апскейлер": "Upscaler",
    "Хранится в bbport.ini; в игре меняется через меню (Insert или L3+R3)":
        "Stored in bbport.ini; in game, change it in the menu (Insert or L3+R3)",
    "TAA (нативное сглаживание)": "TAA (native anti-aliasing)",
    "Выключен": "Off",
    "Пресет": "Preset",
    "Резкость (RCAS)": "Sharpening (RCAS)",
    "Сила резкости": "Sharpness",
    "Векторы движения объектов": "Object motion vectors",
    "Меньше гостинга на персонажах; стоит около 10% FPS": "Less ghosting on characters; costs about 10% FPS",
    "Показывать FPS": "Show FPS",
    "Ассеты найдены": "Assets found",
    "Нет ассетов: tools/fetch_fsr4_assets.sh": "No assets: tools/fetch_fsr4_assets.sh",
    "Ассеты для выбранного режима найдены": "Assets for the selected mode found",
    "{}. Соберите FSR 4.1.1 из своей DLL кнопкой «Выбрать DLL…» ниже":
        "{}. Build FSR 4.1.1 from your own DLL with the “Choose DLL…” button below",
    "FSR 4.1.1 из своей DLL AMD": "FSR 4.1.1 from your own AMD DLL",
    "Отменить": "Cancel",
    "Выбрать DLL…": "Choose DLL…",
    "DLL апскейлера AMD (amd_fidelityfx_upscaler_dx12.dll)": "AMD upscaler DLL (amd_fidelityfx_upscaler_dx12.dll)",
    "нет": "none",
    "Эта DLL не подходит": "This DLL does not fit",
    "{}: версия {}, модели FSR 4: {}.\n\nbbport повторяет только официальную FSR 4.1.x от AMD (модель v07_fp8_no_scale): например, FSR4_LATEST из OptiScaler или amd_fidelityfx_upscaler_dx12.dll из игры с FSR 4.1. Сборки сообщества (4.0.2b и подобные) устроены иначе и пока не поддерживаются.":
        "{}: version {}, FSR 4 models: {}.\n\nbbport replays AMD's official FSR 4.1.x only (model v07_fp8_no_scale): for example FSR4_LATEST from OptiScaler, or amd_fidelityfx_upscaler_dx12.dll from a game with FSR 4.1. Community builds (4.0.2b and the like) are laid out differently and are not supported yet.",
    "Загрузчик не подходит": "The loader does not fit",
    "Загрузчик FidelityFX (amd_fidelityfx_loader_dx12.dll или amd_fidelityfx_dx12.dll)":
        "FidelityFX loader (amd_fidelityfx_loader_dx12.dll or amd_fidelityfx_dx12.dll)",
    "\n— сборка FSR 4.1.1 из {} —\n": "\n— building FSR 4.1.1 from {} —\n",
    "Подготовка…": "Preparing…",
    "Запись проходов DLL под Proton: {} из {}": "Recording the DLL's passes under Proton: {} of {}",
    "Перевод проходов в SPIR-V…": "Translating the passes to SPIR-V…",
    "— сборка FSR 4.1.1 завершилась (код {}) —\n": "— FSR 4.1.1 build finished (code {}) —\n",
    "FSR 4.1.1 собран и выбран": "FSR 4.1.1 built and selected",
    "Сборка FSR 4.1.1 отменена": "FSR 4.1.1 build cancelled",
    "FSR 4.1.1 не собран": "FSR 4.1.1 was not built",
    "DLL не подходит: подробности в журнале": "The DLL does not fit: details in the log",
    "Не хватает программ для сборки: список в журнале": "Tools for the build are missing: the list is in the log",
    "Записанные проходы не совпали с тем, что повторяет bbport (другая версия DLL или новая видеокарта?): подробности в журнале":
        "The recorded passes do not match what bbport replays (another DLL version, or a new GPU?): details in the log",
    "Не найден загрузчик FidelityFX 2.x": "No FidelityFX loader 2.x found",
    "Не найден подходящий Proton: установите GE-Proton 10 или новее (ProtonUp-Qt) или Proton Experimental / Proton-CachyOS в Steam. Если они есть — запустите в Steam любую игру с этим Proton, чтобы Steam поставил его рантайм":
        "No suitable Proton found: install GE-Proton 10 or newer (ProtonUp-Qt), or Proton Experimental / Proton-CachyOS in Steam. If you have them, start any game with that Proton in Steam so that Steam installs its runtime",
    "Ни один Proton не запустил FSR 4.1 из этой DLL. Либо они слишком старые (подходят GE-Proton 10+, Proton Experimental, Proton-CachyOS 11), либо DLL не включает FSR 4.1 на этой видеокарте (Steam Deck?): тогда соберите на ПК с Radeon RX 7000/9000 и скопируйте папку fsr4_411. Подробности в журнале":
        "No Proton started this DLL's FSR 4.1. Either they are too old (GE-Proton 10+, Proton Experimental, Proton-CachyOS 11 work), or the DLL does not enable FSR 4.1 on this GPU (Steam Deck?): then build on a PC with a Radeon RX 7000/9000 and copy the fsr4_411 folder. Details in the log",
    "На NixOS запись идёт на самой системе (systemd --user) через umu-launcher из nix-shell, а здесь их не нашлось: установите umu-launcher или Nix. Подробности в журнале":
        "On NixOS the recording runs on the system itself (systemd --user) with umu-launcher from nix-shell, and neither was found: install umu-launcher or Nix. Details in the log",
    "{}: FSR {}. Это официальная FSR 4.0.x от AMD: она включается только на видеокартах RDNA4 (RX 9000), а под Proton на других видеокартах не запускается, поэтому записать её нельзя.\n\nНужна FSR 4.1.x: например, FSR4_LATEST из OptiScaler или DLL из игры с FSR 4.1.":
        "{}: FSR {}. This is AMD's official FSR 4.0.x: it is enabled on RDNA4 GPUs (RX 9000) only and does not start under Proton on other GPUs, so it cannot be recorded.\n\nFSR 4.1.x is needed: for example FSR4_LATEST from OptiScaler, or the DLL of a game with FSR 4.1.",
    "{}: в этой DLL нет FSR 4. Нужна amd_fidelityfx_upscaler_dx12.dll версии 4.1.x.":
        "{}: this DLL has no FSR 4 inside. amd_fidelityfx_upscaler_dx12.dll version 4.1.x is needed.",
    "Это не загрузчик":
        "This is not the loader",
    "{} — это DLL апскейлера. Загрузчик называется amd_fidelityfx_loader_dx12.dll (у OptiScaler — amd_fidelityfx_dx12.dll) и лежит в той же папке игры, что и DLL апскейлера.":
        "{} is the upscaler DLL. The loader is called amd_fidelityfx_loader_dx12.dll (amd_fidelityfx_dx12.dll in OptiScaler) and lies in the same game folder as the upscaler DLL.",
    "{}: версия {}. Нужен загрузчик FidelityFX 2.x — из той же игры, что и DLL апскейлера.":
        "{}: version {}. A FidelityFX loader 2.x is needed, from the same game as the upscaler DLL.",
    "Рядом с DLL нет загрузчика: выберите amd_fidelityfx_loader_dx12.dll из папки игры":
        "No loader next to the DLL: choose amd_fidelityfx_loader_dx12.dll from the game's folder",
    "Собрать FSR 4.1.1 из amd_fidelityfx_upscaler_dx12.dll 4.1.x (OptiScaler: папка FSR4_LATEST, или из игры с FSR 4.1). Нужен GE-Proton 10+, Proton Experimental или Proton-CachyOS; 2–5 минут (RDNA4: вдвое дольше, ещё и вариант FP8)":
        "Build FSR 4.1.1 from amd_fidelityfx_upscaler_dx12.dll 4.1.x (OptiScaler: the FSR4_LATEST folder, or from a game with FSR 4.1). Needs GE-Proton 10+, Proton Experimental or Proton-CachyOS; 2–5 minutes (RDNA4: twice as long, with the FP8 variant)",
    "Сборка не удалась (код {}): подробности в журнале": "The build failed (code {}): details in the log",
    "Сглаживание в разрешении вывода без модели FSR": "Anti-aliasing at the output resolution, no FSR model",
    "DLSS найден (нужна видеокарта NVIDIA RTX)": "DLSS found (needs an NVIDIA RTX GPU)",
    # Online page (from the Linux co-op fork)
    "Эта сборка без модуля онлайна (libbbnet.so): игра только офлайн": "This build has no online module (libbbnet.so): offline play only",
    'Online ID — это имя учётной записи (NPID), зарегистрированное на сервере, а не адрес email': 'The Online ID is the account name (NPID) you registered on the server, not your email address',
    'UPnP (открыть порт на роутере автоматически)': 'UPnP (open a port on the router automatically)',
    'Выключено: игра остаётся офлайн, как раньше': 'Off: the game stays offline, as before',
    'Выключите при Tailscale или другом VPN': 'Turn it off with Tailscale or another VPN',
    'Играть онлайн': 'Play online',
    'Играть офлайн': 'Play offline',
    'Игровой сервер': 'Game server',
    'Игровой сервер (сообщения, пятна крови, призраки)': 'Game server (messages, bloodstains, ghosts)',
    'Имя учётной записи shadNet, не email. Зарегистрируйтесь на shadnet.shadps4.net или спросите владельца частного сервера. Пароль хранится на этом компьютере вместе с настройками лаунчера': 'Your shadNet account name, not your email. Register at shadnet.shadps4.net or ask the owner of a private server. The password is saved on this computer with the launcher settings',
    'Онлайн': 'Online',
    'Отмена': 'Cancel',
    'Пароль': 'Password',
    'Проверить': 'Test',
    'Проверить соединение': 'Test the connection',
    'Проверка…': 'Checking…',
    'Сервер shadNet': 'shadNet server',
    'Сервер кооператива (колокола и призывы)': 'Co-op server (bells and summons)',
    'Соединение': 'Connection',
    "Сообщения, пятна крови и призраки приходят с The Hunter's Dream; колокола и призывы идут через сервер shadNet. Игра по сети совместима с версией для Windows: нужны версия игры 1.09 и тот же сервер": "Messages, bloodstains and ghosts come from The Hunter's Dream; bells and summons go through a shadNet server. Online play works together with the Windows version: everyone needs game version 1.09 and the same server",
    'У всех в сессии должны быть одна версия игры (1.09) и один сервер. Читы меняют игру и для других игроков: выключайте их при совместной игре': 'Everyone in a session needs the same game version (1.09) and the same server. Cheats change the game for the other players too: turn them off when you play together',
    'Учётная запись': 'Account',
    'Учётная запись для игры онлайн указана, но «Играть онлайн» выключено': 'An online account is filled in, but “Play online” is off',
    'доступен': 'reachable',
    'недоступен': 'not reachable',
    "DLSS: библиотека NVIDIA": "DLSS: NVIDIA's library",
    "Выбрать файл…": "Choose a file…",
    "Убрать выбранную": "Remove the chosen one",
    "Своя: {}": "Your own: {}",
    "Из сборки: {}": "From this build: {}",
    "Нет: выберите libnvidia-ngx-dlss.so.* из DLSS SDK NVIDIA ({})": "None: choose libnvidia-ngx-dlss.so.* from NVIDIA's DLSS SDK ({})",
    "Эта сборка без моста DLSS (libbbport_dlss.so): DLSS работать не будет": "This build has no DLSS bridge (libbbport_dlss.so): DLSS will not work",
    "Библиотека DLSS NVIDIA (libnvidia-ngx-dlss.so.*)": "NVIDIA's DLSS library (libnvidia-ngx-dlss.so.*)",
    "Нужна библиотека для Linux": "A Linux library is needed",
    "{} — библиотека DLSS для Windows; на Linux NVIDIA её не загружает. Нужна libnvidia-ngx-dlss.so.<версия> из DLSS SDK NVIDIA: {}":
        "{} is the Windows DLSS library; NVIDIA's Linux driver does not load it. libnvidia-ngx-dlss.so.<version> from NVIDIA's DLSS SDK is needed: {}",
    "Не удалось прочитать файл": "Could not read the file",
    "Это не библиотека DLSS": "This is not the DLSS library",
    "Нужен файл libnvidia-ngx-dlss.so.<версия> из DLSS SDK NVIDIA: {}": "libnvidia-ngx-dlss.so.<version> from NVIDIA's DLSS SDK is needed: {}",
    "Не удалось скопировать библиотеку": "Could not copy the library",
    "DLSS {}: готово": "DLSS {}: ready",
    "Клавиатура и мышь": "Keyboard and mouse",
    "Камера мышью": "Mouse look",
    "Щелчок в окне игры захватывает мышь, F1 — отпускает": "A click in the game window takes the mouse, F1 releases it",
    "Чувствительность мыши": "Mouse sensitivity",
    "Инвертировать мышь по вертикали": "Invert mouse Y axis",
    "DLSS не найден: выберите библиотеку NVIDIA ниже (и нужна сборка с мостом DLSS). Игра включит FSR 3.1":
        "DLSS not found: choose NVIDIA's library below (a build with the DLSS bridge is needed too). The game will use FSR 3.1",
    "Нет или повреждён файл {}": "Missing or damaged file {}",
    # Effects
    "Эффекты игры": "Game effects",
    "Патчи игры, применяются при запуске": "Game patches, applied at start",
    "Детализация моделей": "Model detail",
    "Как в игре": "As in the game",
    "Максимальная (-2)": "Highest (-2)",
    "Ниже (1)": "Lower (1)",
    "Минимальная (2)": "Lowest (2)",
    "Хроматическая аберрация": "Chromatic aberration",
    "Глубина резкости (DoF)": "Depth of field (DoF)",
    "Размытие в движении": "Motion blur",
    "Затенение SSAO": "SSAO",
    "Собственное сглаживание игры": "The game's own anti-aliasing",
    "Тени от динамических источников": "Dynamic light shadows",
    "Отражения SSR (не было в игре)": "SSR reflections (not in the original game)",
    "Пропуск заставок при запуске": "Skip the intro videos",
    "Свободная камера (Cross + L3 / Space + Z)": "Free camera (Cross + L3 / Space + Z)",
    "Debug menu (левый touchpad / Tab; нужны шрифты)": "Debug menu (left touchpad / Tab; needs fonts)",
    "Нужна папка adhoc из мода Nexus #253 (шрифты adhoc/font) — в dvdroot_ps4 игры или модом; без неё патч не применяется":
        "Needs the adhoc folder from Nexus mod #253 (fonts in adhoc/font), in the game's dvdroot_ps4 or as a mod; without it the patch is not applied",
    # Frame rate
    "Частота кадров": "Frame rate",
    "Режим": "Mode",
    "Какой патч частоты кадров применить к игре": "Which frame rate patch to apply to the game",
    "Без ограничения (патч)": "Unlocked (patch)",
    "30 (как на PS4)": "30 (as on PS4)",
    "Ограничение FPS": "FPS limit",
    "0 — без ограничения; укажите число, чтобы ограничить FPS":
        "0: no limit; set a number to cap the frame rate",
    # Performance
    "Производительность": "Performance",
    "Двухстадийный конвейер GPU": "Two-stage GPU pipeline",
    "Быстрее на 20–30%; при нестабильности выключите": "20–30% faster; turn off if unstable",
    "Авто": "Auto",
    "Включён при 8 и более потоках процессора": "On with 8 or more CPU threads",
    "Включён": "On",
    "Стабильнее, но медленнее": "More stable, but slower",
    "Чтение данных GPU процессором": "GPU data readbacks by the CPU",
    "По умолчанию": "Default",
    "Фоновая загрузка в видеопамять": "Background pre-upload into VRAM",
    "Меньше рывков при подгрузке зон": "Fewer hitches when areas stream in",
    "Обычная": "Normal",
    "Без лишней видеопамяти": "No extra VRAM",
    "Полная": "Full",
    "Около 3 ГБ видеопамяти сверху": "About 3 GB more VRAM",
    # Mode
    "Режим работы": "Mode",
    "Новая модель памяти и трансляции": "New memory and translation model",
    "Новая: видеокарта работает с памятью игры напрямую, как в игре для ПК, а команды графики переводятся, а не эмулируются. Старая — модель памяти 0.3 со всеми исправлениями. Если драйвер не проходит проверку при запуске — старая":
        "The new one: the GPU works with the game's memory directly, as in a PC game, and graphics commands are translated rather than emulated. The old one: the memory model of 0.3 with all the fixes. If the driver fails the startup check, the old one",
    "Модель памяти и трансляции": "Memory and translation model",
    "Авто: новая на AMD, старая на других": "Auto: new on AMD, old on others",
    "Новая": "New",
    "Старая (как в 0.3)": "Old (as in 0.3)",
    "Синхронизация как в 0.3": "Synchronisation as in 0.3",
    "Для поиска регрессий: старая модель памяти и ожидания копий как в релизе 0.3":
        "For finding regressions: the old memory model and copy waits as released in 0.3",
    "Выключена": "Off",
    "Выключены": "Off",
    # Developer
    "Для разработчика": "Developer",
    "Статистика кадров в журнале": "Frame statistics in the log",
    "Сохранять журнал и статистику в файл": "Save the log and statistics to a file",
    "Диагностика вылетов": "Crash diagnostics",
    "Проверяет кучу игры и записывает записи в её память; немного медленнее":
        "Checks the game's heap and logs writes into its memory; a little slower",
    "В папку logs в каталоге данных: для разбора рывков и вылетов":
        "Into the logs folder of the data directory: to look into stutters and crashes",
    "Профиль GPU в журнале": "GPU profile in the log",
    "Слои валидации Vulkan": "Vulkan validation layers",
    "Сильно замедляет": "Much slower",
    "Доп. переменные (ИМЯ=значение через пробел)": "Extra variables (NAME=value, space-separated)",
    # Cheats page
    "Читы": "Cheats",
    "Патчи игры версии 1.09, применяются при запуске. Для обычного прохождения и игры по сети оставьте их выключенными":
        "Game patches for version 1.09, applied at start. Leave them off for a normal play-through and online play",
    "Изменения игрового процесса": "Gameplay tweaks",
    "Бессмертие": "Never die",
    "Урон проходит, но здоровье не опускается ниже 1": "You take damage but never drop below 1 HP",
    "Невидимость": "Stealth",
    "Враги не видят вас и не реагируют, пока вы не атакуете": "Enemies do not see or react to you until you attack",
    "Бесшумность": "Silent footsteps",
    "Враги не слышат вас, но видят": "Enemies do not hear you but can still see you",
    "Rally не угасает": "Rally never fades",
    "Здоровье для Rally не исчезает со временем": "Health you can regain with Rally does not fade over time",
    "Управление врагом": "Enemy control",
    "R3: управлять целью, L3: вернуться. Не вместе со свободной камерой":
        "R3: control the targeted enemy, L3: back. Not together with the free camera",
    "Без Rally": "No Rally",
    "Атаки не возвращают здоровье": "Attacks do not regain health",
    "Камера дальше": "Camera further away",
    "Камера дальше от персонажа": "The camera stays further from the character",
    "Без автоповорота камеры": "No camera auto-rotation",
    "Камера не поворачивается сама при движении; ручное управление и захват цели работают":
        "The camera does not turn by itself when you move; manual camera and lock-on still work",
    "Бег с меньшим наклоном стика": "Easier running",
    "Бег примерно с 70% наклона стика вместо 90%": "Run from about 70% stick tilt instead of 90%",
    "Физика тел как в Dark Souls": "Dark Souls ragdoll physics",
    "Тела и предметы разлетаются от ударов": "Corpses and objects fly around when hit",
    # Add to Steam
    "Добавить в Steam": "Add to Steam",
    "Игра в библиотеке Steam запускается сразу, с настройками этого лаунчера": "From the Steam library the game starts straight away, with this launcher's settings",
    "Добавить": "Add",
    "Steam не найден (или в него ещё никто не входил)": "Steam was not found (or nobody has signed in to it yet)",
    "Закройте Steam и нажмите «Добавить» ещё раз": "Close Steam and press Add again",
    "Пока игра добавляется, Steam нужно закрыть; потом он запустится снова. Закрыть Steam?": "Steam has to close while the game is added; it starts again afterwards. Close Steam?",
    "Отмена": "Cancel",
    "Закрыть Steam": "Close Steam",
    "Steam не закрылся. Закройте его сами и попробуйте ещё раз": "Steam did not close. Close it yourself and try again",
    "Не удалось добавить игру в Steam: {}": "Could not add the game to Steam: {}",
    "Bloodborne добавлен в библиотеку Steam": "Bloodborne was added to your Steam library",
    # Online page
    "Онлайн": "Online",
    "Сообщения, пятна крови и призраки приходят с The Hunter's Dream; колокола и призывы идут через сервер shadNet. Игра по сети совместима с версией для Windows: нужны версия игры 1.09 и тот же сервер": "Messages, bloodstains and ghosts come from The Hunter's Dream; bells and summons go through a shadNet server. Online play works together with the Windows version: everyone needs game version 1.09 and the same server",
    "Играть онлайн": "Play online",
    "Выключено: игра остаётся офлайн, как раньше": "Off: the game stays offline, as before",
    "Игровой сервер (сообщения, пятна крови, призраки)": "Game server (messages, bloodstains, ghosts)",
    "Игровой сервер": "Game server",
    "Сервер кооператива (колокола и призывы)": "Co-op server (bells and summons)",
    "Учётная запись": "Account",
    "Имя учётной записи shadNet, не email. Зарегистрируйтесь на shadnet.shadps4.net или спросите владельца частного сервера. Пароль хранится на этом компьютере вместе с настройками лаунчера": "Your shadNet account name, not your email. Register at shadnet.shadps4.net or ask the owner of a private server. The password is saved on this computer with the launcher settings",
    "Пароль": "Password",
    "Соединение": "Connection",
    "У всех в сессии должны быть одна версия игры (1.09) и один сервер. Читы меняют игру и для других игроков: выключайте их при совместной игре": "Everyone in a session needs the same game version (1.09) and the same server. Cheats change the game for the other players too: turn them off when you play together",
    "UPnP (открыть порт на роутере автоматически)": "UPnP (open a port on the router automatically)",
    "Выключите при Tailscale или другом VPN": "Turn it off with Tailscale or another VPN",
    "Проверить соединение": "Test the connection",
    "Проверить": "Test",
    "Сервер shadNet": "shadNet server",
    "Проверка…": "Checking…",
    "доступен": "reachable",
    "недоступен": "not reachable",
    "Учётная запись для игры онлайн указана, но «Играть онлайн» выключено": "An online account is filled in, but “Play online” is off",
    "Играть офлайн": "Play offline",
    "Online ID — это имя учётной записи (NPID), зарегистрированное на сервере, а не адрес email": "The Online ID is the account name (NPID) you registered on the server, not your email address",
    # DLSS
    "Нужны видеокарта NVIDIA RTX и проприетарный драйвер; иначе используется FSR 3.1": "Needs an NVIDIA RTX graphics card and the proprietary driver; otherwise FSR 3.1 is used",
    "Нет файлов DLSS: tools/build_dlss.sh": "No DLSS files: tools/build_dlss.sh",
    # Discord
    "Статус в Discord": "Discord status",
    "«Играет в Bloodborne» в профиле Discord, онлайн или офлайн": "“Playing Bloodborne” on your Discord profile, online or offline",
    # Button prompts (scripts/menu_prompts.py)
    "Применяется при запуске игры": "Applies when the game starts",
    "Иконки кнопок": "Button prompts",
    "Поменять местами A и B": "Swap A and B",
    "Для контроллеров в стиле Nintendo: подтверждение на A, отмена на B. Применяется при запуске игры": "For Nintendo-style controllers: confirm on A, back on B. Applies when the game starts",
    "Автоматически (по контроллеру)": "Automatic (by controller)",
    "PlayStation (оригинал)": "PlayStation (original)",
    "Меню жестов без значков управления движением": "Gestures menu without motion-control icons",
    # Add to Steam with Flathub's Steam
    'Steam из Flatpak запускает игры в своей песочнице, где нет ни папки игры, ни драйверов: ярлык должен запускать игру вне её (flatpak-spawn --host). Для этого Steam нужно право org.freedesktop.Flatpak, с которым он может запускать программы в вашей системе. Выдать его?':
        'Flatpak Steam runs games inside its sandbox, which has neither the game folder nor the drivers: the shortcut has to start the game outside it (flatpak-spawn --host). For that, Steam needs the org.freedesktop.Flatpak permission, which lets it start programs on your system. Grant it?',
    'Выдать право':
        'Grant permission',
    'Не удалось выдать право Steam: {}':
        'Could not grant Steam the permission: {}',
    "Регион игры":
        "Game region",
    "Вариант текста у языков с региональными версиями: испанский Испании (Европа) или Латинской Америки (Америка)":
        "The regional text of languages that have one: Spanish from Spain (Europe) or Latin American Spanish (the Americas)",
    "Как в дампе игры":
        "As in the game dump",
    "Европа":
        "Europe",
    "Америка":
        "The Americas",
    "Включён брандмауэр: {}":
        "Firewall on: {}",
    "Для UPnP нужны ответы роутера: {}":
        "UPnP needs the router's answers: {}",
    "О программе":
        "About",
    "Версия {}":
        "Version {}",
    "Обновления":
        "Updates",
    "Проверять обновления при запуске":
        "Check for updates at start",
    "Спрашивает GitHub о последнем выпуске; ничего не скачивается без вашего согласия":
        "Asks GitHub for the latest release; nothing is downloaded without your say",
    "Последняя версия":
        "Latest version",
    "Загрузка…":
        "Downloading…",
    "Обновить":
        "Update",
    "Версия {} установлена: перезапустите лаунчер":
        "Version {} installed: restart the launcher",
    "Перезапустить":
        "Restart",
    "Не удалось проверить: {}":
        "Could not check: {}",
    "Установлена версия {}":
        "Version {} installed",
    "Установлена последняя версия ({})":
        "You have the latest version ({})",
    "Доступна версия {} (установлена {})":
        "Version {} is out (you have {})",
    "Открыть страницу":
        "Open the page",
    "Доступна версия {}":
        "Version {} is out",
    "Подробнее":
        "Details",
    "Загрузка… {} %":
        "Downloading… {} %",
    "Загрузка… {} МБ":
        "Downloading… {} MB",
    "Не удалось обновить: {}":
        "Could not update: {}",
    "Сначала закройте игру":
        "Close the game first",
    "Этот проект":
        "This project",
    "Основано на bbport от deadinside28":
        "Based on bbport by deadinside28",
    "Порт для Windows от Supermedo":
        "Windows port by Supermedo",
    "Лицензия":
        "License",
    'GNU GPL v2 или новее · Файлы игры не входят.': 'GNU GPL v2 or later · No game files included.',
    'Bloodborne принадлежит Sony Interactive Entertainment и FromSoftware.': 'Bloodborne belongs to Sony Interactive Entertainment and FromSoftware.',
    "Проверить сейчас":
        "Check now",
    # Online page: your own shadNet server, the co-op port, seamless co-op, the UDP test
    '0: случайный при каждом запуске. Закрепите его, чтобы открыть в брандмауэре или на роутере вручную':
        '0: a random port each time. Pin it to open it in a firewall or on the router by hand',
    'UDP сервера shadNet (призывы)':
        "shadNet server's UDP (summons)",
    'UPnP открывает порт только на роутере; брандмауэр этого компьютера всё равно блокирует кооператив. Откройте порт: {}':
        "UPnP opens the port on the router only; this computer's firewall still blocks co-op. Open the port: {}",
    'Адрес WebAPI (пусто: порт 31315 сервера)':
        "WebAPI address (empty: the server's port 31315)",
    'Адрес сервера (host:port)':
        'Server address (host:port)',
    'Бесшовный кооператив (экспериментально)':
        'Seamless co-op (experimental)',
    'Закрепите порт кооператива выше (например, {}): случайный порт в брандмауэре не открыть':
        'Pin the co-op port above (for example {}): a random port cannot be opened in a firewall',
    'Как запустить свой сервер':
        'How to host your own server',
    'Порт кооператива (UDP)':
        'Co-op port (UDP)',
    'Призывы между разными локациями. Только если на сервере BloodborneSeamlessCoop=true, и у всех игроков так же':
        'Summons between different areas. Only when the server has BloodborneSeamlessCoop=true, and every player turns it on too',
    'Публичный сервер shadPS4':
        "shadPS4's public server",
    'Свой сервер':
        'Your own server',
    'shadnet-p2p: на вашем ПК или VPS':
        'shadnet-p2p: on your PC or a VPS',
    'Сервер shadNet':
        'shadNet server',
    'не отвечает: призывы не соединятся':
        'no answer: summons will not connect',
    'отвечает; ваш публичный адрес: {}':
        'answers; your public address: {}',
    "Поддержать проект": 'Support this project',
    # Trophies page
    'В дампе игры нет трофеев (sce_sys/trophy)':
        'The game dump has no trophies (sce_sys/trophy)',
    'Записываются, когда игра их открывает, и показываются в игре':
        'Recorded when the game unlocks them, and shown in the game',
    'Ключ трофеев':
        'Trophy key',
    'Ключ трофеев PS4 (TrophyKey в shadPS4), 32 шестнадцатеричных символа: с ним названия и описания на языке игры. Хранится на этом компьютере. Без него они на английском':
        "The PS4's trophy key (TrophyKey in shadPS4), 32 hexadecimal digits: with it, the names and descriptions are in the game's language. Kept on this computer. Without it, they are in English",
    'Неверный ключ трофеев: названия недоступны':
        'Wrong trophy key: the names are unavailable',
    'Получен {}':
        'Earned {}',
    'Получено {} из {}':
        '{} of {} earned',
    'Скрытый трофей':
        'Hidden trophy',
    'Трофеи':
        'Trophies',
    'Платиновый':
        'Platinum',
    'Золотой':
        'Gold',
    'Серебряный':
        'Silver',
    'Бронзовый':
        'Bronze',
    "Вход в shadNet": "shadNet sign-in",
    "неверное имя или пароль": "wrong name or password",
    "такой учётной записи нет на этом сервере": "no such account on this server",
    "эта учётная запись уже в сети (игра запущена?)": "this account is already signed in (is the game running?)",
    "вход выполнен": "signed in",
    "вход не удался ({})": "sign-in failed ({})",
    "Загрузки и плавность": "Loading and smoothness",
    "Патчи игры из bbhost, применяются при запуске": "Game patches from bbhost, applied at start",
    "Быстрая загрузка после смерти": "Quick loading after death",
    "Загрузка после смерти или перемещения у лампы идёт, пока грузится область (2–3 с), а не минимум 12 с": "A load after a death or lamp travel lasts while the area loads (2–3 s), not a 12-second minimum",
    "Без рывка каждые ~50 с": "No stutter every ~50 s",
    "Игра быстрее сжимает запись игрока: пропадает рывок ~23 мс примерно каждые 50 с": "The game compresses the player's recording faster: a ~23 ms stutter about every 50 s goes away",
    "Третий поток подготовки ресурсов": "Third resource preparation thread",
    "Во время игры работают три потока подготовки ресурсов, а не два. Экспериментально": "During play three resource preparation threads run, not two. Experimental",
    # About: Thanks
    'Благодарности': 'Thanks',
    'Без них ничего этого не было бы': 'None of this would be possible without them',
    'Порт и его код': 'The port and its code',
    'Помощь и тесты': 'Help and testing',
    'Другие благодарности': 'Also thanks to',
    'bbport — порт, на котором построен весь этот проект': 'bbport, the port this whole project is built on',
    'Игра по сети, DLSS, страница читов, добавление в Steam, значок и пропуск конвейеров, которые драйвер не может создать': 'Online play, DLSS, the cheats page, Add to Steam, the icon and skipping pipelines the driver cannot create',
    'Собрал и адаптировал десятки исправлений: вылеты при загрузке, чёрные изображения, апскейлер, строка производительности в журнале': 'Gathered and adapted dozens of fixes: crashes while loading, black images, the upscaler, the performance line in the log',
    'Чёрный предпросмотр персонажа, картинка экрана загрузки и память кэша текстур': "The black character preview, the loading screen's picture and the texture cache's memory",
    'Кэш текстур вовремя освобождает видеопамять': 'The texture cache frees video memory in time',
    'Вылеты при загрузке областей': 'Crashes while loading areas',
    'Интерфейс, пропадавший не в 1080p, векторы движения больших чудовищ и ошибка памяти': 'The interface vanishing outside 1080p, motion vectors for the large beasts and a memory fault',
    'Вылеты при загрузке некоторых карт и меню жестов с клавиатуры': 'Crashes when loading some maps and the gestures menu from the keyboard',
    'Экранная клавиатура для имени персонажа и уведомление о компиляции шейдеров': "The on-screen keyboard for the character's name and the shader compiling notice",
    "Быстрая загрузка после смерти и перемещения (bbhost) и сервер The Hunter's Dream": "Fast loading after a death or travel (bbhost) and The Hunter's Dream server",
    'Сетевые библиотеки игры по сети и сервер для своего кооператива': 'The online play libraries and the server for your own co-op',
    'Основа поддержки DLSS и модель FSR 4 без шлейфов за персонажами': 'The groundwork for DLSS, and the FSR 4 model without trails behind characters',
    'Апскейлер FSR 3.1': 'The FSR 3.1 upscaler',
    'Игра запускается, когда DLSS нельзя использовать': 'The game starts when DLSS cannot be used',
    'Перевод на упрощённый китайский': 'The Simplified Chinese translation',
    'Звук игры на полной громкости': "The game's audio at full level",
    'Флажки и ползунки внутриигрового меню': "The in-game menu's checkboxes and sliders",
    'Подробные отчёты с журналами и проверка исправлений': 'Detailed reports with logs, and testing the fixes',
    'Идея поменять местами A и B на контроллерах в стиле Nintendo': 'The idea of swapping A and B on Nintendo-style controllers',
    'Проверка исправления видеопамяти': 'Testing the video memory fix',
    'Иконки кнопок Xbox и Switch (Nexus Mods)': 'Xbox and Switch button prompts (Nexus Mods)',
    'Показал, какие текстуры нужны иконкам клавиатуры (Nexus Mods)': 'Showed which textures keyboard prompts need (Nexus Mods)',
    'Патчи игры: высокий FPS, разрешение и другое': 'Game patches: high frame rates, resolution and more',
    'Рендерер и компилятор шейдеров': 'The renderer and shader recompiler',
    'Инструмент для сборки AppImage': 'The tool that builds the AppImage',
    'Нашёл ошибку, из-за которой игра не запускалась на некоторых видеокартах': 'Found the bug that kept the game from starting on some graphics cards',
    # Shader cache
    'Кэш шейдеров': 'Shader cache',
    'Очистить': 'Clear',
    '{}. Если после обновления картинка выглядит странно, очистите его: шейдеры соберутся заново (первые минуты в каждой зоне возможны рывки)': '{}. If the picture looks wrong after an update, clear it: the shaders are built again (some stutter in each area for the first minutes)',
    'Пусто: шейдеры соберутся при игре': 'Empty: the shaders are built as you play',
    'Очистить кэш шейдеров?': 'Clear the shader cache?',
    'Игра соберёт шейдеры заново: первые минуты в каждой зоне возможны рывки. Сохранения и настройки не затрагиваются.': 'The game builds the shaders again: some stutter in each area for the first minutes. Saves and settings are not touched.',
    'Названия трофеев на английском без ключа и звук при получении трофея': 'Trophy names in English without the key, and the sound when one is earned',
    'Буфер трафарета, в который писали цветные изображения': 'The stencil buffer that colour images were writing into',
    'Вход на публичный сервер shadNet без отключения': 'Staying signed in on the public shadNet server',
    'Игра по сети': 'Online play',
    'Сервер shadNet не принимает bbport, игра осталась офлайн. Для игры по сети используйте свой сервер (страница «Онлайн»).': 'The shadNet server does not accept bbport, so the game stayed offline. For online play, use your own server (Online page).',
    'Выход из игры из меню с контроллера и меню в пределах экрана': 'Quitting from the menu with a controller, and the menu kept within the screen',
    'Вылет видеоплеера при его остановке': 'A video player crash when it stops',
    'Язык внутриигрового меню при запуске без окна лаунчера': "The in-game menu's language when starting without the launcher window",
    'DLSS в AppImage на NVIDIA': 'DLSS in the AppImage on NVIDIA',
    'Сверхширокие мониторы без растянутой картинки': 'Ultrawide monitors without a stretched picture',
}

PT_BR = {
    "Папка DLC": "Pasta de DLC",
    "Выбрать папку DLC": "Escolher a pasta de DLC",
    "Не использовать DLC": "Não usar DLC",
    "Найдено DLC: {}": "DLC encontradas: {}",
    "Не используется": "Não usada",
    "Нет DLC этой игры в папке": "Nenhuma DLC deste jogo na pasta",
    # Window, pages, buttons
    "Запустить": "Jogar",
    "Остановить": "Parar",
    "Настройки": "Configurações",
    "Журнал": "Log",
    "Не удалось запустить: {}": "Não foi possível iniciar: {}",
    "Копировать": "Copiar",
    "Экспорт журнала…": "Exportar log…",
    "Экспорт журнала": "Exportar log",
    "Журнал скопирован": "Log copiado",
    "Журнал сохранён: {}": "Log salvo: {}",
    "Не удалось сохранить журнал: {}": "Não foi possível salvar o log: {}",
    "\n— игра завершилась (код {}) —\n": "\n— o jogo foi encerrado (código {}) —\n",
    # Launcher language
    "Язык лаунчера": "Idioma do launcher",
    "Как в системе": "Sistema",
    "Применится после перезапуска лаунчера, пока игра запущена":
        "Será aplicado após reiniciar o launcher enquanto o jogo estiver em execução",
    # Game
    "Игра": "Jogo",
    "Папка игры ({})": "Pasta do jogo ({})",
    "Папка игры": "Pasta do jogo",
    "Выбрать папку с eboot.bin": "Selecionar a pasta com eboot.bin",
    "Открыть в файловом менеджере": "Abrir no gerenciador de arquivos",
    "Папка сохранений": "Pasta de salvamentos",
    "Выбрать папку сохранений": "Selecionar a pasta de salvamentos",
    "Вернуть папку по умолчанию": "Restaurar a pasta padrão",
    "Язык системы": "Idioma do sistema",
    "По умолчанию: {}": "Padrão: {}",
    "Найдены сохранения": "Salvamentos encontrados",
    "Сохранений пока нет: игра создаст их здесь": "Ainda não há salvamentos: o jogo os criará aqui",
    "не выбрана": "não selecionada",
    "Найден eboot.bin": "eboot.bin encontrado",
    "Нет eboot.bin в папке": "Não há eboot.bin na pasta",
    "Папка игры (с eboot.bin)": "Pasta do jogo (com eboot.bin)",
    # Languages
    "Английский": "Inglês",
    "Русский": "Russo",
    "Японский": "Japonês",
    "Французский": "Francês",
    "Испанский": "Espanhol",
    "Немецкий": "Alemão",
    "Итальянский": "Italiano",
    "English": "Inglês",
    # Mods
    "Моды": "Mods",
    "Распакуйте каждый мод в отдельную папку (с dvdroot_ps4 или сразу с chr/, parts/ и т. п.). "
    "При совпадении файлов побеждает мод ниже в списке. Применяется при запуске.":
        "Extraia cada mod para sua própria pasta (com dvdroot_ps4 ou diretamente com chr/, parts/, ...). "
        "Em caso de conflito de arquivos, o mod que estiver mais abaixo na lista terá prioridade. "
        "Aplicado ao iniciar.",
    "Загружать моды": "Carregar mods",
    "Папка модов": "Pasta de mods",
    "Выбрать папку модов": "Selecionar a pasta de mods",
    "Открыть папку модов": "Abrir a pasta de mods",
    "Обновить список": "Atualizar a lista",
    "Загрузить раньше": "Carregar antes",
    "Загрузить позже": "Carregar depois",
    "Модов нет": "Nenhum mod",
    # Patches
    "Сторонние патчи": "Patches de terceiros",
    "XML-патчи в формате shadPS4 для версии 01.09 из папки патчей. Применяются при запуске.":
        "Patches XML no formato do shadPS4 para a versão 01.09, carregados da pasta de patches. "
        "Aplicados ao iniciar.",
    "Папка патчей": "Pasta de patches",
    "Выбрать папку патчей": "Selecionar a pasta de patches",
    "Открыть папку патчей": "Abrir a pasta de patches",
    "Патчей нет": "Nenhum patch",
    "Автор: {}": "Autor: {}",
    # Screen
    "Экран": "Tela",
    "Разрешение вывода": "Resolução de saída",
    "Апскейлер дорисовывает кадр; Steam Deck — 720p": "O upscaler preenche o quadro; Steam Deck: 720p",
    "Полноэкранный режим": "Tela cheia",
    "Смена разрешения на лету": "Alteração de resolução em tempo real",
    "Без перезапуска, но медленнее на Steam Deck и старых GPU":
        "Não exige reinicialização, mas é mais lento no Steam Deck e em GPUs mais antigas",
    "Авто (по видеокарте)": "Automático (pela GPU)",
    "Выключена (быстрее)": "Desativado (mais rápido)",
    "Включена": "Ativado",
    "Режим показа кадров": "Modo de apresentação",
    "Разрешить HDR": "Permitir HDR",
    # Upscaler
    "Апскейлер": "Upscaler",
    "Хранится в bbport.ini; в игре меняется через меню (Insert или L3+R3)":
        "Armazenado em bbport.ini; no jogo, altere pelo menu (Insert ou L3+R3)",
    "TAA (нативное сглаживание)": "TAA (antisserrilhamento nativo)",
    "Выключен": "Desativado",
    "Пресет": "Predefinição",
    "Резкость (RCAS)": "Nitidez (RCAS)",
    "Сила резкости": "Intensidade da nitidez",
    "Векторы движения объектов": "Vetores de movimento dos objetos",
    "Меньше гостинга на персонажах; стоит около 10% FPS": "Menos ghosting nos personagens; custa cerca de 10% de FPS",
    "Показывать FPS": "Mostrar FPS",
    "Ассеты найдены": "Recursos encontrados",
    "Нет ассетов: tools/fetch_fsr4_assets.sh": "Recursos ausentes: tools/fetch_fsr4_assets.sh",
    "Ассеты для выбранного режима найдены": "Recursos encontrados para o modo selecionado",
    "{}. Соберите FSR 4.1.1 из своей DLL кнопкой «Выбрать DLL…» ниже":
        "{}. Gere o FSR 4.1.1 a partir da sua própria DLL com o botão “Escolher DLL…” abaixo",
    "FSR 4.1.1 из своей DLL AMD": "FSR 4.1.1 da sua própria DLL da AMD",
    "Отменить": "Cancelar",
    "Выбрать DLL…": "Escolher DLL…",
    "DLL апскейлера AMD (amd_fidelityfx_upscaler_dx12.dll)": "DLL do upscaler da AMD (amd_fidelityfx_upscaler_dx12.dll)",
    "нет": "nenhum",
    "Эта DLL не подходит": "Esta DLL não serve",
    "{}: версия {}, модели FSR 4: {}.\n\nbbport повторяет только официальную FSR 4.1.x от AMD (модель v07_fp8_no_scale): например, FSR4_LATEST из OptiScaler или amd_fidelityfx_upscaler_dx12.dll из игры с FSR 4.1. Сборки сообщества (4.0.2b и подобные) устроены иначе и пока не поддерживаются.":
        "{}: versão {}, modelos do FSR 4: {}.\n\nO bbport reproduz apenas o FSR 4.1.x oficial da AMD (modelo v07_fp8_no_scale): por exemplo, o FSR4_LATEST do OptiScaler ou a amd_fidelityfx_upscaler_dx12.dll de um jogo com FSR 4.1. Builds da comunidade (4.0.2b e similares) têm outra estrutura e ainda não são suportados.",
    "Загрузчик не подходит": "O carregador não serve",
    "Загрузчик FidelityFX (amd_fidelityfx_loader_dx12.dll или amd_fidelityfx_dx12.dll)":
        "Carregador do FidelityFX (amd_fidelityfx_loader_dx12.dll ou amd_fidelityfx_dx12.dll)",
    "\n— сборка FSR 4.1.1 из {} —\n": "\n— gerando o FSR 4.1.1 a partir de {} —\n",
    "Подготовка…": "Preparando…",
    "Запись проходов DLL под Proton: {} из {}": "Gravando as passagens da DLL no Proton: {} de {}",
    "Перевод проходов в SPIR-V…": "Traduzindo as passagens para SPIR-V…",
    "— сборка FSR 4.1.1 завершилась (код {}) —\n": "— geração do FSR 4.1.1 concluída (código {}) —\n",
    "FSR 4.1.1 собран и выбран": "FSR 4.1.1 gerado e selecionado",
    "Сборка FSR 4.1.1 отменена": "Geração do FSR 4.1.1 cancelada",
    "FSR 4.1.1 не собран": "O FSR 4.1.1 não foi gerado",
    "DLL не подходит: подробности в журнале": "A DLL não serve: detalhes no log",
    "Не хватает программ для сборки: список в журнале": "Faltam programas para a geração: a lista está no log",
    "Записанные проходы не совпали с тем, что повторяет bbport (другая версия DLL или новая видеокарта?): подробности в журнале":
        "As passagens gravadas não batem com o que o bbport reproduz (outra versão da DLL ou GPU nova?): detalhes no log",
    "Не найден загрузчик FidelityFX 2.x": "Carregador do FidelityFX 2.x não encontrado",
    "Не найден подходящий Proton: установите GE-Proton 10 или новее (ProtonUp-Qt) или Proton Experimental / Proton-CachyOS в Steam. Если они есть — запустите в Steam любую игру с этим Proton, чтобы Steam поставил его рантайм":
        "Nenhum Proton adequado encontrado: instale o GE-Proton 10 ou mais novo (ProtonUp-Qt), ou o Proton Experimental / Proton-CachyOS na Steam. Se já os tiver, abra qualquer jogo com esse Proton na Steam para que a Steam instale o runtime dele",
    "Ни один Proton не запустил FSR 4.1 из этой DLL. Либо они слишком старые (подходят GE-Proton 10+, Proton Experimental, Proton-CachyOS 11), либо DLL не включает FSR 4.1 на этой видеокарте (Steam Deck?): тогда соберите на ПК с Radeon RX 7000/9000 и скопируйте папку fsr4_411. Подробности в журнале":
        "Nenhum Proton iniciou o FSR 4.1 desta DLL. Ou eles são antigos demais (funcionam GE-Proton 10+, Proton Experimental, Proton-CachyOS 11), ou a DLL não ativa o FSR 4.1 nesta GPU (Steam Deck?): nesse caso, gere em um PC com Radeon RX 7000/9000 e copie a pasta fsr4_411. Detalhes no log",
    "На NixOS запись идёт на самой системе (systemd --user) через umu-launcher из nix-shell, а здесь их не нашлось: установите umu-launcher или Nix. Подробности в журнале":
        "No NixOS a gravação roda no próprio sistema (systemd --user) com o umu-launcher do nix-shell, e eles não foram encontrados: instale o umu-launcher ou o Nix. Detalhes no log",
    "{}: FSR {}. Это официальная FSR 4.0.x от AMD: она включается только на видеокартах RDNA4 (RX 9000), а под Proton на других видеокартах не запускается, поэтому записать её нельзя.\n\nНужна FSR 4.1.x: например, FSR4_LATEST из OptiScaler или DLL из игры с FSR 4.1.":
        "{}: FSR {}. Este é o FSR 4.0.x oficial da AMD: ele só é ativado em GPUs RDNA4 (RX 9000) e não inicia no Proton em outras GPUs, então não pode ser gravado.\n\nÉ preciso o FSR 4.1.x: por exemplo, o FSR4_LATEST do OptiScaler ou a DLL de um jogo com FSR 4.1.",
    "{}: в этой DLL нет FSR 4. Нужна amd_fidelityfx_upscaler_dx12.dll версии 4.1.x.":
        "{}: esta DLL não contém o FSR 4. É preciso a amd_fidelityfx_upscaler_dx12.dll versão 4.1.x.",
    "Это не загрузчик":
        "Este não é o carregador",
    "{} — это DLL апскейлера. Загрузчик называется amd_fidelityfx_loader_dx12.dll (у OptiScaler — amd_fidelityfx_dx12.dll) и лежит в той же папке игры, что и DLL апскейлера.":
        "{} é a DLL do upscaler. O carregador se chama amd_fidelityfx_loader_dx12.dll (amd_fidelityfx_dx12.dll no OptiScaler) e fica na mesma pasta do jogo que a DLL do upscaler.",
    "{}: версия {}. Нужен загрузчик FidelityFX 2.x — из той же игры, что и DLL апскейлера.":
        "{}: versão {}. É preciso um carregador do FidelityFX 2.x, do mesmo jogo que a DLL do upscaler.",
    "Рядом с DLL нет загрузчика: выберите amd_fidelityfx_loader_dx12.dll из папки игры":
        "Não há carregador ao lado da DLL: escolha a amd_fidelityfx_loader_dx12.dll da pasta do jogo",
    "Собрать FSR 4.1.1 из amd_fidelityfx_upscaler_dx12.dll 4.1.x (OptiScaler: папка FSR4_LATEST, или из игры с FSR 4.1). Нужен GE-Proton 10+, Proton Experimental или Proton-CachyOS; 2–5 минут (RDNA4: вдвое дольше, ещё и вариант FP8)":
        "Gerar o FSR 4.1.1 a partir de amd_fidelityfx_upscaler_dx12.dll 4.1.x (OptiScaler: pasta FSR4_LATEST, ou de um jogo com FSR 4.1). Requer GE-Proton 10+, Proton Experimental ou Proton-CachyOS; 2–5 minutos (RDNA4: o dobro, também com a variante FP8)",
    "Сборка не удалась (код {}): подробности в журнале": "A geração falhou (código {}): detalhes no log",
    "Сглаживание в разрешении вывода без модели FSR": "Antisserrilhamento na resolução de saída, sem modelo FSR",
    "Нет или повреждён файл {}": "Arquivo {} ausente ou corrompido",
    # Presets that are English source strings in the launcher
    "Native AA": "AA nativo",
    "Quality (x1.5)": "Qualidade (x1.5)",
    "Balanced (x1.7)": "Balanceado (x1.7)",
    "Performance (x2)": "Desempenho (x2)",
    "Ultra Performance (x3)": "Desempenho extremo (x3)",
    # Effects
    "Эффекты игры": "Efeitos do jogo",
    "Патчи игры, применяются при запуске": "Patches do jogo, aplicados ao iniciar",
    "Детализация моделей": "Detalhe dos modelos",
    "Как в игре": "Como no jogo",
    "Максимальная (-2)": "Máximo (-2)",
    "Ниже (1)": "Menor (1)",
    "Минимальная (2)": "Mínimo (2)",
    "Хроматическая аберрация": "Aberração cromática",
    "Глубина резкости (DoF)": "Profundidade de campo (DoF)",
    "Размытие в движении": "Desfoque de movimento",
    "Затенение SSAO": "SSAO",
    "Собственное сглаживание игры": "Antisserrilhamento nativo do jogo",
    "Тени от динамических источников": "Sombras de luzes dinâmicas",
    "Отражения SSR (не было в игре)": "Reflexos SSR (não existiam no jogo original)",
    "Пропуск заставок при запуске": "Pular vídeos de introdução",
    "Свободная камера (Cross + L3 / Space + Z)": "Câmera livre (Cross + L3 / Space + Z)",
    "Debug menu (левый touchpad / Tab; нужны шрифты)": "Menu de depuração (touchpad esquerdo / Tab; requer fontes)",
    "Нужна папка adhoc из мода Nexus #253 (шрифты adhoc/font) — в dvdroot_ps4 игры или модом; без неё патч не применяется":
        "Requer a pasta adhoc do mod #253 do Nexus (fontes em adhoc/font), no dvdroot_ps4 do jogo ou como mod; sem ela o patch não é aplicado",
    # Frame rate
    "Частота кадров": "Taxa de quadros",
    "Режим": "Modo",
    "Какой патч частоты кадров применить к игре": "Qual patch de taxa de quadros aplicar ao jogo",
    "Без ограничения (патч)": "Sem limite (patch)",
    "30 (как на PS4)": "30 (como no PS4)",
    "Ограничение FPS": "Limite de FPS",
    "0 — по частоте экрана (не выше 120 Гц); укажите число, чтобы ограничить иначе":
        "0: taxa de atualização da tela (até 120 Hz); defina um número para usar outro limite",
    # Performance
    "Производительность": "Desempenho",
    "Двухстадийный конвейер GPU": "Pipeline de GPU em dois estágios",
    "Быстрее на 20–30%; при нестабильности выключите": "20–30% mais rápido; desative se houver instabilidade",
    "Авто (8+ потоков)": "Automático (8+ threads)",
    "Включён": "Ativado",
    "Выключен (стабильнее)": "Desativado (mais estável)",
    "Чтение данных GPU процессором": "Leitura de dados da GPU pela CPU",
    "Relaxed (по умолчанию)": "Relaxed (padrão)",
    "Выключены": "Desativado",
    # Developer
    "Для разработчика": "Desenvolvedor",
    "Режим работы": "Modo",
    "Новая модель памяти и трансляции": "Novo modelo de memória e tradução",
    "Новая: видеокарта работает с памятью игры напрямую, как в игре для ПК, а команды графики переводятся, а не эмулируются. Старая — модель памяти 0.3 со всеми исправлениями. Если драйвер не проходит проверку при запуске — старая":
        "O novo: a GPU usa a memória do jogo diretamente, como em um jogo de PC, e os comandos gráficos são traduzidos em vez de emulados. O antigo: o modelo de memória da 0.3 com todas as correções. Se o driver falhar na verificação inicial, o antigo",
    "Модель памяти и трансляции": "Modelo de memória e tradução",
    "Авто: новая на AMD, старая на других": "Automático: novo na AMD, antigo nas outras",
    "Новая": "Novo",
    "Старая (как в 0.3)": "Antigo (como na 0.3)",
    "Синхронизация как в 0.3": "Sincronização como na 0.3",
    "Для поиска регрессий: старая модель памяти и ожидания копий как в релизе 0.3":
        "Para encontrar regressões: o modelo de memória antigo e as esperas de cópias como na versão 0.3",
    "Статистика кадров в журнале": "Estatísticas de quadros no log",
    "Профиль GPU в журнале": "Perfil da GPU no log",
    "Слои валидации Vulkan": "Camadas de validação do Vulkan",
    "Сильно замедляет": "Muito mais lento",
    "Доп. переменные (ИМЯ=значение через пробел)": "Variáveis extras (NOME=valor, separadas por espaço)",
    # Cheats page
    "Читы": "Trapaças",
    "Патчи игры версии 1.09, применяются при запуске. Для обычного прохождения и игры по сети оставьте их выключенными":
        "Patches do jogo para a versão 1.09, aplicados ao iniciar. Deixe-os desligados para jogar normalmente e online",
    "Изменения игрового процесса": "Ajustes de jogabilidade",
    "Бессмертие": "Nunca morrer",
    "Урон проходит, но здоровье не опускается ниже 1": "Você leva dano, mas a vida nunca fica abaixo de 1",
    "Невидимость": "Furtividade",
    "Враги не видят вас и не реагируют, пока вы не атакуете": "Os inimigos não veem nem reagem a você até você atacar",
    "Бесшумность": "Passos silenciosos",
    "Враги не слышат вас, но видят": "Os inimigos não ouvem você, mas ainda podem vê-lo",
    "Rally не угасает": "Rally não desaparece",
    "Здоровье для Rally не исчезает со временем": "A vida recuperável com Rally não desaparece com o tempo",
    "Управление врагом": "Controlar inimigo",
    "R3: управлять целью, L3: вернуться. Не вместе со свободной камерой":
        "R3: controlar o inimigo travado, L3: voltar. Não junto com a câmera livre",
    "Без Rally": "Sem Rally",
    "Атаки не возвращают здоровье": "Ataques não recuperam vida",
    "Камера дальше": "Câmera mais distante",
    "Камера дальше от персонажа": "A câmera fica mais longe do personagem",
    "Без автоповорота камеры": "Sem rotação automática da câmera",
    "Камера не поворачивается сама при движении; ручное управление и захват цели работают":
        "A câmera não gira sozinha ao se mover; o controle manual e a trava de alvo continuam funcionando",
    "Бег с меньшим наклоном стика": "Correr com menos inclinação",
    "Бег примерно с 70% наклона стика вместо 90%": "Corre com cerca de 70% de inclinação do analógico em vez de 90%",
    "Физика тел как в Dark Souls": "Física de corpos como em Dark Souls",
    "Тела и предметы разлетаются от ударов": "Corpos e objetos voam ao serem atingidos",
    # Add to Steam
    "Добавить в Steam": "Adicionar ao Steam",
    "Игра в библиотеке Steam запускается сразу, с настройками этого лаунчера": "Na biblioteca do Steam o jogo inicia direto, com as configurações deste launcher",
    "Добавить": "Adicionar",
    "Steam не найден (или в него ещё никто не входил)": "O Steam não foi encontrado (ou ninguém entrou nele ainda)",
    "Закройте Steam и нажмите «Добавить» ещё раз": "Feche o Steam e clique em Adicionar de novo",
    "Пока игра добавляется, Steam нужно закрыть; потом он запустится снова. Закрыть Steam?": "O Steam precisa fechar enquanto o jogo é adicionado; depois ele abre de novo. Fechar o Steam?",
    "Отмена": "Cancelar",
    "Закрыть Steam": "Fechar o Steam",
    "Steam не закрылся. Закройте его сами и попробуйте ещё раз": "O Steam não fechou. Feche-o você mesmo e tente de novo",
    "Не удалось добавить игру в Steam: {}": "Não foi possível adicionar o jogo ao Steam: {}",
    "Bloodborne добавлен в библиотеку Steam": "Bloodborne foi adicionado à sua biblioteca do Steam",
    # Online page
    "Онлайн": "Online",
    "Сообщения, пятна крови и призраки приходят с The Hunter's Dream; колокола и призывы идут через сервер shadNet. Игра по сети совместима с версией для Windows: нужны версия игры 1.09 и тот же сервер": "Mensagens, manchas de sangue e fantasmas vêm do The Hunter's Dream; sinos e invocações passam por um servidor shadNet. O jogo online funciona junto com a versão para Windows: todos precisam da versão 1.09 do jogo e do mesmo servidor",
    "Играть онлайн": "Jogar online",
    "Выключено: игра остаётся офлайн, как раньше": "Desligado: o jogo continua offline, como antes",
    "Игровой сервер (сообщения, пятна крови, призраки)": "Servidor do jogo (mensagens, manchas de sangue, fantasmas)",
    "Игровой сервер": "Servidor do jogo",
    "Сервер кооператива (колокола и призывы)": "Servidor cooperativo (sinos e invocações)",
    "Учётная запись": "Conta",
    "Имя учётной записи shadNet, не email. Зарегистрируйтесь на shadnet.shadps4.net или спросите владельца частного сервера. Пароль хранится на этом компьютере вместе с настройками лаунчера": "O nome da sua conta shadNet, não o e-mail. Registre-se em shadnet.shadps4.net ou peça ao dono de um servidor privado. A senha fica salva neste computador com as configurações do launcher",
    "Пароль": "Senha",
    "Соединение": "Conexão",
    "У всех в сессии должны быть одна версия игры (1.09) и один сервер. Читы меняют игру и для других игроков: выключайте их при совместной игре": "Todos na sessão precisam da mesma versão do jogo (1.09) e do mesmo servidor. As trapaças mudam o jogo também para os outros jogadores: desligue-as ao jogar junto",
    "UPnP (открыть порт на роутере автоматически)": "UPnP (abrir uma porta no roteador automaticamente)",
    "Выключите при Tailscale или другом VPN": "Desligue com Tailscale ou outra VPN",
    "Проверить соединение": "Testar a conexão",
    "Проверить": "Testar",
    "Сервер shadNet": "Servidor shadNet",
    "Проверка…": "Verificando…",
    "доступен": "acessível",
    "недоступен": "inacessível",
    "Учётная запись для игры онлайн указана, но «Играть онлайн» выключено": "Há uma conta online preenchida, mas “Jogar online” está desligado",
    "Играть офлайн": "Jogar offline",
    "Online ID — это имя учётной записи (NPID), зарегистрированное на сервере, а не адрес email": "O Online ID é o nome da conta (NPID) registrado no servidor, não o seu e-mail",
    # DLSS
    "Нужны видеокарта NVIDIA RTX и проприетарный драйвер; иначе используется FSR 3.1": "Requer uma placa NVIDIA RTX e o driver proprietário; caso contrário, é usado o FSR 3.1",
    "Нет файлов DLSS: tools/build_dlss.sh": "Sem arquivos do DLSS: tools/build_dlss.sh",
    # Discord
    "Статус в Discord": "Status no Discord",
    "«Играет в Bloodborne» в профиле Discord, онлайн или офлайн": "“Jogando Bloodborne” no seu perfil do Discord, online ou offline",
    # Button prompts (scripts/menu_prompts.py)
    "Клавиатура": "Teclado",
    "Применяется при запуске игры": "Aplicado ao iniciar o jogo",
    "Иконки кнопок": "Ícones dos botões",
    "Поменять местами A и B": "Trocar A e B",
    "Для контроллеров в стиле Nintendo: подтверждение на A, отмена на B. Применяется при запуске игры": "Para controles no estilo Nintendo: confirmar no A, voltar no B. Aplicado ao iniciar o jogo",
    "Автоматически (по контроллеру)": "Automático (pelo controle)",
    "PlayStation (оригинал)": "PlayStation (original)",
    "Меню жестов без значков управления движением": "Menu de gestos sem ícones de controle por movimento",
    # Add to Steam with Flathub's Steam
    'Steam из Flatpak запускает игры в своей песочнице, где нет ни папки игры, ни драйверов: ярлык должен запускать игру вне её (flatpak-spawn --host). Для этого Steam нужно право org.freedesktop.Flatpak, с которым он может запускать программы в вашей системе. Выдать его?':
        'O Steam do Flatpak roda os jogos dentro da sua sandbox, que não tem a pasta do jogo nem os drivers: o atalho precisa iniciar o jogo fora dela (flatpak-spawn --host). Para isso, o Steam precisa da permissão org.freedesktop.Flatpak, que permite iniciar programas no seu sistema. Conceder?',
    'Выдать право':
        'Conceder permissão',
    'Не удалось выдать право Steam: {}':
        'Não foi possível conceder a permissão ao Steam: {}',
    "Управление":
        "Controles",
    "Геймпад":
        "Gamepad",
    "Назначение кнопок; применяется при запуске игры":
        "Atribuição de botões; aplicada quando o jogo inicia",
    "Назначить":
        "Atribuir",
    "Сбросить":
        "Redefinir",
    "{} (по умолчанию)":
        "{} (padrão)",
    "не назначено":
        "não atribuído",
    "Нажмите клавишу или кнопку… (Esc — отмена)":
        "Pressione uma tecla ou um botão… (Esc cancela)",
    "Крест":
        "Xis",
    "Круг":
        "Círculo",
    "Квадрат":
        "Quadrado",
    "Треугольник":
        "Triângulo",
    "Тачпад, левая половина (жесты)":
        "Touchpad, metade esquerda (gestos)",
    "Тачпад, правая половина (личные вещи)":
        "Touchpad, metade direita (itens-chave)",
    "Крестовина вверх":
        "Direcional para cima",
    "Крестовина вниз":
        "Direcional para baixo",
    "Крестовина влево":
        "Direcional para a esquerda",
    "Крестовина вправо":
        "Direcional para a direita",
    "Движение вперёд":
        "Andar para frente",
    "Движение назад":
        "Andar para trás",
    "Движение влево":
        "Andar para a esquerda",
    "Движение вправо":
        "Andar para a direita",
    "Камера вверх":
        "Câmera para cima",
    "Камера вниз":
        "Câmera para baixo",
    "Камера влево":
        "Câmera para a esquerda",
    "Камера вправо":
        "Câmera para a direita",
    "Контроллер":
        "Controle",
    "Выбранный берётся, как только подключится":
        "O escolhido é usado assim que se conectar",
    "Первый подключённый":
        "O primeiro conectado",
    "{} (не подключён)":
        "{} (não conectado)",
    "Монитор":
        "Monitor",
    "Пропускать выбор «по сети / вне сети»":
        "Pular a escolha “jogar online / offline”",
    "Игра сразу открывает главное меню в режиме вне сети (патч игры)":
        "O jogo abre o menu principal offline direto (um patch do jogo)",
    "Основной":
        "Principal",
    ", основной":
        ", principal",
    "Нужно обновление 1.09: скопируйте файлы дампа обновления 1.09 в папку игры с заменой (найдена версия {})":
        "É preciso a atualização 1.09: copie o dump da atualização 1.09 para a pasta do jogo, substituindo os arquivos (versão encontrada: {})",
    "eboot.bin не от версии 1.09: скопируйте eboot.bin из дампа обновления 1.09 в папку игры с заменой":
        "O eboot.bin não é da 1.09: copie o eboot.bin do dump da atualização 1.09 para a pasta do jogo, substituindo-o",
    "eboot.bin с вшитым патчем 60 FPS от Lance McDonald: из-за него игра падает в меню жестов. Скопируйте чистый eboot.bin из дампа обновления 1.09 в папку игры с заменой":
        "Este eboot.bin já vem com o patch de 60 fps de Lance McDonald, que faz o jogo travar no menu de gestos: copie um eboot.bin limpo do dump da atualização 1.09 para a pasta do jogo, substituindo-o",
    "Это не магазинное издание Bloodborne (найдено {}): нужен Bloodborne любого региона с обновлением 1.09":
        "Não é uma edição comercial de Bloodborne (encontrado: {}): é preciso Bloodborne de qualquer região com a atualização 1.09",
    "eboot.bin не читается как расшифрованный исполняемый файл PS4: сделайте дамп заново":
        "O eboot.bin não pode ser lido como um executável de PS4 descriptografado: faça o dump do jogo de novo",
    "Файлы игры повреждены при распаковке: шейдеры не распаковываются, игра зависнет на загрузке. Распакуйте игру и обновление 1.09 заново исправленным инструментом (issue #81)":
        "Os arquivos do jogo foram danificados na extração: os shaders não descompactam e o jogo travaria ao carregar. Extraia o jogo e a atualização 1.09 de novo com uma ferramenta corrigida (issue #81)",
    "Bloodborne {}, версия 1.09":
        "Bloodborne {}, versão 1.09",
    "0 — без ограничения; укажите число, чтобы ограничить FPS":
        "0: sem limite; defina um número para limitar a taxa de quadros",
    "Авто":
        "Automático",
    "Включён при 8 и более потоках процессора":
        "Ligado com 8 ou mais threads de CPU",
    "Стабильнее, но медленнее":
        "Mais estável, porém mais lento",
    "По умолчанию":
        "Padrão",
    "Фоновая загрузка в видеопамять":
        "Pré-carregamento na VRAM em segundo plano",
    "Меньше рывков при подгрузке зон":
        "Menos travadas ao carregar as áreas",
    "Обычная":
        "Normal",
    "Без лишней видеопамяти":
        "Sem VRAM extra",
    "Полная":
        "Completo",
    "Около 3 ГБ видеопамяти сверху":
        "Cerca de 3 GB a mais de VRAM",
    "Выключена":
        "Desligado",
    "Сохранять журнал и статистику в файл":
        "Salvar o registro e as estatísticas em um arquivo",
    "Диагностика вылетов":
        "Diagnóstico de travamentos",
    "Проверяет кучу игры и записывает записи в её память; немного медленнее":
        "Verifica o heap do jogo e registra as escritas na memória dele; um pouco mais lento",
    "В папку logs в каталоге данных: для разбора рывков и вылетов":
        "Na pasta logs do diretório de dados: para investigar engasgos e travamentos",
    "Регион игры":
        "Região do jogo",
    "Вариант текста у языков с региональными версиями: испанский Испании (Европа) или Латинской Америки (Америка)":
        "A variante de texto dos idiomas que têm uma: espanhol da Espanha (Europa) ou da América Latina (Américas)",
    "Как в дампе игры":
        "Como no dump do jogo",
    "Европа":
        "Europa",
    "Америка":
        "Américas",
    "Включён брандмауэр: {}":
        "Firewall ativo: {}",
    "Для UPnP нужны ответы роутера: {}":
        "O UPnP precisa das respostas do roteador: {}",
    "О программе":
        "Sobre",
    "Версия {}":
        "Versão {}",
    "Обновления":
        "Atualizações",
    "Проверять обновления при запуске":
        "Procurar atualizações ao abrir",
    "Спрашивает GitHub о последнем выпуске; ничего не скачивается без вашего согласия":
        "Consulta o GitHub pela última versão publicada; nada é baixado sem a sua permissão",
    "Последняя версия":
        "Última versão",
    "Загрузка…":
        "Baixando…",
    "Обновить":
        "Atualizar",
    "Версия {} установлена: перезапустите лаунчер":
        "Versão {} instalada: reinicie o launcher",
    "Перезапустить":
        "Reiniciar",
    "Не удалось проверить: {}":
        "Não foi possível verificar: {}",
    "Установлена версия {}":
        "Versão {} instalada",
    "Установлена последняя версия ({})":
        "Você tem a última versão ({})",
    "Доступна версия {} (установлена {})":
        "Saiu a versão {} (você tem a {})",
    "Открыть страницу":
        "Abrir a página",
    "Доступна версия {}":
        "Saiu a versão {}",
    "Подробнее":
        "Detalhes",
    "Загрузка… {} %":
        "Baixando… {} %",
    "Загрузка… {} МБ":
        "Baixando… {} MB",
    "Не удалось обновить: {}":
        "Não foi possível atualizar: {}",
    "Сначала закройте игру":
        "Feche o jogo primeiro",
    "Этот проект":
        "Este projeto",
    "Основано на bbport от deadinside28":
        "Baseado no bbport de deadinside28",
    "Порт для Windows от Supermedo":
        "Port para Windows de Supermedo",
    "Лицензия":
        "Licença",
    'GNU GPL v2 или новее · Файлы игры не входят.': 'GNU GPL v2 ou posterior · Não inclui arquivos do jogo.',
    'Bloodborne принадлежит Sony Interactive Entertainment и FromSoftware.': 'Bloodborne pertence à Sony Interactive Entertainment e à FromSoftware.',
    "Проверить сейчас":
        "Verificar agora",
    # 0.51: mouse look, choosing NVIDIA's DLSS library, the online module
    'DLSS {}: готово':
        'DLSS {}: pronto',
    'DLSS найден (нужна видеокарта NVIDIA RTX)':
        'DLSS encontrado (requer uma GPU NVIDIA RTX)',
    'DLSS не найден: выберите библиотеку NVIDIA ниже (и нужна сборка с мостом DLSS). Игра включит FSR 3.1':
        'DLSS não encontrado: escolha a biblioteca da NVIDIA abaixo (também é preciso uma build com a ponte do DLSS). O jogo usará FSR 3.1',
    'DLSS: библиотека NVIDIA':
        'DLSS: biblioteca da NVIDIA',
    '{} — библиотека DLSS для Windows; на Linux NVIDIA её не загружает. Нужна libnvidia-ngx-dlss.so.<версия> из DLSS SDK NVIDIA: {}':
        '{} é a biblioteca do DLSS para Windows; o driver da NVIDIA para Linux não a carrega. É preciso libnvidia-ngx-dlss.so.<versão> do DLSS SDK da NVIDIA: {}',
    'Библиотека DLSS NVIDIA (libnvidia-ngx-dlss.so.*)':
        'Biblioteca DLSS da NVIDIA (libnvidia-ngx-dlss.so.*)',
    'Выбрать файл…':
        'Escolher arquivo…',
    'Из сборки: {}':
        'Desta build: {}',
    'Инвертировать мышь по вертикали':
        'Inverter o eixo Y do mouse',
    'Камера мышью':
        'Câmera com o mouse',
    'Клавиатура и мышь':
        'Teclado e mouse',
    'Не удалось прочитать файл':
        'Não foi possível ler o arquivo',
    'Не удалось скопировать библиотеку':
        'Não foi possível copiar a biblioteca',
    'Нет: выберите libnvidia-ngx-dlss.so.* из DLSS SDK NVIDIA ({})':
        'Nenhuma: escolha libnvidia-ngx-dlss.so.* do DLSS SDK da NVIDIA ({})',
    'Нужен файл libnvidia-ngx-dlss.so.<версия> из DLSS SDK NVIDIA: {}':
        'É preciso libnvidia-ngx-dlss.so.<versão> do DLSS SDK da NVIDIA: {}',
    'Нужна библиотека для Linux':
        'É preciso uma biblioteca para Linux',
    'Своя: {}':
        'A sua: {}',
    'Убрать выбранную':
        'Remover a escolhida',
    'Чувствительность мыши':
        'Sensibilidade do mouse',
    'Щелчок в окне игры захватывает мышь, F1 — отпускает':
        'Um clique na janela do jogo captura o mouse; F1 o libera',
    'Эта сборка без модуля онлайна (libbbnet.so): игра только офлайн':
        'Esta build não tem o módulo online (libbbnet.so): só é possível jogar offline',
    'Эта сборка без моста DLSS (libbbport_dlss.so): DLSS работать не будет':
        'Esta build não tem a ponte do DLSS (libbbport_dlss.so): o DLSS não vai funcionar',
    'Это не библиотека DLSS':
        'Esta não é a biblioteca do DLSS',
    # Online page: your own shadNet server, the co-op port, seamless co-op, the UDP test
    '0: случайный при каждом запуске. Закрепите его, чтобы открыть в брандмауэре или на роутере вручную':
        '0: uma aleatória a cada vez. Fixe-a para abri-la no firewall ou manualmente no roteador',
    'UDP сервера shadNet (призывы)':
        'UDP do servidor shadNet (invocações)',
    'UPnP открывает порт только на роутере; брандмауэр этого компьютера всё равно блокирует кооператив. Откройте порт: {}':
        'O UPnP só abre a porta no roteador; o firewall deste computador ainda bloqueia o cooperativo. Abra a porta: {}',
    'Адрес WebAPI (пусто: порт 31315 сервера)':
        'Endereço do WebAPI (vazio: a porta 31315 do servidor)',
    'Адрес сервера (host:port)':
        'Endereço do servidor (host:porta)',
    'Бесшовный кооператив (экспериментально)':
        'Cooperativo seamless (experimental)',
    'Закрепите порт кооператива выше (например, {}): случайный порт в брандмауэре не открыть':
        'Fixe a porta do cooperativo acima (por exemplo, {}): uma porta aleatória não pode ser aberta no firewall',
    'Как запустить свой сервер':
        'Como hospedar seu próprio servidor',
    'Порт кооператива (UDP)':
        'Porta do cooperativo (UDP)',
    'Призывы между разными локациями. Только если на сервере BloodborneSeamlessCoop=true, и у всех игроков так же':
        'Invocações entre áreas diferentes. Só se o servidor tiver BloodborneSeamlessCoop=true e todos os jogadores ativarem',
    'Публичный сервер shadPS4':
        'Servidor público do shadPS4',
    'Свой сервер':
        'Servidor próprio',
    'shadnet-p2p: на вашем ПК или VPS':
        'shadnet-p2p: no seu PC ou em um VPS',
    'Сервер shadNet':
        'Servidor shadNet',
    'не отвечает: призывы не соединятся':
        'não responde: as invocações não vão conectar',
    'отвечает; ваш публичный адрес: {}':
        'responde; seu endereço público: {}',
    "Поддержать проект": 'Apoiar este projeto',
    # Trophies page
    'В дампе игры нет трофеев (sce_sys/trophy)':
        'O dump do jogo não tem troféus (sce_sys/trophy)',
    'Записываются, когда игра их открывает, и показываются в игре':
        'Registrados quando o jogo os desbloqueia, e mostrados no jogo',
    'Ключ трофеев':
        'Chave de troféus',
    'Ключ трофеев PS4 (TrophyKey в shadPS4), 32 шестнадцатеричных символа: с ним названия и описания на языке игры. Хранится на этом компьютере. Без него они на английском':
        'A chave de troféus do PS4 (TrophyKey no shadPS4), 32 dígitos hexadecimais: com ela, os nomes e as descrições ficam no idioma do jogo. Fica neste computador. Sem ela, ficam em inglês',
    'Неверный ключ трофеев: названия недоступны':
        'Chave de troféus incorreta: os nomes não estão disponíveis',
    'Получен {}':
        'Conquistado em {}',
    'Получено {} из {}':
        '{} de {} conquistados',
    'Скрытый трофей':
        'Troféu oculto',
    'Трофеи':
        'Troféus',
    'Платиновый':
        'Platina',
    'Золотой':
        'Ouro',
    'Серебряный':
        'Prata',
    'Бронзовый':
        'Bronze',
    "Вход в shadNet": "Login no shadNet",
    "неверное имя или пароль": "nome ou senha incorretos",
    "такой учётной записи нет на этом сервере": "essa conta não existe neste servidor",
    "эта учётная запись уже в сети (игра запущена?)": "esta conta já está conectada (o jogo está aberto?)",
    "вход выполнен": "login feito",
    "вход не удался ({})": "falha no login ({})",
    "Загрузки и плавность": "Carregamento e fluidez",
    "Патчи игры из bbhost, применяются при запуске": "Patches do jogo do bbhost, aplicados ao iniciar",
    "Быстрая загрузка после смерти": "Carregamento rápido após morrer",
    "Загрузка после смерти или перемещения у лампы идёт, пока грузится область (2–3 с), а не минимум 12 с": "O carregamento após morrer ou viajar pela lanterna dura o tempo da área (2–3 s), não um mínimo de 12 s",
    "Без рывка каждые ~50 с": "Sem travada a cada ~50 s",
    "Игра быстрее сжимает запись игрока: пропадает рывок ~23 мс примерно каждые 50 с": "O jogo comprime mais rápido o registro do jogador: some uma travada de ~23 ms a cada uns 50 s",
    "Третий поток подготовки ресурсов": "Terceira thread de preparação de recursos",
    "Во время игры работают три потока подготовки ресурсов, а не два. Экспериментально": "Durante o jogo rodam três threads de preparação de recursos, não duas. Experimental",
    # About: Thanks
    'Благодарности': 'Agradecimentos',
    'Без них ничего этого не было бы': 'Sem eles, nada disto seria possível',
    'Порт и его код': 'O port e seu código',
    'Помощь и тесты': 'Ajuda e testes',
    'Другие благодарности': 'Também agradecemos a',
    'bbport — порт, на котором построен весь этот проект': 'bbport, o port em que todo este projeto se baseia',
    'Игра по сети, DLSS, страница читов, добавление в Steam, значок и пропуск конвейеров, которые драйвер не может создать': 'Jogo online, DLSS, a página de trapaças, Adicionar à Steam, o ícone e pular pipelines que o driver não consegue criar',
    'Собрал и адаптировал десятки исправлений: вылеты при загрузке, чёрные изображения, апскейлер, строка производительности в журнале': 'Reuniu e adaptou dezenas de correções: travamentos ao carregar, imagens pretas, o upscaler, a linha de desempenho no log',
    'Чёрный предпросмотр персонажа, картинка экрана загрузки и память кэша текстур': 'A prévia do personagem preta, a imagem da tela de carregamento e a memória do cache de texturas',
    'Кэш текстур вовремя освобождает видеопамять': 'O cache de texturas libera a memória de vídeo a tempo',
    'Вылеты при загрузке областей': 'Travamentos ao carregar áreas',
    'Интерфейс, пропадавший не в 1080p, векторы движения больших чудовищ и ошибка памяти': 'A interface que sumia fora de 1080p, vetores de movimento das grandes feras e uma falha de memória',
    'Вылеты при загрузке некоторых карт и меню жестов с клавиатуры': 'Travamentos ao carregar alguns mapas e o menu de gestos pelo teclado',
    'Экранная клавиатура для имени персонажа и уведомление о компиляции шейдеров': 'O teclado na tela para o nome do personagem e o aviso de compilação de shaders',
    "Быстрая загрузка после смерти и перемещения (bbhost) и сервер The Hunter's Dream": "Carregamento rápido após morrer ou viajar (bbhost) e o servidor The Hunter's Dream",
    'Сетевые библиотеки игры по сети и сервер для своего кооператива': 'As bibliotecas do jogo online e o servidor para o seu próprio cooperativo',
    'Основа поддержки DLSS и модель FSR 4 без шлейфов за персонажами': 'A base do suporte a DLSS e o modelo do FSR 4 sem rastros atrás dos personagens',
    'Апскейлер FSR 3.1': 'O upscaler FSR 3.1',
    'Игра запускается, когда DLSS нельзя использовать': 'O jogo inicia quando o DLSS não pode ser usado',
    'Перевод на упрощённый китайский': 'A tradução para chinês simplificado',
    'Звук игры на полной громкости': 'O áudio do jogo em volume total',
    'Флажки и ползунки внутриигрового меню': 'As caixas de seleção e os controles deslizantes do menu do jogo',
    'Подробные отчёты с журналами и проверка исправлений': 'Relatórios detalhados com logs e teste das correções',
    'Идея поменять местами A и B на контроллерах в стиле Nintendo': 'A ideia de trocar A e B em controles no estilo Nintendo',
    'Проверка исправления видеопамяти': 'Teste da correção de memória de vídeo',
    'Иконки кнопок Xbox и Switch (Nexus Mods)': 'Ícones de botões do Xbox e do Switch (Nexus Mods)',
    'Показал, какие текстуры нужны иконкам клавиатуры (Nexus Mods)': 'Mostrou quais texturas os ícones de teclado precisam (Nexus Mods)',
    'Патчи игры: высокий FPS, разрешение и другое': 'Patches do jogo: FPS altos, resolução e mais',
    'Рендерер и компилятор шейдеров': 'O renderizador e o recompilador de shaders',
    'Инструмент для сборки AppImage': 'A ferramenta que gera a AppImage',
    'Нашёл ошибку, из-за которой игра не запускалась на некоторых видеокартах': 'Encontrou o erro que impedia o jogo de iniciar em algumas placas de vídeo',
    # Shader cache
    'Кэш шейдеров': 'Cache de shaders',
    'Очистить': 'Limpar',
    '{}. Если после обновления картинка выглядит странно, очистите его: шейдеры соберутся заново (первые минуты в каждой зоне возможны рывки)': '{}. Se a imagem parecer estranha após uma atualização, limpe-o: os shaders são gerados de novo (pode haver travadas nos primeiros minutos de cada área)',
    'Пусто: шейдеры соберутся при игре': 'Vazio: os shaders são gerados enquanto você joga',
    'Очистить кэш шейдеров?': 'Limpar o cache de shaders?',
    'Игра соберёт шейдеры заново: первые минуты в каждой зоне возможны рывки. Сохранения и настройки не затрагиваются.': 'O jogo gera os shaders de novo: pode haver travadas nos primeiros minutos de cada área. Saves e configurações não são afetados.',
    'Названия трофеев на английском без ключа и звук при получении трофея': 'Nomes dos troféus em inglês sem a chave e o som ao conquistar um',
    'Буфер трафарета, в который писали цветные изображения': 'O buffer de estêncil em que imagens de cor escreviam',
    'Вход на публичный сервер shadNet без отключения': 'Continuar conectado no servidor público do shadNet',
    'Игра по сети': 'Jogo online',
    'Сервер shadNet не принимает bbport, игра осталась офлайн. Для игры по сети используйте свой сервер (страница «Онлайн»).': 'O servidor shadNet não aceita o bbport, então o jogo ficou offline. Para jogar online, use seu próprio servidor (página Online).',
    'Выход из игры из меню с контроллера и меню в пределах экрана': 'Sair do jogo pelo menu com o controle e o menu dentro da tela',
    'Вылет видеоплеера при его остановке': 'Um travamento do reprodutor de vídeo ao parar',
    'Язык внутриигрового меню при запуске без окна лаунчера': 'O idioma do menu do jogo ao iniciar sem a janela do launcher',
    'DLSS в AppImage на NVIDIA': 'DLSS no AppImage em NVIDIA',
    'Сверхширокие мониторы без растянутой картинки': 'Monitores ultrawide sem imagem esticada',
}


# Spanish (Spain).
ES = {
    "Папка DLC": "Carpeta de DLC",
    "Выбрать папку DLC": "Elegir la carpeta de DLC",
    "Не использовать DLC": "No usar DLC",
    "Найдено DLC: {}": "DLC encontrados: {}",
    "Не используется": "Sin usar",
    "Нет DLC этой игры в папке": "No hay DLC de este juego en la carpeta",
    "Запустить": "Jugar",
    "Остановить": "Detener",
    "Настройки": "Ajustes",
    "Журнал": "Registro",
    "Не удалось запустить: {}": "No se pudo iniciar: {}",
    "\n— игра завершилась (код {}) —\n": "\n— el juego ha terminado (código {}) —\n",
    "Язык лаунчера": "Idioma del launcher",
    "Как в системе": "Sistema",
    "Применится после перезапуска лаунчера, пока игра запущена": "Se aplica al reiniciar el launcher mientras el juego está en ejecución",
    "Игра": "Juego",
    "Папка игры ({})": "Carpeta del juego ({})",
    "Папка игры": "Carpeta del juego",
    "Выбрать папку с eboot.bin": "Elige la carpeta con eboot.bin",
    "Открыть в файловом менеджере": "Abrir en el gestor de archivos",
    "Папка сохранений": "Carpeta de partidas guardadas",
    "Выбрать папку сохранений": "Elige la carpeta de partidas guardadas",
    "Вернуть папку по умолчанию": "Volver a la carpeta predeterminada",
    "Язык системы": "Idioma del sistema",
    "По умолчанию: {}": "Predeterminado: {}",
    "Найдены сохранения": "Partidas guardadas encontradas",
    "Сохранений пока нет: игра создаст их здесь": "Aún no hay partidas guardadas: el juego las creará aquí",
    "не выбрана": "sin elegir",
    "Найден eboot.bin": "eboot.bin encontrado",
    "Нет eboot.bin в папке": "No hay eboot.bin en la carpeta",
    "Управление": "Controles",
    "Клавиатура": "Teclado",
    "Геймпад": "Mando",
    "Назначение кнопок; применяется при запуске игры": "Asignación de botones; se aplica al iniciar el juego",
    "Назначить": "Asignar",
    "Сбросить": "Restablecer",
    "{} (по умолчанию)": "{} (predeterminado)",
    "не назначено": "sin asignar",
    "Нажмите клавишу или кнопку… (Esc — отмена)": "Pulsa una tecla o un botón… (Esc cancela)",
    "Крест": "Cruz",
    "Круг": "Círculo",
    "Квадрат": "Cuadrado",
    "Треугольник": "Triángulo",
    "Тачпад, левая половина (жесты)": "Panel táctil, mitad izquierda (gestos)",
    "Тачпад, правая половина (личные вещи)": "Panel táctil, mitad derecha (objetos clave)",
    "Крестовина вверх": "Cruceta arriba",
    "Крестовина вниз": "Cruceta abajo",
    "Крестовина влево": "Cruceta izquierda",
    "Крестовина вправо": "Cruceta derecha",
    "Движение вперёд": "Avanzar",
    "Движение назад": "Retroceder",
    "Движение влево": "Moverse a la izquierda",
    "Движение вправо": "Moverse a la derecha",
    "Камера вверх": "Cámara arriba",
    "Камера вниз": "Cámara abajo",
    "Камера влево": "Cámara a la izquierda",
    "Камера вправо": "Cámara a la derecha",
    "Контроллер": "Mando",
    "Выбранный берётся, как только подключится": "Se usa el elegido en cuanto se conecta",
    "Первый подключённый": "El primero conectado",
    "{} (не подключён)": "{} (no conectado)",
    "Нужно обновление 1.09: скопируйте файлы дампа обновления 1.09 в папку игры с заменой (найдена версия {})": "Se necesita la actualización 1.09: copia la actualización 1.09 volcada en la carpeta del juego, reemplazando los archivos (versión encontrada: {})",
    "eboot.bin не от версии 1.09: скопируйте eboot.bin из дампа обновления 1.09 в папку игры с заменой": "eboot.bin no es de la 1.09: copia eboot.bin de la actualización 1.09 volcada en la carpeta del juego, reemplazándolo",
    "eboot.bin с вшитым патчем 60 FPS от Lance McDonald: из-за него игра падает в меню жестов. Скопируйте чистый eboot.bin из дампа обновления 1.09 в папку игры с заменой": "Este eboot.bin trae integrado el parche de 60 FPS de Lance McDonald, que cierra el juego al abrir el menú de gestos: copia un eboot.bin limpio de la actualización 1.09 volcada en la carpeta del juego, reemplazándolo",
    "Это не магазинное издание Bloodborne (найдено {}): нужен Bloodborne любого региона с обновлением 1.09": "No es una edición comercial de Bloodborne (encontrada: {}): hace falta Bloodborne de cualquier región con la actualización 1.09",
    "eboot.bin не читается как расшифрованный исполняемый файл PS4: сделайте дамп заново": "No se puede leer eboot.bin como ejecutable de PS4 descifrado: vuelve a volcar el juego",
    "Bloodborne {}, версия 1.09": "Bloodborne {}, versión 1.09",
    "Папка игры (с eboot.bin)": "Carpeta del juego (con eboot.bin)",
    "Английский": "Inglés",
    "Русский": "Ruso",
    "Японский": "Japonés",
    "Французский": "Francés",
    "Испанский": "Español",
    "Немецкий": "Alemán",
    "Итальянский": "Italiano",
    "Моды": "Mods",
    "Распакуйте каждый мод в отдельную папку (с dvdroot_ps4 или сразу с chr/, parts/ и т. п.). При совпадении файлов побеждает мод ниже в списке. Применяется при запуске.": "Extrae cada mod en su propia carpeta (con dvdroot_ps4, o directamente con chr/, parts/, ...). Si hay archivos en conflicto, gana el mod que esté más abajo en la lista. Se aplica al iniciar.",
    "Загружать моды": "Cargar mods",
    "Папка модов": "Carpeta de mods",
    "Выбрать папку модов": "Elige la carpeta de mods",
    "Открыть папку модов": "Abrir la carpeta de mods",
    "Обновить список": "Actualizar la lista",
    "Загрузить раньше": "Cargar antes",
    "Загрузить позже": "Cargar después",
    "Модов нет": "Ningún mod",
    "Сторонние патчи": "Parches de terceros",
    "XML-патчи в формате shadPS4 для версии 01.09 из папки патчей. Применяются при запуске.": "Parches XML en formato shadPS4 para la versión 01.09, de la carpeta de parches. Se aplican al iniciar.",
    "Папка патчей": "Carpeta de parches",
    "Выбрать папку патчей": "Elige la carpeta de parches",
    "Открыть папку патчей": "Abrir la carpeta de parches",
    "Патчей нет": "Ningún parche",
    "Автор: {}": "Autor: {}",
    "Экран": "Pantalla",
    "Разрешение вывода": "Resolución de salida",
    "Апскейлер дорисовывает кадр; Steam Deck — 720p": "El escalador rellena el fotograma; Steam Deck: 720p",
    "Полноэкранный режим": "Pantalla completa",
    "Смена разрешения на лету": "Cambio de resolución en tiempo real",
    "Без перезапуска, но медленнее на Steam Deck и старых GPU": "No requiere reinicio, pero es más lento en la Steam Deck y en GPU antiguas",
    "Авто (по видеокарте)": "Automático (según la GPU)",
    "Выключена (быстрее)": "Desactivado (más rápido)",
    "Включена": "Activado",
    "Режим показа кадров": "Modo de presentación",
    "Разрешить HDR": "Permitir HDR",
    "Апскейлер": "Escalador",
    "Хранится в bbport.ini; в игре меняется через меню (Insert или L3+R3)": "Se guarda en bbport.ini; dentro del juego, cámbialo en el menú (Insert o L3+R3)",
    "TAA (нативное сглаживание)": "TAA (antialiasing nativo)",
    "Выключен": "Desactivado",
    "Пресет": "Preajuste",
    "Резкость (RCAS)": "Nitidez (RCAS)",
    "Сила резкости": "Intensidad de nitidez",
    "Векторы движения объектов": "Vectores de movimiento de objetos",
    "Меньше гостинга на персонажах; стоит около 10% FPS": "Menos ghosting en los personajes; cuesta alrededor del 10 % de FPS",
    "Показывать FPS": "Mostrar FPS",
    "Ассеты найдены": "Recursos encontrados",
    "Нет ассетов: tools/fetch_fsr4_assets.sh": "Faltan los recursos: tools/fetch_fsr4_assets.sh",
    "Ассеты для выбранного режима найдены": "Recursos del modo seleccionado encontrados",
    "{}. Соберите FSR 4.1.1 из своей DLL кнопкой «Выбрать DLL…» ниже": "{}. Genera FSR 4.1.1 a partir de tu propia DLL con el botón «Elegir DLL…» de abajo",
    "FSR 4.1.1 из своей DLL AMD": "FSR 4.1.1 desde tu propia DLL de AMD",
    "Отменить": "Cancelar",
    "Выбрать DLL…": "Elegir DLL…",
    "DLL апскейлера AMD (amd_fidelityfx_upscaler_dx12.dll)": "DLL del escalador de AMD (amd_fidelityfx_upscaler_dx12.dll)",
    "нет": "ninguno",
    "Эта DLL не подходит": "Esta DLL no sirve",
    "{}: версия {}, модели FSR 4: {}.\n\nbbport повторяет только официальную FSR 4.1.x от AMD (модель v07_fp8_no_scale): например, FSR4_LATEST из OptiScaler или amd_fidelityfx_upscaler_dx12.dll из игры с FSR 4.1. Сборки сообщества (4.0.2b и подобные) устроены иначе и пока не поддерживаются.": "{}: versión {}, modelos de FSR 4: {}.\n\nbbport solo reproduce el FSR 4.1.x oficial de AMD (modelo v07_fp8_no_scale): por ejemplo, FSR4_LATEST de OptiScaler o amd_fidelityfx_upscaler_dx12.dll de un juego con FSR 4.1. Las compilaciones de la comunidad (4.0.2b y similares) tienen otra estructura y todavía no se admiten.",
    "Загрузчик не подходит": "El cargador no sirve",
    "Загрузчик FidelityFX (amd_fidelityfx_loader_dx12.dll или amd_fidelityfx_dx12.dll)": "Cargador de FidelityFX (amd_fidelityfx_loader_dx12.dll o amd_fidelityfx_dx12.dll)",
    "\n— сборка FSR 4.1.1 из {} —\n": "\n— generando FSR 4.1.1 a partir de {} —\n",
    "Подготовка…": "Preparando…",
    "Запись проходов DLL под Proton: {} из {}": "Grabando las pasadas de la DLL en Proton: {} de {}",
    "Перевод проходов в SPIR-V…": "Traduciendo las pasadas a SPIR-V…",
    "— сборка FSR 4.1.1 завершилась (код {}) —\n": "— Generación de FSR 4.1.1 terminada (código {}) —\n",
    "FSR 4.1.1 собран и выбран": "FSR 4.1.1 generado y seleccionado",
    "Сборка FSR 4.1.1 отменена": "Generación de FSR 4.1.1 cancelada",
    "FSR 4.1.1 не собран": "No se generó FSR 4.1.1",
    "DLL не подходит: подробности в журнале": "La DLL no sirve: detalles en el registro",
    "Не хватает программ для сборки: список в журнале": "Faltan herramientas para la generación: la lista está en el registro",
    "Записанные проходы не совпали с тем, что повторяет bbport (другая версия DLL или новая видеокарта?): подробности в журнале": "Las pasadas grabadas no coinciden con lo que reproduce bbport (¿otra versión de la DLL o una GPU nueva?): detalles en el registro",
    "Не найден загрузчик FidelityFX 2.x": "No se encontró ningún cargador de FidelityFX 2.x",
    "Не найден подходящий Proton: установите GE-Proton 10 или новее (ProtonUp-Qt) или Proton Experimental / Proton-CachyOS в Steam. Если они есть — запустите в Steam любую игру с этим Proton, чтобы Steam поставил его рантайм": "No se encontró un Proton adecuado: instala GE-Proton 10 o posterior (ProtonUp-Qt), o Proton Experimental / Proton-CachyOS en Steam. Si ya los tienes, inicia cualquier juego con ese Proton en Steam para que Steam instale su runtime",
    "Ни один Proton не запустил FSR 4.1 из этой DLL. Либо они слишком старые (подходят GE-Proton 10+, Proton Experimental, Proton-CachyOS 11), либо DLL не включает FSR 4.1 на этой видеокарте (Steam Deck?): тогда соберите на ПК с Radeon RX 7000/9000 и скопируйте папку fsr4_411. Подробности в журнале": "Ningún Proton ha podido iniciar el FSR 4.1 de esta DLL. O son demasiado antiguos (funcionan GE-Proton 10+, Proton Experimental y Proton-CachyOS 11), o la DLL no activa FSR 4.1 en esta GPU (¿Steam Deck?): en ese caso, genera en un PC con una Radeon RX 7000/9000 y copia la carpeta fsr4_411. Detalles en el registro",
    "На NixOS запись идёт на самой системе (systemd --user) через umu-launcher из nix-shell, а здесь их не нашлось: установите umu-launcher или Nix. Подробности в журнале": "En NixOS la grabación se ejecuta en el propio sistema (systemd --user) con umu-launcher de nix-shell, y no se ha encontrado ninguno de los dos: instala umu-launcher o Nix. Detalles en el registro",
    "{}: FSR {}. Это официальная FSR 4.0.x от AMD: она включается только на видеокартах RDNA4 (RX 9000), а под Proton на других видеокартах не запускается, поэтому записать её нельзя.\n\nНужна FSR 4.1.x: например, FSR4_LATEST из OptiScaler или DLL из игры с FSR 4.1.": "{}: FSR {}. Este es el FSR 4.0.x oficial de AMD: solo se activa en GPU RDNA4 (RX 9000) y no se inicia en Proton en otras GPU, por lo que no se puede grabar.\n\nHace falta FSR 4.1.x: por ejemplo, FSR4_LATEST de OptiScaler o la DLL de un juego con FSR 4.1.",
    "{}: в этой DLL нет FSR 4. Нужна amd_fidelityfx_upscaler_dx12.dll версии 4.1.x.": "{}: esta DLL no contiene FSR 4. Hace falta amd_fidelityfx_upscaler_dx12.dll versión 4.1.x.",
    "Это не загрузчик": "Este no es el cargador",
    "{} — это DLL апскейлера. Загрузчик называется amd_fidelityfx_loader_dx12.dll (у OptiScaler — amd_fidelityfx_dx12.dll) и лежит в той же папке игры, что и DLL апскейлера.": "{} es la DLL del escalador. El cargador se llama amd_fidelityfx_loader_dx12.dll (amd_fidelityfx_dx12.dll en OptiScaler) y está en la misma carpeta del juego que la DLL del escalador.",
    "{}: версия {}. Нужен загрузчик FidelityFX 2.x — из той же игры, что и DLL апскейлера.": "{}: versión {}. Hace falta un cargador de FidelityFX 2.x, del mismo juego que la DLL del escalador.",
    "Рядом с DLL нет загрузчика: выберите amd_fidelityfx_loader_dx12.dll из папки игры": "No hay cargador junto a la DLL: elige amd_fidelityfx_loader_dx12.dll de la carpeta del juego",
    "Собрать FSR 4.1.1 из amd_fidelityfx_upscaler_dx12.dll 4.1.x (OptiScaler: папка FSR4_LATEST, или из игры с FSR 4.1). Нужен GE-Proton 10+, Proton Experimental или Proton-CachyOS; 2–5 минут (RDNA4: вдвое дольше, ещё и вариант FP8)": "Genera FSR 4.1.1 a partir de amd_fidelityfx_upscaler_dx12.dll 4.1.x (OptiScaler: la carpeta FSR4_LATEST, o la de un juego con FSR 4.1). Requiere GE-Proton 10+, Proton Experimental o Proton-CachyOS; 2–5 minutos (RDNA4: el doble, con la variante FP8)",
    "Сборка не удалась (код {}): подробности в журнале": "La generación ha fallado (código {}): detalles en el registro",
    "Сглаживание в разрешении вывода без модели FSR": "Antialiasing a la resolución de salida, sin modelo FSR",
    "Нет или повреждён файл {}": "Archivo {} ausente o dañado",
    "Эффекты игры": "Efectos del juego",
    "Патчи игры, применяются при запуске": "Parches del juego, se aplican al iniciar",
    "Детализация моделей": "Detalle de los modelos",
    "Как в игре": "Como en el juego",
    "Максимальная (-2)": "Máximo (-2)",
    "Ниже (1)": "Menor (1)",
    "Минимальная (2)": "Mínimo (2)",
    "Хроматическая аберрация": "Aberración cromática",
    "Глубина резкости (DoF)": "Profundidad de campo (DoF)",
    "Размытие в движении": "Desenfoque de movimiento",
    "Затенение SSAO": "SSAO",
    "Собственное сглаживание игры": "Antialiasing propio del juego",
    "Тени от динамических источников": "Sombras de luces dinámicas",
    "Отражения SSR (не было в игре)": "Reflejos SSR (no estaban en el juego original)",
    "Пропуск заставок при запуске": "Omitir los vídeos de introducción",
    "Свободная камера (Cross + L3 / Space + Z)": "Cámara libre (Cross + L3 / Space + Z)",
    "Debug menu (левый touchpad / Tab; нужны шрифты)": "Debug menu (panel táctil izquierdo / Tab; requiere fuentes)",
    "Установите DbgFont14h.ccm и DbgFont14h.tpf в dvdroot_ps4/font из мода Nexus #253": "Instala DbgFont14h.ccm y DbgFont14h.tpf en dvdroot_ps4/font desde el mod n.º 253 de Nexus",
    "Частота кадров": "Tasa de fotogramas",
    "Режим": "Modo",
    "Какой патч частоты кадров применить к игре": "Qué parche de tasa de fotogramas aplicar al juego",
    "Без ограничения (патч)": "Sin límite (parche)",
    "30 (как на PS4)": "30 (como en PS4)",
    "Ограничение FPS": "Límite de FPS",
    "0 — без ограничения; укажите число, чтобы ограничить FPS": "0: sin límite; indica un número para limitar la tasa de fotogramas",
    "Производительность": "Rendimiento",
    "Двухстадийный конвейер GPU": "Pipeline de GPU en dos etapas",
    "Быстрее на 20–30%; при нестабильности выключите": "Un 20–30 % más rápido; desactívalo si hay inestabilidad",
    "Авто": "Automático",
    "Включён при 8 и более потоках процессора": "Activado con 8 o más hilos de CPU",
    "Включён": "Activado",
    "Стабильнее, но медленнее": "Más estable, pero más lento",
    "Чтение данных GPU процессором": "Lectura de datos de la GPU por la CPU",
    "По умолчанию": "Predeterminado",
    "Фоновая загрузка в видеопамять": "Precarga en segundo plano en la VRAM",
    "Меньше рывков при подгрузке зон": "Menos tirones al cargar zonas",
    "Обычная": "Normal",
    "Без лишней видеопамяти": "Sin VRAM adicional",
    "Полная": "Completa",
    "Около 3 ГБ видеопамяти сверху": "Unos 3 GB más de VRAM",
    "Режим работы": "Modo",
    "Новая модель памяти и трансляции": "Nuevo modelo de memoria y traducción",
    "Эксперимент, только видеокарты AMD. Видеокарта работает с памятью игры напрямую, как в игре для ПК, а команды графики переводятся, а не эмулируются; возможны ошибки. Выключено — старая модель памяти, как в 0.3, со всеми исправлениями": "Experimental, solo GPU AMD. La GPU trabaja directamente con la memoria del juego, como en un juego de PC, y los comandos gráficos se traducen en lugar de emularse; pueden producirse errores. Desactivado: el modelo de memoria antiguo, como en la 0.3, con todas las correcciones",
    "Только для видеокарт AMD, а на этом компьютере её нет. Используется старая модель памяти, как в 0.3, со всеми исправлениями": "Solo para GPU AMD, y este equipo no tiene ninguna. Se usa el modelo de memoria antiguo, como en la 0.3, con todas las correcciones",
    "Синхронизация как в 0.3": "Sincronización como en la 0.3",
    "Для поиска регрессий: старая модель памяти и ожидания копий как в релизе 0.3": "Para encontrar regresiones: el modelo de memoria antiguo y las esperas de copia tal como se publicaron en la 0.3",
    "Выключена": "Desactivado",
    "Выключены": "Desactivado",
    "Для разработчика": "Desarrollador",
    "Статистика кадров в журнале": "Estadísticas de fotogramas en el registro",
    "Сохранять журнал и статистику в файл": "Guardar el registro y las estadísticas en un archivo",
    "Диагностика вылетов": "Diagnóstico de fallos",
    "Проверяет кучу игры и записывает записи в её память; немного медленнее": "Comprueba el heap del juego y registra las escrituras en su memoria; algo más lento",
    "В папку logs в каталоге данных: для разбора рывков и вылетов": "En la carpeta logs del directorio de datos: para investigar tirones y fallos",
    "Профиль GPU в журнале": "Perfil de la GPU en el registro",
    "Слои валидации Vulkan": "Capas de validación de Vulkan",
    "Сильно замедляет": "Mucho más lento",
    "Доп. переменные (ИМЯ=значение через пробел)": "Variables adicionales (NOMBRE=valor, separadas por espacios)",
    "Читы": "Trucos",
    "Патчи игры версии 1.09, применяются при запуске. Для обычного прохождения и игры по сети оставьте их выключенными": "Parches del juego para la versión 1.09, se aplican al iniciar. Déjalos desactivados para una partida normal y para jugar online",
    "Изменения игрового процесса": "Ajustes de jugabilidad",
    "Бессмертие": "Nunca morir",
    "Урон проходит, но здоровье не опускается ниже 1": "Recibes daño, pero la salud nunca baja de 1",
    "Невидимость": "Sigilo",
    "Враги не видят вас и не реагируют, пока вы не атакуете": "Los enemigos no te ven ni reaccionan hasta que atacas",
    "Бесшумность": "Pasos silenciosos",
    "Враги не слышат вас, но видят": "Los enemigos no te oyen, pero aún pueden verte",
    "Rally не угасает": "Rally nunca se desvanece",
    "Здоровье для Rally не исчезает со временем": "La salud que puedes recuperar con Rally no se desvanece con el tiempo",
    "Управление врагом": "Control de enemigos",
    "R3: управлять целью, L3: вернуться. Не вместе со свободной камерой": "R3: controlar al enemigo fijado, L3: volver. No funciona junto con la cámara libre",
    "Без Rally": "Sin Rally",
    "Атаки не возвращают здоровье": "Los ataques no recuperan salud",
    "Камера дальше": "Cámara más alejada",
    "Камера дальше от персонажа": "La cámara se mantiene más lejos del personaje",
    "Без автоповорота камеры": "Sin giro automático de cámara",
    "Камера не поворачивается сама при движении; ручное управление и захват цели работают": "La cámara no gira sola al moverte; la cámara manual y la fijación de objetivo siguen funcionando",
    "Бег с меньшим наклоном стика": "Correr con menos inclinación",
    "Бег примерно с 70% наклона стика вместо 90%": "Correr a partir de un 70 % de inclinación del stick en lugar del 90 %",
    "Физика тел как в Dark Souls": "Física ragdoll de Dark Souls",
    "Тела и предметы разлетаются от ударов": "Los cadáveres y los objetos salen volando al recibir golpes",
    # Add to Steam
    "Добавить в Steam": "Añadir a Steam",
    "Игра в библиотеке Steam запускается сразу, с настройками этого лаунчера": "Desde la biblioteca de Steam el juego arranca directamente, con los ajustes de este launcher",
    "Добавить": "Añadir",
    "Steam не найден (или в него ещё никто не входил)": "No se ha encontrado Steam (o nadie ha iniciado sesión todavía)",
    "Закройте Steam и нажмите «Добавить» ещё раз": "Cierra Steam y vuelve a pulsar Añadir",
    "Пока игра добавляется, Steam нужно закрыть; потом он запустится снова. Закрыть Steam?": "Steam tiene que cerrarse mientras se añade el juego; después se vuelve a abrir. ¿Cerrar Steam?",
    "Отмена": "Cancelar",
    "Закрыть Steam": "Cerrar Steam",
    "Steam не закрылся. Закройте его сами и попробуйте ещё раз": "Steam no se ha cerrado. Ciérralo tú y vuelve a intentarlo",
    "Не удалось добавить игру в Steam: {}": "No se pudo añadir el juego a Steam: {}",
    "Bloodborne добавлен в библиотеку Steam": "Bloodborne se ha añadido a tu biblioteca de Steam",
    # Online page
    "Онлайн": "Online",
    "Сообщения, пятна крови и призраки приходят с The Hunter's Dream; колокола и призывы идут через сервер shadNet. Игра по сети совместима с версией для Windows: нужны версия игры 1.09 и тот же сервер": "Los mensajes, las manchas de sangre y los fantasmas vienen de The Hunter's Dream; las campanas y las invocaciones pasan por un servidor shadNet. El juego online es compatible con la versión de Windows: todos necesitan la versión 1.09 del juego y el mismo servidor",
    "Играть онлайн": "Jugar online",
    "Выключено: игра остаётся офлайн, как раньше": "Desactivado: el juego sigue sin conexión, como antes",
    "Игровой сервер (сообщения, пятна крови, призраки)": "Servidor del juego (mensajes, manchas de sangre, fantasmas)",
    "Игровой сервер": "Servidor del juego",
    "Сервер кооператива (колокола и призывы)": "Servidor cooperativo (campanas e invocaciones)",
    "Учётная запись": "Cuenta",
    "Имя учётной записи shadNet, не email. Зарегистрируйтесь на shadnet.shadps4.net или спросите владельца частного сервера. Пароль хранится на этом компьютере вместе с настройками лаунчера": "El nombre de tu cuenta de shadNet, no el correo. Regístrate en shadnet.shadps4.net o pídesela a quien gestione un servidor privado. La contraseña se guarda en este ordenador con los ajustes del launcher",
    "Пароль": "Contraseña",
    "Соединение": "Conexión",
    "У всех в сессии должны быть одна версия игры (1.09) и один сервер. Читы меняют игру и для других игроков: выключайте их при совместной игре": "Todos en la sesión necesitan la misma versión del juego (1.09) y el mismo servidor. Los trucos cambian el juego también para los demás jugadores: desactívalos al jugar juntos",
    "UPnP (открыть порт на роутере автоматически)": "UPnP (abrir un puerto en el router automáticamente)",
    "Выключите при Tailscale или другом VPN": "Desactívalo con Tailscale u otra VPN",
    "Проверить соединение": "Probar la conexión",
    "Проверить": "Probar",
    "Сервер shadNet": "Servidor shadNet",
    "Проверка…": "Comprobando…",
    "доступен": "accesible",
    "недоступен": "no accesible",
    "Учётная запись для игры онлайн указана, но «Играть онлайн» выключено": "Hay una cuenta online puesta, pero «Jugar online» está desactivado",
    "Играть офлайн": "Jugar sin conexión",
    "Online ID — это имя учётной записи (NPID), зарегистрированное на сервере, а не адрес email": "El Online ID es el nombre de cuenta (NPID) que registraste en el servidor, no tu correo",
    # DLSS
    "Нужны видеокарта NVIDIA RTX и проприетарный драйвер; иначе используется FSR 3.1": "Necesita una gráfica NVIDIA RTX y el driver propietario; si no, se usa FSR 3.1",
    "Нет файлов DLSS: tools/build_dlss.sh": "No están los archivos de DLSS: tools/build_dlss.sh",
    # Discord
    "Статус в Discord": "Estado en Discord",
    "«Играет в Bloodborne» в профиле Discord, онлайн или офлайн": "«Jugando a Bloodborne» en tu perfil de Discord, online o sin conexión",
    # Button prompts (scripts/menu_prompts.py)
    "Применяется при запуске игры": "Se aplica al iniciar el juego",
    "Иконки кнопок": "Iconos de botones",
    "Поменять местами A и B": "Intercambiar A y B",
    "Для контроллеров в стиле Nintendo: подтверждение на A, отмена на B. Применяется при запуске игры": "Para mandos estilo Nintendo: confirmar con A, volver con B. Se aplica al iniciar el juego",
    "Автоматически (по контроллеру)": "Automático (según el mando)",
    "PlayStation (оригинал)": "PlayStation (original)",
    "Меню жестов без значков управления движением": "Menú de gestos sin iconos de control por movimiento",
    # Add to Steam with Flathub's Steam
    'Steam из Flatpak запускает игры в своей песочнице, где нет ни папки игры, ни драйверов: ярлык должен запускать игру вне её (flatpak-spawn --host). Для этого Steam нужно право org.freedesktop.Flatpak, с которым он может запускать программы в вашей системе. Выдать его?':
        'El Steam de Flatpak ejecuta los juegos dentro de su sandbox, donde no están ni la carpeta del juego ni los drivers: el atajo tiene que arrancar el juego fuera de ella (flatpak-spawn --host). Para eso Steam necesita el permiso org.freedesktop.Flatpak, que le permite ejecutar programas en tu sistema. ¿Concederlo?',
    'Выдать право':
        'Conceder permiso',
    'Не удалось выдать право Steam: {}':
        'No se pudo conceder el permiso a Steam: {}',
    "Копировать":
        "Copiar",
    "Экспорт журнала…":
        "Exportar registro…",
    "Экспорт журнала":
        "Exportar registro",
    "Журнал скопирован":
        "Registro copiado",
    "Журнал сохранён: {}":
        "Registro guardado: {}",
    "Не удалось сохранить журнал: {}":
        "No se pudo guardar el registro: {}",
    "Монитор":
        "Monitor",
    "Пропускать выбор «по сети / вне сети»":
        "Saltar la elección «jugar en línea / sin conexión»",
    "Игра сразу открывает главное меню в режиме вне сети (патч игры)":
        "El juego abre el menú principal sin conexión directamente (un parche del juego)",
    "Основной":
        "Principal",
    ", основной":
        ", principal",
    "Файлы игры повреждены при распаковке: шейдеры не распаковываются, игра зависнет на загрузке. Распакуйте игру и обновление 1.09 заново исправленным инструментом (issue #81)":
        "Los archivos del juego se dañaron al extraerlos: los shaders no se descomprimen y el juego se quedaría colgado al cargar. Vuelve a extraer el juego y la actualización 1.09 con una herramienta corregida (issue #81)",
    "Нужна папка adhoc из мода Nexus #253 (шрифты adhoc/font) — в dvdroot_ps4 игры или модом; без неё патч не применяется":
        "Necesita la carpeta adhoc del mod #253 de Nexus (fuentes en adhoc/font), en dvdroot_ps4 del juego o como mod; sin ella el parche no se aplica",
    "Новая: видеокарта работает с памятью игры напрямую, как в игре для ПК, а команды графики переводятся, а не эмулируются. Старая — модель памяти 0.3 со всеми исправлениями. Если драйвер не проходит проверку при запуске — старая":
        "El nuevo: la tarjeta gráfica trabaja directamente con la memoria del juego, como en un juego de PC, y los comandos gráficos se traducen en vez de emularse. El antiguo: el modelo de memoria de la 0.3 con todas las correcciones. Si el controlador no pasa la comprobación al arrancar, el antiguo",
    "Модель памяти и трансляции":
        "Modelo de memoria y traducción",
    "Авто: новая на AMD, старая на других":
        "Automático: nuevo en AMD, antiguo en las demás",
    "Новая":
        "Nuevo",
    "Старая (как в 0.3)":
        "Antiguo (como en la 0.3)",
    "Регион игры":
        "Región del juego",
    "Вариант текста у языков с региональными версиями: испанский Испании (Европа) или Латинской Америки (Америка)":
        "La variante de texto de los idiomas que la tienen: español de España (Europa) o de Latinoamérica (América)",
    "Как в дампе игры":
        "Como en el volcado del juego",
    "Европа":
        "Europa",
    "Америка":
        "América",
    "Включён брандмауэр: {}":
        "Cortafuegos activado: {}",
    "Для UPnP нужны ответы роутера: {}":
        "El UPnP necesita las respuestas del router: {}",
    "О программе":
        "Acerca de",
    "Версия {}":
        "Versión {}",
    "Обновления":
        "Actualizaciones",
    "Проверять обновления при запуске":
        "Buscar actualizaciones al abrir",
    "Спрашивает GitHub о последнем выпуске; ничего не скачивается без вашего согласия":
        "Consulta en GitHub la última versión publicada; no se descarga nada sin que lo digas",
    "Последняя версия":
        "Última versión",
    "Загрузка…":
        "Descargando…",
    "Обновить":
        "Actualizar",
    "Версия {} установлена: перезапустите лаунчер":
        "Versión {} instalada: reinicia el launcher",
    "Перезапустить":
        "Reiniciar",
    "Не удалось проверить: {}":
        "No se pudo comprobar: {}",
    "Установлена версия {}":
        "Versión {} instalada",
    "Установлена последняя версия ({})":
        "Tienes la última versión ({})",
    "Доступна версия {} (установлена {})":
        "Ha salido la versión {} (tienes la {})",
    "Открыть страницу":
        "Abrir la página",
    "Доступна версия {}":
        "Ha salido la versión {}",
    "Подробнее":
        "Ver",
    "Загрузка… {} %":
        "Descargando… {} %",
    "Загрузка… {} МБ":
        "Descargando… {} MB",
    "Не удалось обновить: {}":
        "No se pudo actualizar: {}",
    "Сначала закройте игру":
        "Cierra el juego primero",
    "Этот проект":
        "Este proyecto",
    "Основано на bbport от deadinside28":
        "Basado en bbport, de deadinside28",
    "Порт для Windows от Supermedo":
        "Port para Windows, de Supermedo",
    "Лицензия":
        "Licencia",
    'GNU GPL v2 или новее · Файлы игры не входят.': 'GNU GPL v2 o posterior · No incluye archivos del juego.',
    'Bloodborne принадлежит Sony Interactive Entertainment и FromSoftware.': 'Bloodborne pertenece a Sony Interactive Entertainment y FromSoftware.',
    "Проверить сейчас":
        "Comprobar ahora",
    # 0.51: mouse look, choosing NVIDIA's DLSS library, the online module
    'DLSS {}: готово':
        'DLSS {}: listo',
    'DLSS найден (нужна видеокарта NVIDIA RTX)':
        'DLSS encontrado (necesita una GPU NVIDIA RTX)',
    'DLSS не найден: выберите библиотеку NVIDIA ниже (и нужна сборка с мостом DLSS). Игра включит FSR 3.1':
        'DLSS no encontrado: elige la biblioteca de NVIDIA abajo (también hace falta una compilación con el puente de DLSS). El juego usará FSR 3.1',
    'DLSS: библиотека NVIDIA':
        'DLSS: biblioteca de NVIDIA',
    '{} — библиотека DLSS для Windows; на Linux NVIDIA её не загружает. Нужна libnvidia-ngx-dlss.so.<версия> из DLSS SDK NVIDIA: {}':
        '{} es la biblioteca de DLSS para Windows; el controlador de NVIDIA para Linux no la carga. Hace falta libnvidia-ngx-dlss.so.<versión> del DLSS SDK de NVIDIA: {}',
    'Библиотека DLSS NVIDIA (libnvidia-ngx-dlss.so.*)':
        'Biblioteca DLSS de NVIDIA (libnvidia-ngx-dlss.so.*)',
    'Выбрать файл…':
        'Elegir archivo…',
    'Из сборки: {}':
        'De esta compilación: {}',
    'Инвертировать мышь по вертикали':
        'Invertir el eje Y del ratón',
    'Камера мышью':
        'Cámara con el ratón',
    'Клавиатура и мышь':
        'Teclado y ratón',
    'Не удалось прочитать файл':
        'No se pudo leer el archivo',
    'Не удалось скопировать библиотеку':
        'No se pudo copiar la biblioteca',
    'Нет: выберите libnvidia-ngx-dlss.so.* из DLSS SDK NVIDIA ({})':
        'Ninguna: elige libnvidia-ngx-dlss.so.* del DLSS SDK de NVIDIA ({})',
    'Нужен файл libnvidia-ngx-dlss.so.<версия> из DLSS SDK NVIDIA: {}':
        'Hace falta libnvidia-ngx-dlss.so.<versión> del DLSS SDK de NVIDIA: {}',
    'Нужна библиотека для Linux':
        'Hace falta una biblioteca para Linux',
    'Своя: {}':
        'La tuya: {}',
    'Убрать выбранную':
        'Quitar la elegida',
    'Чувствительность мыши':
        'Sensibilidad del ratón',
    'Щелчок в окне игры захватывает мышь, F1 — отпускает':
        'Un clic en la ventana del juego captura el ratón; F1 lo suelta',
    'Эта сборка без модуля онлайна (libbbnet.so): игра только офлайн':
        'Esta compilación no tiene el módulo online (libbbnet.so): solo se puede jugar sin conexión',
    'Эта сборка без моста DLSS (libbbport_dlss.so): DLSS работать не будет':
        'Esta compilación no tiene el puente de DLSS (libbbport_dlss.so): DLSS no funcionará',
    'Это не библиотека DLSS':
        'No es la biblioteca de DLSS',
    # Online page: your own shadNet server, the co-op port, seamless co-op, the UDP test
    '0: случайный при каждом запуске. Закрепите его, чтобы открыть в брандмауэре или на роутере вручную':
        '0: uno aleatorio cada vez. Fíjalo para abrirlo en el cortafuegos o a mano en el router',
    'UDP сервера shadNet (призывы)':
        'UDP del servidor shadNet (invocaciones)',
    'UPnP открывает порт только на роутере; брандмауэр этого компьютера всё равно блокирует кооператив. Откройте порт: {}':
        'El UPnP solo abre el puerto en el router; el cortafuegos de este equipo sigue bloqueando el cooperativo. Abre el puerto: {}',
    'Адрес WebAPI (пусто: порт 31315 сервера)':
        'Dirección del WebAPI (vacía: el puerto 31315 del servidor)',
    'Адрес сервера (host:port)':
        'Dirección del servidor (host:puerto)',
    'Бесшовный кооператив (экспериментально)':
        'Cooperativo seamless (experimental)',
    'Закрепите порт кооператива выше (например, {}): случайный порт в брандмауэре не открыть':
        'Fija el puerto del cooperativo arriba (por ejemplo, {}): un puerto aleatorio no se puede abrir en el cortafuegos',
    'Как запустить свой сервер':
        'Cómo montar tu propio servidor',
    'Порт кооператива (UDP)':
        'Puerto del cooperativo (UDP)',
    'Призывы между разными локациями. Только если на сервере BloodborneSeamlessCoop=true, и у всех игроков так же':
        'Invocaciones entre zonas distintas. Solo si el servidor tiene BloodborneSeamlessCoop=true y todos los jugadores lo activan',
    'Публичный сервер shadPS4':
        'Servidor público de shadPS4',
    'Свой сервер':
        'Servidor propio',
    'shadnet-p2p: на вашем ПК или VPS':
        'shadnet-p2p: en tu PC o en un VPS',
    'Сервер shadNet':
        'Servidor shadNet',
    'не отвечает: призывы не соединятся':
        'no responde: las invocaciones no conectarán',
    'отвечает; ваш публичный адрес: {}':
        'responde; tu dirección pública: {}',
    "Поддержать проект": 'Apoyar este proyecto',
    # Trophies page
    'В дампе игры нет трофеев (sce_sys/trophy)':
        'El volcado del juego no tiene trofeos (sce_sys/trophy)',
    'Записываются, когда игра их открывает, и показываются в игре':
        'Se guardan cuando el juego los desbloquea, y se muestran en el juego',
    'Ключ трофеев':
        'Clave de trofeos',
    'Ключ трофеев PS4 (TrophyKey в shadPS4), 32 шестнадцатеричных символа: с ним названия и описания на языке игры. Хранится на этом компьютере. Без него они на английском':
        'La clave de trofeos de PS4 (TrophyKey en shadPS4), 32 dígitos hexadecimales: con ella, los nombres y las descripciones salen en el idioma del juego. Se guarda en este equipo. Sin ella salen en inglés',
    'Неверный ключ трофеев: названия недоступны':
        'Clave de trofeos incorrecta: los nombres no están disponibles',
    'Получен {}':
        'Conseguido el {}',
    'Получено {} из {}':
        '{} de {} conseguidos',
    'Скрытый трофей':
        'Trofeo oculto',
    'Трофеи':
        'Trofeos',
    'Платиновый':
        'Platino',
    'Золотой':
        'Oro',
    'Серебряный':
        'Plata',
    'Бронзовый':
        'Bronce',
    "Вход в shadNet": "Inicio de sesión en shadNet",
    "неверное имя или пароль": "nombre o contraseña incorrectos",
    "такой учётной записи нет на этом сервере": "esa cuenta no existe en este servidor",
    "эта учётная запись уже в сети (игра запущена?)": "esta cuenta ya tiene la sesión iniciada (¿está el juego abierto?)",
    "вход выполнен": "sesión iniciada",
    "вход не удался ({})": "no se pudo iniciar sesión ({})",
    "Загрузки и плавность": "Cargas y fluidez",
    "Патчи игры из bbhost, применяются при запуске": "Parches del juego de bbhost, se aplican al arrancar",
    "Быстрая загрузка после смерти": "Carga rápida al morir",
    "Загрузка после смерти или перемещения у лампы идёт, пока грузится область (2–3 с), а не минимум 12 с": "La carga tras morir o viajar con una lámpara dura lo que tarda la zona (2–3 s), no un mínimo de 12 s",
    "Без рывка каждые ~50 с": "Sin tirón cada ~50 s",
    "Игра быстрее сжимает запись игрока: пропадает рывок ~23 мс примерно каждые 50 с": "El juego comprime más rápido el registro del jugador: desaparece un tirón de ~23 ms cada unos 50 s",
    "Третий поток подготовки ресурсов": "Tercer hilo de preparación de recursos",
    "Во время игры работают три потока подготовки ресурсов, а не два. Экспериментально": "Durante el juego funcionan tres hilos de preparación de recursos, no dos. Experimental",
    # About: Thanks
    'Благодарности': 'Agradecimientos',
    'Без них ничего этого не было бы': 'Sin ellos, nada de esto sería posible',
    'Порт и его код': 'El port y su código',
    'Помощь и тесты': 'Ayuda y pruebas',
    'Другие благодарности': 'También gracias a',
    'bbport — порт, на котором построен весь этот проект': 'bbport, el port en el que se basa todo este proyecto',
    'Игра по сети, DLSS, страница читов, добавление в Steam, значок и пропуск конвейеров, которые драйвер не может создать': 'Juego online, DLSS, la página de trucos, Añadir a Steam, el icono y saltar los pipelines que el driver no puede crear',
    'Собрал и адаптировал десятки исправлений: вылеты при загрузке, чёрные изображения, апскейлер, строка производительности в журнале': 'Reunió y adaptó decenas de arreglos: cierres al cargar, imágenes en negro, el escalado, la línea de rendimiento del registro',
    'Чёрный предпросмотр персонажа, картинка экрана загрузки и память кэша текстур': 'La vista previa del personaje en negro, la imagen de la pantalla de carga y la memoria de la caché de texturas',
    'Кэш текстур вовремя освобождает видеопамять': 'Que la caché de texturas libere la memoria de vídeo a tiempo',
    'Вылеты при загрузке областей': 'Cierres al cargar zonas',
    'Интерфейс, пропадавший не в 1080p, векторы движения больших чудовищ и ошибка памяти': 'La interfaz que desaparecía fuera de 1080p, los vectores de movimiento de las bestias grandes y un fallo de memoria',
    'Вылеты при загрузке некоторых карт и меню жестов с клавиатуры': 'Cierres al cargar algunos mapas y el menú de gestos desde el teclado',
    'Экранная клавиатура для имени персонажа и уведомление о компиляции шейдеров': 'El teclado en pantalla para el nombre del personaje y el aviso de compilación de shaders',
    "Быстрая загрузка после смерти и перемещения (bbhost) и сервер The Hunter's Dream": "Cargas rápidas tras morir o viajar (bbhost) y el servidor The Hunter's Dream",
    'Сетевые библиотеки игры по сети и сервер для своего кооператива': 'Las librerías del juego online y el servidor para el cooperativo propio',
    'Основа поддержки DLSS и модель FSR 4 без шлейфов за персонажами': 'La base del soporte de DLSS y el modelo de FSR 4 sin estelas tras los personajes',
    'Апскейлер FSR 3.1': 'El escalado FSR 3.1',
    'Игра запускается, когда DLSS нельзя использовать': 'Que el juego arranque cuando no se puede usar DLSS',
    'Перевод на упрощённый китайский': 'La traducción al chino simplificado',
    'Звук игры на полной громкости': 'El sonido del juego a volumen completo',
    'Флажки и ползунки внутриигрового меню': 'Las casillas y los deslizadores del menú del juego',
    'Подробные отчёты с журналами и проверка исправлений': 'Reportes detallados con registros y pruebas de los arreglos',
    'Идея поменять местами A и B на контроллерах в стиле Nintendo': 'La idea de cambiar A y B en mandos de estilo Nintendo',
    'Проверка исправления видеопамяти': 'Probar el arreglo de la memoria de vídeo',
    'Иконки кнопок Xbox и Switch (Nexus Mods)': 'Iconos de botones de Xbox y Switch (Nexus Mods)',
    'Показал, какие текстуры нужны иконкам клавиатуры (Nexus Mods)': 'Mostró qué texturas necesitan los iconos de teclado (Nexus Mods)',
    'Патчи игры: высокий FPS, разрешение и другое': 'Parches del juego: FPS altos, resolución y más',
    'Рендерер и компилятор шейдеров': 'El renderizador y el recompilador de shaders',
    'Инструмент для сборки AppImage': 'La herramienta que crea la AppImage',
    'Нашёл ошибку, из-за которой игра не запускалась на некоторых видеокартах': 'Encontró el fallo que impedía arrancar el juego en algunas gráficas',
    # Shader cache
    'Кэш шейдеров': 'Caché de shaders',
    'Очистить': 'Borrar',
    '{}. Если после обновления картинка выглядит странно, очистите его: шейдеры соберутся заново (первые минуты в каждой зоне возможны рывки)': '{}. Si la imagen se ve rara tras una actualización, bórrala: los shaders se vuelven a generar (puede haber tirones los primeros minutos en cada zona)',
    'Пусто: шейдеры соберутся при игре': 'Vacía: los shaders se generan mientras juegas',
    'Очистить кэш шейдеров?': '¿Borrar la caché de shaders?',
    'Игра соберёт шейдеры заново: первые минуты в каждой зоне возможны рывки. Сохранения и настройки не затрагиваются.': 'El juego volverá a generar los shaders: puede haber tirones los primeros minutos en cada zona. Las partidas y los ajustes no se tocan.',
    'Названия трофеев на английском без ключа и звук при получении трофея': 'Los nombres de los trofeos en inglés sin la clave y el sonido al conseguir uno',
    'Буфер трафарета, в который писали цветные изображения': 'El búfer de estarcido en el que escribían imágenes de color',
    'Вход на публичный сервер shadNet без отключения': 'Seguir conectado en el servidor público de shadNet',
    'Игра по сети': 'Juego en línea',
    'Сервер shadNet не принимает bbport, игра осталась офлайн. Для игры по сети используйте свой сервер (страница «Онлайн»).': 'El servidor shadNet no acepta bbport, así que el juego se ha quedado sin conexión. Para jugar en línea, usa tu propio servidor (página Online).',
    'Выход из игры из меню с контроллера и меню в пределах экрана': 'Salir del juego desde el menú con el mando y el menú dentro de la pantalla',
    'Вылет видеоплеера при его остановке': 'Un cierre del reproductor de vídeo al detenerse',
    'Язык внутриигрового меню при запуске без окна лаунчера': 'El idioma del menú del juego al arrancar sin la ventana del launcher',
    'DLSS в AppImage на NVIDIA': 'DLSS en la AppImage con NVIDIA',
    'Сверхширокие мониторы без растянутой картинки': 'Monitores ultrapanorámicos sin la imagen estirada',
}


# Italian.
IT = {
    "Папка DLC": "Cartella dei DLC",
    "Выбрать папку DLC": "Scegli la cartella dei DLC",
    "Не использовать DLC": "Non usare i DLC",
    "Найдено DLC: {}": "DLC trovati: {}",
    "Не используется": "Non usata",
    "Нет DLC этой игры в папке": "Nessun DLC di questo gioco nella cartella",
    "Запустить": "Gioca",
    "Остановить": "Ferma",
    "Настройки": "Impostazioni",
    "Журнал": "Log",
    "Не удалось запустить: {}": "Impossibile avviare: {}",
    "\n— игра завершилась (код {}) —\n": "\n— il gioco è terminato (codice {}) —\n",
    "Язык лаунчера": "Lingua del launcher",
    "Как в системе": "Sistema",
    "Применится после перезапуска лаунчера, пока игра запущена": "Si applica dopo il riavvio del launcher mentre il gioco è in esecuzione",
    "Игра": "Gioco",
    "Папка игры ({})": "Cartella del gioco ({})",
    "Папка игры": "Cartella del gioco",
    "Выбрать папку с eboot.bin": "Scegli la cartella con eboot.bin",
    "Открыть в файловом менеджере": "Apri nel gestore di file",
    "Папка сохранений": "Cartella dei salvataggi",
    "Выбрать папку сохранений": "Scegli la cartella dei salvataggi",
    "Вернуть папку по умолчанию": "Torna alla cartella predefinita",
    "Язык системы": "Lingua di sistema",
    "По умолчанию: {}": "Predefinito: {}",
    "Найдены сохранения": "Salvataggi trovati",
    "Сохранений пока нет: игра создаст их здесь": "Ancora nessun salvataggio: il gioco li creerà qui",
    "не выбрана": "non scelta",
    "Найден eboot.bin": "eboot.bin trovato",
    "Нет eboot.bin в папке": "Nessun eboot.bin nella cartella",
    "Управление": "Controlli",
    "Клавиатура": "Tastiera",
    "Геймпад": "Gamepad",
    "Назначение кнопок; применяется при запуске игры": "Assegnazione dei tasti; si applica all'avvio del gioco",
    "Назначить": "Assegna",
    "Сбросить": "Ripristina",
    "{} (по умолчанию)": "{} (predefinito)",
    "не назначено": "non assegnato",
    "Нажмите клавишу или кнопку… (Esc — отмена)": "Premi un tasto o un pulsante… (Esc per annullare)",
    "Крест": "Croce",
    "Круг": "Cerchio",
    "Квадрат": "Quadrato",
    "Треугольник": "Triangolo",
    "Тачпад, левая половина (жесты)": "Touchpad, metà sinistra (gesti)",
    "Тачпад, правая половина (личные вещи)": "Touchpad, metà destra (oggetti chiave)",
    "Крестовина вверх": "Croce direzionale su",
    "Крестовина вниз": "Croce direzionale giù",
    "Крестовина влево": "Croce direzionale sinistra",
    "Крестовина вправо": "Croce direzionale destra",
    "Движение вперёд": "Muoviti avanti",
    "Движение назад": "Muoviti indietro",
    "Движение влево": "Muoviti a sinistra",
    "Движение вправо": "Muoviti a destra",
    "Камера вверх": "Camera su",
    "Камера вниз": "Camera giù",
    "Камера влево": "Camera a sinistra",
    "Камера вправо": "Camera a destra",
    "Контроллер": "Controller",
    "Выбранный берётся, как только подключится": "Quello scelto viene usato non appena si connette",
    "Первый подключённый": "Il primo connesso",
    "{} (не подключён)": "{} (non connesso)",
    "Нужно обновление 1.09: скопируйте файлы дампа обновления 1.09 в папку игры с заменой (найдена версия {})": "Serve l'aggiornamento 1.09: copia l'aggiornamento 1.09 estratto nella cartella del gioco, sostituendo i file (versione trovata {})",
    "eboot.bin не от версии 1.09: скопируйте eboot.bin из дампа обновления 1.09 в папку игры с заменой": "eboot.bin non è della 1.09: copia eboot.bin dall'aggiornamento 1.09 estratto nella cartella del gioco, sostituendolo",
    "eboot.bin с вшитым патчем 60 FPS от Lance McDonald: из-за него игра падает в меню жестов. Скопируйте чистый eboot.bin из дампа обновления 1.09 в папку игры с заменой": "Questo eboot.bin contiene la patch a 60 FPS di Lance McDonald, che fa chiudere il gioco nel menu dei gesti: copia un eboot.bin pulito dall'aggiornamento 1.09 estratto nella cartella del gioco, sostituendolo",
    "Это не магазинное издание Bloodborne (найдено {}): нужен Bloodborne любого региона с обновлением 1.09": "Non è un'edizione commerciale di Bloodborne (trovato {}): serve Bloodborne di qualsiasi regione con l'aggiornamento 1.09",
    "eboot.bin не читается как расшифрованный исполняемый файл PS4: сделайте дамп заново": "eboot.bin non può essere letto come eseguibile PS4 decriptato: estrai di nuovo il gioco",
    "Bloodborne {}, версия 1.09": "Bloodborne {}, versione 1.09",
    "Папка игры (с eboot.bin)": "Cartella del gioco (con eboot.bin)",
    "Английский": "Inglese",
    "Русский": "Russo",
    "Японский": "Giapponese",
    "Французский": "Francese",
    "Испанский": "Spagnolo",
    "Немецкий": "Tedesco",
    "Итальянский": "Italiano",
    "Моды": "Mod",
    "Распакуйте каждый мод в отдельную папку (с dvdroot_ps4 или сразу с chr/, parts/ и т. п.). При совпадении файлов побеждает мод ниже в списке. Применяется при запуске.": "Estrai ogni mod nella sua cartella (con dvdroot_ps4, oppure direttamente chr/, parts/, ...). In caso di conflitto di file vince la mod più in basso nell'elenco. Si applica all'avvio.",
    "Загружать моды": "Carica le mod",
    "Папка модов": "Cartella delle mod",
    "Выбрать папку модов": "Scegli la cartella delle mod",
    "Открыть папку модов": "Apri la cartella delle mod",
    "Обновить список": "Aggiorna l'elenco",
    "Загрузить раньше": "Carica prima",
    "Загрузить позже": "Carica dopo",
    "Модов нет": "Nessuna mod",
    "Сторонние патчи": "Patch di terze parti",
    "XML-патчи в формате shadPS4 для версии 01.09 из папки патчей. Применяются при запуске.": "Patch XML in formato shadPS4 per la versione 01.09 dalla cartella delle patch. Si applicano all'avvio.",
    "Папка патчей": "Cartella delle patch",
    "Выбрать папку патчей": "Scegli la cartella delle patch",
    "Открыть папку патчей": "Apri la cartella delle patch",
    "Патчей нет": "Nessuna patch",
    "Автор: {}": "Autore: {}",
    "Экран": "Schermo",
    "Разрешение вывода": "Risoluzione di uscita",
    "Апскейлер дорисовывает кадр; Steam Deck — 720p": "L'upscaler riempie il fotogramma; Steam Deck: 720p",
    "Полноэкранный режим": "Schermo intero",
    "Смена разрешения на лету": "Cambio di risoluzione in tempo reale",
    "Без перезапуска, но медленнее на Steam Deck и старых GPU": "Non serve riavviare, ma è più lento su Steam Deck e GPU meno recenti",
    "Авто (по видеокарте)": "Auto (in base alla GPU)",
    "Выключена (быстрее)": "Disattivato (più veloce)",
    "Включена": "Attivato",
    "Режим показа кадров": "Modalità di presentazione",
    "Разрешить HDR": "Consenti HDR",
    "Апскейлер": "Upscaler",
    "Хранится в bbport.ini; в игре меняется через меню (Insert или L3+R3)": "Salvato in bbport.ini; in gioco, cambialo nel menu (Insert o L3+R3)",
    "TAA (нативное сглаживание)": "TAA (anti-aliasing nativo)",
    "Выключен": "Disattivato",
    "Пресет": "Preset",
    "Резкость (RCAS)": "Nitidezza (RCAS)",
    "Сила резкости": "Nitidezza",
    "Векторы движения объектов": "Vettori di movimento degli oggetti",
    "Меньше гостинга на персонажах; стоит около 10% FPS": "Meno ghosting sui personaggi; costa circa il 10% di FPS",
    "Показывать FPS": "Mostra FPS",
    "Ассеты найдены": "Risorse trovate",
    "Нет ассетов: tools/fetch_fsr4_assets.sh": "Nessuna risorsa: tools/fetch_fsr4_assets.sh",
    "Ассеты для выбранного режима найдены": "Risorse per la modalità selezionata trovate",
    "{}. Соберите FSR 4.1.1 из своей DLL кнопкой «Выбрать DLL…» ниже": "{}. Crea FSR 4.1.1 dalla tua DLL con il pulsante «Scegli DLL…» qui sotto",
    "FSR 4.1.1 из своей DLL AMD": "FSR 4.1.1 dalla tua DLL AMD",
    "Отменить": "Annulla",
    "Выбрать DLL…": "Scegli DLL…",
    "DLL апскейлера AMD (amd_fidelityfx_upscaler_dx12.dll)": "DLL dell'upscaler AMD (amd_fidelityfx_upscaler_dx12.dll)",
    "нет": "nessuno",
    "Эта DLL не подходит": "Questa DLL non è adatta",
    "{}: версия {}, модели FSR 4: {}.\n\nbbport повторяет только официальную FSR 4.1.x от AMD (модель v07_fp8_no_scale): например, FSR4_LATEST из OptiScaler или amd_fidelityfx_upscaler_dx12.dll из игры с FSR 4.1. Сборки сообщества (4.0.2b и подобные) устроены иначе и пока не поддерживаются.": "{}: versione {}, modelli FSR 4: {}.\n\nbbport riproduce solo l'FSR 4.1.x ufficiale di AMD (modello v07_fp8_no_scale): per esempio FSR4_LATEST di OptiScaler, oppure amd_fidelityfx_upscaler_dx12.dll di un gioco con FSR 4.1. Le build della community (4.0.2b e simili) hanno una struttura diversa e non sono ancora supportate.",
    "Загрузчик не подходит": "Il loader non è adatto",
    "Загрузчик FidelityFX (amd_fidelityfx_loader_dx12.dll или amd_fidelityfx_dx12.dll)": "Loader FidelityFX (amd_fidelityfx_loader_dx12.dll o amd_fidelityfx_dx12.dll)",
    "\n— сборка FSR 4.1.1 из {} —\n": "\n— creazione di FSR 4.1.1 da {} —\n",
    "Подготовка…": "Preparazione…",
    "Запись проходов DLL под Proton: {} из {}": "Registrazione dei passaggi della DLL con Proton: {} di {}",
    "Перевод проходов в SPIR-V…": "Traduzione dei passaggi in SPIR-V…",
    "— сборка FSR 4.1.1 завершилась (код {}) —\n": "— creazione di FSR 4.1.1 terminata (codice {}) —\n",
    "FSR 4.1.1 собран и выбран": "FSR 4.1.1 creato e selezionato",
    "Сборка FSR 4.1.1 отменена": "Creazione di FSR 4.1.1 annullata",
    "FSR 4.1.1 не собран": "FSR 4.1.1 non è stato creato",
    "DLL не подходит: подробности в журнале": "La DLL non è adatta: dettagli nel log",
    "Не хватает программ для сборки: список в журнале": "Mancano gli strumenti per la build: l'elenco è nel log",
    "Записанные проходы не совпали с тем, что повторяет bbport (другая версия DLL или новая видеокарта?): подробности в журнале": "I passaggi registrati non corrispondono a quelli che bbport riproduce (un'altra versione della DLL, o una nuova GPU?): dettagli nel log",
    "Не найден загрузчик FidelityFX 2.x": "Nessun loader FidelityFX 2.x trovato",
    "Не найден подходящий Proton: установите GE-Proton 10 или новее (ProtonUp-Qt) или Proton Experimental / Proton-CachyOS в Steam. Если они есть — запустите в Steam любую игру с этим Proton, чтобы Steam поставил его рантайм": "Nessun Proton adatto trovato: installa GE-Proton 10 o successivo (ProtonUp-Qt), oppure Proton Experimental / Proton-CachyOS in Steam. Se li hai, avvia un qualsiasi gioco con quel Proton in Steam, così che Steam installi il suo runtime",
    "Ни один Proton не запустил FSR 4.1 из этой DLL. Либо они слишком старые (подходят GE-Proton 10+, Proton Experimental, Proton-CachyOS 11), либо DLL не включает FSR 4.1 на этой видеокарте (Steam Deck?): тогда соберите на ПК с Radeon RX 7000/9000 и скопируйте папку fsr4_411. Подробности в журнале": "Nessun Proton ha avviato l'FSR 4.1 di questa DLL. O sono troppo vecchi (funzionano GE-Proton 10+, Proton Experimental, Proton-CachyOS 11), oppure la DLL non attiva FSR 4.1 su questa GPU (Steam Deck?): in tal caso crea la build su un PC con una Radeon RX 7000/9000 e copia la cartella fsr4_411. Dettagli nel log",
    "На NixOS запись идёт на самой системе (systemd --user) через umu-launcher из nix-shell, а здесь их не нашлось: установите umu-launcher или Nix. Подробности в журнале": "Su NixOS la registrazione viene eseguita sul sistema stesso (systemd --user) con umu-launcher da nix-shell, e nessuno dei due è stato trovato: installa umu-launcher o Nix. Dettagli nel log",
    "{}: FSR {}. Это официальная FSR 4.0.x от AMD: она включается только на видеокартах RDNA4 (RX 9000), а под Proton на других видеокартах не запускается, поэтому записать её нельзя.\n\nНужна FSR 4.1.x: например, FSR4_LATEST из OptiScaler или DLL из игры с FSR 4.1.": "{}: FSR {}. Questo è l'FSR 4.0.x ufficiale di AMD: è attivo solo sulle GPU RDNA4 (RX 9000) e su altre GPU non si avvia con Proton, quindi non può essere registrato.\n\nServe FSR 4.1.x: per esempio FSR4_LATEST di OptiScaler, o la DLL di un gioco con FSR 4.1.",
    "{}: в этой DLL нет FSR 4. Нужна amd_fidelityfx_upscaler_dx12.dll версии 4.1.x.": "{}: questa DLL non contiene FSR 4. Serve amd_fidelityfx_upscaler_dx12.dll versione 4.1.x.",
    "Это не загрузчик": "Questo non è il loader",
    "{} — это DLL апскейлера. Загрузчик называется amd_fidelityfx_loader_dx12.dll (у OptiScaler — amd_fidelityfx_dx12.dll) и лежит в той же папке игры, что и DLL апскейлера.": "{} è la DLL dell'upscaler. Il loader si chiama amd_fidelityfx_loader_dx12.dll (amd_fidelityfx_dx12.dll in OptiScaler) e si trova nella stessa cartella del gioco della DLL dell'upscaler.",
    "{}: версия {}. Нужен загрузчик FidelityFX 2.x — из той же игры, что и DLL апскейлера.": "{}: versione {}. Serve un loader FidelityFX 2.x, dello stesso gioco della DLL dell'upscaler.",
    "Рядом с DLL нет загрузчика: выберите amd_fidelityfx_loader_dx12.dll из папки игры": "Nessun loader accanto alla DLL: scegli amd_fidelityfx_loader_dx12.dll dalla cartella del gioco",
    "Собрать FSR 4.1.1 из amd_fidelityfx_upscaler_dx12.dll 4.1.x (OptiScaler: папка FSR4_LATEST, или из игры с FSR 4.1). Нужен GE-Proton 10+, Proton Experimental или Proton-CachyOS; 2–5 минут (RDNA4: вдвое дольше, ещё и вариант FP8)": "Crea FSR 4.1.1 da amd_fidelityfx_upscaler_dx12.dll 4.1.x (OptiScaler: la cartella FSR4_LATEST, oppure da un gioco con FSR 4.1). Richiede GE-Proton 10+, Proton Experimental o Proton-CachyOS; 2–5 minuti (RDNA4: il doppio, con la variante FP8)",
    "Сборка не удалась (код {}): подробности в журнале": "La build non è riuscita (codice {}): dettagli nel log",
    "Сглаживание в разрешении вывода без модели FSR": "Anti-aliasing alla risoluzione di uscita, senza modello FSR",
    "Нет или повреждён файл {}": "File {} mancante o danneggiato",
    "Эффекты игры": "Effetti del gioco",
    "Патчи игры, применяются при запуске": "Patch del gioco, applicate all'avvio",
    "Детализация моделей": "Dettaglio dei modelli",
    "Как в игре": "Come nel gioco",
    "Максимальная (-2)": "Massimo (-2)",
    "Ниже (1)": "Più basso (1)",
    "Минимальная (2)": "Minimo (2)",
    "Хроматическая аберрация": "Aberrazione cromatica",
    "Глубина резкости (DoF)": "Profondità di campo (DoF)",
    "Размытие в движении": "Motion blur",
    "Затенение SSAO": "SSAO",
    "Собственное сглаживание игры": "L'anti-aliasing integrato del gioco",
    "Тени от динамических источников": "Ombre dinamiche delle luci",
    "Отражения SSR (не было в игре)": "Riflessi SSR (assenti nel gioco originale)",
    "Пропуск заставок при запуске": "Salta i video introduttivi",
    "Свободная камера (Cross + L3 / Space + Z)": "Camera libera (Cross + L3 / Space + Z)",
    "Debug menu (левый touchpad / Tab; нужны шрифты)": "Debug menu (touchpad sinistro / Tab; richiede i font)",
    "Установите DbgFont14h.ccm и DbgFont14h.tpf в dvdroot_ps4/font из мода Nexus #253": "Installa DbgFont14h.ccm e DbgFont14h.tpf in dvdroot_ps4/font dalla mod Nexus n. 253",
    "Частота кадров": "Frequenza dei fotogrammi",
    "Режим": "Modalità",
    "Какой патч частоты кадров применить к игре": "Quale patch della frequenza dei fotogrammi applicare al gioco",
    "Без ограничения (патч)": "Sbloccata (patch)",
    "30 (как на PS4)": "30 (come su PS4)",
    "Ограничение FPS": "Limite di FPS",
    "0 — без ограничения; укажите число, чтобы ограничить FPS": "0: nessun limite; imposta un numero per limitare la frequenza dei fotogrammi",
    "Производительность": "Prestazioni",
    "Двухстадийный конвейер GPU": "Pipeline GPU a due stadi",
    "Быстрее на 20–30%; при нестабильности выключите": "Più veloce del 20–30%; disattivala se è instabile",
    "Авто": "Auto",
    "Включён при 8 и более потоках процессора": "Attivata con 8 o più thread CPU",
    "Включён": "Attivata",
    "Стабильнее, но медленнее": "Più stabile, ma più lenta",
    "Чтение данных GPU процессором": "Letture dei dati della GPU da parte della CPU",
    "По умолчанию": "Predefinito",
    "Фоновая загрузка в видеопамять": "Precaricamento in background nella VRAM",
    "Меньше рывков при подгрузке зон": "Meno scatti quando le aree vengono caricate",
    "Обычная": "Normale",
    "Без лишней видеопамяти": "Nessuna VRAM extra",
    "Полная": "Completo",
    "Около 3 ГБ видеопамяти сверху": "Circa 3 GB di VRAM in più",
    "Режим работы": "Modalità",
    "Новая модель памяти и трансляции": "Nuovo modello di memoria e traduzione",
    "Эксперимент, только видеокарты AMD. Видеокарта работает с памятью игры напрямую, как в игре для ПК, а команды графики переводятся, а не эмулируются; возможны ошибки. Выключено — старая модель памяти, как в 0.3, со всеми исправлениями": "Sperimentale, solo GPU AMD. La GPU lavora direttamente con la memoria del gioco, come in un gioco per PC, e i comandi grafici vengono tradotti anziché emulati; sono possibili errori. Disattivato: il vecchio modello di memoria, come nella 0.3, con tutte le correzioni",
    "Только для видеокарт AMD, а на этом компьютере её нет. Используется старая модель памяти, как в 0.3, со всеми исправлениями": "Solo GPU AMD, e questo computer non ne ha. Viene usato il vecchio modello di memoria, come nella 0.3, con tutte le correzioni",
    "Синхронизация как в 0.3": "Sincronizzazione come nella 0.3",
    "Для поиска регрессий: старая модель памяти и ожидания копий как в релизе 0.3": "Per trovare regressioni: il vecchio modello di memoria e le attese di copia come rilasciati nella 0.3",
    "Выключена": "Disattivata",
    "Выключены": "Disattivata",
    "Для разработчика": "Sviluppatore",
    "Статистика кадров в журнале": "Statistiche dei fotogrammi nel log",
    "Сохранять журнал и статистику в файл": "Salva il log e le statistiche in un file",
    "Диагностика вылетов": "Diagnostica dei crash",
    "Проверяет кучу игры и записывает записи в её память; немного медленнее": "Controlla l'heap del gioco e registra le scritture nella sua memoria; un po' più lento",
    "В папку logs в каталоге данных: для разбора рывков и вылетов": "Nella cartella logs della directory dei dati: per analizzare scatti e crash",
    "Профиль GPU в журнале": "Profilo GPU nel log",
    "Слои валидации Vulkan": "Layer di validazione Vulkan",
    "Сильно замедляет": "Molto più lento",
    "Доп. переменные (ИМЯ=значение через пробел)": "Variabili aggiuntive (NOME=valore, separate da spazi)",
    "Читы": "Cheat",
    "Патчи игры версии 1.09, применяются при запуске. Для обычного прохождения и игры по сети оставьте их выключенными": "Patch del gioco per la versione 1.09, applicate all'avvio. Lasciale disattivate per una partita normale e per il gioco online",
    "Изменения игрового процесса": "Modifiche al gameplay",
    "Бессмертие": "Non morire mai",
    "Урон проходит, но здоровье не опускается ниже 1": "Subisci danni ma non scendi mai sotto 1 HP",
    "Невидимость": "Furtività",
    "Враги не видят вас и не реагируют, пока вы не атакуете": "I nemici non ti vedono né reagiscono finché non attacchi",
    "Бесшумность": "Passi silenziosi",
    "Враги не слышат вас, но видят": "I nemici non ti sentono ma possono ancora vederti",
    "Rally не угасает": "Rally non svanisce mai",
    "Здоровье для Rally не исчезает со временем": "La salute recuperabile con Rally non svanisce nel tempo",
    "Управление врагом": "Controllo dei nemici",
    "R3: управлять целью, L3: вернуться. Не вместе со свободной камерой": "R3: controlla il nemico bersagliato, L3: indietro. Non insieme alla camera libera",
    "Без Rally": "Niente Rally",
    "Атаки не возвращают здоровье": "Gli attacchi non recuperano salute",
    "Камера дальше": "Camera più lontana",
    "Камера дальше от персонажа": "La camera resta più lontana dal personaggio",
    "Без автоповорота камеры": "Nessuna rotazione automatica della camera",
    "Камера не поворачивается сама при движении; ручное управление и захват цели работают": "La camera non ruota da sola quando ti muovi; camera manuale e lock-on funzionano ancora",
    "Бег с меньшим наклоном стика": "Corsa più facile",
    "Бег примерно с 70% наклона стика вместо 90%": "Corri inclinando lo stick di circa il 70% invece del 90%",
    "Физика тел как в Dark Souls": "Fisica ragdoll di Dark Souls",
    "Тела и предметы разлетаются от ударов": "Cadaveri e oggetti volano via quando vengono colpiti",
    # Add to Steam
    "Добавить в Steam": "Aggiungi a Steam",
    "Игра в библиотеке Steam запускается сразу, с настройками этого лаунчера": "Dalla libreria di Steam il gioco si avvia subito, con le impostazioni di questo launcher",
    "Добавить": "Aggiungi",
    "Steam не найден (или в него ещё никто не входил)": "Steam non trovato (o nessuno vi ha ancora effettuato l'accesso)",
    "Закройте Steam и нажмите «Добавить» ещё раз": "Chiudi Steam e premi di nuovo Aggiungi",
    "Пока игра добавляется, Steam нужно закрыть; потом он запустится снова. Закрыть Steam?": "Steam deve chiudersi mentre il gioco viene aggiunto; poi si riavvia. Chiudere Steam?",
    "Отмена": "Annulla",
    "Закрыть Steam": "Chiudi Steam",
    "Steam не закрылся. Закройте его сами и попробуйте ещё раз": "Steam non si è chiuso. Chiudilo tu e riprova",
    "Не удалось добавить игру в Steam: {}": "Impossibile aggiungere il gioco a Steam: {}",
    "Bloodborne добавлен в библиотеку Steam": "Bloodborne è stato aggiunto alla tua libreria di Steam",
    # Online page
    "Онлайн": "Online",
    "Сообщения, пятна крови и призраки приходят с The Hunter's Dream; колокола и призывы идут через сервер shadNet. Игра по сети совместима с версией для Windows: нужны версия игры 1.09 и тот же сервер": "Messaggi, macchie di sangue e fantasmi arrivano da The Hunter's Dream; campane ed evocazioni passano per un server shadNet. Il gioco online è compatibile con la versione per Windows: tutti devono avere la versione 1.09 del gioco e lo stesso server",
    "Играть онлайн": "Gioca online",
    "Выключено: игра остаётся офлайн, как раньше": "Disattivato: il gioco resta offline, come prima",
    "Игровой сервер (сообщения, пятна крови, призраки)": "Server di gioco (messaggi, macchie di sangue, fantasmi)",
    "Игровой сервер": "Server di gioco",
    "Сервер кооператива (колокола и призывы)": "Server cooperativo (campane ed evocazioni)",
    "Учётная запись": "Account",
    "Имя учётной записи shadNet, не email. Зарегистрируйтесь на shadnet.shadps4.net или спросите владельца частного сервера. Пароль хранится на этом компьютере вместе с настройками лаунчера": "Il nome del tuo account shadNet, non l'email. Registrati su shadnet.shadps4.net o chiedi a chi gestisce un server privato. La password viene salvata su questo computer con le impostazioni del launcher",
    "Пароль": "Password",
    "Соединение": "Connessione",
    "У всех в сессии должны быть одна версия игры (1.09) и один сервер. Читы меняют игру и для других игроков: выключайте их при совместной игре": "Tutti nella sessione devono avere la stessa versione del gioco (1.09) e lo stesso server. I cheat cambiano il gioco anche per gli altri giocatori: disattivali quando giocate insieme",
    "UPnP (открыть порт на роутере автоматически)": "UPnP (apri automaticamente una porta sul router)",
    "Выключите при Tailscale или другом VPN": "Disattivalo con Tailscale o un'altra VPN",
    "Проверить соединение": "Prova la connessione",
    "Проверить": "Prova",
    "Сервер shadNet": "Server shadNet",
    "Проверка…": "Verifica…",
    "доступен": "raggiungibile",
    "недоступен": "non raggiungibile",
    "Учётная запись для игры онлайн указана, но «Играть онлайн» выключено": "È impostato un account online, ma “Gioca online” è disattivato",
    "Играть офлайн": "Gioca offline",
    "Online ID — это имя учётной записи (NPID), зарегистрированное на сервере, а не адрес email": "L'Online ID è il nome dell'account (NPID) registrato sul server, non il tuo indirizzo email",
    # DLSS
    "Нужны видеокарта NVIDIA RTX и проприетарный драйвер; иначе используется FSR 3.1": "Richiede una scheda NVIDIA RTX e il driver proprietario; altrimenti si usa FSR 3.1",
    "Нет файлов DLSS: tools/build_dlss.sh": "File DLSS mancanti: tools/build_dlss.sh",
    # Discord
    "Статус в Discord": "Stato su Discord",
    "«Играет в Bloodborne» в профиле Discord, онлайн или офлайн": "“Sta giocando a Bloodborne” sul tuo profilo Discord, online o offline",
    # Button prompts (scripts/menu_prompts.py)
    "Применяется при запуске игры": "Si applica all'avvio del gioco",
    "Иконки кнопок": "Icone dei pulsanti",
    "Поменять местами A и B": "Scambia A e B",
    "Для контроллеров в стиле Nintendo: подтверждение на A, отмена на B. Применяется при запуске игры": "Per controller in stile Nintendo: conferma con A, indietro con B. Si applica all'avvio del gioco",
    "Автоматически (по контроллеру)": "Automatico (in base al controller)",
    "PlayStation (оригинал)": "PlayStation (originale)",
    "Меню жестов без значков управления движением": "Menu dei gesti senza icone del controllo di movimento",
    # Add to Steam with Flathub's Steam
    'Steam из Flatpak запускает игры в своей песочнице, где нет ни папки игры, ни драйверов: ярлык должен запускать игру вне её (flatpak-spawn --host). Для этого Steam нужно право org.freedesktop.Flatpak, с которым он может запускать программы в вашей системе. Выдать его?':
        'Steam da Flatpak avvia i giochi nella sua sandbox, dove non ci sono né la cartella del gioco né i driver: il collegamento deve avviare il gioco fuori da essa (flatpak-spawn --host). Per questo Steam ha bisogno del permesso org.freedesktop.Flatpak, che gli consente di avviare programmi sul tuo sistema. Concederlo?',
    'Выдать право':
        'Concedi il permesso',
    'Не удалось выдать право Steam: {}':
        'Impossibile concedere il permesso a Steam: {}',
    "Копировать":
        "Copia",
    "Экспорт журнала…":
        "Esporta registro…",
    "Экспорт журнала":
        "Esporta registro",
    "Журнал скопирован":
        "Registro copiato",
    "Журнал сохранён: {}":
        "Registro salvato: {}",
    "Не удалось сохранить журнал: {}":
        "Impossibile salvare il registro: {}",
    "Монитор":
        "Monitor",
    "Пропускать выбор «по сети / вне сети»":
        "Salta la scelta «gioca online / offline»",
    "Игра сразу открывает главное меню в режиме вне сети (патч игры)":
        "Il gioco apre subito il menu principale offline (una patch del gioco)",
    "Основной":
        "Principale",
    ", основной":
        ", principale",
    "Файлы игры повреждены при распаковке: шейдеры не распаковываются, игра зависнет на загрузке. Распакуйте игру и обновление 1.09 заново исправленным инструментом (issue #81)":
        "I file del gioco si sono danneggiati durante l'estrazione: gli shader non si decomprimono e il gioco si bloccherebbe durante il caricamento. Estrai di nuovo il gioco e l'aggiornamento 1.09 con uno strumento corretto (issue #81)",
    "Нужна папка adhoc из мода Nexus #253 (шрифты adhoc/font) — в dvdroot_ps4 игры или модом; без неё патч не применяется":
        "Serve la cartella adhoc della mod #253 di Nexus (font in adhoc/font), in dvdroot_ps4 del gioco o come mod; senza di essa la patch non viene applicata",
    "Новая: видеокарта работает с памятью игры напрямую, как в игре для ПК, а команды графики переводятся, а не эмулируются. Старая — модель памяти 0.3 со всеми исправлениями. Если драйвер не проходит проверку при запуске — старая":
        "Il nuovo: la scheda video lavora direttamente con la memoria del gioco, come in un gioco per PC, e i comandi grafici vengono tradotti invece che emulati. Il vecchio: il modello di memoria della 0.3 con tutte le correzioni. Se il driver non supera il controllo all'avvio, il vecchio",
    "Модель памяти и трансляции":
        "Modello di memoria e traduzione",
    "Авто: новая на AMD, старая на других":
        "Automatico: nuovo su AMD, vecchio sulle altre",
    "Новая":
        "Nuovo",
    "Старая (как в 0.3)":
        "Vecchio (come nella 0.3)",
    "Регион игры":
        "Regione del gioco",
    "Вариант текста у языков с региональными версиями: испанский Испании (Европа) или Латинской Америки (Америка)":
        "La variante del testo delle lingue che ne hanno una: spagnolo di Spagna (Europa) o dell'America Latina (America)",
    "Как в дампе игры":
        "Come nel dump del gioco",
    "Европа":
        "Europa",
    "Америка":
        "America",
    "Включён брандмауэр: {}":
        "Firewall attivo: {}",
    "Для UPnP нужны ответы роутера: {}":
        "L'UPnP ha bisogno delle risposte del router: {}",
    "О программе":
        "Informazioni",
    "Версия {}":
        "Versione {}",
    "Обновления":
        "Aggiornamenti",
    "Проверять обновления при запуске":
        "Cerca aggiornamenti all'avvio",
    "Спрашивает GitHub о последнем выпуске; ничего не скачивается без вашего согласия":
        "Chiede a GitHub l'ultima versione pubblicata; non si scarica nulla senza il tuo consenso",
    "Последняя версия":
        "Ultima versione",
    "Загрузка…":
        "Download…",
    "Обновить":
        "Aggiorna",
    "Версия {} установлена: перезапустите лаунчер":
        "Versione {} installata: riavvia il launcher",
    "Перезапустить":
        "Riavvia",
    "Не удалось проверить: {}":
        "Impossibile controllare: {}",
    "Установлена версия {}":
        "Versione {} installata",
    "Установлена последняя версия ({})":
        "Hai l'ultima versione ({})",
    "Доступна версия {} (установлена {})":
        "È uscita la versione {} (hai la {})",
    "Открыть страницу":
        "Apri la pagina",
    "Доступна версия {}":
        "È uscita la versione {}",
    "Подробнее":
        "Dettagli",
    "Загрузка… {} %":
        "Download… {} %",
    "Загрузка… {} МБ":
        "Download… {} MB",
    "Не удалось обновить: {}":
        "Impossibile aggiornare: {}",
    "Сначала закройте игру":
        "Chiudi prima il gioco",
    "Этот проект":
        "Questo progetto",
    "Основано на bbport от deadinside28":
        "Basato su bbport di deadinside28",
    "Порт для Windows от Supermedo":
        "Port per Windows di Supermedo",
    "Лицензия":
        "Licenza",
    'GNU GPL v2 или новее · Файлы игры не входят.': 'GNU GPL v2 o successiva · Nessun file del gioco incluso.',
    'Bloodborne принадлежит Sony Interactive Entertainment и FromSoftware.': 'Bloodborne appartiene a Sony Interactive Entertainment e FromSoftware.',
    "Проверить сейчас":
        "Controlla ora",
    # 0.51: mouse look, choosing NVIDIA's DLSS library, the online module
    'DLSS {}: готово':
        'DLSS {}: pronto',
    'DLSS найден (нужна видеокарта NVIDIA RTX)':
        'DLSS trovato (serve una GPU NVIDIA RTX)',
    'DLSS не найден: выберите библиотеку NVIDIA ниже (и нужна сборка с мостом DLSS). Игра включит FSR 3.1':
        'DLSS non trovato: scegli la libreria NVIDIA qui sotto (serve anche una build con il bridge DLSS). Il gioco userà FSR 3.1',
    'DLSS: библиотека NVIDIA':
        'DLSS: libreria NVIDIA',
    '{} — библиотека DLSS для Windows; на Linux NVIDIA её не загружает. Нужна libnvidia-ngx-dlss.so.<версия> из DLSS SDK NVIDIA: {}':
        '{} è la libreria DLSS per Windows; il driver NVIDIA per Linux non la carica. Serve libnvidia-ngx-dlss.so.<versione> dal DLSS SDK di NVIDIA: {}',
    'Библиотека DLSS NVIDIA (libnvidia-ngx-dlss.so.*)':
        'Libreria DLSS di NVIDIA (libnvidia-ngx-dlss.so.*)',
    'Выбрать файл…':
        'Scegli file…',
    'Из сборки: {}':
        'Da questa build: {}',
    'Инвертировать мышь по вертикали':
        "Inverti l'asse Y del mouse",
    'Камера мышью':
        'Visuale con il mouse',
    'Клавиатура и мышь':
        'Tastiera e mouse',
    'Не удалось прочитать файл':
        'Impossibile leggere il file',
    'Не удалось скопировать библиотеку':
        'Impossibile copiare la libreria',
    'Нет: выберите libnvidia-ngx-dlss.so.* из DLSS SDK NVIDIA ({})':
        'Nessuna: scegli libnvidia-ngx-dlss.so.* dal DLSS SDK di NVIDIA ({})',
    'Нужен файл libnvidia-ngx-dlss.so.<версия> из DLSS SDK NVIDIA: {}':
        'Serve libnvidia-ngx-dlss.so.<versione> dal DLSS SDK di NVIDIA: {}',
    'Нужна библиотека для Linux':
        'Serve una libreria per Linux',
    'Своя: {}':
        'La tua: {}',
    'Убрать выбранную':
        'Rimuovi quella scelta',
    'Чувствительность мыши':
        'Sensibilità del mouse',
    'Щелчок в окне игры захватывает мышь, F1 — отпускает':
        'Un clic nella finestra del gioco cattura il mouse, F1 lo rilascia',
    'Эта сборка без модуля онлайна (libbbnet.so): игра только офлайн':
        'Questa build non ha il modulo online (libbbnet.so): solo gioco offline',
    'Эта сборка без моста DLSS (libbbport_dlss.so): DLSS работать не будет':
        'Questa build non ha il bridge DLSS (libbbport_dlss.so): DLSS non funzionerà',
    'Это не библиотека DLSS':
        'Non è la libreria DLSS',
    # Online page: your own shadNet server, the co-op port, seamless co-op, the UDP test
    '0: случайный при каждом запуске. Закрепите его, чтобы открыть в брандмауэре или на роутере вручную':
        '0: una casuale ogni volta. Fissala per aprirla nel firewall o a mano sul router',
    'UDP сервера shadNet (призывы)':
        'UDP del server shadNet (evocazioni)',
    'UPnP открывает порт только на роутере; брандмауэр этого компьютера всё равно блокирует кооператив. Откройте порт: {}':
        'UPnP apre la porta solo sul router; il firewall di questo computer blocca comunque la cooperativa. Apri la porta: {}',
    'Адрес WebAPI (пусто: порт 31315 сервера)':
        'Indirizzo WebAPI (vuoto: la porta 31315 del server)',
    'Адрес сервера (host:port)':
        'Indirizzo del server (host:porta)',
    'Бесшовный кооператив (экспериментально)':
        'Cooperativa seamless (sperimentale)',
    'Закрепите порт кооператива выше (например, {}): случайный порт в брандмауэре не открыть':
        'Fissa la porta della cooperativa qui sopra (per esempio {}): una porta casuale non si può aprire nel firewall',
    'Как запустить свой сервер':
        'Come ospitare un tuo server',
    'Порт кооператива (UDP)':
        'Porta della cooperativa (UDP)',
    'Призывы между разными локациями. Только если на сервере BloodborneSeamlessCoop=true, и у всех игроков так же':
        'Evocazioni tra zone diverse. Solo se il server ha BloodborneSeamlessCoop=true e tutti i giocatori la attivano',
    'Публичный сервер shadPS4':
        'Server pubblico di shadPS4',
    'Свой сервер':
        'Server tuo',
    'shadnet-p2p: на вашем ПК или VPS':
        'shadnet-p2p: sul tuo PC o su un VPS',
    'Сервер shadNet':
        'Server shadNet',
    'не отвечает: призывы не соединятся':
        'non risponde: le evocazioni non si collegheranno',
    'отвечает; ваш публичный адрес: {}':
        'risponde; il tuo indirizzo pubblico: {}',
    "Поддержать проект": 'Sostieni questo progetto',
    # Trophies page
    'В дампе игры нет трофеев (sce_sys/trophy)':
        'Il dump del gioco non ha trofei (sce_sys/trophy)',
    'Записываются, когда игра их открывает, и показываются в игре':
        'Registrati quando il gioco li sblocca, e mostrati nel gioco',
    'Ключ трофеев':
        'Chiave dei trofei',
    'Ключ трофеев PS4 (TrophyKey в shadPS4), 32 шестнадцатеричных символа: с ним названия и описания на языке игры. Хранится на этом компьютере. Без него они на английском':
        'La chiave dei trofei PS4 (TrophyKey in shadPS4), 32 cifre esadecimali: con essa nomi e descrizioni sono nella lingua del gioco. Resta su questo computer. Senza, sono in inglese',
    'Неверный ключ трофеев: названия недоступны':
        'Chiave dei trofei errata: i nomi non sono disponibili',
    'Получен {}':
        'Ottenuto il {}',
    'Получено {} из {}':
        '{} di {} ottenuti',
    'Скрытый трофей':
        'Trofeo nascosto',
    'Трофеи':
        'Trofei',
    'Платиновый':
        'Platino',
    'Золотой':
        'Oro',
    'Серебряный':
        'Argento',
    'Бронзовый':
        'Bronzo',
    "Вход в shadNet": "Accesso a shadNet",
    "неверное имя или пароль": "nome o password errati",
    "такой учётной записи нет на этом сервере": "questo account non esiste su questo server",
    "эта учётная запись уже в сети (игра запущена?)": "questo account ha già effettuato l'accesso (il gioco è aperto?)",
    "вход выполнен": "accesso riuscito",
    "вход не удался ({})": "accesso non riuscito ({})",
    "Загрузки и плавность": "Caricamenti e fluidità",
    "Патчи игры из bbhost, применяются при запуске": "Patch del gioco da bbhost, applicate all'avvio",
    "Быстрая загрузка после смерти": "Caricamento rapido dopo la morte",
    "Загрузка после смерти или перемещения у лампы идёт, пока грузится область (2–3 с), а не минимум 12 с": "Il caricamento dopo la morte o un viaggio dalla lanterna dura quanto serve all'area (2–3 s), non un minimo di 12 s",
    "Без рывка каждые ~50 с": "Nessuno scatto ogni ~50 s",
    "Игра быстрее сжимает запись игрока: пропадает рывок ~23 мс примерно каждые 50 с": "Il gioco comprime più in fretta la registrazione del giocatore: sparisce uno scatto di ~23 ms ogni 50 s circa",
    "Третий поток подготовки ресурсов": "Terzo thread di preparazione delle risorse",
    "Во время игры работают три потока подготовки ресурсов, а не два. Экспериментально": "Durante il gioco lavorano tre thread di preparazione delle risorse, non due. Sperimentale",
    # About: Thanks
    'Благодарности': 'Ringraziamenti',
    'Без них ничего этого не было бы': 'Senza di loro, niente di tutto questo sarebbe possibile',
    'Порт и его код': 'Il port e il suo codice',
    'Помощь и тесты': 'Aiuto e test',
    'Другие благодарности': 'Grazie anche a',
    'bbport — порт, на котором построен весь этот проект': 'bbport, il port su cui si basa tutto questo progetto',
    'Игра по сети, DLSS, страница читов, добавление в Steam, значок и пропуск конвейеров, которые драйвер не может создать': 'Gioco online, DLSS, la pagina dei trucchi, Aggiungi a Steam, l’icona e saltare le pipeline che il driver non riesce a creare',
    'Собрал и адаптировал десятки исправлений: вылеты при загрузке, чёрные изображения, апскейлер, строка производительности в журнале': 'Ha raccolto e adattato decine di correzioni: crash durante il caricamento, immagini nere, l’upscaler, la riga delle prestazioni nel log',
    'Чёрный предпросмотр персонажа, картинка экрана загрузки и память кэша текстур': 'L’anteprima nera del personaggio, l’immagine della schermata di caricamento e la memoria della cache delle texture',
    'Кэш текстур вовремя освобождает видеопамять': 'La cache delle texture libera la memoria video in tempo',
    'Вылеты при загрузке областей': 'Crash durante il caricamento delle aree',
    'Интерфейс, пропадавший не в 1080p, векторы движения больших чудовищ и ошибка памяти': 'L’interfaccia che spariva fuori da 1080p, i vettori di movimento delle grandi bestie e un errore di memoria',
    'Вылеты при загрузке некоторых карт и меню жестов с клавиатуры': 'Crash al caricamento di alcune mappe e il menu dei gesti da tastiera',
    'Экранная клавиатура для имени персонажа и уведомление о компиляции шейдеров': 'La tastiera su schermo per il nome del personaggio e l’avviso di compilazione degli shader',
    "Быстрая загрузка после смерти и перемещения (bbhost) и сервер The Hunter's Dream": "Caricamenti rapidi dopo una morte o un viaggio (bbhost) e il server The Hunter's Dream",
    'Сетевые библиотеки игры по сети и сервер для своего кооператива': 'Le librerie del gioco online e il server per la propria cooperativa',
    'Основа поддержки DLSS и модель FSR 4 без шлейфов за персонажами': 'La base del supporto DLSS e il modello FSR 4 senza scie dietro i personaggi',
    'Апскейлер FSR 3.1': 'L’upscaler FSR 3.1',
    'Игра запускается, когда DLSS нельзя использовать': 'Il gioco si avvia quando DLSS non può essere usato',
    'Перевод на упрощённый китайский': 'La traduzione in cinese semplificato',
    'Звук игры на полной громкости': 'L’audio del gioco a pieno volume',
    'Флажки и ползунки внутриигрового меню': 'Le caselle e i cursori del menu di gioco',
    'Подробные отчёты с журналами и проверка исправлений': 'Segnalazioni dettagliate con log e test delle correzioni',
    'Идея поменять местами A и B на контроллерах в стиле Nintendo': 'L’idea di scambiare A e B sui controller in stile Nintendo',
    'Проверка исправления видеопамяти': 'Test della correzione della memoria video',
    'Иконки кнопок Xbox и Switch (Nexus Mods)': 'Icone dei pulsanti Xbox e Switch (Nexus Mods)',
    'Показал, какие текстуры нужны иконкам клавиатуры (Nexus Mods)': 'Ha mostrato quali texture servono alle icone della tastiera (Nexus Mods)',
    'Патчи игры: высокий FPS, разрешение и другое': 'Patch del gioco: FPS alti, risoluzione e altro',
    'Рендерер и компилятор шейдеров': 'Il renderer e il ricompilatore degli shader',
    'Инструмент для сборки AppImage': 'Lo strumento che crea l’AppImage',
    'Нашёл ошибку, из-за которой игра не запускалась на некоторых видеокартах': 'Ha trovato il bug che impediva l’avvio del gioco su alcune schede video',
    # Shader cache
    'Кэш шейдеров': 'Cache degli shader',
    'Очистить': 'Svuota',
    '{}. Если после обновления картинка выглядит странно, очистите его: шейдеры соберутся заново (первые минуты в каждой зоне возможны рывки)': '{}. Se l’immagine sembra strana dopo un aggiornamento, svuotala: gli shader vengono ricreati (possibili scatti nei primi minuti di ogni area)',
    'Пусто: шейдеры соберутся при игре': 'Vuota: gli shader vengono creati mentre giochi',
    'Очистить кэш шейдеров?': 'Svuotare la cache degli shader?',
    'Игра соберёт шейдеры заново: первые минуты в каждой зоне возможны рывки. Сохранения и настройки не затрагиваются.': 'Il gioco ricrea gli shader: possibili scatti nei primi minuti di ogni area. Salvataggi e impostazioni non vengono toccati.',
    'Названия трофеев на английском без ключа и звук при получении трофея': 'I nomi dei trofei in inglese senza la chiave e il suono quando se ne ottiene uno',
    'Буфер трафарета, в который писали цветные изображения': 'Lo stencil buffer in cui scrivevano immagini a colori',
    'Вход на публичный сервер shadNet без отключения': 'Restare connessi al server pubblico di shadNet',
    'Игра по сети': 'Gioco online',
    'Сервер shadNet не принимает bbport, игра осталась офлайн. Для игры по сети используйте свой сервер (страница «Онлайн»).': 'Il server shadNet non accetta bbport, quindi il gioco è rimasto offline. Per giocare online usa un tuo server (pagina Online).',
    'Выход из игры из меню с контроллера и меню в пределах экрана': 'Uscire dal gioco dal menu con il controller e il menu entro lo schermo',
    'Вылет видеоплеера при его остановке': 'Un crash del lettore video quando si ferma',
    'Язык внутриигрового меню при запуске без окна лаунчера': 'La lingua del menu di gioco avviando senza la finestra del launcher',
    'DLSS в AppImage на NVIDIA': "DLSS nell'AppImage su NVIDIA",
    'Сверхширокие мониторы без растянутой картинки': 'Monitor ultrawide senza immagine stirata',
}


# French.
FR = {
    "Папка DLC": "Dossier des DLC",
    "Выбрать папку DLC": "Choisir le dossier des DLC",
    "Не использовать DLC": "Ne pas utiliser de DLC",
    "Найдено DLC: {}": "DLC trouvés : {}",
    "Не используется": "Non utilisé",
    "Нет DLC этой игры в папке": "Aucun DLC de ce jeu dans le dossier",
    "Запустить": "Jouer",
    "Остановить": "Arrêter",
    "Настройки": "Paramètres",
    "Журнал": "Journal",
    "Не удалось запустить: {}": "Impossible de lancer : {}",
    "\n— игра завершилась (код {}) —\n": "\n— le jeu s'est arrêté (code {}) —\n",
    "Язык лаунчера": "Langue du lanceur",
    "Как в системе": "Système",
    "Применится после перезапуска лаунчера, пока игра запущена": "S'applique après le redémarrage du lanceur lorsque le jeu est en cours d'exécution",
    "Игра": "Jeu",
    "Папка игры ({})": "Dossier du jeu ({})",
    "Папка игры": "Dossier du jeu",
    "Выбрать папку с eboot.bin": "Choisissez le dossier contenant eboot.bin",
    "Открыть в файловом менеджере": "Ouvrir dans le gestionnaire de fichiers",
    "Папка сохранений": "Dossier des sauvegardes",
    "Выбрать папку сохранений": "Choisissez le dossier des sauvegardes",
    "Вернуть папку по умолчанию": "Revenir au dossier par défaut",
    "Язык системы": "Langue du système",
    "По умолчанию: {}": "Par défaut : {}",
    "Найдены сохранения": "Sauvegardes trouvées",
    "Сохранений пока нет: игра создаст их здесь": "Aucune sauvegarde pour l'instant : le jeu les créera ici",
    "не выбрана": "non choisi",
    "Найден eboot.bin": "eboot.bin trouvé",
    "Нет eboot.bin в папке": "Pas de eboot.bin dans le dossier",
    "Управление": "Commandes",
    "Клавиатура": "Clavier",
    "Геймпад": "Manette",
    "Назначение кнопок; применяется при запуске игры": "Affectation des boutons ; appliquée au lancement du jeu",
    "Назначить": "Assigner",
    "Сбросить": "Réinitialiser",
    "{} (по умолчанию)": "{} (par défaut)",
    "не назначено": "non assigné",
    "Нажмите клавишу или кнопку… (Esc — отмена)": "Appuyez sur une touche ou un bouton… (Échap pour annuler)",
    "Крест": "Croix",
    "Круг": "Rond",
    "Квадрат": "Carré",
    "Треугольник": "Triangle",
    "Тачпад, левая половина (жесты)": "Pavé tactile, moitié gauche (gestes)",
    "Тачпад, правая половина (личные вещи)": "Pavé tactile, moitié droite (objets clés)",
    "Крестовина вверх": "Croix directionnelle haut",
    "Крестовина вниз": "Croix directionnelle bas",
    "Крестовина влево": "Croix directionnelle gauche",
    "Крестовина вправо": "Croix directionnelle droite",
    "Движение вперёд": "Avancer",
    "Движение назад": "Reculer",
    "Движение влево": "Aller à gauche",
    "Движение вправо": "Aller à droite",
    "Камера вверх": "Caméra vers le haut",
    "Камера вниз": "Caméra vers le bas",
    "Камера влево": "Caméra vers la gauche",
    "Камера вправо": "Caméra vers la droite",
    "Контроллер": "Manette",
    "Выбранный берётся, как только подключится": "Celle choisie est utilisée dès qu'elle se connecte",
    "Первый подключённый": "Première connectée",
    "{} (не подключён)": "{} (non connectée)",
    "Нужно обновление 1.09: скопируйте файлы дампа обновления 1.09 в папку игры с заменой (найдена версия {})": "La mise à jour 1.09 est nécessaire : copiez la mise à jour 1.09 extraite dans le dossier du jeu, en remplaçant les fichiers (version trouvée : {})",
    "eboot.bin не от версии 1.09: скопируйте eboot.bin из дампа обновления 1.09 в папку игры с заменой": "eboot.bin n'est pas celui de la 1.09 : copiez eboot.bin de la mise à jour 1.09 extraite dans le dossier du jeu, en le remplaçant",
    "eboot.bin с вшитым патчем 60 FPS от Lance McDonald: из-за него игра падает в меню жестов. Скопируйте чистый eboot.bin из дампа обновления 1.09 в папку игры с заменой": "Cet eboot.bin intègre le patch 60 FPS de Lance McDonald, qui fait planter le jeu dans le menu des gestes : copiez un eboot.bin propre de la mise à jour 1.09 extraite dans le dossier du jeu, en le remplaçant",
    "Это не магазинное издание Bloodborne (найдено {}): нужен Bloodborne любого региона с обновлением 1.09": "Ce n'est pas une édition commerciale de Bloodborne (trouvé : {}) : il faut Bloodborne de n'importe quelle région avec la mise à jour 1.09",
    "eboot.bin не читается как расшифрованный исполняемый файл PS4: сделайте дамп заново": "eboot.bin ne peut pas être lu comme un exécutable PS4 déchiffré : extrayez de nouveau le jeu",
    "Bloodborne {}, версия 1.09": "Bloodborne {}, version 1.09",
    "Папка игры (с eboot.bin)": "Dossier du jeu (avec eboot.bin)",
    "Английский": "Anglais",
    "Русский": "Russe",
    "Японский": "Japonais",
    "Французский": "Français",
    "Испанский": "Espagnol",
    "Немецкий": "Allemand",
    "Итальянский": "Italien",
    "Моды": "Mods",
    "Распакуйте каждый мод в отдельную папку (с dvdroot_ps4 или сразу с chr/, parts/ и т. п.). При совпадении файлов побеждает мод ниже в списке. Применяется при запуске.": "Extrayez chaque mod dans son propre dossier (avec dvdroot_ps4, ou directement chr/, parts/, ...). En cas de conflit de fichiers, le mod situé plus bas dans la liste l'emporte. Appliqué au démarrage.",
    "Загружать моды": "Charger les mods",
    "Папка модов": "Dossier des mods",
    "Выбрать папку модов": "Choisissez le dossier des mods",
    "Открыть папку модов": "Ouvrir le dossier des mods",
    "Обновить список": "Actualiser la liste",
    "Загрузить раньше": "Charger plus tôt",
    "Загрузить позже": "Charger plus tard",
    "Модов нет": "Aucun mod",
    "Сторонние патчи": "Correctifs tiers",
    "XML-патчи в формате shadPS4 для версии 01.09 из папки патчей. Применяются при запуске.": "Correctifs XML au format shadPS4 pour la version 01.09, depuis le dossier des correctifs. Appliqués au démarrage.",
    "Папка патчей": "Dossier des correctifs",
    "Выбрать папку патчей": "Choisissez le dossier des correctifs",
    "Открыть папку патчей": "Ouvrir le dossier des correctifs",
    "Патчей нет": "Aucun correctif",
    "Автор: {}": "Auteur : {}",
    "Экран": "Affichage",
    "Разрешение вывода": "Résolution de sortie",
    "Апскейлер дорисовывает кадр; Steam Deck — 720p": "L'upscaler remplit l'image ; Steam Deck : 720p",
    "Полноэкранный режим": "Plein écran",
    "Смена разрешения на лету": "Changement de résolution en direct",
    "Без перезапуска, но медленнее на Steam Deck и старых GPU": "Aucun redémarrage nécessaire, mais plus lent sur le Steam Deck et les GPU plus anciens",
    "Авто (по видеокарте)": "Auto (selon le GPU)",
    "Выключена (быстрее)": "Désactivé (plus rapide)",
    "Включена": "Activé",
    "Режим показа кадров": "Mode de présentation",
    "Разрешить HDR": "Autoriser le HDR",
    "Апскейлер": "Upscaler",
    "Хранится в bbport.ini; в игре меняется через меню (Insert или L3+R3)": "Enregistré dans bbport.ini ; en jeu, modifiez-le dans le menu (Insert ou L3+R3)",
    "TAA (нативное сглаживание)": "TAA (anticrénelage natif)",
    "Выключен": "Désactivé",
    "Пресет": "Préréglage",
    "Резкость (RCAS)": "Netteté (RCAS)",
    "Сила резкости": "Netteté",
    "Векторы движения объектов": "Vecteurs de mouvement des objets",
    "Меньше гостинга на персонажах; стоит около 10% FPS": "Moins de ghosting sur les personnages ; coûte environ 10 % de FPS",
    "Показывать FPS": "Afficher les FPS",
    "Ассеты найдены": "Ressources trouvées",
    "Нет ассетов: tools/fetch_fsr4_assets.sh": "Pas de ressources : tools/fetch_fsr4_assets.sh",
    "Ассеты для выбранного режима найдены": "Ressources du mode sélectionné trouvées",
    "{}. Соберите FSR 4.1.1 из своей DLL кнопкой «Выбрать DLL…» ниже": "{}. Générez FSR 4.1.1 à partir de votre propre DLL avec le bouton « Choisir la DLL… » ci-dessous",
    "FSR 4.1.1 из своей DLL AMD": "FSR 4.1.1 à partir de votre propre DLL AMD",
    "Отменить": "Annuler",
    "Выбрать DLL…": "Choisir la DLL…",
    "DLL апскейлера AMD (amd_fidelityfx_upscaler_dx12.dll)": "DLL de l'upscaler AMD (amd_fidelityfx_upscaler_dx12.dll)",
    "нет": "aucun",
    "Эта DLL не подходит": "Cette DLL ne convient pas",
    "{}: версия {}, модели FSR 4: {}.\n\nbbport повторяет только официальную FSR 4.1.x от AMD (модель v07_fp8_no_scale): например, FSR4_LATEST из OptiScaler или amd_fidelityfx_upscaler_dx12.dll из игры с FSR 4.1. Сборки сообщества (4.0.2b и подобные) устроены иначе и пока не поддерживаются.": "{} : version {}, modèles FSR 4 : {}.\n\nbbport ne rejoue que le FSR 4.1.x officiel d'AMD (modèle v07_fp8_no_scale) : par exemple FSR4_LATEST d'OptiScaler, ou amd_fidelityfx_upscaler_dx12.dll d'un jeu avec FSR 4.1. Les builds communautaires (4.0.2b et similaires) ont une structure différente et ne sont pas encore pris en charge.",
    "Загрузчик не подходит": "Le loader ne convient pas",
    "Загрузчик FidelityFX (amd_fidelityfx_loader_dx12.dll или amd_fidelityfx_dx12.dll)": "Loader FidelityFX (amd_fidelityfx_loader_dx12.dll ou amd_fidelityfx_dx12.dll)",
    "\n— сборка FSR 4.1.1 из {} —\n": "\n— génération de FSR 4.1.1 à partir de {} —\n",
    "Подготовка…": "Préparation…",
    "Запись проходов DLL под Proton: {} из {}": "Enregistrement des passes de la DLL sous Proton : {} sur {}",
    "Перевод проходов в SPIR-V…": "Traduction des passes en SPIR-V…",
    "— сборка FSR 4.1.1 завершилась (код {}) —\n": "— génération de FSR 4.1.1 terminée (code {}) —\n",
    "FSR 4.1.1 собран и выбран": "FSR 4.1.1 généré et sélectionné",
    "Сборка FSR 4.1.1 отменена": "Génération de FSR 4.1.1 annulée",
    "FSR 4.1.1 не собран": "FSR 4.1.1 n'a pas été généré",
    "DLL не подходит: подробности в журнале": "La DLL ne convient pas : détails dans le journal",
    "Не хватает программ для сборки: список в журнале": "Des outils nécessaires à la génération sont manquants : la liste est dans le journal",
    "Записанные проходы не совпали с тем, что повторяет bbport (другая версия DLL или новая видеокарта?): подробности в журнале": "Les passes enregistrées ne correspondent pas à ce que bbport rejoue (autre version de la DLL, ou nouveau GPU ?) : détails dans le journal",
    "Не найден загрузчик FidelityFX 2.x": "Aucun loader FidelityFX 2.x trouvé",
    "Не найден подходящий Proton: установите GE-Proton 10 или новее (ProtonUp-Qt) или Proton Experimental / Proton-CachyOS в Steam. Если они есть — запустите в Steam любую игру с этим Proton, чтобы Steam поставил его рантайм": "Aucun Proton adapté trouvé : installez GE-Proton 10 ou plus récent (ProtonUp-Qt), ou Proton Experimental / Proton-CachyOS dans Steam. Si vous les avez, lancez n'importe quel jeu avec ce Proton dans Steam afin que Steam installe son runtime",
    "Ни один Proton не запустил FSR 4.1 из этой DLL. Либо они слишком старые (подходят GE-Proton 10+, Proton Experimental, Proton-CachyOS 11), либо DLL не включает FSR 4.1 на этой видеокарте (Steam Deck?): тогда соберите на ПК с Radeon RX 7000/9000 и скопируйте папку fsr4_411. Подробности в журнале": "Aucun Proton n'a lancé le FSR 4.1 de cette DLL. Soit ils sont trop anciens (GE-Proton 10+, Proton Experimental, Proton-CachyOS 11 fonctionnent), soit la DLL n'active pas FSR 4.1 sur ce GPU (Steam Deck ?) : dans ce cas, faites la génération sur un PC avec une Radeon RX 7000/9000 et copiez le dossier fsr4_411. Détails dans le journal",
    "На NixOS запись идёт на самой системе (systemd --user) через umu-launcher из nix-shell, а здесь их не нашлось: установите umu-launcher или Nix. Подробности в журнале": "Sous NixOS, l'enregistrement s'exécute sur le système lui-même (systemd --user) avec umu-launcher depuis nix-shell, et aucun des deux n'a été trouvé : installez umu-launcher ou Nix. Détails dans le journal",
    "{}: FSR {}. Это официальная FSR 4.0.x от AMD: она включается только на видеокартах RDNA4 (RX 9000), а под Proton на других видеокартах не запускается, поэтому записать её нельзя.\n\nНужна FSR 4.1.x: например, FSR4_LATEST из OptiScaler или DLL из игры с FSR 4.1.": "{} : FSR {}. Il s'agit du FSR 4.0.x officiel d'AMD : il n'est activé que sur les GPU RDNA4 (RX 9000) et ne démarre pas sous Proton sur les autres GPU, il ne peut donc pas être enregistré.\n\nFSR 4.1.x est nécessaire : par exemple FSR4_LATEST d'OptiScaler, ou la DLL d'un jeu avec FSR 4.1.",
    "{}: в этой DLL нет FSR 4. Нужна amd_fidelityfx_upscaler_dx12.dll версии 4.1.x.": "{} : cette DLL ne contient pas FSR 4. amd_fidelityfx_upscaler_dx12.dll version 4.1.x est nécessaire.",
    "Это не загрузчик": "Ce n'est pas le loader",
    "{} — это DLL апскейлера. Загрузчик называется amd_fidelityfx_loader_dx12.dll (у OptiScaler — amd_fidelityfx_dx12.dll) и лежит в той же папке игры, что и DLL апскейлера.": "{} est la DLL de l'upscaler. Le loader s'appelle amd_fidelityfx_loader_dx12.dll (amd_fidelityfx_dx12.dll dans OptiScaler) et se trouve dans le même dossier de jeu que la DLL de l'upscaler.",
    "{}: версия {}. Нужен загрузчик FidelityFX 2.x — из той же игры, что и DLL апскейлера.": "{} : version {}. Un loader FidelityFX 2.x est nécessaire, provenant du même jeu que la DLL de l'upscaler.",
    "Рядом с DLL нет загрузчика: выберите amd_fidelityfx_loader_dx12.dll из папки игры": "Pas de loader à côté de la DLL : choisissez amd_fidelityfx_loader_dx12.dll dans le dossier du jeu",
    "Собрать FSR 4.1.1 из amd_fidelityfx_upscaler_dx12.dll 4.1.x (OptiScaler: папка FSR4_LATEST, или из игры с FSR 4.1). Нужен GE-Proton 10+, Proton Experimental или Proton-CachyOS; 2–5 минут (RDNA4: вдвое дольше, ещё и вариант FP8)": "Générez FSR 4.1.1 à partir de amd_fidelityfx_upscaler_dx12.dll 4.1.x (OptiScaler : le dossier FSR4_LATEST, ou celle d'un jeu avec FSR 4.1). Nécessite GE-Proton 10+, Proton Experimental ou Proton-CachyOS ; 2 à 5 minutes (RDNA4 : deux fois plus long, avec la variante FP8)",
    "Сборка не удалась (код {}): подробности в журнале": "La génération a échoué (code {}) : détails dans le journal",
    "Сглаживание в разрешении вывода без модели FSR": "Anticrénelage à la résolution de sortie, sans modèle FSR",
    "Нет или повреждён файл {}": "Fichier {} manquant ou endommagé",
    "Эффекты игры": "Effets du jeu",
    "Патчи игры, применяются при запуске": "Correctifs du jeu, appliqués au démarrage",
    "Детализация моделей": "Détail des modèles",
    "Как в игре": "Comme dans le jeu",
    "Максимальная (-2)": "Maximal (-2)",
    "Ниже (1)": "Plus bas (1)",
    "Минимальная (2)": "Minimal (2)",
    "Хроматическая аберрация": "Aberration chromatique",
    "Глубина резкости (DoF)": "Profondeur de champ (DoF)",
    "Размытие в движении": "Flou de mouvement",
    "Затенение SSAO": "SSAO",
    "Собственное сглаживание игры": "Anticrénelage propre au jeu",
    "Тени от динамических источников": "Ombres des lumières dynamiques",
    "Отражения SSR (не было в игре)": "Réflexions SSR (absentes du jeu original)",
    "Пропуск заставок при запуске": "Passer les vidéos d'introduction",
    "Свободная камера (Cross + L3 / Space + Z)": "Caméra libre (Cross + L3 / Space + Z)",
    "Debug menu (левый touchpad / Tab; нужны шрифты)": "Debug menu (pavé tactile gauche / Tab ; nécessite des polices)",
    "Установите DbgFont14h.ccm и DbgFont14h.tpf в dvdroot_ps4/font из мода Nexus #253": "Installez DbgFont14h.ccm et DbgFont14h.tpf dans dvdroot_ps4/font depuis le mod Nexus n° 253",
    "Частота кадров": "Fréquence d'images",
    "Режим": "Mode",
    "Какой патч частоты кадров применить к игре": "Quel correctif de fréquence d'images appliquer au jeu",
    "Без ограничения (патч)": "Illimitée (correctif)",
    "30 (как на PS4)": "30 (comme sur PS4)",
    "Ограничение FPS": "Limite de FPS",
    "0 — без ограничения; укажите число, чтобы ограничить FPS": "0 : aucune limite ; indiquez un nombre pour plafonner la fréquence d'images",
    "Производительность": "Performances",
    "Двухстадийный конвейер GPU": "Pipeline GPU à deux étapes",
    "Быстрее на 20–30%; при нестабильности выключите": "20 à 30 % plus rapide ; désactivez en cas d'instabilité",
    "Авто": "Auto",
    "Включён при 8 и более потоках процессора": "Activé avec 8 threads CPU ou plus",
    "Включён": "Activé",
    "Стабильнее, но медленнее": "Plus stable, mais plus lent",
    "Чтение данных GPU процессором": "Relecture des données GPU par le CPU",
    "По умолчанию": "Par défaut",
    "Фоновая загрузка в видеопамять": "Préchargement en arrière-plan dans la VRAM",
    "Меньше рывков при подгрузке зон": "Moins de saccades lors du chargement des zones",
    "Обычная": "Normal",
    "Без лишней видеопамяти": "Pas de VRAM supplémentaire",
    "Полная": "Complet",
    "Около 3 ГБ видеопамяти сверху": "Environ 3 Go de VRAM en plus",
    "Режим работы": "Mode",
    "Новая модель памяти и трансляции": "Nouveau modèle de mémoire et de traduction",
    "Эксперимент, только видеокарты AMD. Видеокарта работает с памятью игры напрямую, как в игре для ПК, а команды графики переводятся, а не эмулируются; возможны ошибки. Выключено — старая модель памяти, как в 0.3, со всеми исправлениями": "Expérimental, GPU AMD uniquement. Le GPU travaille directement avec la mémoire du jeu, comme dans un jeu PC, et les commandes graphiques sont traduites plutôt qu'émulées ; des erreurs sont possibles. Désactivé : l'ancien modèle de mémoire, comme dans la 0.3, avec tous les correctifs",
    "Только для видеокарт AMD, а на этом компьютере её нет. Используется старая модель памяти, как в 0.3, со всеми исправлениями": "GPU AMD uniquement, et cet ordinateur n'en a pas. L'ancien modèle de mémoire est utilisé, comme dans la 0.3, avec tous les correctifs",
    "Синхронизация как в 0.3": "Synchronisation comme dans la 0.3",
    "Для поиска регрессий: старая модель памяти и ожидания копий как в релизе 0.3": "Pour trouver des régressions : l'ancien modèle de mémoire et les attentes de copie tels que publiés dans la 0.3",
    "Выключена": "Désactivé",
    "Выключены": "Désactivé",
    "Для разработчика": "Développeur",
    "Статистика кадров в журнале": "Statistiques d'images dans le journal",
    "Сохранять журнал и статистику в файл": "Enregistrer le journal et les statistiques dans un fichier",
    "Диагностика вылетов": "Diagnostic des plantages",
    "Проверяет кучу игры и записывает записи в её память; немного медленнее": "Vérifie le tas du jeu et journalise les écritures dans sa mémoire ; un peu plus lent",
    "В папку logs в каталоге данных: для разбора рывков и вылетов": "Dans le dossier logs du répertoire de données : pour analyser les saccades et les plantages",
    "Профиль GPU в журнале": "Profil GPU dans le journal",
    "Слои валидации Vulkan": "Couches de validation Vulkan",
    "Сильно замедляет": "Beaucoup plus lent",
    "Доп. переменные (ИМЯ=значение через пробел)": "Variables supplémentaires (NOM=valeur, séparées par des espaces)",
    "Читы": "Triche",
    "Патчи игры версии 1.09, применяются при запуске. Для обычного прохождения и игры по сети оставьте их выключенными": "Correctifs du jeu pour la version 1.09, appliqués au démarrage. Laissez-les désactivés pour une partie normale et le jeu en ligne",
    "Изменения игрового процесса": "Ajustements de gameplay",
    "Бессмертие": "Ne jamais mourir",
    "Урон проходит, но здоровье не опускается ниже 1": "Vous subissez des dégâts mais ne descendez jamais sous 1 PV",
    "Невидимость": "Discrétion",
    "Враги не видят вас и не реагируют, пока вы не атакуете": "Les ennemis ne vous voient pas et ne réagissent pas tant que vous n'attaquez pas",
    "Бесшумность": "Pas silencieux",
    "Враги не слышат вас, но видят": "Les ennemis ne vous entendent pas mais peuvent encore vous voir",
    "Rally не угасает": "Le Rally ne s'estompe jamais",
    "Здоровье для Rally не исчезает со временем": "La santé récupérable avec Rally ne s'estompe pas avec le temps",
    "Управление врагом": "Contrôle des ennemis",
    "R3: управлять целью, L3: вернуться. Не вместе со свободной камерой": "R3 : contrôler l'ennemi ciblé, L3 : revenir. Incompatible avec la caméra libre",
    "Без Rally": "Pas de Rally",
    "Атаки не возвращают здоровье": "Les attaques ne rendent pas de santé",
    "Камера дальше": "Caméra plus éloignée",
    "Камера дальше от персонажа": "La caméra reste plus loin du personnage",
    "Без автоповорота камеры": "Pas de rotation automatique de la caméra",
    "Камера не поворачивается сама при движении; ручное управление и захват цели работают": "La caméra ne tourne pas toute seule quand vous bougez ; la caméra manuelle et le verrouillage de cible fonctionnent toujours",
    "Бег с меньшим наклоном стика": "Course facilitée",
    "Бег примерно с 70% наклона стика вместо 90%": "Courir à partir d'environ 70 % d'inclinaison du stick au lieu de 90 %",
    "Физика тел как в Dark Souls": "Physique ragdoll de Dark Souls",
    "Тела и предметы разлетаются от ударов": "Les cadavres et les objets sont projetés quand on les frappe",
    # Add to Steam
    "Добавить в Steam": "Ajouter à Steam",
    "Игра в библиотеке Steam запускается сразу, с настройками этого лаунчера": "Depuis la bibliothèque Steam, le jeu démarre directement avec les réglages de ce launcher",
    "Добавить": "Ajouter",
    "Steam не найден (или в него ещё никто не входил)": "Steam est introuvable (ou personne ne s'y est encore connecté)",
    "Закройте Steam и нажмите «Добавить» ещё раз": "Fermez Steam et cliquez à nouveau sur Ajouter",
    "Пока игра добавляется, Steam нужно закрыть; потом он запустится снова. Закрыть Steam?": "Steam doit être fermé pendant l'ajout du jeu ; il redémarre ensuite. Fermer Steam ?",
    "Отмена": "Annuler",
    "Закрыть Steam": "Fermer Steam",
    "Steam не закрылся. Закройте его сами и попробуйте ещё раз": "Steam ne s'est pas fermé. Fermez-le vous-même et réessayez",
    "Не удалось добавить игру в Steam: {}": "Impossible d'ajouter le jeu à Steam : {}",
    "Bloodborne добавлен в библиотеку Steam": "Bloodborne a été ajouté à votre bibliothèque Steam",
    # Online page
    "Онлайн": "En ligne",
    "Сообщения, пятна крови и призраки приходят с The Hunter's Dream; колокола и призывы идут через сервер shadNet. Игра по сети совместима с версией для Windows: нужны версия игры 1.09 и тот же сервер": "Les messages, taches de sang et fantômes viennent de The Hunter's Dream ; les cloches et invocations passent par un serveur shadNet. Le jeu en ligne fonctionne avec la version Windows : tout le monde doit avoir la version 1.09 du jeu et le même serveur",
    "Играть онлайн": "Jouer en ligne",
    "Выключено: игра остаётся офлайн, как раньше": "Désactivé : le jeu reste hors ligne, comme avant",
    "Игровой сервер (сообщения, пятна крови, призраки)": "Serveur de jeu (messages, taches de sang, fantômes)",
    "Игровой сервер": "Serveur de jeu",
    "Сервер кооператива (колокола и призывы)": "Serveur coopératif (cloches et invocations)",
    "Учётная запись": "Compte",
    "Имя учётной записи shadNet, не email. Зарегистрируйтесь на shadnet.shadps4.net или спросите владельца частного сервера. Пароль хранится на этом компьютере вместе с настройками лаунчера": "Le nom de votre compte shadNet, pas votre e-mail. Inscrivez-vous sur shadnet.shadps4.net ou demandez à l'administrateur d'un serveur privé. Le mot de passe est enregistré sur cet ordinateur avec les réglages du launcher",
    "Пароль": "Mot de passe",
    "Соединение": "Connexion",
    "У всех в сессии должны быть одна версия игры (1.09) и один сервер. Читы меняют игру и для других игроков: выключайте их при совместной игре": "Tout le monde dans la session doit avoir la même version du jeu (1.09) et le même serveur. Les triches modifient aussi le jeu des autres joueurs : désactivez-les en jouant ensemble",
    "UPnP (открыть порт на роутере автоматически)": "UPnP (ouvrir un port sur le routeur automatiquement)",
    "Выключите при Tailscale или другом VPN": "Désactivez-le avec Tailscale ou un autre VPN",
    "Проверить соединение": "Tester la connexion",
    "Проверить": "Tester",
    "Сервер shadNet": "Serveur shadNet",
    "Проверка…": "Vérification…",
    "доступен": "accessible",
    "недоступен": "inaccessible",
    "Учётная запись для игры онлайн указана, но «Играть онлайн» выключено": "Un compte en ligne est renseigné, mais « Jouer en ligne » est désactivé",
    "Играть офлайн": "Jouer hors ligne",
    "Online ID — это имя учётной записи (NPID), зарегистрированное на сервере, а не адрес email": "L'Online ID est le nom du compte (NPID) enregistré sur le serveur, pas votre adresse e-mail",
    # DLSS
    "Нужны видеокарта NVIDIA RTX и проприетарный драйвер; иначе используется FSR 3.1": "Nécessite une carte NVIDIA RTX et le pilote propriétaire ; sinon FSR 3.1 est utilisé",
    "Нет файлов DLSS: tools/build_dlss.sh": "Fichiers DLSS absents : tools/build_dlss.sh",
    # Discord
    "Статус в Discord": "Statut Discord",
    "«Играет в Bloodborne» в профиле Discord, онлайн или офлайн": "« Joue à Bloodborne » sur votre profil Discord, en ligne ou hors ligne",
    # Button prompts (scripts/menu_prompts.py)
    "Применяется при запуске игры": "S'applique au lancement du jeu",
    "Иконки кнопок": "Icônes des boutons",
    "Поменять местами A и B": "Inverser A et B",
    "Для контроллеров в стиле Nintendo: подтверждение на A, отмена на B. Применяется при запуске игры": "Pour les manettes de type Nintendo : valider avec A, retour avec B. Appliqué au lancement du jeu",
    "Автоматически (по контроллеру)": "Automatique (selon la manette)",
    'PlayStation (оригинал)': "PlayStation (d'origine)",
    "Меню жестов без значков управления движением": "Menu des gestes sans icônes de détection de mouvement",
    # Add to Steam with Flathub's Steam
    'Steam из Flatpak запускает игры в своей песочнице, где нет ни папки игры, ни драйверов: ярлык должен запускать игру вне её (flatpak-spawn --host). Для этого Steam нужно право org.freedesktop.Flatpak, с которым он может запускать программы в вашей системе. Выдать его?':
        "Steam en Flatpak lance les jeux dans son bac à sable, qui n'a ni le dossier du jeu ni les pilotes : le raccourci doit lancer le jeu en dehors (flatpak-spawn --host). Pour cela, Steam a besoin de l'autorisation org.freedesktop.Flatpak, qui lui permet de lancer des programmes sur votre système. L'accorder ?",
    'Выдать право':
        "Accorder l'autorisation",
    'Не удалось выдать право Steam: {}':
        "Impossible d'accorder l'autorisation à Steam : {}",
    "Копировать":
        "Copier",
    "Экспорт журнала…":
        "Exporter le journal…",
    "Экспорт журнала":
        "Exporter le journal",
    "Журнал скопирован":
        "Journal copié",
    "Журнал сохранён: {}":
        "Journal enregistré : {}",
    "Не удалось сохранить журнал: {}":
        "Impossible d'enregistrer le journal : {}",
    "Монитор":
        "Écran",
    "Пропускать выбор «по сети / вне сети»":
        "Passer le choix « jouer en ligne / hors ligne »",
    "Игра сразу открывает главное меню в режиме вне сети (патч игры)":
        "Le jeu ouvre directement le menu principal hors ligne (un patch du jeu)",
    "Основной":
        "Principal",
    ", основной":
        ", principal",
    "Файлы игры повреждены при распаковке: шейдеры не распаковываются, игра зависнет на загрузке. Распакуйте игру и обновление 1.09 заново исправленным инструментом (issue #81)":
        "Les fichiers du jeu ont été endommagés à l'extraction : les shaders ne se décompressent pas et le jeu se bloquerait au chargement. Extrayez à nouveau le jeu et la mise à jour 1.09 avec un outil corrigé (issue #81)",
    "Нужна папка adhoc из мода Nexus #253 (шрифты adhoc/font) — в dvdroot_ps4 игры или модом; без неё патч не применяется":
        "Nécessite le dossier adhoc du mod Nexus #253 (polices dans adhoc/font), dans dvdroot_ps4 du jeu ou en tant que mod ; sans lui, le patch n'est pas appliqué",
    "Новая: видеокарта работает с памятью игры напрямую, как в игре для ПК, а команды графики переводятся, а не эмулируются. Старая — модель памяти 0.3 со всеми исправлениями. Если драйвер не проходит проверку при запуске — старая":
        "Le nouveau : la carte graphique travaille directement avec la mémoire du jeu, comme dans un jeu PC, et les commandes graphiques sont traduites au lieu d'être émulées. L'ancien : le modèle mémoire de la 0.3 avec toutes les corrections. Si le pilote échoue à la vérification au démarrage, l'ancien",
    "Модель памяти и трансляции":
        "Modèle de mémoire et de traduction",
    "Авто: новая на AMD, старая на других":
        "Auto : nouveau sur AMD, ancien sur les autres",
    "Новая":
        "Nouveau",
    "Старая (как в 0.3)":
        "Ancien (comme dans la 0.3)",
    "Регион игры":
        "Région du jeu",
    "Вариант текста у языков с региональными версиями: испанский Испании (Европа) или Латинской Америки (Америка)":
        "La variante du texte des langues qui en ont une : espagnol d'Espagne (Europe) ou d'Amérique latine (Amériques)",
    "Как в дампе игры":
        "Comme dans le dump du jeu",
    "Европа":
        "Europe",
    "Америка":
        "Amériques",
    "Включён брандмауэр: {}":
        "Pare-feu actif : {}",
    "Для UPnP нужны ответы роутера: {}":
        "L'UPnP a besoin des réponses du routeur : {}",
    "О программе":
        "À propos",
    "Версия {}":
        "Version {}",
    "Обновления":
        "Mises à jour",
    "Проверять обновления при запуске":
        "Rechercher les mises à jour au démarrage",
    "Спрашивает GitHub о последнем выпуске; ничего не скачивается без вашего согласия":
        "Demande à GitHub la dernière version publiée ; rien n'est téléchargé sans votre accord",
    "Последняя версия":
        "Dernière version",
    "Загрузка…":
        "Téléchargement…",
    "Обновить":
        "Mettre à jour",
    "Версия {} установлена: перезапустите лаунчер":
        "Version {} installée : redémarrez le launcher",
    "Перезапустить":
        "Redémarrer",
    "Не удалось проверить: {}":
        "Vérification impossible : {}",
    "Установлена версия {}":
        "Version {} installée",
    "Установлена последняя версия ({})":
        "Vous avez la dernière version ({})",
    "Доступна версия {} (установлена {})":
        "La version {} est sortie (vous avez la {})",
    "Открыть страницу":
        "Ouvrir la page",
    "Доступна версия {}":
        "La version {} est sortie",
    "Подробнее":
        "Détails",
    "Загрузка… {} %":
        "Téléchargement… {} %",
    "Загрузка… {} МБ":
        "Téléchargement… {} Mo",
    "Не удалось обновить: {}":
        "Mise à jour impossible : {}",
    "Сначала закройте игру":
        "Fermez d'abord le jeu",
    "Этот проект":
        "Ce projet",
    "Основано на bbport от deadinside28":
        "Basé sur bbport de deadinside28",
    "Порт для Windows от Supermedo":
        "Portage Windows de Supermedo",
    "Лицензия":
        "Licence",
    'GNU GPL v2 или новее · Файлы игры не входят.': 'GNU GPL v2 ou ultérieure · Aucun fichier du jeu inclus.',
    'Bloodborne принадлежит Sony Interactive Entertainment и FromSoftware.': 'Bloodborne appartient à Sony Interactive Entertainment et FromSoftware.',
    "Проверить сейчас":
        "Vérifier maintenant",
    # 0.51: mouse look, choosing NVIDIA's DLSS library, the online module
    'DLSS {}: готово':
        'DLSS {} : prêt',
    'DLSS найден (нужна видеокарта NVIDIA RTX)':
        'DLSS trouvé (nécessite un GPU NVIDIA RTX)',
    'DLSS не найден: выберите библиотеку NVIDIA ниже (и нужна сборка с мостом DLSS). Игра включит FSR 3.1':
        'DLSS introuvable : choisissez la bibliothèque NVIDIA ci-dessous (une version avec le pont DLSS est aussi nécessaire). Le jeu utilisera FSR 3.1',
    'DLSS: библиотека NVIDIA':
        'DLSS : bibliothèque NVIDIA',
    '{} — библиотека DLSS для Windows; на Linux NVIDIA её не загружает. Нужна libnvidia-ngx-dlss.so.<версия> из DLSS SDK NVIDIA: {}':
        '{} est la bibliothèque DLSS pour Windows ; le pilote NVIDIA pour Linux ne la charge pas. Il faut libnvidia-ngx-dlss.so.<version> du DLSS SDK de NVIDIA : {}',
    'Библиотека DLSS NVIDIA (libnvidia-ngx-dlss.so.*)':
        'Bibliothèque DLSS de NVIDIA (libnvidia-ngx-dlss.so.*)',
    'Выбрать файл…':
        'Choisir un fichier…',
    'Из сборки: {}':
        'De cette version : {}',
    'Инвертировать мышь по вертикали':
        "Inverser l'axe Y de la souris",
    'Камера мышью':
        'Caméra à la souris',
    'Клавиатура и мышь':
        'Clavier et souris',
    'Не удалось прочитать файл':
        'Impossible de lire le fichier',
    'Не удалось скопировать библиотеку':
        'Impossible de copier la bibliothèque',
    'Нет: выберите libnvidia-ngx-dlss.so.* из DLSS SDK NVIDIA ({})':
        'Aucune : choisissez libnvidia-ngx-dlss.so.* du DLSS SDK de NVIDIA ({})',
    'Нужен файл libnvidia-ngx-dlss.so.<версия> из DLSS SDK NVIDIA: {}':
        'Il faut libnvidia-ngx-dlss.so.<version> du DLSS SDK de NVIDIA : {}',
    'Нужна библиотека для Linux':
        'Une bibliothèque pour Linux est nécessaire',
    'Своя: {}':
        'La vôtre : {}',
    'Убрать выбранную':
        'Retirer celle choisie',
    'Чувствительность мыши':
        'Sensibilité de la souris',
    'Щелчок в окне игры захватывает мышь, F1 — отпускает':
        'Un clic dans la fenêtre du jeu capture la souris, F1 la libère',
    'Эта сборка без модуля онлайна (libbbnet.so): игра только офлайн':
        "Cette version n'a pas le module en ligne (libbbnet.so) : jeu hors ligne uniquement",
    'Эта сборка без моста DLSS (libbbport_dlss.so): DLSS работать не будет':
        "Cette version n'a pas le pont DLSS (libbbport_dlss.so) : DLSS ne fonctionnera pas",
    'Это не библиотека DLSS':
        "Ce n'est pas la bibliothèque DLSS",
    # Online page: your own shadNet server, the co-op port, seamless co-op, the UDP test
    '0: случайный при каждом запуске. Закрепите его, чтобы открыть в брандмауэре или на роутере вручную':
        '0 : un port aléatoire à chaque fois. Fixez-le pour l’ouvrir dans le pare-feu ou à la main sur le routeur',
    'UDP сервера shadNet (призывы)':
        'UDP du serveur shadNet (invocations)',
    'UPnP открывает порт только на роутере; брандмауэр этого компьютера всё равно блокирует кооператив. Откройте порт: {}':
        'UPnP n’ouvre le port que sur le routeur ; le pare-feu de cet ordinateur bloque quand même la coopération. Ouvrez le port : {}',
    'Адрес WebAPI (пусто: порт 31315 сервера)':
        'Adresse WebAPI (vide : le port 31315 du serveur)',
    'Адрес сервера (host:port)':
        'Adresse du serveur (hôte:port)',
    'Бесшовный кооператив (экспериментально)':
        'Coopération seamless (expérimental)',
    'Закрепите порт кооператива выше (например, {}): случайный порт в брандмауэре не открыть':
        'Fixez le port de coopération ci-dessus (par exemple {}) : un port aléatoire ne peut pas être ouvert dans un pare-feu',
    'Как запустить свой сервер':
        'Héberger votre propre serveur',
    'Порт кооператива (UDP)':
        'Port de coopération (UDP)',
    'Призывы между разными локациями. Только если на сервере BloodborneSeamlessCoop=true, и у всех игроков так же':
        'Invocations entre zones différentes. Seulement si le serveur a BloodborneSeamlessCoop=true et que tous les joueurs l’activent',
    'Публичный сервер shadPS4':
        'Serveur public de shadPS4',
    'Свой сервер':
        'Votre propre serveur',
    'shadnet-p2p: на вашем ПК или VPS':
        'shadnet-p2p : sur votre PC ou un VPS',
    'Сервер shadNet':
        'Serveur shadNet',
    'не отвечает: призывы не соединятся':
        'pas de réponse : les invocations ne se connecteront pas',
    'отвечает; ваш публичный адрес: {}':
        'répond ; votre adresse publique : {}',
    "Поддержать проект": 'Soutenir ce projet',
    # Trophies page
    'В дампе игры нет трофеев (sce_sys/trophy)':
        'Le dump du jeu n’a pas de trophées (sce_sys/trophy)',
    'Записываются, когда игра их открывает, и показываются в игре':
        'Enregistrés quand le jeu les débloque, et affichés dans le jeu',
    'Ключ трофеев':
        'Clé des trophées',
    'Ключ трофеев PS4 (TrophyKey в shadPS4), 32 шестнадцатеричных символа: с ним названия и описания на языке игры. Хранится на этом компьютере. Без него они на английском':
        'La clé des trophées PS4 (TrophyKey dans shadPS4), 32 chiffres hexadécimaux : avec elle, les noms et descriptions sont dans la langue du jeu. Conservée sur cet ordinateur. Sans elle, ils sont en anglais',
    'Неверный ключ трофеев: названия недоступны':
        'Clé des trophées incorrecte : les noms ne sont pas disponibles',
    'Получен {}':
        'Obtenu le {}',
    'Получено {} из {}':
        '{} sur {} obtenus',
    'Скрытый трофей':
        'Trophée caché',
    'Трофеи':
        'Trophées',
    'Платиновый':
        'Platine',
    'Золотой':
        'Or',
    'Серебряный':
        'Argent',
    'Бронзовый':
        'Bronze',
    "Вход в shadNet": "Connexion à shadNet",
    "неверное имя или пароль": "nom ou mot de passe incorrect",
    "такой учётной записи нет на этом сервере": "ce compte n'existe pas sur ce serveur",
    "эта учётная запись уже в сети (игра запущена?)": "ce compte est déjà connecté (le jeu est-il lancé ?)",
    "вход выполнен": "connecté",
    "вход не удался ({})": "échec de la connexion ({})",
    "Загрузки и плавность": "Chargements et fluidité",
    "Патчи игры из bbhost, применяются при запуске": "Patchs du jeu issus de bbhost, appliqués au démarrage",
    "Быстрая загрузка после смерти": "Chargement rapide après la mort",
    "Загрузка после смерти или перемещения у лампы идёт, пока грузится область (2–3 с), а не минимум 12 с": "Le chargement après une mort ou un voyage par lanterne dure le temps de charger la zone (2–3 s), pas 12 s minimum",
    "Без рывка каждые ~50 с": "Plus de saccade toutes les ~50 s",
    "Игра быстрее сжимает запись игрока: пропадает рывок ~23 мс примерно каждые 50 с": "Le jeu compresse plus vite l'enregistrement du joueur : une saccade de ~23 ms toutes les 50 s environ disparaît",
    "Третий поток подготовки ресурсов": "Troisième thread de préparation des ressources",
    "Во время игры работают три потока подготовки ресурсов, а не два. Экспериментально": "En jeu, trois threads de préparation des ressources tournent, et non deux. Expérimental",
    # About: Thanks
    'Благодарности': 'Remerciements',
    'Без них ничего этого не было бы': 'Sans eux, rien de tout cela ne serait possible',
    'Порт и его код': 'Le port et son code',
    'Помощь и тесты': 'Aide et tests',
    'Другие благодарности': 'Merci aussi à',
    'bbport — порт, на котором построен весь этот проект': 'bbport, le port sur lequel repose tout ce projet',
    'Игра по сети, DLSS, страница читов, добавление в Steam, значок и пропуск конвейеров, которые драйвер не может создать': 'Jeu en ligne, DLSS, la page des triches, Ajouter à Steam, l’icône et ignorer les pipelines que le pilote ne peut pas créer',
    'Собрал и адаптировал десятки исправлений: вылеты при загрузке, чёрные изображения, апскейлер, строка производительности в журнале': 'A rassemblé et adapté des dizaines de correctifs : plantages au chargement, images noires, l’upscaler, la ligne de performances du journal',
    'Чёрный предпросмотр персонажа, картинка экрана загрузки и память кэша текстур': 'L’aperçu noir du personnage, l’image de l’écran de chargement et la mémoire du cache de textures',
    'Кэш текстур вовремя освобождает видеопамять': 'Le cache de textures libère la mémoire vidéo à temps',
    'Вылеты при загрузке областей': 'Plantages au chargement des zones',
    'Интерфейс, пропадавший не в 1080p, векторы движения больших чудовищ и ошибка памяти': 'L’interface qui disparaissait hors 1080p, les vecteurs de mouvement des grandes bêtes et une erreur mémoire',
    'Вылеты при загрузке некоторых карт и меню жестов с клавиатуры': 'Plantages au chargement de certaines cartes et le menu des gestes au clavier',
    'Экранная клавиатура для имени персонажа и уведомление о компиляции шейдеров': 'Le clavier à l’écran pour le nom du personnage et l’avis de compilation des shaders',
    "Быстрая загрузка после смерти и перемещения (bbhost) и сервер The Hunter's Dream": "Chargements rapides après une mort ou un voyage (bbhost) et le serveur The Hunter's Dream",
    'Сетевые библиотеки игры по сети и сервер для своего кооператива': 'Les bibliothèques du jeu en ligne et le serveur pour votre propre coopération',
    'Основа поддержки DLSS и модель FSR 4 без шлейфов за персонажами': 'La base de la prise en charge de DLSS et le modèle FSR 4 sans traînées derrière les personnages',
    'Апскейлер FSR 3.1': 'L’upscaler FSR 3.1',
    'Игра запускается, когда DLSS нельзя использовать': 'Le jeu démarre quand DLSS ne peut pas être utilisé',
    'Перевод на упрощённый китайский': 'La traduction en chinois simplifié',
    'Звук игры на полной громкости': 'Le son du jeu à plein volume',
    'Флажки и ползунки внутриигрового меню': 'Les cases et les curseurs du menu en jeu',
    'Подробные отчёты с журналами и проверка исправлений': 'Rapports détaillés avec journaux et tests des correctifs',
    'Идея поменять местами A и B на контроллерах в стиле Nintendo': 'L’idée d’inverser A et B sur les manettes de style Nintendo',
    'Проверка исправления видеопамяти': 'Test du correctif de la mémoire vidéo',
    'Иконки кнопок Xbox и Switch (Nexus Mods)': 'Icônes de boutons Xbox et Switch (Nexus Mods)',
    'Показал, какие текстуры нужны иконкам клавиатуры (Nexus Mods)': 'A montré quelles textures il faut aux icônes clavier (Nexus Mods)',
    'Патчи игры: высокий FPS, разрешение и другое': 'Patchs du jeu : FPS élevés, résolution et plus',
    'Рендерер и компилятор шейдеров': 'Le moteur de rendu et le recompilateur de shaders',
    'Инструмент для сборки AppImage': 'L’outil qui crée l’AppImage',
    'Нашёл ошибку, из-за которой игра не запускалась на некоторых видеокартах': 'A trouvé le bug qui empêchait le jeu de démarrer sur certaines cartes graphiques',
    # Shader cache
    'Кэш шейдеров': 'Cache des shaders',
    'Очистить': 'Vider',
    '{}. Если после обновления картинка выглядит странно, очистите его: шейдеры соберутся заново (первые минуты в каждой зоне возможны рывки)': '{}. Si l’image semble étrange après une mise à jour, videz-le : les shaders sont reconstruits (quelques saccades les premières minutes dans chaque zone)',
    'Пусто: шейдеры соберутся при игре': 'Vide : les shaders sont construits pendant que vous jouez',
    'Очистить кэш шейдеров?': 'Vider le cache des shaders ?',
    'Игра соберёт шейдеры заново: первые минуты в каждой зоне возможны рывки. Сохранения и настройки не затрагиваются.': 'Le jeu reconstruit les shaders : quelques saccades les premières minutes dans chaque zone. Les sauvegardes et les réglages ne sont pas touchés.',
    'Названия трофеев на английском без ключа и звук при получении трофея': 'Les noms des trophées en anglais sans la clé et le son à l’obtention d’un trophée',
    'Буфер трафарета, в который писали цветные изображения': 'Le tampon de stencil dans lequel écrivaient des images couleur',
    'Вход на публичный сервер shadNet без отключения': 'Rester connecté au serveur public shadNet',
    'Игра по сети': 'Jeu en ligne',
    'Сервер shadNet не принимает bbport, игра осталась офлайн. Для игры по сети используйте свой сервер (страница «Онлайн»).': 'Le serveur shadNet n’accepte pas bbport, le jeu est donc resté hors ligne. Pour jouer en ligne, utilisez votre propre serveur (page En ligne).',
    'Выход из игры из меню с контроллера и меню в пределах экрана': 'Quitter le jeu depuis le menu à la manette et le menu qui tient dans l’écran',
    'Вылет видеоплеера при его остановке': 'Un plantage du lecteur vidéo à son arrêt',
    'Язык внутриигрового меню при запуске без окна лаунчера': 'La langue du menu en jeu au lancement sans la fenêtre du launcher',
    'DLSS в AppImage на NVIDIA': 'DLSS dans l’AppImage sur NVIDIA',
    'Сверхширокие мониторы без растянутой картинки': 'Les écrans ultra-larges sans image étirée',
}


# German.
DE = {
    "Папка DLC": "DLC-Ordner",
    "Выбрать папку DLC": "DLC-Ordner wählen",
    "Не использовать DLC": "Keine DLC verwenden",
    "Найдено DLC: {}": "Gefundene DLC: {}",
    "Не используется": "Nicht verwendet",
    "Нет DLC этой игры в папке": "Keine DLC dieses Spiels im Ordner",
    "Запустить": "Spielen",
    "Остановить": "Stoppen",
    "Настройки": "Einstellungen",
    "Журнал": "Protokoll",
    "Не удалось запустить: {}": "Start fehlgeschlagen: {}",
    "\n— игра завершилась (код {}) —\n": "\n— das Spiel wurde beendet (Code {}) —\n",
    "Язык лаунчера": "Sprache des Launchers",
    "Как в системе": "System",
    "Применится после перезапуска лаунчера, пока игра запущена": "Wird nach einem Neustart des Launchers übernommen, sobald das Spiel läuft",
    "Игра": "Spiel",
    "Папка игры ({})": "Spielordner ({})",
    "Папка игры": "Spielordner",
    "Выбрать папку с eboot.bin": "Ordner mit eboot.bin auswählen",
    "Открыть в файловом менеджере": "Im Dateimanager öffnen",
    "Папка сохранений": "Ordner für Spielstände",
    "Выбрать папку сохранений": "Ordner für Spielstände auswählen",
    "Вернуть папку по умолчанию": "Zurück zum Standardordner",
    "Язык системы": "Systemsprache",
    "По умолчанию: {}": "Standard: {}",
    "Найдены сохранения": "Spielstände gefunden",
    "Сохранений пока нет: игра создаст их здесь": "Noch keine Spielstände: Das Spiel legt sie hier an",
    "не выбрана": "nicht ausgewählt",
    "Найден eboot.bin": "eboot.bin gefunden",
    "Нет eboot.bin в папке": "Keine eboot.bin im Ordner",
    "Управление": "Steuerung",
    "Клавиатура": "Tastatur",
    "Геймпад": "Gamepad",
    "Назначение кнопок; применяется при запуске игры": "Tastenbelegung; wird beim Spielstart übernommen",
    "Назначить": "Zuweisen",
    "Сбросить": "Zurücksetzen",
    "{} (по умолчанию)": "{} (Standard)",
    "не назначено": "nicht zugewiesen",
    "Нажмите клавишу или кнопку… (Esc — отмена)": "Drücke eine Taste oder einen Knopf … (Esc bricht ab)",
    "Крест": "Kreuz",
    "Круг": "Kreis",
    "Квадрат": "Quadrat",
    "Треугольник": "Dreieck",
    "Тачпад, левая половина (жесты)": "Touchpad, linke Hälfte (Gesten)",
    "Тачпад, правая половина (личные вещи)": "Touchpad, rechte Hälfte (Schlüsselgegenstände)",
    "Крестовина вверх": "Steuerkreuz oben",
    "Крестовина вниз": "Steuerkreuz unten",
    "Крестовина влево": "Steuerkreuz links",
    "Крестовина вправо": "Steuerkreuz rechts",
    "Движение вперёд": "Vorwärts bewegen",
    "Движение назад": "Rückwärts bewegen",
    "Движение влево": "Nach links bewegen",
    "Движение вправо": "Nach rechts bewegen",
    "Камера вверх": "Kamera nach oben",
    "Камера вниз": "Kamera nach unten",
    "Камера влево": "Kamera nach links",
    "Камера вправо": "Kamera nach rechts",
    "Контроллер": "Controller",
    "Выбранный берётся, как только подключится": "Der ausgewählte Controller wird verwendet, sobald er verbunden ist",
    "Первый подключённый": "Zuerst verbundener",
    "{} (не подключён)": "{} (nicht verbunden)",
    "Нужно обновление 1.09: скопируйте файлы дампа обновления 1.09 в папку игры с заменой (найдена версия {})": "Das Update 1.09 wird benötigt: Kopiere das extrahierte Update 1.09 in den Spielordner und ersetze dabei die Dateien (gefundene Version {})",
    "eboot.bin не от версии 1.09: скопируйте eboot.bin из дампа обновления 1.09 в папку игры с заменой": "Die eboot.bin ist nicht von 1.09: Kopiere die eboot.bin aus dem extrahierten Update 1.09 in den Spielordner und ersetze sie",
    "eboot.bin с вшитым патчем 60 FPS от Lance McDonald: из-за него игра падает в меню жестов. Скопируйте чистый eboot.bin из дампа обновления 1.09 в папку игры с заменой": "Diese eboot.bin enthält den 60-FPS-Patch von Lance McDonald, durch den das Spiel im Gestenmenü abstürzt: Kopiere eine saubere eboot.bin aus dem extrahierten Update 1.09 in den Spielordner und ersetze sie",
    "Это не магазинное издание Bloodborne (найдено {}): нужен Bloodborne любого региона с обновлением 1.09": "Keine Verkaufsversion von Bloodborne (gefunden: {}): Bloodborne aus beliebiger Region mit Update 1.09 wird benötigt",
    "eboot.bin не читается как расшифрованный исполняемый файл PS4: сделайте дамп заново": "Die eboot.bin lässt sich nicht als entschlüsselte PS4-Programmdatei lesen: Erstelle den Dump des Spiels erneut",
    "Bloodborne {}, версия 1.09": "Bloodborne {}, Version 1.09",
    "Папка игры (с eboot.bin)": "Spielordner (mit eboot.bin)",
    "Английский": "Englisch",
    "Русский": "Russisch",
    "Японский": "Japanisch",
    "Французский": "Französisch",
    "Испанский": "Spanisch",
    "Немецкий": "Deutsch",
    "Итальянский": "Italienisch",
    "Моды": "Mods",
    "Распакуйте каждый мод в отдельную папку (с dvdroot_ps4 или сразу с chr/, parts/ и т. п.). При совпадении файлов побеждает мод ниже в списке. Применяется при запуске.": "Entpacke jede Mod in einen eigenen Ordner (mit dvdroot_ps4 oder direkt mit chr/, parts/ usw.). Bei Dateikonflikten gewinnt die Mod weiter unten in der Liste. Wird beim Start angewendet.",
    "Загружать моды": "Mods laden",
    "Папка модов": "Mods-Ordner",
    "Выбрать папку модов": "Mods-Ordner auswählen",
    "Открыть папку модов": "Mods-Ordner öffnen",
    "Обновить список": "Liste aktualisieren",
    "Загрузить раньше": "Früher laden",
    "Загрузить позже": "Später laden",
    "Модов нет": "Keine Mods",
    "Сторонние патчи": "Patches von Drittanbietern",
    "XML-патчи в формате shadPS4 для версии 01.09 из папки патчей. Применяются при запуске.": "XML-Patches im shadPS4-Format für Version 01.09 aus dem Patches-Ordner. Werden beim Start angewendet.",
    "Папка патчей": "Patches-Ordner",
    "Выбрать папку патчей": "Patches-Ordner auswählen",
    "Открыть папку патчей": "Patches-Ordner öffnen",
    "Патчей нет": "Keine Patches",
    "Автор: {}": "Autor: {}",
    "Экран": "Anzeige",
    "Разрешение вывода": "Ausgabeauflösung",
    "Апскейлер дорисовывает кадр; Steam Deck — 720p": "Der Upscaler füllt das Bild aus; Steam Deck: 720p",
    "Полноэкранный режим": "Vollbild",
    "Смена разрешения на лету": "Auflösungswechsel im laufenden Betrieb",
    "Без перезапуска, но медленнее на Steam Deck и старых GPU": "Kein Neustart nötig, aber langsamer auf dem Steam Deck und älteren GPUs",
    "Авто (по видеокарте)": "Auto (je nach GPU)",
    "Выключена (быстрее)": "Aus (schneller)",
    "Включена": "An",
    "Режим показа кадров": "Präsentationsmodus",
    "Разрешить HDR": "HDR zulassen",
    "Апскейлер": "Upscaler",
    "Хранится в bbport.ini; в игре меняется через меню (Insert или L3+R3)": "Wird in bbport.ini gespeichert; im Spiel änderst du es im Menü (Insert oder L3+R3)",
    "TAA (нативное сглаживание)": "TAA (native Kantenglättung)",
    "Выключен": "Aus",
    "Пресет": "Voreinstellung",
    "Резкость (RCAS)": "Schärfen (RCAS)",
    "Сила резкости": "Schärfe",
    "Векторы движения объектов": "Bewegungsvektoren von Objekten",
    "Меньше гостинга на персонажах; стоит около 10% FPS": "Weniger Geisterbilder bei Figuren; kostet etwa 10 % FPS",
    "Показывать FPS": "FPS anzeigen",
    "Ассеты найдены": "Assets gefunden",
    "Нет ассетов: tools/fetch_fsr4_assets.sh": "Keine Assets: tools/fetch_fsr4_assets.sh",
    "Ассеты для выбранного режима найдены": "Assets für den gewählten Modus gefunden",
    "{}. Соберите FSR 4.1.1 из своей DLL кнопкой «Выбрать DLL…» ниже": "{}. Erstelle FSR 4.1.1 aus deiner eigenen DLL über die Schaltfläche „DLL auswählen …“ unten",
    "FSR 4.1.1 из своей DLL AMD": "FSR 4.1.1 aus deiner eigenen AMD-DLL",
    "Отменить": "Abbrechen",
    "Выбрать DLL…": "DLL auswählen …",
    "DLL апскейлера AMD (amd_fidelityfx_upscaler_dx12.dll)": "AMD-Upscaler-DLL (amd_fidelityfx_upscaler_dx12.dll)",
    "нет": "keine",
    "Эта DLL не подходит": "Diese DLL passt nicht",
    "{}: версия {}, модели FSR 4: {}.\n\nbbport повторяет только официальную FSR 4.1.x от AMD (модель v07_fp8_no_scale): например, FSR4_LATEST из OptiScaler или amd_fidelityfx_upscaler_dx12.dll из игры с FSR 4.1. Сборки сообщества (4.0.2b и подобные) устроены иначе и пока не поддерживаются.": "{}: Version {}, FSR-4-Modelle: {}.\n\nbbport gibt nur das offizielle AMD FSR 4.1.x wieder (Modell v07_fp8_no_scale): zum Beispiel FSR4_LATEST von OptiScaler oder amd_fidelityfx_upscaler_dx12.dll aus einem Spiel mit FSR 4.1. Community-Builds (4.0.2b und ähnliche) sind anders aufgebaut und werden noch nicht unterstützt.",
    "Загрузчик не подходит": "Der Loader passt nicht",
    "Загрузчик FidelityFX (amd_fidelityfx_loader_dx12.dll или amd_fidelityfx_dx12.dll)": "FidelityFX-Loader (amd_fidelityfx_loader_dx12.dll oder amd_fidelityfx_dx12.dll)",
    "\n— сборка FSR 4.1.1 из {} —\n": "\n— FSR 4.1.1 wird aus {} erstellt —\n",
    "Подготовка…": "Wird vorbereitet …",
    "Запись проходов DLL под Proton: {} из {}": "Die Durchläufe der DLL werden unter Proton aufgezeichnet: {} von {}",
    "Перевод проходов в SPIR-V…": "Durchläufe werden in SPIR-V übersetzt …",
    "— сборка FSR 4.1.1 завершилась (код {}) —\n": "— Erstellung von FSR 4.1.1 beendet (Code {}) —\n",
    "FSR 4.1.1 собран и выбран": "FSR 4.1.1 erstellt und ausgewählt",
    "Сборка FSR 4.1.1 отменена": "Erstellung von FSR 4.1.1 abgebrochen",
    "FSR 4.1.1 не собран": "FSR 4.1.1 wurde nicht erstellt",
    "DLL не подходит: подробности в журнале": "Die DLL passt nicht: Details im Protokoll",
    "Не хватает программ для сборки: список в журнале": "Werkzeuge für die Erstellung fehlen: Die Liste steht im Protokoll",
    "Записанные проходы не совпали с тем, что повторяет bbport (другая версия DLL или новая видеокарта?): подробности в журнале": "Die aufgezeichneten Durchläufe passen nicht zu dem, was bbport wiedergibt (andere DLL-Version oder neue GPU?): Details im Protokoll",
    "Не найден загрузчик FidelityFX 2.x": "Kein FidelityFX-Loader 2.x gefunden",
    "Не найден подходящий Proton: установите GE-Proton 10 или новее (ProtonUp-Qt) или Proton Experimental / Proton-CachyOS в Steam. Если они есть — запустите в Steam любую игру с этим Proton, чтобы Steam поставил его рантайм": "Kein passendes Proton gefunden: Installiere GE-Proton 10 oder neuer (ProtonUp-Qt) oder Proton Experimental / Proton-CachyOS in Steam. Wenn du sie hast, starte ein beliebiges Spiel mit diesem Proton in Steam, damit Steam dessen Runtime installiert",
    "Ни один Proton не запустил FSR 4.1 из этой DLL. Либо они слишком старые (подходят GE-Proton 10+, Proton Experimental, Proton-CachyOS 11), либо DLL не включает FSR 4.1 на этой видеокарте (Steam Deck?): тогда соберите на ПК с Radeon RX 7000/9000 и скопируйте папку fsr4_411. Подробности в журнале": "Kein Proton hat FSR 4.1 dieser DLL gestartet. Entweder sind sie zu alt (GE-Proton 10+, Proton Experimental und Proton-CachyOS 11 funktionieren), oder die DLL aktiviert FSR 4.1 auf dieser GPU nicht (Steam Deck?): Erstelle es dann auf einem PC mit Radeon RX 7000/9000 und kopiere den Ordner fsr4_411. Details im Protokoll",
    "На NixOS запись идёт на самой системе (systemd --user) через umu-launcher из nix-shell, а здесь их не нашлось: установите umu-launcher или Nix. Подробности в журнале": "Unter NixOS läuft die Aufzeichnung direkt auf dem System (systemd --user) mit umu-launcher aus nix-shell, und keines von beiden wurde gefunden: Installiere umu-launcher oder Nix. Details im Protokoll",
    "{}: FSR {}. Это официальная FSR 4.0.x от AMD: она включается только на видеокартах RDNA4 (RX 9000), а под Proton на других видеокартах не запускается, поэтому записать её нельзя.\n\nНужна FSR 4.1.x: например, FSR4_LATEST из OptiScaler или DLL из игры с FSR 4.1.": "{}: FSR {}. Das ist das offizielle AMD FSR 4.0.x: Es ist nur auf RDNA4-GPUs (RX 9000) aktiviert und startet unter Proton auf anderen GPUs nicht, daher lässt es sich nicht aufzeichnen.\n\nBenötigt wird FSR 4.1.x: zum Beispiel FSR4_LATEST von OptiScaler oder die DLL eines Spiels mit FSR 4.1.",
    "{}: в этой DLL нет FSR 4. Нужна amd_fidelityfx_upscaler_dx12.dll версии 4.1.x.": "{}: Diese DLL enthält kein FSR 4. Benötigt wird amd_fidelityfx_upscaler_dx12.dll in Version 4.1.x.",
    "Это не загрузчик": "Das ist nicht der Loader",
    "{} — это DLL апскейлера. Загрузчик называется amd_fidelityfx_loader_dx12.dll (у OptiScaler — amd_fidelityfx_dx12.dll) и лежит в той же папке игры, что и DLL апскейлера.": "{} ist die Upscaler-DLL. Der Loader heißt amd_fidelityfx_loader_dx12.dll (bei OptiScaler amd_fidelityfx_dx12.dll) und liegt im selben Spielordner wie die Upscaler-DLL.",
    "{}: версия {}. Нужен загрузчик FidelityFX 2.x — из той же игры, что и DLL апскейлера.": "{}: Version {}. Benötigt wird ein FidelityFX-Loader 2.x aus demselben Spiel wie die Upscaler-DLL.",
    "Рядом с DLL нет загрузчика: выберите amd_fidelityfx_loader_dx12.dll из папки игры": "Kein Loader neben der DLL: Wähle amd_fidelityfx_loader_dx12.dll aus dem Ordner des Spiels",
    "Собрать FSR 4.1.1 из amd_fidelityfx_upscaler_dx12.dll 4.1.x (OptiScaler: папка FSR4_LATEST, или из игры с FSR 4.1). Нужен GE-Proton 10+, Proton Experimental или Proton-CachyOS; 2–5 минут (RDNA4: вдвое дольше, ещё и вариант FP8)": "Erstellt FSR 4.1.1 aus amd_fidelityfx_upscaler_dx12.dll 4.1.x (OptiScaler: der Ordner FSR4_LATEST, oder aus einem Spiel mit FSR 4.1). Benötigt GE-Proton 10+, Proton Experimental oder Proton-CachyOS; 2–5 Minuten (RDNA4: doppelt so lange, mit der FP8-Variante)",
    "Сборка не удалась (код {}): подробности в журнале": "Die Erstellung ist fehlgeschlagen (Code {}): Details im Protokoll",
    "Сглаживание в разрешении вывода без модели FSR": "Kantenglättung in Ausgabeauflösung, ohne FSR-Modell",
    "Нет или повреждён файл {}": "Datei {} fehlt oder ist beschädigt",
    "Эффекты игры": "Spieleffekte",
    "Патчи игры, применяются при запуске": "Spiel-Patches, werden beim Start angewendet",
    "Детализация моделей": "Modelldetails",
    "Как в игре": "Wie im Spiel",
    "Максимальная (-2)": "Höchste (-2)",
    "Ниже (1)": "Niedriger (1)",
    "Минимальная (2)": "Niedrigste (2)",
    "Хроматическая аберрация": "Chromatische Aberration",
    "Глубина резкости (DoF)": "Tiefenunschärfe (DoF)",
    "Размытие в движении": "Bewegungsunschärfe",
    "Затенение SSAO": "SSAO",
    "Собственное сглаживание игры": "Die spieleigene Kantenglättung",
    "Тени от динамических источников": "Schatten dynamischer Lichter",
    "Отражения SSR (не было в игре)": "SSR-Spiegelungen (nicht im Originalspiel)",
    "Пропуск заставок при запуске": "Intro-Videos überspringen",
    "Свободная камера (Cross + L3 / Space + Z)": "Freie Kamera (Cross + L3 / Space + Z)",
    "Debug menu (левый touchpad / Tab; нужны шрифты)": "Debug menu (linkes Touchpad / Tab; benötigt Schriftarten)",
    "Установите DbgFont14h.ccm и DbgFont14h.tpf в dvdroot_ps4/font из мода Nexus #253": "Installiere DbgFont14h.ccm und DbgFont14h.tpf aus der Nexus-Mod #253 nach dvdroot_ps4/font",
    "Частота кадров": "Bildrate",
    "Режим": "Modus",
    "Какой патч частоты кадров применить к игре": "Welcher Bildraten-Patch auf das Spiel angewendet wird",
    "Без ограничения (патч)": "Unbegrenzt (Patch)",
    "30 (как на PS4)": "30 (wie auf der PS4)",
    "Ограничение FPS": "FPS-Limit",
    "0 — без ограничения; укажите число, чтобы ограничить FPS": "0: kein Limit; gib eine Zahl ein, um die Bildrate zu begrenzen",
    "Производительность": "Leistung",
    "Двухстадийный конвейер GPU": "Zweistufige GPU-Pipeline",
    "Быстрее на 20–30%; при нестабильности выключите": "20–30 % schneller; bei Instabilität ausschalten",
    "Авто": "Auto",
    "Включён при 8 и более потоках процессора": "An ab 8 CPU-Threads",
    "Включён": "An",
    "Стабильнее, но медленнее": "Stabiler, aber langsamer",
    "Чтение данных GPU процессором": "Auslesen von GPU-Daten durch die CPU",
    "По умолчанию": "Standard",
    "Фоновая загрузка в видеопамять": "Vorab-Upload in den VRAM im Hintergrund",
    "Меньше рывков при подгрузке зон": "Weniger Ruckler beim Nachladen von Bereichen",
    "Обычная": "Normal",
    "Без лишней видеопамяти": "Kein zusätzlicher VRAM",
    "Полная": "Voll",
    "Около 3 ГБ видеопамяти сверху": "Etwa 3 GB mehr VRAM",
    "Режим работы": "Modus",
    "Новая модель памяти и трансляции": "Neues Speicher- und Übersetzungsmodell",
    "Эксперимент, только видеокарты AMD. Видеокарта работает с памятью игры напрямую, как в игре для ПК, а команды графики переводятся, а не эмулируются; возможны ошибки. Выключено — старая модель памяти, как в 0.3, со всеми исправлениями": "Experimentell, nur für AMD-GPUs. Die GPU arbeitet direkt mit dem Speicher des Spiels, wie bei einem PC-Spiel, und Grafikbefehle werden übersetzt statt emuliert; Fehler sind möglich. Aus: das alte Speichermodell wie in 0.3, mit allen Korrekturen",
    "Только для видеокарт AMD, а на этом компьютере её нет. Используется старая модель памяти, как в 0.3, со всеми исправлениями": "Nur für AMD-GPUs, und dieser Computer hat keine. Es wird das alte Speichermodell wie in 0.3 verwendet, mit allen Korrekturen",
    "Синхронизация как в 0.3": "Synchronisierung wie in 0.3",
    "Для поиска регрессий: старая модель памяти и ожидания копий как в релизе 0.3": "Zum Aufspüren von Regressionen: das alte Speichermodell und die Kopier-Wartezeiten wie in 0.3 veröffentlicht",
    "Выключена": "Aus",
    "Выключены": "Aus",
    "Для разработчика": "Entwickler",
    "Статистика кадров в журнале": "Bildstatistiken im Protokoll",
    "Сохранять журнал и статистику в файл": "Protokoll und Statistiken in einer Datei speichern",
    "Диагностика вылетов": "Absturzdiagnose",
    "Проверяет кучу игры и записывает записи в её память; немного медленнее": "Prüft den Heap des Spiels und protokolliert Schreibzugriffe in dessen Speicher; etwas langsamer",
    "В папку logs в каталоге данных: для разбора рывков и вылетов": "In den Ordner logs des Datenverzeichnisses: zur Analyse von Rucklern und Abstürzen",
    "Профиль GPU в журнале": "GPU-Profil im Protokoll",
    "Слои валидации Vulkan": "Vulkan-Validierungsebenen",
    "Сильно замедляет": "Deutlich langsamer",
    "Доп. переменные (ИМЯ=значение через пробел)": "Zusätzliche Variablen (NAME=Wert, durch Leerzeichen getrennt)",
    "Читы": "Cheats",
    "Патчи игры версии 1.09, применяются при запуске. Для обычного прохождения и игры по сети оставьте их выключенными": "Spiel-Patches für Version 1.09, werden beim Start angewendet. Lass sie für einen normalen Durchlauf und für Online-Spiele aus",
    "Изменения игрового процесса": "Gameplay-Anpassungen",
    "Бессмертие": "Unsterblich",
    "Урон проходит, но здоровье не опускается ниже 1": "Du nimmst Schaden, fällst aber nie unter 1 HP",
    "Невидимость": "Heimlichkeit",
    "Враги не видят вас и не реагируют, пока вы не атакуете": "Gegner sehen dich nicht und reagieren nicht auf dich, bis du angreifst",
    "Бесшумность": "Lautlose Schritte",
    "Враги не слышат вас, но видят": "Gegner hören dich nicht, können dich aber noch sehen",
    "Rally не угасает": "Rally verblasst nie",
    "Здоровье для Rally не исчезает со временем": "Lebenspunkte, die du per Rally zurückholen kannst, verblassen nicht mit der Zeit",
    "Управление врагом": "Gegnerkontrolle",
    "R3: управлять целью, L3: вернуться. Не вместе со свободной камерой": "R3: anvisierten Gegner steuern, L3: zurück. Nicht zusammen mit der freien Kamera",
    "Без Rally": "Kein Rally",
    "Атаки не возвращают здоровье": "Angriffe stellen keine Lebenspunkte wieder her",
    "Камера дальше": "Kamera weiter entfernt",
    "Камера дальше от персонажа": "Die Kamera bleibt weiter von der Figur entfernt",
    "Без автоповорота камеры": "Keine automatische Kameradrehung",
    "Камера не поворачивается сама при движении; ручное управление и захват цели работают": "Die Kamera dreht sich beim Bewegen nicht von selbst; manuelle Kamera und Zielerfassung funktionieren weiterhin",
    "Бег с меньшим наклоном стика": "Leichteres Rennen",
    "Бег примерно с 70% наклона стика вместо 90%": "Rennen ab etwa 70 % Stick-Neigung statt 90 %",
    "Физика тел как в Dark Souls": "Ragdoll-Physik wie in Dark Souls",
    "Тела и предметы разлетаются от ударов": "Leichen und Objekte fliegen bei Treffern umher",
    # Add to Steam
    "Добавить в Steam": "Zu Steam hinzufügen",
    "Игра в библиотеке Steam запускается сразу, с настройками этого лаунчера": "Aus der Steam-Bibliothek startet das Spiel direkt, mit den Einstellungen dieses Launchers",
    "Добавить": "Hinzufügen",
    "Steam не найден (или в него ещё никто не входил)": "Steam wurde nicht gefunden (oder es hat sich noch niemand angemeldet)",
    "Закройте Steam и нажмите «Добавить» ещё раз": "Schließe Steam und klicke erneut auf Hinzufügen",
    "Пока игра добавляется, Steam нужно закрыть; потом он запустится снова. Закрыть Steam?": "Steam muss geschlossen werden, während das Spiel hinzugefügt wird; danach startet es wieder. Steam schließen?",
    "Отмена": "Abbrechen",
    "Закрыть Steam": "Steam schließen",
    "Steam не закрылся. Закройте его сами и попробуйте ещё раз": "Steam wurde nicht geschlossen. Schließe es selbst und versuche es erneut",
    "Не удалось добавить игру в Steam: {}": "Spiel konnte nicht zu Steam hinzugefügt werden: {}",
    "Bloodborne добавлен в библиотеку Steam": "Bloodborne wurde deiner Steam-Bibliothek hinzugefügt",
    # Online page
    "Онлайн": "Online",
    "Сообщения, пятна крови и призраки приходят с The Hunter's Dream; колокола и призывы идут через сервер shadNet. Игра по сети совместима с версией для Windows: нужны версия игры 1.09 и тот же сервер": "Nachrichten, Blutflecken und Geister kommen von The Hunter's Dream; Glocken und Beschwörungen laufen über einen shadNet-Server. Online-Spiel funktioniert zusammen mit der Windows-Version: Alle brauchen Spielversion 1.09 und denselben Server",
    "Играть онлайн": "Online spielen",
    "Выключено: игра остаётся офлайн, как раньше": "Aus: Das Spiel bleibt offline wie bisher",
    "Игровой сервер (сообщения, пятна крови, призраки)": "Spielserver (Nachrichten, Blutflecken, Geister)",
    "Игровой сервер": "Spielserver",
    "Сервер кооператива (колокола и призывы)": "Koop-Server (Glocken und Beschwörungen)",
    "Учётная запись": "Konto",
    "Имя учётной записи shadNet, не email. Зарегистрируйтесь на shadnet.shadps4.net или спросите владельца частного сервера. Пароль хранится на этом компьютере вместе с настройками лаунчера": "Dein shadNet-Kontoname, nicht deine E-Mail. Registriere dich auf shadnet.shadps4.net oder frag den Betreiber eines privaten Servers. Das Passwort wird mit den Launcher-Einstellungen auf diesem Computer gespeichert",
    "Пароль": "Passwort",
    "Соединение": "Verbindung",
    "У всех в сессии должны быть одна версия игры (1.09) и один сервер. Читы меняют игру и для других игроков: выключайте их при совместной игре": "Alle in einer Sitzung brauchen dieselbe Spielversion (1.09) und denselben Server. Cheats verändern das Spiel auch für die anderen Spieler: Schalte sie beim gemeinsamen Spielen aus",
    "UPnP (открыть порт на роутере автоматически)": "UPnP (Port am Router automatisch öffnen)",
    "Выключите при Tailscale или другом VPN": "Bei Tailscale oder einem anderen VPN ausschalten",
    "Проверить соединение": "Verbindung testen",
    "Проверить": "Testen",
    "Сервер shadNet": "shadNet-Server",
    "Проверка…": "Prüfe…",
    "доступен": "erreichbar",
    "недоступен": "nicht erreichbar",
    "Учётная запись для игры онлайн указана, но «Играть онлайн» выключено": "Ein Online-Konto ist eingetragen, aber „Online spielen“ ist aus",
    "Играть офлайн": "Offline spielen",
    "Online ID — это имя учётной записи (NPID), зарегистрированное на сервере, а не адрес email": "Die Online-ID ist der auf dem Server registrierte Kontoname (NPID), nicht deine E-Mail-Adresse",
    # DLSS
    "Нужны видеокарта NVIDIA RTX и проприетарный драйвер; иначе используется FSR 3.1": "Benötigt eine NVIDIA-RTX-Grafikkarte und den proprietären Treiber; sonst wird FSR 3.1 verwendet",
    "Нет файлов DLSS: tools/build_dlss.sh": "Keine DLSS-Dateien: tools/build_dlss.sh",
    # Discord
    "Статус в Discord": "Discord-Status",
    "«Играет в Bloodborne» в профиле Discord, онлайн или офлайн": "„Spielt Bloodborne“ in deinem Discord-Profil, online oder offline",
    # Button prompts (scripts/menu_prompts.py)
    "Применяется при запуске игры": "Wird beim Spielstart übernommen",
    "Иконки кнопок": "Tastensymbole",
    "Поменять местами A и B": "A und B tauschen",
    "Для контроллеров в стиле Nintendo: подтверждение на A, отмена на B. Применяется при запуске игры": "Für Controller im Nintendo-Stil: Bestätigen mit A, Zurück mit B. Wird beim Spielstart übernommen",
    "Автоматически (по контроллеру)": "Automatisch (nach Controller)",
    "PlayStation (оригинал)": "PlayStation (Original)",
    "Меню жестов без значков управления движением": "Gestenmenü ohne Symbole der Bewegungssteuerung",
    # Add to Steam with Flathub's Steam
    'Steam из Flatpak запускает игры в своей песочнице, где нет ни папки игры, ни драйверов: ярлык должен запускать игру вне её (flatpak-spawn --host). Для этого Steam нужно право org.freedesktop.Flatpak, с которым он может запускать программы в вашей системе. Выдать его?':
        'Steam aus Flatpak startet Spiele in seiner Sandbox, in der weder der Spielordner noch die Treiber sind: Die Verknüpfung muss das Spiel außerhalb davon starten (flatpak-spawn --host). Dafür braucht Steam die Berechtigung org.freedesktop.Flatpak, mit der es Programme auf deinem System starten kann. Erteilen?',
    'Выдать право':
        'Berechtigung erteilen',
    'Не удалось выдать право Steam: {}':
        'Steam konnte die Berechtigung nicht erteilt werden: {}',
    "Копировать":
        "Kopieren",
    "Экспорт журнала…":
        "Protokoll exportieren…",
    "Экспорт журнала":
        "Protokoll exportieren",
    "Журнал скопирован":
        "Protokoll kopiert",
    "Журнал сохранён: {}":
        "Protokoll gespeichert: {}",
    "Не удалось сохранить журнал: {}":
        "Protokoll konnte nicht gespeichert werden: {}",
    "Монитор":
        "Monitor",
    "Пропускать выбор «по сети / вне сети»":
        "Die Auswahl „online / offline spielen“ überspringen",
    "Игра сразу открывает главное меню в режиме вне сети (патч игры)":
        "Das Spiel öffnet das Hauptmenü sofort offline (ein Spiel-Patch)",
    "Основной":
        "Hauptmonitor",
    ", основной":
        ", Hauptmonitor",
    "Файлы игры повреждены при распаковке: шейдеры не распаковываются, игра зависнет на загрузке. Распакуйте игру и обновление 1.09 заново исправленным инструментом (issue #81)":
        "Die Spieldateien wurden beim Entpacken beschädigt: Die Shader lassen sich nicht entpacken und das Spiel würde beim Laden hängen bleiben. Entpacke das Spiel und das Update 1.09 erneut mit einem korrigierten Werkzeug (Issue #81)",
    "Нужна папка adhoc из мода Nexus #253 (шрифты adhoc/font) — в dvdroot_ps4 игры или модом; без неё патч не применяется":
        "Benötigt den Ordner adhoc aus der Nexus-Mod #253 (Schriften in adhoc/font), im dvdroot_ps4 des Spiels oder als Mod; ohne ihn wird der Patch nicht angewendet",
    "Новая: видеокарта работает с памятью игры напрямую, как в игре для ПК, а команды графики переводятся, а не эмулируются. Старая — модель памяти 0.3 со всеми исправлениями. Если драйвер не проходит проверку при запуске — старая":
        "Das neue: Die Grafikkarte arbeitet direkt mit dem Speicher des Spiels, wie bei einem PC-Spiel, und Grafikbefehle werden übersetzt statt emuliert. Das alte: das Speichermodell von 0.3 mit allen Korrekturen. Besteht der Treiber die Prüfung beim Start nicht, das alte",
    "Модель памяти и трансляции":
        "Speicher- und Übersetzungsmodell",
    "Авто: новая на AMD, старая на других":
        "Automatisch: neu auf AMD, alt auf anderen",
    "Новая":
        "Neu",
    "Старая (как в 0.3)":
        "Alt (wie in 0.3)",
    "Регион игры":
        "Spielregion",
    "Вариант текста у языков с региональными версиями: испанский Испании (Европа) или Латинской Америки (Америка)":
        "Die regionale Textvariante von Sprachen, die eine haben: Spanisch aus Spanien (Europa) oder Lateinamerika (Amerika)",
    "Как в дампе игры":
        "Wie im Dump des Spiels",
    "Европа":
        "Europa",
    "Америка":
        "Amerika",
    "Включён брандмауэр: {}":
        "Firewall aktiv: {}",
    "Для UPnP нужны ответы роутера: {}":
        "UPnP braucht die Antworten des Routers: {}",
    "О программе":
        "Über",
    "Версия {}":
        "Version {}",
    "Обновления":
        "Updates",
    "Проверять обновления при запуске":
        "Beim Start nach Updates suchen",
    "Спрашивает GitHub о последнем выпуске; ничего не скачивается без вашего согласия":
        "Fragt GitHub nach der neuesten Version; ohne deine Zustimmung wird nichts heruntergeladen",
    "Последняя версия":
        "Neueste Version",
    "Загрузка…":
        "Wird heruntergeladen…",
    "Обновить":
        "Aktualisieren",
    "Версия {} установлена: перезапустите лаунчер":
        "Version {} installiert: Launcher neu starten",
    "Перезапустить":
        "Neu starten",
    "Не удалось проверить: {}":
        "Prüfung fehlgeschlagen: {}",
    "Установлена версия {}":
        "Version {} installiert",
    "Установлена последняя версия ({})":
        "Du hast die neueste Version ({})",
    "Доступна версия {} (установлена {})":
        "Version {} ist erschienen (du hast {})",
    "Открыть страницу":
        "Seite öffnen",
    "Доступна версия {}":
        "Version {} ist erschienen",
    "Подробнее":
        "Details",
    "Загрузка… {} %":
        "Wird heruntergeladen… {} %",
    "Загрузка… {} МБ":
        "Wird heruntergeladen… {} MB",
    "Не удалось обновить: {}":
        "Aktualisierung fehlgeschlagen: {}",
    "Сначала закройте игру":
        "Schließe zuerst das Spiel",
    "Этот проект":
        "Dieses Projekt",
    "Основано на bbport от deadinside28":
        "Basiert auf bbport von deadinside28",
    "Порт для Windows от Supermedo":
        "Windows-Port von Supermedo",
    "Лицензия":
        "Lizenz",
    'GNU GPL v2 или новее · Файлы игры не входят.': 'GNU GPL v2 oder neuer · Keine Spieldateien enthalten.',
    'Bloodborne принадлежит Sony Interactive Entertainment и FromSoftware.': 'Bloodborne gehört Sony Interactive Entertainment und FromSoftware.',
    "Проверить сейчас":
        "Jetzt prüfen",
    # 0.51: mouse look, choosing NVIDIA's DLSS library, the online module
    'DLSS {}: готово':
        'DLSS {}: bereit',
    'DLSS найден (нужна видеокарта NVIDIA RTX)':
        'DLSS gefunden (benötigt eine NVIDIA-RTX-Grafikkarte)',
    'DLSS не найден: выберите библиотеку NVIDIA ниже (и нужна сборка с мостом DLSS). Игра включит FSR 3.1':
        'DLSS nicht gefunden: Wähle unten die NVIDIA-Bibliothek (außerdem ist ein Build mit der DLSS-Brücke nötig). Das Spiel verwendet FSR 3.1',
    'DLSS: библиотека NVIDIA':
        'DLSS: NVIDIA-Bibliothek',
    '{} — библиотека DLSS для Windows; на Linux NVIDIA её не загружает. Нужна libnvidia-ngx-dlss.so.<версия> из DLSS SDK NVIDIA: {}':
        '{} ist die DLSS-Bibliothek für Windows; NVIDIAs Linux-Treiber lädt sie nicht. Benötigt wird libnvidia-ngx-dlss.so.<Version> aus NVIDIAs DLSS SDK: {}',
    'Библиотека DLSS NVIDIA (libnvidia-ngx-dlss.so.*)':
        'NVIDIAs DLSS-Bibliothek (libnvidia-ngx-dlss.so.*)',
    'Выбрать файл…':
        'Datei wählen…',
    'Из сборки: {}':
        'Aus diesem Build: {}',
    'Инвертировать мышь по вертикали':
        'Maus-Y-Achse umkehren',
    'Камера мышью':
        'Kamera mit der Maus',
    'Клавиатура и мышь':
        'Tastatur und Maus',
    'Не удалось прочитать файл':
        'Die Datei konnte nicht gelesen werden',
    'Не удалось скопировать библиотеку':
        'Die Bibliothek konnte nicht kopiert werden',
    'Нет: выберите libnvidia-ngx-dlss.so.* из DLSS SDK NVIDIA ({})':
        'Keine: Wähle libnvidia-ngx-dlss.so.* aus NVIDIAs DLSS SDK ({})',
    'Нужен файл libnvidia-ngx-dlss.so.<версия> из DLSS SDK NVIDIA: {}':
        'Benötigt wird libnvidia-ngx-dlss.so.<Version> aus NVIDIAs DLSS SDK: {}',
    'Нужна библиотека для Linux':
        'Eine Linux-Bibliothek wird benötigt',
    'Своя: {}':
        'Eigene: {}',
    'Убрать выбранную':
        'Gewählte entfernen',
    'Чувствительность мыши':
        'Mausempfindlichkeit',
    'Щелчок в окне игры захватывает мышь, F1 — отпускает':
        'Ein Klick ins Spielfenster fängt die Maus, F1 gibt sie frei',
    'Эта сборка без модуля онлайна (libbbnet.so): игра только офлайн':
        'Dieser Build hat kein Online-Modul (libbbnet.so): nur Offline-Spiel',
    'Эта сборка без моста DLSS (libbbport_dlss.so): DLSS работать не будет':
        'Dieser Build hat keine DLSS-Brücke (libbbport_dlss.so): DLSS funktioniert nicht',
    'Это не библиотека DLSS':
        'Das ist nicht die DLSS-Bibliothek',
    # Online page: your own shadNet server, the co-op port, seamless co-op, the UDP test
    '0: случайный при каждом запуске. Закрепите его, чтобы открыть в брандмауэре или на роутере вручную':
        '0: jedes Mal ein zufälliger Port. Lege ihn fest, um ihn in der Firewall oder von Hand am Router zu öffnen',
    'UDP сервера shadNet (призывы)':
        'UDP des shadNet-Servers (Beschwörungen)',
    'UPnP открывает порт только на роутере; брандмауэр этого компьютера всё равно блокирует кооператив. Откройте порт: {}':
        'UPnP öffnet den Port nur am Router; die Firewall dieses Computers blockiert den Koop trotzdem. Öffne den Port: {}',
    'Адрес WebAPI (пусто: порт 31315 сервера)':
        'WebAPI-Adresse (leer: Port 31315 des Servers)',
    'Адрес сервера (host:port)':
        'Serveradresse (Host:Port)',
    'Бесшовный кооператив (экспериментально)':
        'Nahtloser Koop (experimentell)',
    'Закрепите порт кооператива выше (например, {}): случайный порт в брандмауэре не открыть':
        'Lege oben den Koop-Port fest (zum Beispiel {}): ein zufälliger Port lässt sich in der Firewall nicht öffnen',
    'Как запустить свой сервер':
        'Eigenen Server betreiben',
    'Порт кооператива (UDP)':
        'Koop-Port (UDP)',
    'Призывы между разными локациями. Только если на сервере BloodborneSeamlessCoop=true, и у всех игроков так же':
        'Beschwörungen zwischen verschiedenen Gebieten. Nur wenn der Server BloodborneSeamlessCoop=true hat und alle Spieler es einschalten',
    'Публичный сервер shadPS4':
        'Öffentlicher Server von shadPS4',
    'Свой сервер':
        'Eigener Server',
    'shadnet-p2p: на вашем ПК или VPS':
        'shadnet-p2p: auf deinem PC oder einem VPS',
    'Сервер shadNet':
        'shadNet-Server',
    'не отвечает: призывы не соединятся':
        'keine Antwort: Beschwörungen werden nicht verbunden',
    'отвечает; ваш публичный адрес: {}':
        'antwortet; deine öffentliche Adresse: {}',
    "Поддержать проект": 'Dieses Projekt unterstützen',
    # Trophies page
    'В дампе игры нет трофеев (sce_sys/trophy)':
        'Der Spiel-Dump hat keine Trophäen (sce_sys/trophy)',
    'Записываются, когда игра их открывает, и показываются в игре':
        'Werden gespeichert, wenn das Spiel sie freischaltet, und im Spiel angezeigt',
    'Ключ трофеев':
        'Trophäen-Schlüssel',
    'Ключ трофеев PS4 (TrophyKey в shadPS4), 32 шестнадцатеричных символа: с ним названия и описания на языке игры. Хранится на этом компьютере. Без него они на английском':
        'Der Trophäen-Schlüssel der PS4 (TrophyKey in shadPS4), 32 Hexadezimalziffern: damit sind Namen und Beschreibungen in der Sprache des Spiels. Bleibt auf diesem Computer. Ohne ihn sind sie auf Englisch',
    'Неверный ключ трофеев: названия недоступны':
        'Falscher Trophäen-Schlüssel: die Namen sind nicht verfügbar',
    'Получен {}':
        'Erhalten am {}',
    'Получено {} из {}':
        '{} von {} erhalten',
    'Скрытый трофей':
        'Versteckte Trophäe',
    'Трофеи':
        'Trophäen',
    'Платиновый':
        'Platin',
    'Золотой':
        'Gold',
    'Серебряный':
        'Silber',
    'Бронзовый':
        'Bronze',
    "Вход в shadNet": "shadNet-Anmeldung",
    "неверное имя или пароль": "falscher Name oder falsches Passwort",
    "такой учётной записи нет на этом сервере": "dieses Konto gibt es auf diesem Server nicht",
    "эта учётная запись уже в сети (игра запущена?)": "dieses Konto ist bereits angemeldet (läuft das Spiel?)",
    "вход выполнен": "angemeldet",
    "вход не удался ({})": "Anmeldung fehlgeschlagen ({})",
    "Загрузки и плавность": "Laden und Flüssigkeit",
    "Патчи игры из bbhost, применяются при запуске": "Spiel-Patches aus bbhost, beim Start angewendet",
    "Быстрая загрузка после смерти": "Schnelles Laden nach dem Tod",
    "Загрузка после смерти или перемещения у лампы идёт, пока грузится область (2–3 с), а не минимум 12 с": "Das Laden nach dem Tod oder einer Laternenreise dauert so lange wie das Gebiet (2–3 s), nicht mindestens 12 s",
    "Без рывка каждые ~50 с": "Kein Ruckler alle ~50 s",
    "Игра быстрее сжимает запись игрока: пропадает рывок ~23 мс примерно каждые 50 с": "Das Spiel komprimiert die Spieleraufzeichnung schneller: ein Ruckler von ~23 ms etwa alle 50 s verschwindet",
    "Третий поток подготовки ресурсов": "Dritter Thread zur Ressourcenvorbereitung",
    "Во время игры работают три потока подготовки ресурсов, а не два. Экспериментально": "Im Spiel laufen drei Threads zur Ressourcenvorbereitung statt zwei. Experimentell",
    # About: Thanks
    'Благодарности': 'Danksagungen',
    'Без них ничего этого не было бы': 'Ohne sie wäre nichts davon möglich',
    'Порт и его код': 'Der Port und sein Code',
    'Помощь и тесты': 'Hilfe und Tests',
    'Другие благодарности': 'Dank auch an',
    'bbport — порт, на котором построен весь этот проект': 'bbport, der Port, auf dem dieses ganze Projekt aufbaut',
    'Игра по сети, DLSS, страница читов, добавление в Steam, значок и пропуск конвейеров, которые драйвер не может создать': 'Online-Spiel, DLSS, die Cheat-Seite, Zu Steam hinzufügen, das Symbol und das Überspringen von Pipelines, die der Treiber nicht erstellen kann',
    'Собрал и адаптировал десятки исправлений: вылеты при загрузке, чёрные изображения, апскейлер, строка производительности в журнале': 'Hat Dutzende Korrekturen gesammelt und angepasst: Abstürze beim Laden, schwarze Bilder, der Upscaler, die Leistungszeile im Log',
    'Чёрный предпросмотр персонажа, картинка экрана загрузки и память кэша текстур': 'Die schwarze Charaktervorschau, das Bild des Ladebildschirms und der Speicher des Texturcaches',
    'Кэш текстур вовремя освобождает видеопамять': 'Der Texturcache gibt Videospeicher rechtzeitig frei',
    'Вылеты при загрузке областей': 'Abstürze beim Laden von Gebieten',
    'Интерфейс, пропадавший не в 1080p, векторы движения больших чудовищ и ошибка памяти': 'Die Oberfläche, die außerhalb von 1080p verschwand, Bewegungsvektoren der großen Bestien und ein Speicherfehler',
    'Вылеты при загрузке некоторых карт и меню жестов с клавиатуры': 'Abstürze beim Laden mancher Karten und das Gestenmenü über die Tastatur',
    'Экранная клавиатура для имени персонажа и уведомление о компиляции шейдеров': 'Die Bildschirmtastatur für den Charakternamen und der Hinweis zum Kompilieren der Shader',
    "Быстрая загрузка после смерти и перемещения (bbhost) и сервер The Hunter's Dream": "Schnelles Laden nach Tod oder Reise (bbhost) und der Server The Hunter's Dream",
    'Сетевые библиотеки игры по сети и сервер для своего кооператива': 'Die Bibliotheken für das Online-Spiel und der Server für den eigenen Koop',
    'Основа поддержки DLSS и модель FSR 4 без шлейфов за персонажами': 'Die Grundlage für DLSS und das FSR-4-Modell ohne Schlieren hinter Figuren',
    'Апскейлер FSR 3.1': 'Der FSR-3.1-Upscaler',
    'Игра запускается, когда DLSS нельзя использовать': 'Das Spiel startet, wenn DLSS nicht nutzbar ist',
    'Перевод на упрощённый китайский': 'Die Übersetzung ins vereinfachte Chinesisch',
    'Звук игры на полной громкости': 'Der Spielton in voller Lautstärke',
    'Флажки и ползунки внутриигрового меню': 'Die Kontrollkästchen und Schieberegler des Spielmenüs',
    'Подробные отчёты с журналами и проверка исправлений': 'Ausführliche Berichte mit Logs und Tests der Korrekturen',
    'Идея поменять местами A и B на контроллерах в стиле Nintendo': 'Die Idee, A und B bei Controllern im Nintendo-Stil zu tauschen',
    'Проверка исправления видеопамяти': 'Test der Videospeicher-Korrektur',
    'Иконки кнопок Xbox и Switch (Nexus Mods)': 'Xbox- und Switch-Tastensymbole (Nexus Mods)',
    'Показал, какие текстуры нужны иконкам клавиатуры (Nexus Mods)': 'Hat gezeigt, welche Texturen Tastatursymbole brauchen (Nexus Mods)',
    'Патчи игры: высокий FPS, разрешение и другое': 'Spiel-Patches: hohe Bildraten, Auflösung und mehr',
    'Рендерер и компилятор шейдеров': 'Der Renderer und der Shader-Recompiler',
    'Инструмент для сборки AppImage': 'Das Werkzeug, das das AppImage baut',
    'Нашёл ошибку, из-за которой игра не запускалась на некоторых видеокартах': 'Hat den Fehler gefunden, der den Spielstart auf manchen Grafikkarten verhinderte',
    # Shader cache
    'Кэш шейдеров': 'Shader-Cache',
    'Очистить': 'Leeren',
    '{}. Если после обновления картинка выглядит странно, очистите его: шейдеры соберутся заново (первые минуты в каждой зоне возможны рывки)': '{}. Wenn das Bild nach einem Update seltsam aussieht, leeren: Die Shader werden neu erstellt (in den ersten Minuten jedes Gebiets kann es ruckeln)',
    'Пусто: шейдеры соберутся при игре': 'Leer: Die Shader werden beim Spielen erstellt',
    'Очистить кэш шейдеров?': 'Shader-Cache leeren?',
    'Игра соберёт шейдеры заново: первые минуты в каждой зоне возможны рывки. Сохранения и настройки не затрагиваются.': 'Das Spiel erstellt die Shader neu: In den ersten Minuten jedes Gebiets kann es ruckeln. Spielstände und Einstellungen bleiben unberührt.',
    'Названия трофеев на английском без ключа и звук при получении трофея': 'Trophäennamen auf Englisch ohne Schlüssel und der Ton beim Erhalt einer Trophäe',
    'Буфер трафарета, в который писали цветные изображения': 'Der Stencil-Puffer, in den Farbbilder schrieben',
    'Вход на публичный сервер shadNet без отключения': 'Auf dem öffentlichen shadNet-Server angemeldet bleiben',
    'Игра по сети': 'Online-Spiel',
    'Сервер shadNet не принимает bbport, игра осталась офлайн. Для игры по сети используйте свой сервер (страница «Онлайн»).': 'Der shadNet-Server akzeptiert bbport nicht, daher blieb das Spiel offline. Für das Online-Spiel einen eigenen Server verwenden (Seite Online).',
    'Выход из игры из меню с контроллера и меню в пределах экрана': 'Das Spiel im Menü mit dem Controller beenden und das Menü innerhalb des Bildschirms',
    'Вылет видеоплеера при его остановке': 'Ein Absturz des Videoplayers beim Anhalten',
    'Язык внутриигрового меню при запуске без окна лаунчера': 'Die Sprache des Spielmenüs beim Start ohne Launcher-Fenster',
    'DLSS в AppImage на NVIDIA': 'DLSS im AppImage auf NVIDIA',
    'Сверхширокие мониторы без растянутой картинки': 'Ultrawide-Monitore ohne gestrecktes Bild',
}


# Simplified Chinese.
ZH_CN = {
    # Window, pages, buttons
    "Запустить": "启动",
    "Остановить": "停止",
    "Настройки": "设置",
    "Журнал": "日志",
    "Не удалось запустить: {}": "无法启动：{}",
    "\n— игра завершилась (код {}) —\n": "\n— 游戏已退出（代码 {}）—\n",
    # Launcher language
    "Язык лаунчера": "启动器语言",
    "Как в системе": "跟随系统",
    "Применится после перезапуска лаунчера, пока игра запущена":
        "游戏运行期间更改语言，需要重启启动器后才会生效",
    # Game
    "Игра": "游戏",
    "Папка игры ({})": "游戏文件夹（{}）",
    "Папка игры": "游戏文件夹",
    "Выбрать папку с eboot.bin": "选择包含 eboot.bin 的文件夹",
    "Открыть в файловом менеджере": "在文件管理器中打开",
    "Папка сохранений": "存档文件夹",
    "Выбрать папку сохранений": "选择存档文件夹",
    "Вернуть папку по умолчанию": "恢复默认文件夹",
    "Язык системы": "系统语言",
    "По умолчанию: {}": "默认：{}",
    "Найдены сохранения": "已找到存档",
    "Сохранений пока нет: игра создаст их здесь": "暂无存档：游戏会在此创建",
    "не выбрана": "未选择",
    "Найден eboot.bin": "已找到 eboot.bin",
    "Нет eboot.bin в папке": "文件夹中没有 eboot.bin",
    "Управление": "操作设置",
    "Клавиатура": "键盘",
    "Геймпад": "手柄",
    "Назначение кнопок; применяется при запуске игры": "按键绑定；在游戏启动时生效",
    "Назначить": "绑定",
    "Сбросить": "重置",
    "{} (по умолчанию)": "{}（默认）",
    "не назначено": "未绑定",
    "Нажмите клавишу или кнопку… (Esc — отмена)": "按下一个按键或手柄按钮…（按 Esc 取消）",
    "Крест": "叉键",
    "Круг": "圆圈键",
    "Квадрат": "方块键",
    "Треугольник": "三角键",
    "Тачпад, левая половина (жесты)": "触摸板左侧（手势）",
    "Тачпад, правая половина (личные вещи)": "触摸板右侧（重要物品）",
    "Крестовина вверх": "方向键上",
    "Крестовина вниз": "方向键下",
    "Крестовина влево": "方向键左",
    "Крестовина вправо": "方向键右",
    "Движение вперёд": "向前移动",
    "Движение назад": "向后移动",
    "Движение влево": "向左移动",
    "Движение вправо": "向右移动",
    "Камера вверх": "镜头向上",
    "Камера вниз": "镜头向下",
    "Камера влево": "镜头向左",
    "Камера вправо": "镜头向右",
    "Контроллер": "控制器",
    "Выбранный берётся, как только подключится": "所选手柄一旦连接即会被使用",
    "Первый подключённый": "第一个已连接的手柄",
    "{} (не подключён)": "{}（未连接）",
    "Нужно обновление 1.09: скопируйте файлы дампа обновления 1.09 в папку игры с заменой (найдена версия {})":
        "需要 1.09 更新：请将转储出的 1.09 更新文件复制到游戏文件夹并覆盖（当前检测到版本 {}）",
    "eboot.bin не от версии 1.09: скопируйте eboot.bin из дампа обновления 1.09 в папку игры с заменой":
        "eboot.bin 不是 1.09 版本：请将 1.09 更新转储中的 eboot.bin 复制到游戏文件夹并覆盖",
    "Это не магазинное издание Bloodborne (найдено {}): нужен Bloodborne любого региона с обновлением 1.09":
        "这不是 Bloodborne 的正式发行版（当前检测到 {}）：需要任意地区已安装 1.09 更新的 Bloodborne",
    "eboot.bin с вшитым патчем 60 FPS от Lance McDonald: из-за него игра падает в меню жестов. Скопируйте чистый eboot.bin из дампа обновления 1.09 в папку игры с заменой":
        "此 eboot.bin 内置了 Lance McDonald 的 60 FPS 补丁，会导致游戏在打开手势菜单时崩溃：请将 1.09 更新转储中干净的 eboot.bin 复制到游戏文件夹并覆盖",
    "eboot.bin не читается как расшифрованный исполняемый файл PS4: сделайте дамп заново":
        "无法将 eboot.bin 识别为已解密的 PS4 可执行文件：请重新转储游戏",
    "Файлы игры повреждены при распаковке: шейдеры не распаковываются, игра зависнет на загрузке. Распакуйте игру и обновление 1.09 заново исправленным инструментом (issue #81)":
        "游戏文件在解包时已损坏：着色器无法解压，游戏会在加载时卡住。请使用修复后的工具重新解包游戏和 1.09 更新（issue #81）",
    "Bloodborne {}, версия 1.09": "血源诅咒 {}，版本 1.09",
    "Папка игры (с eboot.bin)": "游戏文件夹（含 eboot.bin）",
    # Languages
    "Английский": "英语",
    "Русский": "俄语",
    "Японский": "日语",
    "Французский": "法语",
    "Испанский": "西班牙语",
    "Немецкий": "德语",
    "Итальянский": "意大利语",
    "English": "英语",
    # Mods
    "Моды": "模组",
    "Распакуйте каждый мод в отдельную папку (с dvdroot_ps4 или сразу с chr/, parts/ и т. п.). "
    "При совпадении файлов побеждает мод ниже в списке. Применяется при запуске.":
        "将每个模组解压到独立的文件夹中（文件夹内可以是 dvdroot_ps4，也可以直接是 chr/、parts/ 等）。"
        "文件冲突时，列表中靠下的模组优先。设置会在游戏启动时生效。",
    "Загружать моды": "加载模组",
    "Папка модов": "模组文件夹",
    "Выбрать папку модов": "选择模组文件夹",
    "Открыть папку модов": "打开模组文件夹",
    "Обновить список": "刷新列表",
    "Загрузить раньше": "提前加载",
    "Загрузить позже": "延后加载",
    "Модов нет": "没有模组",
    # Patches
    "Сторонние патчи": "第三方补丁",
    "XML-патчи в формате shadPS4 для версии 01.09 из папки патчей. Применяются при запуске.":
        "补丁文件夹中、shadPS4 格式、适用于 01.09 版本的 XML 补丁。会在游戏启动时生效。",
    "Папка патчей": "补丁文件夹",
    "Выбрать папку патчей": "选择补丁文件夹",
    "Открыть папку патчей": "打开补丁文件夹",
    "Патчей нет": "没有补丁",
    "Автор: {}": "作者：{}",
    # Screen
    "Экран": "显示",
    "Разрешение вывода": "输出分辨率",
    "Апскейлер дорисовывает кадр; Steam Deck — 720p": "超分辨率会将画面放大到此分辨率；Steam Deck 建议 720p",
    "Полноэкранный режим": "全屏模式",
    "Смена разрешения на лету": "实时切换分辨率",
    "Без перезапуска, но медленнее на Steam Deck и старых GPU":
        "无需重启，但在 Steam Deck 和较旧的显卡上速度更慢",
    "Авто (по видеокарте)": "自动（根据显卡）",
    "Выключена (быстрее)": "关闭（更快）",
    "Включена": "开启",
    "Режим показа кадров": "呈现模式",
    "Разрешить HDR": "允许 HDR",
    # Upscaler
    "Апскейлер": "超分辨率",
    "Хранится в bbport.ini; в игре меняется через меню (Insert или L3+R3)":
        "保存在 bbport.ini 中；游戏内可通过菜单切换（Insert 或 L3+R3）",
    "TAA (нативное сглаживание)": "TAA（原生抗锯齿）",
    "Выключен": "关闭",
    "Пресет": "预设",
    "Резкость (RCAS)": "锐化（RCAS）",
    "Сила резкости": "锐化强度",
    "Векторы движения объектов": "物体运动矢量",
    "Меньше гостинга на персонажах; стоит около 10% FPS": "减少角色拖影；大约损失 10% 帧率",
    "Показывать FPS": "显示帧率",
    "Ассеты найдены": "已找到资源文件",
    "Нет ассетов: tools/fetch_fsr4_assets.sh": "缺少资源文件：请运行 tools/fetch_fsr4_assets.sh",
    "Ассеты для выбранного режима найдены": "已找到所选模式对应的资源文件",
    "{}. Соберите FSR 4.1.1 из своей DLL кнопкой «Выбрать DLL…» ниже":
        "{}。请用下方的「选择 DLL…」按钮，从你自己的 DLL 构建 FSR 4.1.1",
    "FSR 4.1.1 из своей DLL AMD": "用你自己的 AMD DLL 构建 FSR 4.1.1",
    "Отменить": "取消",
    "Выбрать DLL…": "选择 DLL…",
    "DLL апскейлера AMD (amd_fidelityfx_upscaler_dx12.dll)": "AMD 超分辨率 DLL（amd_fidelityfx_upscaler_dx12.dll）",
    "нет": "无",
    "Эта DLL не подходит": "此 DLL 不适用",
    "{}: версия {}, модели FSR 4: {}.\n\nbbport повторяет только официальную FSR 4.1.x от AMD (модель v07_fp8_no_scale): например, FSR4_LATEST из OptiScaler или amd_fidelityfx_upscaler_dx12.dll из игры с FSR 4.1. Сборки сообщества (4.0.2b и подобные) устроены иначе и пока не поддерживаются.":
        "{}：版本 {}，FSR 4 模型：{}。\n\nbbport 仅支持复现 AMD 官方的 FSR 4.1.x（v07_fp8_no_scale 模型）：例如 OptiScaler 中的 FSR4_LATEST，或来自支持 FSR 4.1 的游戏的 amd_fidelityfx_upscaler_dx12.dll。社区构建版本（如 4.0.2b 等）结构不同，暂不支持。",
    "Загрузчик не подходит": "此加载器不适用",
    "Загрузчик FidelityFX (amd_fidelityfx_loader_dx12.dll или amd_fidelityfx_dx12.dll)":
        "FidelityFX 加载器（amd_fidelityfx_loader_dx12.dll 或 amd_fidelityfx_dx12.dll）",
    "\n— сборка FSR 4.1.1 из {} —\n": "\n— 正在从 {} 构建 FSR 4.1.1 —\n",
    "Подготовка…": "准备中…",
    "Запись проходов DLL под Proton: {} из {}": "正在 Proton 下录制 DLL 渲染通道：{} / {}",
    "Перевод проходов в SPIR-V…": "正在将渲染通道转换为 SPIR-V…",
    "— сборка FSR 4.1.1 завершилась (код {}) —\n": "— FSR 4.1.1 构建已完成（代码 {}）—\n",
    "FSR 4.1.1 собран и выбран": "FSR 4.1.1 已构建并选用",
    "Сборка FSR 4.1.1 отменена": "FSR 4.1.1 构建已取消",
    "FSR 4.1.1 не собран": "FSR 4.1.1 尚未构建",
    "DLL не подходит: подробности в журнале": "DLL 不适用：详情见日志",
    "Не хватает программ для сборки: список в журнале": "缺少构建所需的程序：清单见日志",
    "Записанные проходы не совпали с тем, что повторяет bbport (другая версия DLL или новая видеокарта?): подробности в журнале":
        "录制的渲染通道与 bbport 复现的内容不一致（可能是 DLL 版本不同，或显卡型号较新？）：详情见日志",
    "Не найден загрузчик FidelityFX 2.x": "未找到 FidelityFX 2.x 加载器",
    "Не найден подходящий Proton: установите GE-Proton 10 или новее (ProtonUp-Qt) или Proton Experimental / Proton-CachyOS в Steam. Если они есть — запустите в Steam любую игру с этим Proton, чтобы Steam поставил его рантайм":
        "未找到合适的 Proton：请安装 GE-Proton 10 或更高版本（可用 ProtonUp-Qt），或在 Steam 中使用 Proton Experimental / Proton-CachyOS。如果已经安装，请在 Steam 中用该 Proton 启动任意游戏，让 Steam 安装它的运行时",
    "Ни один Proton не запустил FSR 4.1 из этой DLL. Либо они слишком старые (подходят GE-Proton 10+, Proton Experimental, Proton-CachyOS 11), либо DLL не включает FSR 4.1 на этой видеокарте (Steam Deck?): тогда соберите на ПК с Radeon RX 7000/9000 и скопируйте папку fsr4_411. Подробности в журнале":
        "没有任何 Proton 能从此 DLL 启动 FSR 4.1。要么是 Proton 版本太旧（需要 GE-Proton 10+、Proton Experimental 或 Proton-CachyOS 11），要么是这块显卡无法启用 FSR 4.1（例如 Steam Deck？）：这种情况下，请在装有 Radeon RX 7000/9000 的电脑上构建，再把 fsr4_411 文件夹复制过来。详情见日志",
    "На NixOS запись идёт на самой системе (systemd --user) через umu-launcher из nix-shell, а здесь их не нашлось: установите umu-launcher или Nix. Подробности в журнале":
        "在 NixOS 上，录制通过 nix-shell 中的 umu-launcher 在系统本身（systemd --user）上进行，但未能找到它们：请安装 umu-launcher 或 Nix。详情见日志",
    "{}: FSR {}. Это официальная FSR 4.0.x от AMD: она включается только на видеокартах RDNA4 (RX 9000), а под Proton на других видеокартах не запускается, поэтому записать её нельзя.\n\nНужна FSR 4.1.x: например, FSR4_LATEST из OptiScaler или DLL из игры с FSR 4.1.":
        "{}：FSR {}。这是 AMD 官方的 FSR 4.0.x：仅在 RDNA4 显卡（RX 9000）上启用，在其他显卡上通过 Proton 无法运行，因此无法录制。\n\n需要 FSR 4.1.x：例如 OptiScaler 中的 FSR4_LATEST，或来自支持 FSR 4.1 的游戏的 DLL。",
    "{}: в этой DLL нет FSR 4. Нужна amd_fidelityfx_upscaler_dx12.dll версии 4.1.x.":
        "{}：此 DLL 中不包含 FSR 4。需要版本为 4.1.x 的 amd_fidelityfx_upscaler_dx12.dll。",
    "Это не загрузчик":
        "这不是加载器",
    "{} — это DLL апскейлера. Загрузчик называется amd_fidelityfx_loader_dx12.dll (у OptiScaler — amd_fidelityfx_dx12.dll) и лежит в той же папке игры, что и DLL апскейлера.":
        "{} 是超分辨率 DLL。加载器名为 amd_fidelityfx_loader_dx12.dll（在 OptiScaler 中为 amd_fidelityfx_dx12.dll），与超分辨率 DLL 位于同一个游戏文件夹中。",
    "{}: версия {}. Нужен загрузчик FidelityFX 2.x — из той же игры, что и DLL апскейлера.":
        "{}：版本 {}。需要来自同一游戏、与超分辨率 DLL 配套的 FidelityFX 2.x 加载器。",
    "Рядом с DLL нет загрузчика: выберите amd_fidelityfx_loader_dx12.dll из папки игры":
        "DLL 旁边没有加载器：请从游戏文件夹中选择 amd_fidelityfx_loader_dx12.dll",
    "Собрать FSR 4.1.1 из amd_fidelityfx_upscaler_dx12.dll 4.1.x (OptiScaler: папка FSR4_LATEST, или из игры с FSR 4.1). Нужен GE-Proton 10+, Proton Experimental или Proton-CachyOS; 2–5 минут (RDNA4: вдвое дольше, ещё и вариант FP8)":
        "从 amd_fidelityfx_upscaler_dx12.dll 4.1.x 构建 FSR 4.1.1（OptiScaler：FSR4_LATEST 文件夹，或来自支持 FSR 4.1 的游戏）。需要 GE-Proton 10+、Proton Experimental 或 Proton-CachyOS；耗时 2–5 分钟（RDNA4：耗时加倍，并额外构建 FP8 版本）",
    "Сборка не удалась (код {}): подробности в журнале": "构建失败（代码 {}）：详情见日志",
    "Сглаживание в разрешении вывода без модели FSR": "在输出分辨率下进行抗锯齿，不使用 FSR 模型",
    "DLSS найден (нужна видеокарта NVIDIA RTX)": "已找到 DLSS（需要 NVIDIA RTX 显卡）",
    "DLSS: библиотека NVIDIA": "DLSS：NVIDIA 库",
    "Выбрать файл…": "选择文件…",
    "Убрать выбранную": "移除所选",
    "Своя: {}": "自定义：{}",
    "Из сборки: {}": "随版本附带：{}",
    "Нет: выберите libnvidia-ngx-dlss.so.* из DLSS SDK NVIDIA ({})": "无：请选择 NVIDIA DLSS SDK 中的 libnvidia-ngx-dlss.so.*（{}）",
    "Эта сборка без моста DLSS (libbbport_dlss.so): DLSS работать не будет": "此版本没有 DLSS 桥接（libbbport_dlss.so）：DLSS 无法工作",
    "Библиотека DLSS NVIDIA (libnvidia-ngx-dlss.so.*)": "NVIDIA DLSS 库（libnvidia-ngx-dlss.so.*）",
    "Нужна библиотека для Linux": "需要 Linux 版本的库",
    "{} — библиотека DLSS для Windows; на Linux NVIDIA её не загружает. Нужна libnvidia-ngx-dlss.so.<версия> из DLSS SDK NVIDIA: {}":
        "{} 是 Windows 版 DLSS 库，NVIDIA 的 Linux 驱动不会加载它。需要 NVIDIA DLSS SDK 中的 libnvidia-ngx-dlss.so.<版本>：{}",
    "Не удалось прочитать файл": "无法读取文件",
    "Это не библиотека DLSS": "这不是 DLSS 库",
    "Нужен файл libnvidia-ngx-dlss.so.<версия> из DLSS SDK NVIDIA: {}": "需要 NVIDIA DLSS SDK 中的 libnvidia-ngx-dlss.so.<版本>：{}",
    "Не удалось скопировать библиотеку": "无法复制该库",
    "DLSS {}: готово": "DLSS {}：已就绪",
    "Клавиатура и мышь": "键盘和鼠标",
    "Камера мышью": "鼠标控制视角",
    "Щелчок в окне игры захватывает мышь, F1 — отпускает": "在游戏窗口中单击以捕获鼠标，按 F1 释放",
    "Чувствительность мыши": "鼠标灵敏度",
    "Инвертировать мышь по вертикали": "反转鼠标纵轴",
    "DLSS не найден: выберите библиотеку NVIDIA ниже (и нужна сборка с мостом DLSS). Игра включит FSR 3.1":
        "未找到 DLSS：请在下方选择 NVIDIA 的库（还需要带 DLSS 桥接的版本）。游戏将改用 FSR 3.1",
    "Нет или повреждён файл {}": "文件 {} 缺失或已损坏",
    # Effects
    "Эффекты игры": "游戏效果",
    "Патчи игры, применяются при запуске": "游戏补丁，会在启动时生效",
    "Детализация моделей": "模型细节",
    "Как в игре": "游戏默认",
    "Максимальная (-2)": "最高（-2）",
    "Ниже (1)": "较低（1）",
    "Минимальная (2)": "最低（2）",
    "Хроматическая аберрация": "色差",
    "Глубина резкости (DoF)": "景深（DoF）",
    "Размытие в движении": "动态模糊",
    "Затенение SSAO": "SSAO 环境光遮蔽",
    "Собственное сглаживание игры": "游戏自带抗锯齿",
    "Тени от динамических источников": "动态光源阴影",
    "Отражения SSR (не было в игре)": "SSR 反射（原版游戏中没有）",
    "Пропуск заставок при запуске": "跳过开场动画",
    "Свободная камера (Cross + L3 / Space + Z)": "自由镜头（叉键 + L3 / 空格 + Z）",
    "Debug menu (левый touchpad / Tab; нужны шрифты)": "调试菜单（左触摸板 / Tab；需要字体文件）",
    "Установите DbgFont14h.ccm и DbgFont14h.tpf в dvdroot_ps4/font из мода Nexus #253":
        "请从 Nexus 模组 #253 中，将 DbgFont14h.ccm 和 DbgFont14h.tpf 安装到 dvdroot_ps4/font",
    # Frame rate
    "Частота кадров": "帧率",
    "Режим": "模式",
    "Какой патч частоты кадров применить к игре": "对游戏应用哪种帧率补丁",
    "Без ограничения (патч)": "不限制（补丁解锁）",
    "30 (как на PS4)": "30（与 PS4 一致）",
    "Ограничение FPS": "帧率上限",
    "0 — без ограничения; укажите число, чтобы ограничить FPS":
        "0 表示不限制；填写一个数字可限制帧率",
    # Performance
    "Производительность": "性能",
    "Двухстадийный конвейер GPU": "双阶段 GPU 管线",
    "Быстрее на 20–30%; при нестабильности выключите": "可提速 20–30%；如不稳定请关闭",
    "Авто": "自动",
    "Включён при 8 и более потоках процессора": "处理器有 8 个或以上线程时自动开启",
    "Включён": "开启",
    "Стабильнее, но медленнее": "更稳定，但速度更慢",
    "Чтение данных GPU процессором": "由 CPU 读取 GPU 数据（readback）",
    "По умолчанию": "默认",
    "Фоновая загрузка в видеопамять": "后台预加载至显存",
    "Меньше рывков при подгрузке зон": "区域加载时卡顿更少",
    "Обычная": "普通",
    "Без лишней видеопамяти": "不占用额外显存",
    "Полная": "完整",
    "Около 3 ГБ видеопамяти сверху": "额外占用约 3 GB 显存",
    # Mode
    "Режим работы": "工作模式",
    "Новая модель памяти и трансляции": "新内存与指令转译模型",
    "Новая: видеокарта работает с памятью игры напрямую, как в игре для ПК, а команды графики переводятся, а не эмулируются. Старая — модель памяти 0.3 со всеми исправлениями. Если драйвер не проходит проверку при запуске — старая":
        "新模型：显卡像 PC 游戏那样直接读写游戏内存，图形指令被转译而非模拟。旧模型：0.3 版的内存模型，包含所有修复。如果驱动未通过启动检查，则使用旧模型",
    "Модель памяти и трансляции": "内存与指令转译模型",
    "Авто: новая на AMD, старая на других": "自动：AMD 用新模型，其他显卡用旧模型",
    "Новая": "新模型",
    "Старая (как в 0.3)": "旧模型（与 0.3 版相同）",
    "Синхронизация как в 0.3": "与 0.3 版相同的同步方式",
    "Для поиска регрессий: старая модель памяти и ожидания копий как в релизе 0.3":
        "用于排查回归问题：采用与 0.3 版发布时相同的旧内存模型与复制等待方式",
    "Выключена": "关闭",
    "Выключены": "关闭",
    # Developer
    "Для разработчика": "开发者选项",
    "Статистика кадров в журнале": "在日志中记录帧统计",
    "Сохранять журнал и статистику в файл": "将日志和统计信息保存到文件",
    "Диагностика вылетов": "崩溃诊断",
    "Проверяет кучу игры и записывает записи в её память; немного медленнее":
        "检查游戏堆内存并记录对其的写入操作；速度会略有下降",
    "В папку logs в каталоге данных: для разбора рывков и вылетов":
        "保存到数据目录下的 logs 文件夹：便于排查卡顿和崩溃问题",
    "Профиль GPU в журнале": "在日志中记录 GPU 性能剖析",
    "Слои валидации Vulkan": "Vulkan 验证层",
    "Сильно замедляет": "会大幅降低速度",
    "Доп. переменные (ИМЯ=значение через пробел)": "附加环境变量（用空格分隔的 名称=值）",
    # Add to Steam with Flathub's Steam
    'Steam из Flatpak запускает игры в своей песочнице, где нет ни папки игры, ни драйверов: ярлык должен запускать игру вне её (flatpak-spawn --host). Для этого Steam нужно право org.freedesktop.Flatpak, с которым он может запускать программы в вашей системе. Выдать его?':
        'Flatpak 版 Steam 在其沙盒中运行游戏，沙盒里既没有游戏文件夹也没有驱动：快捷方式需要在沙盒外启动游戏（flatpak-spawn --host）。为此 Steam 需要 org.freedesktop.Flatpak 权限，该权限允许它在你的系统上启动程序。是否授予？',
    'Выдать право':
        '授予权限',
    'Не удалось выдать право Steam: {}':
        '无法为 Steam 授予权限：{}',
    "Регион игры":
        "游戏地区",
    "Вариант текста у языков с региональными версиями: испанский Испании (Европа) или Латинской Америки (Америка)":
        "有地区版本的语言所用的文本：西班牙的西班牙语（欧洲）或拉丁美洲西班牙语（美洲）",
    "Как в дампе игры":
        "与游戏转储相同",
    "Европа":
        "欧洲",
    "Америка":
        "美洲",
    "Включён брандмауэр: {}":
        "防火墙已开启：{}",
    "Для UPnP нужны ответы роутера: {}":
        "UPnP 需要接收路由器的应答：{}",
    "О программе":
        "关于",
    "Версия {}":
        "版本 {}",
    "Обновления":
        "更新",
    "Проверять обновления при запуске":
        "启动时检查更新",
    "Спрашивает GitHub о последнем выпуске; ничего не скачивается без вашего согласия":
        "向 GitHub 查询最新发布版本；未经你同意不会下载任何内容",
    "Последняя версия":
        "最新版本",
    "Загрузка…":
        "正在下载…",
    "Обновить":
        "更新",
    "Версия {} установлена: перезапустите лаунчер":
        "版本 {} 已安装：请重启启动器",
    "Перезапустить":
        "重启",
    "Не удалось проверить: {}":
        "无法检查：{}",
    "Установлена версия {}":
        "已安装版本 {}",
    "Установлена последняя версия ({})":
        "已是最新版本（{}）",
    "Доступна версия {} (установлена {})":
        "版本 {} 已发布（当前为 {}）",
    "Открыть страницу":
        "打开页面",
    "Доступна версия {}":
        "版本 {} 已发布",
    "Подробнее":
        "详情",
    "Загрузка… {} %":
        "正在下载… {} %",
    "Загрузка… {} МБ":
        "正在下载… {} MB",
    "Не удалось обновить: {}":
        "无法更新：{}",
    "Сначала закройте игру":
        "请先关闭游戏",
    "Этот проект":
        "本项目",
    "Основано на bbport от deadinside28":
        "基于 deadinside28 的 bbport",
    "Порт для Windows от Supermedo":
        "Supermedo 的 Windows 移植版",
    "Лицензия":
        "许可证",
    'GNU GPL v2 или новее · Файлы игры не входят.': 'GNU GPL v2 或更高版本 · 不含游戏文件。',
    'Bloodborne принадлежит Sony Interactive Entertainment и FromSoftware.': 'Bloodborne 归 Sony Interactive Entertainment 和 FromSoftware 所有。',
    "Проверить сейчас":
        "立即检查",
    # Texts added after the upstream translation
    ", основной": "，主显示器",
    "0: случайный при каждом запуске. Закрепите его, чтобы открыть в брандмауэре или на роутере вручную": "0：每次使用随机端口。如需在防火墙或路由器上手动开放，请固定一个端口",
    "Bloodborne добавлен в библиотеку Steam": "Bloodborne 已添加到你的 Steam 库",
    "Online ID — это имя учётной записи (NPID), зарегистрированное на сервере, а не адрес email": "Online ID 是你在服务器上注册的账号名（NPID），而不是邮箱地址",
    "PlayStation (оригинал)": "PlayStation（原版）",
    "Steam не закрылся. Закройте его сами и попробуйте ещё раз": "Steam 没有关闭。请手动关闭后重试",
    "Steam не найден (или в него ещё никто не входил)": "未找到 Steam（或尚无人登录过）",
    "UDP сервера shadNet (призывы)": "shadNet 服务器的 UDP（召唤）",
    "UPnP (открыть порт на роутере автоматически)": "UPnP（自动在路由器上打开端口）",
    "UPnP открывает порт только на роутере; брандмауэр этого компьютера всё равно блокирует кооператив. Откройте порт: {}": "UPnP 只会在路由器上开放端口，本机防火墙仍会阻止联机合作。请开放端口：{}",
    "«Играет в Bloodborne» в профиле Discord, онлайн или офлайн": "无论在线或离线，都在你的 Discord 个人资料上显示“正在玩 Bloodborne”",
    "Автоматически (по контроллеру)": "自动（按手柄）",
    "Адрес WebAPI (пусто: порт 31315 сервера)": "WebAPI 地址（留空：使用服务器的 31315 端口）",
    "Адрес сервера (host:port)": "服务器地址（主机:端口）",
    "Бесшовный кооператив (экспериментально)": "无缝联机合作（实验性）",
    "В дампе игры нет трофеев (sce_sys/trophy)": "游戏转储中没有奖杯（sce_sys/trophy）",
    "Выбрать папку DLC": "选择 DLC 文件夹",
    "Выключено: игра остаётся офлайн, как раньше": "关闭：游戏和以前一样保持离线",
    "Выключите при Tailscale или другом VPN": "使用 Tailscale 或其他 VPN 时请关闭",
    "Добавить": "添加",
    "Добавить в Steam": "添加到 Steam",
    "Журнал скопирован": "日志已复制",
    "Журнал сохранён: {}": "日志已保存：{}",
    "Закрепите порт кооператива выше (например, {}): случайный порт в брандмауэре не открыть": "请在上方固定联机合作端口（例如 {}）：随机端口无法在防火墙中开放",
    "Закройте Steam и нажмите «Добавить» ещё раз": "请关闭 Steam 后再次点击“添加”",
    "Закрыть Steam": "关闭 Steam",
    "Записываются, когда игра их открывает, и показываются в игре": "游戏解锁奖杯时记录，并在游戏中显示",
    "Игра в библиотеке Steam запускается сразу, с настройками этого лаунчера": "从 Steam 库启动时会直接进入游戏，并使用本启动器的设置",
    "Игра сразу открывает главное меню в режиме вне сети (патч игры)": "游戏直接以离线模式进入主菜单（游戏补丁）",
    "Играть онлайн": "在线游玩",
    "Играть офлайн": "离线游玩",
    "Игровой сервер": "游戏服务器",
    "Игровой сервер (сообщения, пятна крови, призраки)": "游戏服务器（留言、血迹、幻影）",
    "Изменения игрового процесса": "玩法调整",
    "Иконки кнопок": "按键图标",
    "Поменять местами A и B": "交换 A 和 B",
    "Для контроллеров в стиле Nintendo: подтверждение на A, отмена на B. Применяется при запуске игры": "适用于任天堂风格的手柄：A 确认，B 返回。启动游戏时生效",
    "Имя учётной записи shadNet, не email. Зарегистрируйтесь на shadnet.shadps4.net или спросите владельца частного сервера. Пароль хранится на этом компьютере вместе с настройками лаунчера": "shadNet 账号名，不是邮箱。请在 shadnet.shadps4.net 注册，或向私人服务器的主人索取。密码会和启动器设置一起保存在这台电脑上",
    "Как запустить свой сервер": "如何搭建自己的服务器",
    "Ключ трофеев": "奖杯密钥",
    'Ключ трофеев PS4 (TrophyKey в shadPS4), 32 шестнадцатеричных символа: с ним названия и описания на языке игры. Хранится на этом компьютере. Без него они на английском':
        'PS4 的奖杯密钥（shadPS4 中的 TrophyKey），32 位十六进制数：填写后奖杯名称和说明使用游戏语言。仅保存在本机。未填写时为英文',
    "Копировать": "复制",
    "Меню жестов без значков управления движением": "手势菜单不显示体感操作图标",
    "Монитор": "显示器",
    "Найдено DLC: {}": "找到的 DLC：{}",
    "Не использовать DLC": "不使用 DLC",
    "Не используется": "未使用",
    "Не удалось добавить игру в Steam: {}": "无法将游戏添加到 Steam：{}",
    "Не удалось сохранить журнал: {}": "无法保存日志：{}",
    "Неверный ключ трофеев: названия недоступны": "奖杯密钥错误：无法显示名称",
    "Нет DLC этой игры в папке": "该文件夹中没有本游戏的 DLC",
    "Нужна папка adhoc из мода Nexus #253 (шрифты adhoc/font) — в dvdroot_ps4 игры или модом; без неё патч не применяется": "需要 Nexus 模组 #253 中的 adhoc 文件夹（字体位于 adhoc/font），放入游戏的 dvdroot_ps4 或作为模组加载；缺少它时不会应用此补丁",
    "Онлайн": "联机",
    "Основной": "主显示器",
    "Отмена": "取消",
    "Папка DLC": "DLC 文件夹",
    "Пароль": "密码",
    "Патчи игры версии 1.09, применяются при запуске. Для обычного прохождения и игры по сети оставьте их выключенными": "适用于 1.09 版本的游戏补丁，在启动时生效。正常游玩和在线游玩时请保持关闭",
    "Поддержать проект": "支持本项目",
    "Пока игра добавляется, Steam нужно закрыть; потом он запустится снова. Закрыть Steam?": "添加游戏时需要关闭 Steam，完成后会重新启动。要关闭 Steam 吗？",
    "Получен {}": "获得于 {}",
    "Получено {} из {}": "已获得 {} / {}",
    "Порт кооператива (UDP)": "联机合作端口（UDP）",
    "Призывы между разными локациями. Только если на сервере BloodborneSeamlessCoop=true, и у всех игроков так же": "可在不同区域之间召唤。仅当服务器设置了 BloodborneSeamlessCoop=true，且所有玩家都开启时有效",
    "Применяется при запуске игры": "在游戏启动时生效",
    "Проверить": "检测",
    "Проверить соединение": "检测连接",
    "Проверка…": "检测中…",
    "Пропускать выбор «по сети / вне сети»": "跳过「在线 / 离线」选择",
    "Публичный сервер shadPS4": "shadPS4 公共服务器",
    "Свой сервер": "自己的服务器",
    "Сервер shadNet": "shadNet 服务器",
    "Сервер кооператива (колокола и призывы)": "联机合作服务器（铃铛与召唤）",
    "Скрытый трофей": "隐藏奖杯",
    "Соединение": "连接",
    "Сообщения, пятна крови и призраки приходят с The Hunter's Dream; колокола и призывы идут через сервер shadNet. Игра по сети совместима с версией для Windows: нужны версия игры 1.09 и тот же сервер": "留言、血迹和幻影来自 The Hunter's Dream；铃铛与召唤通过 shadNet 服务器进行。联机可与 Windows 版互通：所有人都需要游戏版本 1.09 并使用同一服务器",
    "Статус в Discord": "Discord 状态",
    "Трофеи": "奖杯",
    "У всех в сессии должны быть одна версия игры (1.09) и один сервер. Читы меняют игру и для других игроков: выключайте их при совместной игре": "同一会话中的所有人必须使用相同的游戏版本（1.09）和同一服务器。作弊功能也会改变其他玩家的游戏：一起游玩时请关闭",
    "Учётная запись": "账号",
    "Учётная запись для игры онлайн указана, но «Играть онлайн» выключено": "已填写联机账号，但「在线游玩」未开启",
    "Читы": "作弊",
    "Экспорт журнала": "导出日志",
    "Экспорт журнала…": "导出日志…",
    "Эта сборка без модуля онлайна (libbbnet.so): игра только офлайн": "此版本没有联机模块（libbbnet.so）：只能离线游玩",
    "доступен": "可连接",
    "не отвечает: призывы не соединятся": "无响应：召唤将无法连接",
    "недоступен": "无法连接",
    "отвечает; ваш публичный адрес: {}": "有响应；你的公网地址：{}",
    "Вход в shadNet": "shadNet 登录",
    "неверное имя или пароль": "用户名或密码错误",
    "такой учётной записи нет на этом сервере": "此服务器上没有该账户",
    "эта учётная запись уже в сети (игра запущена?)": "该账户已经登录（游戏正在运行吗？）",
    "вход выполнен": "已登录",
    "вход не удался ({})": "登录失败（{}）",
    "Загрузки и плавность": "加载与流畅度",
    "Патчи игры из bbhost, применяются при запуске": "来自 bbhost 的游戏补丁，在启动时生效",
    "Быстрая загрузка после смерти": "死亡后快速加载",
    "Загрузка после смерти или перемещения у лампы идёт, пока грузится область (2–3 с), а не минимум 12 с": "死亡或通过提灯传送后的加载只持续区域加载所需的时间（2–3 秒），而不是至少 12 秒",
    "Без рывка каждые ~50 с": "消除每约 50 秒一次的卡顿",
    "Игра быстрее сжимает запись игрока: пропадает рывок ~23 мс примерно каждые 50 с": "游戏更快地压缩玩家记录：约每 50 秒一次、约 23 毫秒的卡顿消失",
    "Третий поток подготовки ресурсов": "第三个资源准备线程",
    "Во время игры работают три потока подготовки ресурсов, а не два. Экспериментально": "游戏中运行三个资源准备线程，而不是两个。实验性",
    # About: Thanks
    'Благодарности': '致谢',
    'Без них ничего этого не было бы': '没有他们，这一切都不可能实现',
    'Порт и его код': '移植及其代码',
    'Помощь и тесты': '帮助与测试',
    'Другие благодарности': '同样感谢',
    'bbport — порт, на котором построен весь этот проект': 'bbport，整个项目所基于的移植',
    'Игра по сети, DLSS, страница читов, добавление в Steam, значок и пропуск конвейеров, которые драйвер не может создать': '联机、DLSS、作弊页面、添加到 Steam、图标，以及跳过驱动无法创建的管线',
    'Собрал и адаптировал десятки исправлений: вылеты при загрузке, чёрные изображения, апскейлер, строка производительности в журнале': '收集并改编了数十项修复：加载时崩溃、黑色图像、超分辨率、日志中的性能行',
    'Чёрный предпросмотр персонажа, картинка экрана загрузки и память кэша текстур': '黑色的角色预览、加载画面图片与纹理缓存的内存',
    'Кэш текстур вовремя освобождает видеопамять': '纹理缓存及时释放显存',
    'Вылеты при загрузке областей': '加载区域时的崩溃',
    'Интерфейс, пропадавший не в 1080p, векторы движения больших чудовищ и ошибка памяти': '非 1080p 下消失的界面、大型野兽的运动矢量与一处内存错误',
    'Вылеты при загрузке некоторых карт и меню жестов с клавиатуры': '加载部分地图时的崩溃与键盘打开的手势菜单',
    'Экранная клавиатура для имени персонажа и уведомление о компиляции шейдеров': '角色名的屏幕键盘与着色器编译提示',
    "Быстрая загрузка после смерти и перемещения (bbhost) и сервер The Hunter's Dream": "死亡或传送后的快速加载（bbhost）与 The Hunter's Dream 服务器",
    'Сетевые библиотеки игры по сети и сервер для своего кооператива': '联机库与自建合作服务器',
    'Основа поддержки DLSS и модель FSR 4 без шлейфов за персонажами': 'DLSS 支持的基础，以及角色身后无拖影的 FSR 4 模型',
    'Апскейлер FSR 3.1': 'FSR 3.1 超分辨率',
    'Игра запускается, когда DLSS нельзя использовать': '无法使用 DLSS 时游戏仍可启动',
    'Перевод на упрощённый китайский': '简体中文翻译',
    'Звук игры на полной громкости': '游戏音频满音量',
    'Флажки и ползунки внутриигрового меню': '游戏内菜单的复选框与滑块',
    'Подробные отчёты с журналами и проверка исправлений': '附带日志的详细报告与修复测试',
    'Идея поменять местами A и B на контроллерах в стиле Nintendo': '在任天堂风格手柄上交换 A 与 B 的建议',
    'Проверка исправления видеопамяти': '测试显存修复',
    'Иконки кнопок Xbox и Switch (Nexus Mods)': 'Xbox 与 Switch 按键图标（Nexus Mods）',
    'Показал, какие текстуры нужны иконкам клавиатуры (Nexus Mods)': '指明了键盘图标需要哪些纹理（Nexus Mods）',
    'Патчи игры: высокий FPS, разрешение и другое': '游戏补丁：高帧率、分辨率等',
    'Рендерер и компилятор шейдеров': '渲染器与着色器重编译器',
    'Инструмент для сборки AppImage': '构建 AppImage 的工具',
    'Нашёл ошибку, из-за которой игра не запускалась на некоторых видеокартах': '发现了导致游戏在部分显卡上无法启动的错误',
    # Shader cache
    'Кэш шейдеров': '着色器缓存',
    'Очистить': '清除',
    '{}. Если после обновления картинка выглядит странно, очистите его: шейдеры соберутся заново (первые минуты в каждой зоне возможны рывки)': '{}。如果更新后画面异常，请清除：着色器会重新生成（每个区域的前几分钟可能卡顿）',
    'Пусто: шейдеры соберутся при игре': '空：着色器会在游玩时生成',
    'Очистить кэш шейдеров?': '清除着色器缓存？',
    'Игра соберёт шейдеры заново: первые минуты в каждой зоне возможны рывки. Сохранения и настройки не затрагиваются.': '游戏会重新生成着色器：每个区域的前几分钟可能卡顿。存档和设置不受影响。',
    'Названия трофеев на английском без ключа и звук при получении трофея': '无密钥时的英文奖杯名称与获得奖杯时的音效',
    'Буфер трафарета, в который писали цветные изображения': '被颜色图像写入的模板缓冲区',
    'Вход на публичный сервер shadNet без отключения': '在公共 shadNet 服务器上保持登录',
    'Игра по сети': '联机游戏',
    'Сервер shadNet не принимает bbport, игра осталась офлайн. Для игры по сети используйте свой сервер (страница «Онлайн»).': 'shadNet 服务器不接受 bbport，因此游戏保持离线。如需联机，请使用自己的服务器（“联机”页面）。',
    'Выход из игры из меню с контроллера и меню в пределах экрана': '用手柄从菜单退出游戏，以及菜单不超出屏幕',
    'Вылет видеоплеера при его остановке': '视频播放器停止时的崩溃',
    'Язык внутриигрового меню при запуске без окна лаунчера': '不经启动器窗口启动时游戏内菜单的语言',
    'DLSS в AppImage на NVIDIA': 'NVIDIA 上 AppImage 中的 DLSS',
    'Сверхширокие мониторы без растянутой картинки': '超宽屏显示器画面不再被拉伸',
}

# Translations by language code; Russian is the key itself. Strings missing in a translation
# fall back to English, not to the Russian key.
TRANSLATIONS = {"en": EN, "pt_BR": PT_BR, "es": ES, "it": IT, "fr": FR, "de": DE,
                "zh_CN": ZH_CN}
LANGUAGES = ("ru", *TRANSLATIONS)


def system_locale(env=os.environ):
    """The desktop's locale, lower case with underscores ("es_es.utf_8"), or ""."""
    for key in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        value = env.get(key, "")
        if value:
            return value.lower().replace("-", "_")
    return ""


def system_language():
    locale = system_locale()
    if locale.startswith("pt_br"):
        return "pt_BR"
    if locale.startswith("zh"):
        return "zh_CN"
    short = locale[:2]
    return short if short in LANGUAGES else "en"


# The PS4 system language (sceSystemServiceParamGetInt) the game picks its text and voices by,
# for the languages the game has; anything else gets English.
GAME_LANGUAGES = {"ja": 0, "en": 1, "fr": 2, "es": 3, "de": 4, "it": 5, "ru": 8}


def system_game_language(env=os.environ):
    return GAME_LANGUAGES.get(system_locale(env)[:2], 1)


_language = "ru"


def set_language(choice):
    """choice: one of LANGUAGES or "" (the system's)."""
    global _language
    _language = choice if choice in LANGUAGES else system_language()


def language():
    return _language


def tr(text):
    table = TRANSLATIONS.get(_language)
    if table is None:
        return text
    return table.get(text, EN.get(text, text))

