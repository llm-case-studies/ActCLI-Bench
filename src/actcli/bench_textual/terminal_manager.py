"""Terminal lifecycle, state management, and I/O handling.

This module manages terminal instances, their emulators, PTY sizing,
and output buffering. Extracted from app.py to isolate complex
dimension handling logic.

DIMENSION ORDERING CLARITY:
- Our API uses: (cols, rows) = (WIDTH, HEIGHT)
- PTY uses: (rows, cols) = (HEIGHT, WIDTH) in winsize struct
- pyte uses: columns (width), lines (height)

See tests/bench_textual/test_terminal_manager.py for comprehensive
documentation of these orderings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Callable, List
import re
from datetime import datetime

from .terminal_runner import TerminalRunner
from .term_emulator import EmulatedTerminal


@dataclass
class TerminalState:
    """Consolidated state for a single terminal.

    Replaces multiple scattered dictionaries with a single state object.
    """
    item: TerminalRunner
    emulator: EmulatedTerminal
    scroll_buffer: List[str] = field(default_factory=list)
    scroll_offset: int = 0
    winsize_history: List[str] = field(default_factory=list)
    output_buffer: str = ""
    last_synced_size: Optional[tuple[int, int]] = None


class TerminalManager:
    """Manages terminal lifecycle, sizing, and I/O.

    Responsibilities:
    - Create and destroy terminals
    - Manage terminal state (emulator, buffers, history)
    - Handle PTY resize events
    - Process terminal output
    - Write to terminal stdin
    """

    def __init__(
        self,
        debug_logger: Optional[Callable[[str], None]] = None,
        log_manager: Optional[object] = None,  # LogManager
        max_scrollback_lines: int = 2000,
        on_output_callback: Optional[Callable[[str, str], None]] = None
    ):
        """Initialize terminal manager.

        Args:
            debug_logger: Optional callback for debug messages
            log_manager: Optional LogManager for output logging
            max_scrollback_lines: Maximum lines to keep in scrollback buffer
            on_output_callback: Optional callback(name, text) called when terminal output arrives
        """
        self.terminals: Dict[str, TerminalState] = {}
        self.active_terminal: Optional[str] = None
        self._debug_logger = debug_logger or (lambda msg: None)
        self._log_manager = log_manager
        self.max_scrollback_lines = max_scrollback_lines
        self._emulator_mode_logged: set[str] = set()
        self._on_output_callback = on_output_callback

    def add_terminal(self, name: str, command: List[str]) -> bool:
        """Create and start a new terminal.

        Args:
            name: Terminal identifier
            command: Command to execute (e.g., ["bash", "-c", "tree"])

        Returns:
            True if terminal started successfully
        """
        if name in self.terminals:
            self._debug_logger(f"Terminal '{name}' already exists")
            return False

        # Create PTY runner
        runner = TerminalRunner(
            name=name,
            command=command,
            muted=True,
            debug_logger=self._debug_logger
        )

        # Set output callback to capture terminal output
        def on_output(text: str):
            self._append_terminal_output(name, text)

        def on_exit(code: int):
            self._debug_logger(f"Terminal '{name}' exited with code {code}")

        runner.on_output(on_output)
        runner.on_exit(on_exit)

        # Create emulator first (before starting, so it's ready for output)
        emulator = EmulatedTerminal(debug_logger=self._debug_logger)

        # Log emulator mode once
        self._log_emulator_mode(name, emulator)

        # Create state object
        state = TerminalState(
            item=runner,
            emulator=emulator,
            scroll_buffer=[],
            scroll_offset=0,
            winsize_history=[],
            output_buffer="",
            last_synced_size=None
        )

        # Add to terminals dict BEFORE starting, so output callbacks can find it
        self.terminals[name] = state

        # Set as active if first terminal
        if self.active_terminal is None:
            self.active_terminal = name

        # Start the PTY (may exit quickly, but that's OK - we've already added it)
        started = runner.start()
        if not started:
            self._debug_logger(f"Terminal '{name}' started but exited quickly")
        else:
            self._debug_logger(f"Added terminal '{name}': {' '.join(command)}")

        # Return True even if process exited quickly - the terminal was created
        return True

    def remove_terminal(self, name: str) -> bool:
        """Stop and remove a terminal.

        Args:
            name: Terminal identifier

        Returns:
            True if terminal was removed
        """
        if name not in self.terminals:
            return False

        state = self.terminals[name]
        state.item.close()
        del self.terminals[name]

        # Update active terminal if needed
        if self.active_terminal == name:
            self.active_terminal = next(iter(self.terminals.keys()), None)

        self._debug_logger(f"Removed terminal '{name}'")
        return True

    def sync_terminal_size(self, name: str, cols: int, rows: int) -> None:
        """Synchronize terminal size: emulator and PTY.

        This is the central method for handling terminal resize.

        Args:
            name: Terminal identifier
            cols: Width in columns (chars per line)
            rows: Height in rows (number of lines)
        """
        if name not in self.terminals:
            return

        state = self.terminals[name]
        emu = state.emulator
        runner = state.item

        # Skip if size hasn't changed
        if state.last_synced_size == (cols, rows):
            return

        # Resize emulator (pyte screen)
        old_size = (emu.cols, emu.rows)
        emu.resize(cols=cols, rows=rows)
        self._debug_logger(f"Resized emulator from {old_size} to {cols}x{rows}")
        state.last_synced_size = (cols, rows)

        # Resize PTY (note: PTY uses rows, cols order!)
        try:
            runner.set_winsize(rows=rows, cols=cols)
            actual = runner.get_winsize()

            # Log to winsize history
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            history_entry = (
                f"{timestamp} view={cols}x{rows} "
                f"emu={emu.cols}x{emu.rows} "
                f"requested={rows}x{cols} actual={actual}"
            )
            state.winsize_history.append(history_entry)

            # Keep last 20 entries
            if len(state.winsize_history) > 20:
                state.winsize_history = state.winsize_history[-20:]

            self._debug_logger(f"Synced PTY winsize: requested={rows}x{cols} actual={actual}")

        except Exception as e:
            self._debug_logger(f"PTY resize failed: {e}")

    def write_to_terminal(self, name: str, data: str) -> bool:
        """Write data to terminal's stdin.

        Args:
            name: Terminal identifier
            data: Data to write

        Returns:
            True if write succeeded
        """
        if name not in self.terminals:
            return False

        state = self.terminals[name]
        state.item.write(data)
        return True

    def get_terminal_text(self, name: str, show_cursor: bool = True) -> Optional[str]:
        """Get rendered terminal text from emulator.

        Args:
            name: Terminal identifier
            show_cursor: Whether to show cursor indicator

        Returns:
            Rendered text, or None if terminal doesn't exist
        """
        if name not in self.terminals:
            return None

        state = self.terminals[name]
        return state.emulator.text_with_cursor(show=show_cursor)

    def get_scrollback_text(
        self,
        name: str,
        offset: int = 0,
        height: int = 40
    ) -> Optional[str]:
        """Get scrollback buffer text.

        Args:
            name: Terminal identifier
            offset: Scroll offset (0 = bottom/present)
            height: Number of lines to show

        Returns:
            Scrollback text with indicator, or None if terminal doesn't exist
        """
        if name not in self.terminals:
            return None

        state = self.terminals[name]
        buf = state.scroll_buffer

        if not buf:
            return None

        # Calculate view window
        start = max(0, len(buf) - height - offset)
        view = buf[start:start + height]

        # Add indicator if scrolled
        indicator = f"[SCROLLBACK offset={offset}]\n" if offset > 0 else ""
        return indicator + "\n".join(view)

    def _append_terminal_output(self, name: str, text: str) -> None:
        """Process output from terminal PTY.

        This is called by the PTY runner's output callback.

        Args:
            name: Terminal identifier
            text: Raw output from PTY
        """
        if name not in self.terminals:
            return

        state = self.terminals[name]
        emu = state.emulator

        # Respond to Device Status Report requests (ESC[6n)
        if "\x1b[6n" in text:
            self._respond_to_dsr(name, state)

        # Feed to emulator
        emu.feed(text)

        # Update output buffer
        state.output_buffer += text
        if len(state.output_buffer) > 4096:
            state.output_buffer = state.output_buffer[-4096:]

        # Update scrollback buffer (ANSI-stripped plain text)
        for line in text.splitlines():
            clean = self._strip_ansi(line)
            if clean:
                state.scroll_buffer.append(clean)
                if len(state.scroll_buffer) > self.max_scrollback_lines:
                    state.scroll_buffer.pop(0)

                # Log to LogManager if available
                if self._log_manager:
                    try:
                        self._log_manager.add("output", f"[{name}] {clean}")
                    except Exception:
                        pass

        # Notify app.py if callback is set
        if self._on_output_callback:
            self._on_output_callback(name, text)

    def _respond_to_dsr(self, name: str, state: TerminalState) -> None:
        """Reply to Device Status Report (cursor position) requests."""

        emu = state.emulator
        if emu.mode != "pyte":
            return

        cursor = getattr(emu._screen, "cursor", None)  # type: ignore[attr-defined]
        if cursor is None:
            return

        row = getattr(cursor, "y", 0) + 1
        col = getattr(cursor, "x", 0) + 1
        response = f"\x1b[{row};{col}R"

        self._debug_logger(f"[{name}] DSR → responding with {repr(response)}")
        try:
            state.item.write(response)
        except Exception:
            pass

    def _strip_ansi(self, s: str) -> str:
        """Strip ANSI escape sequences from string.

        Args:
            s: String potentially containing ANSI codes

        Returns:
            Cleaned string
        """
        patterns = [
            r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])",
            r"\x1B\][^\x07]*\x07",
            r"\x1B\][^\x1B]*\x1B\\",
            r"\x1B[PX^_][^\x1B]*\x1B\\",
            r"\x1B[\[\]()][0-9;]*[A-Za-z<>]",
        ]
        result = s
        for pattern in patterns:
            result = re.sub(pattern, "", result)
        return result

    def _log_emulator_mode(self, name: str, emulator: EmulatedTerminal) -> None:
        """Log emulator mode once per terminal.

        Args:
            name: Terminal identifier
            emulator: EmulatedTerminal instance
        """
        if name in self._emulator_mode_logged:
            return

        self._emulator_mode_logged.add(name)

        if emulator.mode == "pyte":
            version = emulator.pyte_version or "unknown"
            msg = f"EmulatedTerminal: using pyte {version}"
        else:
            msg = "EmulatedTerminal: pyte not available -- falling back to plain"

        self._debug_logger(f"[{name}] {msg}")

    def get_terminal_state(self, name: str) -> Optional[TerminalState]:
        """Get terminal state object.

        Args:
            name: Terminal identifier

        Returns:
            TerminalState or None if not found
        """
        return self.terminals.get(name)

    def list_terminals(self) -> List[str]:
        """Get list of terminal names.

        Returns:
            List of terminal identifiers
        """
        return list(self.terminals.keys())

    def is_terminal_alive(self, name: str) -> bool:
        """Check if terminal process is alive.

        Args:
            name: Terminal identifier

        Returns:
            True if terminal is alive
        """
        if name not in self.terminals:
            return False

        return self.terminals[name].item.is_alive()
