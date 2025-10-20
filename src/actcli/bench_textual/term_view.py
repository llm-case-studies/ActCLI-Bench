from __future__ import annotations

from typing import Callable, Optional

from textual.widgets import Static
from textual.events import Key, MouseScroll


class TermView(Static):
    """Focusable terminal view that forwards keystrokes to a writer.

    The bench sets a writer callback that receives text/escape sequences
    which are written to the active PTY.
    """

    can_focus = True

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._writer: Optional[Callable[[str], None]] = None
        self._navigator: Optional[Callable[[str, int], bool]] = None

    def set_writer(self, writer: Callable[[str], None]) -> None:
        self._writer = writer

    def set_navigator(self, handler: Callable[[str, int], bool]) -> None:
        """Set navigator handler; returns True if handled.

        action in {'pageup','pagedown','home','end','wheel'}; amount is lines.
        """
        self._navigator = handler

    # --- Key handling -------------------------------------------------

    def on_key(self, event: Key) -> None:  # type: ignore[override]
        # Scrollback with Ctrl+PageUp/PageDown/Home/End
        if self._navigator and event.key:
            k = event.key.lower()
            mods = set(event.modifiers or [])
            if 'ctrl' in mods and k in ('pageup','pagedown','home','end'):
                mapping = {
                    'pageup': ('pageup', -20),
                    'pagedown': ('pagedown', 20),
                    'home': ('home', 0),
                    'end': ('end', 0),
                }
                action, amount = mapping[k]
                if self._navigator(action, amount):
                    event.stop()
                    return
        if not self._writer:
            return

        seq: Optional[str] = None
        k = event.key.lower() if event.key else ""

        # Printable characters
        if event.character and len(event.character) == 1:
            seq = event.character

        # Control keys
        mapping = {
            "enter": "\r",
            "return": "\r",
            "backspace": "\x7f",
            "tab": "\t",
            "escape": "\x1b",
            "left": "\x1b[D",
            "right": "\x1b[C",
            "up": "\x1b[A",
            "down": "\x1b[B",
            "home": "\x1b[H",
            "end": "\x1b[F",
            "pageup": "\x1b[5~",
            "pagedown": "\x1b[6~",
            "delete": "\x1b[3~",
            "insert": "\x1b[2~",
            "ctrl+c": "\x03",
            "ctrl+d": "\x04",
            "ctrl+z": "\x1a",
            "ctrl+l": "\x0c",
        }

        if seq is None:
            seq = mapping.get(k)

        if seq is not None:
            try:
                self._writer(seq)
                event.stop()
            except Exception:
                pass

    def on_mouse_scroll(self, event: MouseScroll) -> None:  # type: ignore[override]
        if self._navigator:
            amount = 3 if event.delta_y > 0 else -3
            if self._navigator('wheel', amount):
                event.stop()
