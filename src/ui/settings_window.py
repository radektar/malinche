"""Settings window for changing application configuration."""

import rumps
from pathlib import Path

from src.config import UserSettings, SUPPORTED_LANGUAGES, SUPPORTED_MODELS
from src.ui.dialogs import choose_folder_dialog
from src.ui.constants import TEXTS
from src.logger import logger
from src.vault_index import is_icloud_synced
from src.setup.dependency_manager import DependencyManager


def _truncate_path(path: str, max_length: int = 60) -> str:
    if len(path) <= max_length:
        return path
    return "..." + path[-(max_length - 3):]


_API_KEY_PLACEHOLDER = "—"  # Wartość wyświetlana gdy klucz jest, ale nie pokazujemy go.


def _mask_api_key(key: str | None) -> str:
    """Wyświetlana wartość pola klucza: maskowana albo pusta."""
    if not key:
        return ""
    return _API_KEY_PLACEHOLDER  # Pusta linia maskuje pełną wartość; secure field i tak ją chroni.


def _show_native_settings_panel(settings: UserSettings) -> bool:
    """Show one native panel with folder/language/model/api-key in one place."""
    from AppKit import (
        NSAlert,
        NSPopUpButton,
        NSRect,
        NSSecureTextField,
        NSTextField,
        NSView,
    )

    from src.ui.folder_picker import (
        FolderPickerTarget,
        PICK_FOLDER_RESPONSE,
        apply_basic_settings,
        make_folder_picker_button,
        select_folder_with_warning,
    )

    selected_folder = str(settings.output_dir)
    language_codes = list(SUPPORTED_LANGUAGES.keys())
    model_codes = list(SUPPORTED_MODELS.keys())
    selected_language = settings.language if settings.language in language_codes else language_codes[0]
    selected_model = settings.whisper_model if settings.whisper_model in model_codes else model_codes[0]
    original_api_key = settings.ai_api_key or ""

    picker_target = FolderPickerTarget.alloc().init()

    while True:
        alert = NSAlert.alloc().init()
        alert.setMessageText_(TEXTS["settings_title"])
        alert.setInformativeText_(TEXTS["settings_message"])
        alert.addButtonWithTitle_("Zapisz")
        alert.addButtonWithTitle_("Anuluj")

        # Powiększone z 170 do 230 — dwa nowe wiersze na klucz API.
        accessory = NSView.alloc().initWithFrame_(NSRect((0, 0), (460, 230)))

        folder_label = NSTextField.alloc().initWithFrame_(NSRect((0, 200), (130, 20)))
        folder_label.setStringValue_("Folder docelowy:")
        folder_label.setBezeled_(False)
        folder_label.setDrawsBackground_(False)
        folder_label.setEditable_(False)
        folder_label.setSelectable_(False)
        accessory.addSubview_(folder_label)

        folder_value = NSTextField.alloc().initWithFrame_(NSRect((130, 200), (330, 20)))
        folder_value.setStringValue_(_truncate_path(selected_folder))
        folder_value.setBezeled_(False)
        folder_value.setDrawsBackground_(False)
        folder_value.setEditable_(False)
        folder_value.setSelectable_(True)
        accessory.addSubview_(folder_value)

        pick_button = make_folder_picker_button(
            NSRect((130, 168), (200, 28)),
            target=picker_target,
            title="Zmień folder...",
        )
        if pick_button is not None:
            accessory.addSubview_(pick_button)

        language_label = NSTextField.alloc().initWithFrame_(NSRect((0, 128), (130, 20)))
        language_label.setStringValue_("Język:")
        language_label.setBezeled_(False)
        language_label.setDrawsBackground_(False)
        language_label.setEditable_(False)
        language_label.setSelectable_(False)
        accessory.addSubview_(language_label)

        language_popup = NSPopUpButton.alloc().initWithFrame_(NSRect((130, 124), (330, 26)))
        for code, name in SUPPORTED_LANGUAGES.items():
            language_popup.addItemWithTitle_(f"{name} ({code})")
        language_popup.selectItemAtIndex_(language_codes.index(selected_language))
        accessory.addSubview_(language_popup)

        model_label = NSTextField.alloc().initWithFrame_(NSRect((0, 88), (130, 20)))
        model_label.setStringValue_("Model:")
        model_label.setBezeled_(False)
        model_label.setDrawsBackground_(False)
        model_label.setEditable_(False)
        model_label.setSelectable_(False)
        accessory.addSubview_(model_label)

        model_popup = NSPopUpButton.alloc().initWithFrame_(NSRect((130, 84), (330, 26)))
        for code, name in SUPPORTED_MODELS.items():
            model_popup.addItemWithTitle_(f"{code.upper()}: {name}")
        model_popup.selectItemAtIndex_(model_codes.index(selected_model))
        accessory.addSubview_(model_popup)

        api_key_label = NSTextField.alloc().initWithFrame_(NSRect((0, 48), (130, 20)))
        api_key_label.setStringValue_("Klucz Claude API:")
        api_key_label.setBezeled_(False)
        api_key_label.setDrawsBackground_(False)
        api_key_label.setEditable_(False)
        api_key_label.setSelectable_(False)
        accessory.addSubview_(api_key_label)

        api_key_field = NSSecureTextField.alloc().initWithFrame_(NSRect((130, 44), (330, 26)))
        # Pokazujemy maskowany placeholder gdy istnieje klucz; użytkownik widzi
        # że klucz jest set, ale samego sk-ant-... nie wyświetlamy.
        api_key_field.setStringValue_(_mask_api_key(original_api_key))
        api_key_field.setPlaceholderString_(
            "sk-ant-... (puste = bez zmian; wyczyść aby usunąć)"
        )
        accessory.addSubview_(api_key_field)

        api_key_hint = NSTextField.alloc().initWithFrame_(NSRect((0, 8), (460, 28)))
        api_key_hint.setStringValue_(
            "Klucz pobierzesz z console.anthropic.com → Settings → API keys."
            "\nAby usunąć klucz, wyczyść pole. Aby zachować obecny — zostaw bez zmian."
        )
        api_key_hint.setBezeled_(False)
        api_key_hint.setDrawsBackground_(False)
        api_key_hint.setEditable_(False)
        api_key_hint.setSelectable_(False)
        accessory.addSubview_(api_key_hint)

        alert.setAccessoryView_(accessory)
        response = alert.runModal()

        selected_language = language_codes[language_popup.indexOfSelectedItem()]
        selected_model = model_codes[model_popup.indexOfSelectedItem()]

        # Odczyt API key — interpretacja:
        # * pusty string = user wyczyścił → usuwamy klucz
        # * placeholder _API_KEY_PLACEHOLDER = user nic nie zmienił → zachowujemy oryginalny
        # * cokolwiek innego = user wpisał nowy klucz → zapisujemy
        api_key_input = str(api_key_field.stringValue() or "").strip()
        if api_key_input == _API_KEY_PLACEHOLDER:
            new_api_key: str | None = original_api_key or None
        elif api_key_input == "":
            new_api_key = None
        else:
            new_api_key = api_key_input

        if response == PICK_FOLDER_RESPONSE:
            picked = select_folder_with_warning(
                choose_folder_dialog,
                warn_non_icloud=lambda _p: rumps.alert(
                    title="Folder poza iCloud",
                    message=(
                        "Wybrany folder nie jest w iCloud. "
                        "Deduplikacja multi-device będzie działać tylko lokalnie."
                    ),
                    ok="OK",
                ),
                is_icloud_check=lambda p: is_icloud_synced(Path(p)),
                title="Wybierz folder docelowy",
                message="Wybierz folder, w którym będą zapisywane transkrypcje.",
            )
            if picked:
                selected_folder = picked
            # Po reotwarciu okna przywróć obecnie wpisany klucz, żeby nie zniknął.
            original_api_key = new_api_key or ""
            continue

        if response == 1001:
            return False

        basic_changed = apply_basic_settings(
            settings,
            selected_folder=selected_folder,
            selected_language=selected_language,
            selected_model=selected_model,
            supported_languages=SUPPORTED_LANGUAGES,
            supported_models=SUPPORTED_MODELS,
        )
        api_key_changed = (settings.ai_api_key or None) != new_api_key
        if api_key_changed:
            settings.ai_api_key = new_api_key
        return basic_changed or api_key_changed


