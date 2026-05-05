"""Reusable dialog functions for UI."""

from datetime import datetime, timedelta
from typing import Optional
import rumps

from src.ui.constants import TEXTS, APP_NAME


def choose_folder_dialog(title: Optional[str] = None, message: Optional[str] = None) -> Optional[str]:
    """Open native folder picker dialog using NSOpenPanel.
    
    Args:
        title: Dialog title (defaults to TEXTS["folder_picker_title"])
        message: Dialog message (defaults to TEXTS["folder_picker_message"])
        
    Returns:
        Selected folder path or None if cancelled
    """
    try:
        from AppKit import NSOpenPanel
        
        panel = NSOpenPanel.openPanel()
        panel.setCanChooseFiles_(False)
        panel.setCanChooseDirectories_(True)
        panel.setAllowsMultipleSelection_(False)
        panel.setTitle_(title or TEXTS["folder_picker_title"])
        panel.setPrompt_("Choose")
        
        if panel.runModal() == 1:  # NSModalResponseOK
            url = panel.URLs()[0]
            return url.path()
    except ImportError:
        # Fallback if AppKit not available
        pass
    return None


def choose_date_dialog(default_days: int = 7) -> Optional[datetime]:
    """Show date selection dialog.
    
    Args:
        default_days: Default number of days ago (for input default)
        
    Returns:
        Selected datetime or None if cancelled
    """
    from src.logger import logger
    
    # Use alert with three buttons - ok, cancel, other
    # rumps.alert returns: 1 for ok, 0 for cancel, 2 for other (if other is provided)
    response = rumps.alert(
        title=TEXTS["reset_memory_title"],
        message=TEXTS["reset_memory_message"],
        ok=TEXTS["reset_memory_7days"],
        cancel=TEXTS["reset_memory_custom"],
        other=TEXTS["reset_memory_30days"],
    )
    
    logger.info(f"Date dialog response: {response} (type: {type(response)})")
    
    if response == 1:  # 7 days (ok button)
        logger.info("Selected: 7 days")
        return datetime.now() - timedelta(days=7)
    elif response == -1:  # 30 days (other button) - rumps returns -1 for "other"
        logger.info("Selected: 30 days")
        return datetime.now() - timedelta(days=30)
    elif response == 0:  # Custom date (cancel button)
        logger.info("Selected: Custom date")
        # Show input dialog
        default_date = (datetime.now() - timedelta(days=default_days)).strftime("%Y-%m-%d")
        window = rumps.Window(
            title="Enter date",
            message=TEXTS["reset_memory_custom_input"],
            default_text=default_date,
            ok="OK",
            cancel="Cancel",
            dimensions=(200, 24),
        )
        result = window.run()

        if result.clicked == 0:  # Cancel
            return None

        try:
            return datetime.strptime(result.text.strip(), "%Y-%m-%d")
        except ValueError:
            rumps.alert("Error", TEXTS["reset_memory_invalid_date"], ok="OK")
            return None
    
    return None


def show_about_dialog() -> None:
    """Show About dialog with app information."""
    rumps.alert(
        title=f"About {APP_NAME}",
        message=TEXTS["about_message"],
        ok="OK",
    )

