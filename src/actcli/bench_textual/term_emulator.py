"""Simple VT100 terminal emulator wrapper using pyte.

When pyte is not installed, falls back to a noop renderer that
just accumulates plain text lines.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class _NoopScreen:
    cols: int
    rows: int
    _buffer: list[str]

    def __init__(self, cols: int, rows: int) -> None:
        self.cols = cols
        self.rows = rows
        self._buffer = []

    def feed(self, data: str) -> None:
        self._buffer.extend(data.splitlines())

    def display_text(self) -> str:
        lines = self._buffer[-self.rows :]
        return "\n".join(line[: self.cols] for line in lines)

    def resize(self, cols: int, rows: int) -> None:
        self.cols = cols
        self.rows = rows


class EmulatedTerminal:
    def __init__(self, cols: int = 120, rows: int = 32) -> None:
        self.cols = cols
        self.rows = rows
        self._use_pyte = False
        try:
            import pyte  # type: ignore

            self._screen = pyte.Screen(cols, rows)
            self._stream = pyte.ByteStream(self._screen)
            self._use_pyte = True
        except Exception:
            self._screen = _NoopScreen(cols, rows)  # type: ignore
            self._stream = None

    def feed(self, data) -> None:
        if self._use_pyte:
            try:
                if isinstance(data, str):
                    b = data.encode("utf-8", errors="replace")
                else:
                    b = data
                self._stream.feed(b)  # type: ignore[attr-defined]
            except Exception:
                pass
        else:
            self._screen.feed(data)  # type: ignore

    def text(self) -> str:
        if self._use_pyte:
            try:
                # pyte's Screen.display yields the visible lines
                return "\n".join(self._screen.display)  # type: ignore[attr-defined]
            except Exception:
                return ""
        else:
            return self._screen.display_text()  # type: ignore

    def resize(self, cols: int, rows: int) -> None:
        self.cols = cols
        self.rows = rows
        if self._use_pyte:
            try:
                self._screen.resize(cols, rows)  # type: ignore[attr-defined]
            except Exception:
                pass
        else:
            self._screen.resize(cols, rows)  # type: ignore
