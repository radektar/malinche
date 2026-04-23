"""Native download progress window for dependency downloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class DownloadWindowState:
    """Simple state container used by wizard/menu."""

    title: str
    detail: str
    progress: float = 0.0
    closed: bool = False


class DownloadWindow:
    """Best-effort native progress window.

    Falls back to no-op behavior when AppKit is unavailable.
    """

    def __init__(self, title: str, detail: str):
        self.state = DownloadWindowState(title=title, detail=detail)
        self._appkit = None
        self._window = None
        self._label = None
        self._progress = None
        try:
            from AppKit import (
                NSWindow,
                NSWindowStyleMaskTitled,
                NSWindowStyleMaskClosable,
                NSRect,
                NSTextField,
                NSProgressIndicator,
                NSBackingStoreBuffered,
            )

            self._appkit = {
                "NSWindow": NSWindow,
                "NSWindowStyleMaskTitled": NSWindowStyleMaskTitled,
                "NSWindowStyleMaskClosable": NSWindowStyleMaskClosable,
                "NSRect": NSRect,
                "NSTextField": NSTextField,
                "NSProgressIndicator": NSProgressIndicator,
                "NSBackingStoreBuffered": NSBackingStoreBuffered,
            }
        except ImportError:
            self._appkit = None

    def show(self) -> None:
        if not self._appkit:
            return
        NSWindow = self._appkit["NSWindow"]
        NSRect = self._appkit["NSRect"]
        NSTextField = self._appkit["NSTextField"]
        NSProgressIndicator = self._appkit["NSProgressIndicator"]
        style = (
            self._appkit["NSWindowStyleMaskTitled"]
            | self._appkit["NSWindowStyleMaskClosable"]
        )

        self._window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSRect((0, 0), (460, 140)),
            style,
            self._appkit["NSBackingStoreBuffered"],
            False,
        )
        self._window.setTitle_(self.state.title)

        content = self._window.contentView()
        self._label = NSTextField.alloc().initWithFrame_(NSRect((20, 80), (420, 40)))
        self._label.setStringValue_(self.state.detail)
        self._label.setBezeled_(False)
        self._label.setDrawsBackground_(False)
        self._label.setEditable_(False)
        self._label.setSelectable_(False)
        content.addSubview_(self._label)

        self._progress = NSProgressIndicator.alloc().initWithFrame_(NSRect((20, 40), (420, 20)))
        self._progress.setIndeterminate_(False)
        self._progress.setMinValue_(0.0)
        self._progress.setMaxValue_(100.0)
        self._progress.setDoubleValue_(0.0)
        content.addSubview_(self._progress)
        self._window.makeKeyAndOrderFront_(None)

    def update(self, detail: Optional[str] = None, progress: Optional[float] = None) -> None:
        if detail is not None:
            self.state.detail = detail
        if progress is not None:
            self.state.progress = max(0.0, min(1.0, progress))

        if self._label is not None:
            self._label.setStringValue_(self.state.detail)
        if self._progress is not None:
            self._progress.setDoubleValue_(self.state.progress * 100.0)

    def close(self) -> None:
        self.state.closed = True
        if self._window is not None:
            self._window.close()

