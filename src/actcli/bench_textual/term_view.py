from __future__ import annotations

from typing import Callable, Optional

from textual.widgets import Static
from textual.events import Key
try:
    # Older Textual has MouseScrollUp/MouseScrollDown
    from textual.events import MouseScroll  # type: ignore
except Exception:  # pragma: no cover
    MouseScroll = None  # type: ignore
    from textual.events import MouseScrollUp, MouseScrollDown  # type: ignore


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
        self._on_focus_callback: Optional[Callable[[], None]] = None
        self._size_listener: Optional[Callable[[], None]] = None
        self._key_logger: Optional[Callable[[str, Optional[str], set[str]], None]] = None

        # Try to disable text wrapping - Static widget might be auto-wrapping
        # Check if these attributes exist and set them
        if hasattr(self, 'wrap'):
            self.wrap = False
        if hasattr(self, 'auto_wrap'):
            self.auto_wrap = False

    def set_writer(self, writer: Callable[[str], None]) -> None:
        self._writer = writer

    def set_navigator(self, handler: Callable[[str, int], bool]) -> None:
        """Set navigator handler; returns True if handled.

        action in {'pageup','pagedown','home','end','wheel'}; amount is lines.
        """
        self._navigator = handler

    def set_on_focus(self, callback: Callable[[], None]) -> None:
        """Set callback to call when view gains focus."""
        self._on_focus_callback = callback

    def set_size_listener(self, callback: Callable[[], None]) -> None:
        """Set callback invoked when the widget is resized."""
        self._size_listener = callback

    def set_key_logger(self, callback: Callable[[str, Optional[str], set[str]], None]) -> None:
        """Set callback invoked for raw key events."""
        self._key_logger = callback

    def on_focus(self) -> None:
        """Called when the view gains focus."""
        self.add_class("has-focus")
        if self._on_focus_callback:
            self._on_focus_callback()

    def on_blur(self) -> None:  # type: ignore[override]
        """Remove focus styling when focus is lost."""
        try:
            self.remove_class("has-focus")
        except Exception:
            pass

    def on_resize(self, event) -> None:  # type: ignore[override]
        if self._size_listener:
            try:
                self._size_listener()
            except Exception:
                pass
        parent = super()
        handler = getattr(parent, "on_resize", None)
        if callable(handler):
            return handler(event)
        return None

    # --- Key handling -------------------------------------------------

    def on_key(self, event: Key) -> None:  # type: ignore[override]
        try:
            # Scrollback with Ctrl+PageUp/PageDown/Home/End
            if self._navigator and getattr(event, 'key', None):
                k = (event.key or '').lower()
                mods = set(getattr(event, 'modifiers', []) or [])
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
            k = (event.key or '').lower()
            mods = set(getattr(event, "modifiers", []) or [])

            if self._key_logger:
                try:
                    self._key_logger(k, getattr(event, 'character', None), mods)
                except Exception:
                    pass

            # Printable characters
            ch = getattr(event, 'character', None)
            if ch and len(ch) == 1:
                seq = ch
            elif not ch and k and len(k) == 1 and not any(mod in getattr(event, "modifiers", []) for mod in ("ctrl", "alt", "meta")):
                seq = k

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
            }

            if seq is None:
                seq = mapping.get(k)

            # Ctrl+<char> handling
            if seq is None and "ctrl" in mods and k and len(k) == 1:
                ctrl_char = k.upper()
                seq = chr(ord(ctrl_char) & 0x1F)

            if seq is not None:
                try:
                    self._writer(seq)
                    event.stop()
                except Exception:
                    pass
        except Exception:
            # Swallow any unexpected key handling issues to avoid crashing the app
            pass

    def on_mouse_scroll_up(self, event) -> None:  # type: ignore[override]
        # Fallback for Textual versions without MouseScroll
        if self._navigator:
            if self._navigator('wheel', -3):
                event.stop()

    def on_mouse_scroll_down(self, event) -> None:  # type: ignore[override]
        if self._navigator:
            if self._navigator('wheel', 3):
                event.stop()

    # Newer Textual unified event
    if MouseScroll is not None:  # type: ignore
        def on_mouse_scroll(self, event: MouseScroll) -> None:  # type: ignore[override]
            if self._navigator:
                amount = 3 if getattr(event, 'delta_y', 0) > 0 else -3
                if self._navigator('wheel', amount):
                    event.stop()
