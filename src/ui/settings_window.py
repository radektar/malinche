"""Settings window for changing application configuration."""

from typing import Optional
import rumps

from src.config import UserSettings, SUPPORTED_LANGUAGES, SUPPORTED_MODELS
from src.ui.dialogs import choose_folder_dialog
from src.logger import logger


def show_settings_window() -> bool:
    """Show settings window and allow user to change configuration.
    
    Returns:
        True if settings were changed and saved, False otherwise
    """
    settings = UserSettings.load()
    changed = False
    
    # Show main settings menu in a loop until user is done
    while True:
        # Truncate long paths for display
        output_dir_display = settings.output_dir
        if len(output_dir_display) > 50:
            output_dir_display = "..." + output_dir_display[-47:]
        
        response = rumps.alert(
            title="⚙️ Ustawienia Malinche",
            message=(
                "Wybierz co chcesz zmienić:\n\n"
                f"📂 Folder docelowy:\n   {output_dir_display}\n"
                f"🗣️ Język: {SUPPORTED_LANGUAGES.get(settings.language, settings.language)}\n"
                f"🎯 Model: {SUPPORTED_MODELS.get(settings.whisper_model, settings.whisper_model)}\n"
            ),
            ok="Zmień folder",
            cancel="Zmień język",
            other="Zmień model",
        )
        
        item_changed = False
        if response == 1:  # Zmień folder
            item_changed = _change_output_folder(settings)
        elif response == 0:  # Zmień język (cancel button)
            item_changed = _change_language(settings)
        elif response == -1:  # Zmień model (other button)
            item_changed = _change_model(settings)
        
        if item_changed:
            changed = True
        
        # Ask if user wants to change more settings
        continue_response = rumps.alert(
            title="⚙️ Ustawienia",
            message=(
                "Zmiana zapisana.\n\n"
                "Czy chcesz zmienić coś jeszcze?"
            ),
            ok="Tak, zmień więcej",
            cancel="Zapisz i zamknij",
        )
        
        if continue_response == 0:  # Zapisz i zamknij
            break
    
    # If settings changed, save them
    if changed:
        settings.save()
        logger.info("Ustawienia zostały zmienione i zapisane")
        rumps.alert(
            title="✅ Ustawienia zapisane",
            message="Zmiany zostały zapisane i będą użyte przy następnej transkrypcji.",
            ok="OK"
        )
        return True
    else:
        # User didn't make any changes, just closed
        return False


def _change_output_folder(settings: UserSettings) -> bool:
    """Change output folder setting.
    
    Args:
        settings: UserSettings instance to modify
        
    Returns:
        True if folder was changed, False otherwise
    """
    # Show current folder and ask if user wants to change it
    response = rumps.alert(
        title="📂 Folder docelowy",
        message=(
            f"Aktualny folder:\n{settings.output_dir}\n\n"
            "Czy chcesz zmienić folder docelowy?"
        ),
        ok="Zmień folder",
        cancel="Anuluj",
    )
    
    if response != 1:  # Cancel
        return False
    
    # Open folder picker
    folder_path = choose_folder_dialog()
    if folder_path:
        settings.output_dir = folder_path
        logger.info(f"Zmieniono folder docelowy na: {folder_path}")
        return True
    
    return False


