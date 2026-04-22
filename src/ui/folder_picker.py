"""Helpers for embedding a folder picker button inside NSAlert accessory views."""

from typing import Callable, Optional

try:
    from AppKit import NSApp, NSButton, NSRect
    from Foundation import NSObject

    APPKIT_AVAILABLE = True
except ImportError:  # pragma: no cover - headless tests
    NSApp = None  # type: ignore[assignment]
    NSButton = None  # type: ignore[assignment]
    NSRect = None  # type: ignore[assignment]
    NSObject = object  # type: ignore[assignment]
    APPKIT_AVAILABLE = False


# Custom modal return code used to signal "user pressed folder picker button".
PICK_FOLDER_RESPONSE = 1099


if APPKIT_AVAILABLE:

    class FolderPickerTarget(NSObject):  # type: ignore[misc]
        """Objective-C target for the folder picker button."""

        def pickFolder_(self, _sender):  # noqa: N802 - ObjC selector
            NSApp.stopModalWithCode_(PICK_FOLDER_RESPONSE)

else:

    class FolderPickerTarget:  # type: ignore[no-redef]
        """Stub used when AppKit is unavailable (tests / CI)."""

        def pickFolder_(self, _sender):  # pragma: no cover
            raise RuntimeError("AppKit not available")


def make_folder_picker_button(
    frame: "NSRect",
    target: FolderPickerTarget,
    title: str = "Wybierz folder...",
):
    """Create an NSButton wired to the supplied target.

    Args:
        frame: Button frame rectangle.
        target: Persistent target object (caller must keep a reference).
        title: Button label.

    Returns:
        Configured NSButton instance, or None if AppKit is unavailable.
    """
    if not APPKIT_AVAILABLE:
        return None
    button = NSButton.alloc().initWithFrame_(frame)
    button.setTitle_(title)
    button.setBezelStyle_(1)  # NSBezelStyleRounded
    button.setTarget_(target)
    button.setAction_("pickFolder:")
    return button


def apply_basic_settings(
    settings,
    selected_folder: str,
    selected_language: str,
    selected_model: str,
    supported_languages,
    supported_models,
) -> bool:
    """Validate and persist folder/language/model into UserSettings.

    Returns True when any field actually changed.
    """
    if selected_language not in supported_languages:
        raise ValueError(f"Unsupported language: {selected_language}")
    if selected_model not in supported_models:
        raise ValueError(f"Unsupported model: {selected_model}")
    if not selected_folder:
        raise ValueError("Output folder must not be empty")

    changed = (
        str(settings.output_dir) != selected_folder
        or settings.language != selected_language
        or settings.whisper_model != selected_model
    )
    if changed:
        settings.output_dir = selected_folder
        settings.language = selected_language
        settings.whisper_model = selected_model
    return changed


def select_folder_with_warning(
    choose_folder: Callable[..., Optional[str]],
    warn_non_icloud: Callable[[str], None],
    is_icloud_check: Callable[[str], bool],
    title: str,
    message: str,
) -> Optional[str]:
    """Run folder picker and surface iCloud warning through caller hooks.

    Returns the selected folder path or None if cancelled.
    """
    picked = choose_folder(title=title, message=message)
    if not picked:
        return None
    if not is_icloud_check(picked):
        warn_non_icloud(picked)
    return picked