def show_settings_window() -> bool:
    """Show settings window and allow user to change configuration."""
    settings = UserSettings.load()
    old_model = settings.whisper_model

    try:
        changed = _show_native_settings_panel(settings)
    except ImportError:
        logger.warning("AppKit not available, using text fallback")
        window = rumps.Window(
            title=TEXTS["settings_title"],
            message=(
                "Nie udało się uruchomić natywnego panelu.\n"
                "Wpisz folder docelowy ręcznie:"
            ),
            default_text=settings.output_dir,
            ok="Zapisz",
            cancel="Anuluj",
            dimensions=(350, 24),
        )
        result = window.run()
        if result.clicked == 0:
            return False
        new_folder = result.text.strip()
        changed = bool(new_folder and new_folder != settings.output_dir)
        if changed:
            settings.output_dir = new_folder

    if not changed:
        return False

    settings.save()
    logger.info("Ustawienia zostały zmienione i zapisane")

    # If model changed, asynchronously queue missing model artifacts.
    if settings.whisper_model != old_model:
        manager = DependencyManager()
        missing = manager.needed()
        if missing:
            total_mb = sum(size for _, size in missing) / 1_000_000
            rumps.alert(
                title="Pobieranie modelu",
                message=(
                    f"Nowy model: {settings.whisper_model}\n"
                    f"Brakujące dane: ~{total_mb:.0f}MB.\n\n"
                    "Pobieranie rozpocznie się w tle."
                ),
                ok="OK",
            )
            manager.download_async()

    rumps.alert(
        title=TEXTS["saved_title"],
        message=TEXTS["saved_message"],
        ok="OK",
    )
    return True

