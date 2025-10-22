"""Simple VT100 terminal emulator wrapper using pyte.

When pyte is not installed, falls back to a noop renderer that
just accumulates plain text lines.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Callable
import wcwidth
import re


# ANSI escape sequence pattern
# Matches: ESC [ ... m (SGR), ESC ] ... (OSC), ESC [ ... (CSI), etc.
_ANSI_ESCAPE_PATTERN = re.compile(
    r'\x1b\['  # CSI sequences: ESC [
    r'[0-9;]*'  # parameters
    r'[a-zA-Z]'  # final byte
    r'|'
    r'\x1b\]'  # OSC sequences: ESC ]
    r'[^\x07]*'  # data
    r'(?:\x07|\x1b\\)'  # terminator: BEL or ESC \
    r'|'
    r'\x1b[PX^_]'  # Other escape sequences
    r'[^\x1b]*'
    r'\x1b\\'
)


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text.

    This is critical for correct cursor positioning because:
    - ANSI codes take up bytes in the string
    - But have ZERO visual width
    - So we must strip them before calculating visual columns
    """
    return _ANSI_ESCAPE_PATTERN.sub('', text)


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
    def __init__(
        self,
        cols: int = 120,
        rows: int = 32,
        debug_logger: Optional[Callable[[str], None]] = None
    ) -> None:
        self.cols = cols
        self.rows = rows
        self._use_pyte = False
        self._pyte_version: Optional[str] = None
        self._debug_logger = debug_logger
        try:
            import pyte  # type: ignore

            # pyte.Screen(columns, lines) - note the order!
            self._screen = pyte.Screen(columns=cols, lines=rows)
            self._stream = pyte.ByteStream(self._screen)
            self._use_pyte = True
            self._pyte_version = getattr(pyte, "__version__", None)
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

    def _index_from_column(self, line: str, column: int) -> int:
        """Return string index that corresponds to a visual column.

        Uses wcwidth to account for wide/combining characters.
        """
        if self._debug_logger:
            # Log raw line with escape codes visible
            raw_repr = repr(line)
            self._debug_logger(f"[_index_from_column] target_column={column}, line_len={len(line)}")
            self._debug_logger(f"[_index_from_column] raw_line={raw_repr[:200]}")

            # Try stripping ANSI and compare
            stripped = _strip_ansi(line)
            if stripped != line:
                self._debug_logger(f"[_index_from_column] ANSI detected! stripped_len={len(stripped)}, original_len={len(line)}")
                self._debug_logger(f"[_index_from_column] stripped={repr(stripped[:100])}")

        if column <= 0:
            return 0
        width = 0
        for i, ch in enumerate(line):
            w = wcwidth.wcwidth(ch)
            if w < 0:
                w = 0
            if width + w >= column:
                if self._debug_logger:
                    self._debug_logger(f"[_index_from_column] found at index={i+1}, char={repr(ch)}, accumulated_width={width}")
                return i + 1
            width += w

        if self._debug_logger:
            self._debug_logger(f"[_index_from_column] reached end, returning len={len(line)}, accumulated_width={width}")
        return len(line)

    def _find_input_line(self, lines: list[str], cursor_y: int, cursor_x: int) -> tuple[int, int]:
        """Find the actual input line when cursor is misplaced.

        Some terminals (Gemini, Claude) use full-screen redraws and never update
        pyte's cursor position. This function searches for the input prompt and
        places the cursor at the end of visible content.

        Returns: (line_index, column_position) or (-1, -1) if not found
        """
        # Strategy: Look for input prompt pattern anywhere in the screen
        # Start from the cursor line and search backwards

        # First check if cursor line has the input prompt (most common case for bash)
        if cursor_y < len(lines):
            line = lines[cursor_y]
            # Check for prompt patterns on the cursor line
            if '>' in line:
                # Could be bash prompt or input box prompt
                stripped = line.lstrip()
                if not (stripped.startswith('│ >') or stripped.startswith('> ')):
                    # Not an input box, probably bash - trust pyte
                    if self._debug_logger:
                        self._debug_logger(f"[_find_input_line] Cursor line has content, trusting pyte")
                    return (-1, -1)

        # Look for input box patterns (Gemini/Claude style)
        # Search from bottom up, limiting to reasonable range
        search_start = min(len(lines) - 1, cursor_y + 5)
        search_end = max(0, cursor_y - 15)

        for i in range(search_start, search_end, -1):
            if i >= len(lines):
                continue
            line = lines[i]

            # Look for input box pattern: "│ >" or standalone "> "
            if '│ >' in line:
                # Found Gemini/Claude style input box
                prompt_idx = line.index('│ >') + 3  # After "│ >"

                # Extract content between prompt and trailing │
                content_after_prompt = line[prompt_idx:]
                if '│' in content_after_prompt:
                    content_after_prompt = content_after_prompt[:content_after_prompt.rindex('│')]

                # Remove placeholder text patterns
                content = content_after_prompt.strip()

                # Skip if this looks like placeholder text (common patterns)
                if content.startswith('Type your message') or content.startswith('type '):
                    content = ''  # Treat as empty, cursor goes right after prompt

                cursor_col = prompt_idx + len(content)
                if content:  # If there's content, add 1 space after it
                    cursor_col += 1

                if self._debug_logger:
                    self._debug_logger(f"[_find_input_line] Found input box at line {i}, col {cursor_col}")
                    self._debug_logger(f"[_find_input_line] Input line: {repr(line[:100])}")
                    self._debug_logger(f"[_find_input_line] Content: {repr(content)}")

                return (i, cursor_col)

        # No input box found, trust pyte
        if self._debug_logger:
            self._debug_logger(f"[_find_input_line] No input box found, trusting pyte")
        return (-1, -1)

    def text_with_cursor(self, cursor_char: str = "▌", show: bool = True) -> str:
        """Return screen text with a visual caret at the current cursor.

        When pyte is active, uses screen.cursor (x,y). Otherwise, appends
        a caret at end of the last line.
        """
        if not show:
            return self.text()
        if not self._use_pyte:
            base = self._screen.display_text()  # type: ignore
            if not base:
                return cursor_char
            lines = base.splitlines()
            if lines:
                lines[-1] = f"{lines[-1]}{cursor_char}"
            return "\n".join(lines)

        try:
            # Obtain current display and cursor position
            lines = list(self._screen.display)  # type: ignore[attr-defined]
            cx = getattr(self._screen, "cursor").x  # type: ignore[attr-defined]
            cy = getattr(self._screen, "cursor").y  # type: ignore[attr-defined]

            if self._debug_logger:
                self._debug_logger(f"[text_with_cursor] pyte cursor position: (x={cx}, y={cy})")
                self._debug_logger(f"[text_with_cursor] total lines in display: {len(lines)}")

            # Check if cursor is on a blank line and try to find actual input
            actual_line, actual_col = self._find_input_line(lines, cy, cx)
            if actual_line != -1:
                # Found actual input line, override cursor position
                if self._debug_logger:
                    self._debug_logger(f"[text_with_cursor] Overriding cursor: ({cx},{cy}) -> ({actual_col},{actual_line})")
                cx = actual_col
                cy = actual_line

            if 0 <= cy < len(lines):
                line = lines[cy]
                if self._debug_logger:
                    self._debug_logger(f"[text_with_cursor] line[{cy}] length={len(line)}, content={repr(line[:80])}")
                    # Log the full line in hex to see any hidden characters
                    line_bytes = line.encode('utf-8', errors='replace')
                    if len(line_bytes) > 200:
                        self._debug_logger(f"[text_with_cursor] line_bytes(truncated)={line_bytes[:200]}")
                    else:
                        self._debug_logger(f"[text_with_cursor] line_bytes={line_bytes}")

                # Map column to string index
                idx = self._index_from_column(line, cx)

                if self._debug_logger:
                    self._debug_logger(f"[text_with_cursor] calculated string index={idx} for column={cx}")

                if idx >= len(line):
                    line = line + " "
                    idx = len(line) - 1
                    if self._debug_logger:
                        self._debug_logger(f"[text_with_cursor] index beyond line, appended space, new_idx={idx}")

                # Insert cursor character
                modified_line = line[:idx] + cursor_char + line[idx:]
                if self._debug_logger:
                    self._debug_logger(f"[text_with_cursor] inserting cursor at idx={idx}")
                    self._debug_logger(f"[text_with_cursor] before={repr(line[max(0,idx-10):idx+10])}")
                    self._debug_logger(f"[text_with_cursor] after={repr(modified_line[max(0,idx-10):idx+15])}")

                lines[cy] = modified_line
            return "\n".join(lines)
        except Exception as e:
            if self._debug_logger:
                self._debug_logger(f"[text_with_cursor] ERROR: {e}")
            return self.text()

    def resize(self, cols: int, rows: int) -> None:
        self.cols = cols
        self.rows = rows
        if self._use_pyte:
            try:
                # CRITICAL: pyte.Screen.resize(lines, columns) not (columns, lines)!
                self._screen.resize(lines=rows, columns=cols)  # type: ignore[attr-defined]
                # Debug: verify the resize actually worked
                if self._debug_logger:
                    actual_cols = getattr(self._screen, 'columns', '?')
                    actual_rows = getattr(self._screen, 'lines', '?')
                    self._debug_logger(f"[Emulator] resize(cols={cols}, rows={rows}) → pyte screen is now {actual_cols}x{actual_rows}")
            except Exception as e:
                if self._debug_logger:
                    self._debug_logger(f"[Emulator] resize(cols={cols}, rows={rows}) FAILED: {e}")
        else:
            self._screen.resize(cols, rows)  # type: ignore

    @property
    def mode(self) -> str:
        """Current rendering mode."""
        return "pyte" if self._use_pyte else "plain"

    @property
    def pyte_version(self) -> str:
        """Return detected pyte version or 'none' when unavailable."""
        return self._pyte_version or "none"
