"""UI constants - easy to replace during redesign."""

# Application metadata
APP_VERSION = "2.0.0-beta.8"
APP_NAME = "Malinche"
APP_AUTHOR = "Malinche Team"
APP_WEBSITE = "https://malinche.app"
APP_GITHUB = "https://github.com/radektar/malinche"

# UI texts dictionary
TEXTS = {
    "settings_title": "Malinche Settings",
    "settings_message": "Configure output folder, language, and transcription model.",
    "wizard_basic_title": "Basic configuration",
    "wizard_basic_message": "Configure output folder, language, and transcription model.",
    "saved_title": "Settings saved",
    "saved_message": "Changes will apply to the next transcription.",
    "about_title": "About",
    "about_message": (
        f"{APP_NAME} v{APP_VERSION}\n\n"
        "Automatic transcription of audio recordings\n"
        "from voice recorders and SD cards.\n\n"
        f"Website: {APP_WEBSITE}\n"
        f"GitHub: {APP_GITHUB}\n\n"
        "© 2025 — Open Source (MIT)"
    ),
    "reset_memory_title": "Reset memory",
    "reset_memory_message": (
        "From which date should recordings be re-processed?\n\n"
        "Pick an option:"
    ),
    "reset_memory_7days": "7 days",
    "reset_memory_30days": "30 days",
    "reset_memory_custom": "Custom date…",
    "reset_memory_custom_input": "Format: YYYY-MM-DD (e.g., 2026-12-01)",
    "reset_memory_invalid_date": "Invalid date format. Use YYYY-MM-DD.",
    "reset_memory_success": "Memory reset",
    "reset_memory_error": "Memory reset failed. Check logs.",
    "folder_picker_title": "📂 Output folder",
    "folder_picker_message": "Where should transcripts be saved?",
    "folder_picker_select": "Choose folder…",
    "folder_picker_default": "Use default",
    "folder_picker_back": "Back",
}