def _change_language(settings: UserSettings) -> bool:
    """Change transcription language setting.
    
    Args:
        settings: UserSettings instance to modify
        
    Returns:
        True if language was changed, False otherwise
    """
    try:
        from AppKit import NSAlert, NSPopUpButton, NSRect
        
        alert = NSAlert.alloc().init()
        alert.setMessageText_("🗣️ Język transkrypcji")
        alert.setInformativeText_(
            "Wybierz domyślny język dla wszystkich nagrań.\n\n"
            "To ustawienie będzie użyte przy następnej transkrypcji."
        )
        
        # Create dropdown
        popup = NSPopUpButton.alloc().initWithFrame_(NSRect((0, 0), (250, 24)))
        for code, name in SUPPORTED_LANGUAGES.items():
            popup.addItemWithTitle_(f"{name} ({code})")
        
        # Set current value
        lang_codes = list(SUPPORTED_LANGUAGES.keys())
        if settings.language in lang_codes:
            current_idx = lang_codes.index(settings.language)
            popup.selectItemAtIndex_(current_idx)
        
        # Add to alert
        alert.setAccessoryView_(popup)
        alert.addButtonWithTitle_("Zapisz")
        alert.addButtonWithTitle_("Anuluj")
        
        response = alert.runModal()
        # NSAlert button responses: 1000=Zapisz, 1001=Anuluj
        if response == 1000:  # Zapisz
            selected_idx = popup.indexOfSelectedItem()
            selected_code = lang_codes[selected_idx]
            if selected_code != settings.language:
                settings.language = selected_code
                logger.info(f"Zmieniono język na: {selected_code}")
                return True
        
        return False
        
    except ImportError:
        # Fallback to text input if AppKit not available
        logger.warning("AppKit not available, using text input fallback")
        lang_options = "\n".join(
            [f"• {code}: {name}" for code, name in SUPPORTED_LANGUAGES.items()]
        )
        
        window = rumps.Window(
            title="🗣️ Język transkrypcji",
            message=(
                f"Wpisz kod języka:\n\n"
                f"Dostępne opcje:\n{lang_options}\n\n"
                f"Aktualny: {settings.language}"
            ),
            default_text=settings.language,
            ok="Zapisz",
            cancel="Anuluj",
            dimensions=(200, 24),
        )
        result = window.run()
        
        if result.clicked == 0:  # Cancel
            return False
        
        lang = result.text.strip().lower()
        if lang in SUPPORTED_LANGUAGES:
            if lang != settings.language:
                settings.language = lang
                logger.info(f"Zmieniono język na: {lang}")
                return True
        
        return False


def _change_model(settings: UserSettings) -> bool:
    """Change Whisper model setting.
    
    Args:
        settings: UserSettings instance to modify
        
    Returns:
        True if model was changed, False otherwise
    """
    try:
        from AppKit import NSAlert, NSPopUpButton, NSRect
        
        alert = NSAlert.alloc().init()
        alert.setMessageText_("🎯 Model transkrypcji")
        alert.setInformativeText_(
            "Wybierz model Whisper do transkrypcji.\n\n"
            "Większe modele = lepsza jakość, ale wolniejsze.\n"
            "Zalecany: Small (dobra jakość i szybkość)."
        )
        
        # Create dropdown
        popup = NSPopUpButton.alloc().initWithFrame_(NSRect((0, 0), (300, 24)))
        for code, name in SUPPORTED_MODELS.items():
            popup.addItemWithTitle_(f"{code.upper()}: {name}")
        
        # Set current value
        model_codes = list(SUPPORTED_MODELS.keys())
        if settings.whisper_model in model_codes:
            current_idx = model_codes.index(settings.whisper_model)
            popup.selectItemAtIndex_(current_idx)
        
        # Add to alert
        alert.setAccessoryView_(popup)
        alert.addButtonWithTitle_("Zapisz")
        alert.addButtonWithTitle_("Anuluj")
        
        response = alert.runModal()
        # NSAlert button responses: 1000=Zapisz, 1001=Anuluj
        if response == 1000:  # Zapisz
            selected_idx = popup.indexOfSelectedItem()
            selected_code = model_codes[selected_idx]
            if selected_code != settings.whisper_model:
                settings.whisper_model = selected_code
                logger.info(f"Zmieniono model na: {selected_code}")
                return True
        
        return False
        
    except ImportError:
        # Fallback to text input if AppKit not available
        logger.warning("AppKit not available, using text input fallback")
        model_options = "\n".join(
            [f"• {code}: {name}" for code, name in SUPPORTED_MODELS.items()]
        )
        
        window = rumps.Window(
            title="🎯 Model transkrypcji",
            message=(
                f"Wpisz kod modelu:\n\n"
                f"Dostępne opcje:\n{model_options}\n\n"
                f"Aktualny: {settings.whisper_model}"
            ),
            default_text=settings.whisper_model,
            ok="Zapisz",
            cancel="Anuluj",
            dimensions=(200, 24),
        )
        result = window.run()
        
        if result.clicked == 0:  # Cancel
            return False
        
        model = result.text.strip().lower()
        if model in SUPPORTED_MODELS:
            if model != settings.whisper_model:
                settings.whisper_model = model
                logger.info(f"Zmieniono model na: {model}")
                return True
        
        return False

