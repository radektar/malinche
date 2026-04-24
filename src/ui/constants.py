"""UI constants - easy to replace during redesign."""

# Application metadata
APP_VERSION = "2.0.0-alpha.13"
APP_NAME = "Malinche"
APP_AUTHOR = "Malinche Team"
APP_WEBSITE = "https://malinche.app"
APP_GITHUB = "https://github.com/radektar/malinche"

# UI texts dictionary (for future localization)
TEXTS = {
    "settings_title": "Ustawienia Malinche",
    "settings_message": "Skonfiguruj folder docelowy, język i model transkrypcji.",
    "wizard_basic_title": "Podstawowa konfiguracja",
    "wizard_basic_message": "Skonfiguruj folder docelowy, język i model transkrypcji.",
    "saved_title": "Ustawienia zapisane",
    "saved_message": "Zmiany zostały zapisane i będą użyte przy następnej transkrypcji.",
    "about_title": "O aplikacji",
    "about_message": (
        f"{APP_NAME} v{APP_VERSION}\n\n"
        "Automatyczna transkrypcja nagrań audio\n"
        "z dyktafonów i kart SD.\n\n"
        f"Strona: {APP_WEBSITE}\n"
        f"GitHub: {APP_GITHUB}\n\n"
        "© 2025 - Open Source (MIT)"
    ),
    "reset_memory_title": "Resetuj pamięć",
    "reset_memory_message": (
        "Od jakiej daty chcesz przetworzyć nagrania ponownie?\n\n"
        "Wybierz opcję:"
    ),
    "reset_memory_7days": "7 dni",
    "reset_memory_30days": "30 dni",
    "reset_memory_custom": "Inna data...",
    "reset_memory_custom_input": "Format: YYYY-MM-DD (np. 2025-12-01)",
    "reset_memory_invalid_date": "Nieprawidłowy format daty. Użyj formatu YYYY-MM-DD.",
    "reset_memory_success": "Pamięć zresetowana",
    "reset_memory_error": "Nie udało się zresetować pamięci. Sprawdź logi.",
    "folder_picker_title": "📂 Folder na transkrypcje",
    "folder_picker_message": "Gdzie zapisywać pliki z transkrypcjami?",
    "folder_picker_select": "Wybierz folder...",
    "folder_picker_default": "Użyj domyślnego",
    "folder_picker_back": "Wstecz",
}


