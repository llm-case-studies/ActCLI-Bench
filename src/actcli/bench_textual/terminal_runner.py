"""Minimal PTY terminal runner for Textual bench.

This wrapper aims to behave like an integrated terminal:
- Full stdin passthrough to the child process
- Periodic non-blocking reads from the PTY master to capture output
- A simple, line-oriented callback to stream output to the UI

Notes:
- This is a minimal fidelity terminal stream; it does not emulate
  cursor addressing. For higher fidelity, consider layering an emulator
  (e.g., `pyte`) on top.
"""

from __future__ import annotations

import os
import pty
import select
import sys
import threading
import fcntl
import termios
import struct
import signal
from dataclasses import dataclass, field
from typing import Callable, List, Optional
import shlex
import time


OutputCallback = Callable[[str], None]
ExitCallback = Callable[[int], None]


@dataclass
class TerminalRunner:
    name: str
    command: List[str]
    muted: bool = True
    pid: Optional[int] = None
    master_fd: Optional[int] = None
    _reader_thread: Optional[threading.Thread] = None
    _stop_event: threading.Event = field(default_factory=threading.Event)
    _on_output: Optional[OutputCallback] = None
    _on_exit: Optional[ExitCallback] = None
    _first_output: bytearray = field(default_factory=bytearray, init=False, repr=False)
    _last_requested_rows: Optional[int] = field(default=None, init=False, repr=False)
    _last_requested_cols: Optional[int] = field(default=None, init=False, repr=False)
    _post_output_resize_pending: bool = field(default=False, init=False, repr=False)
    _post_output_resize_done: bool = field(default=False, init=False, repr=False)
    _pending_scheduled_resize: Optional[threading.Timer] = field(default=None, init=False, repr=False)

    def on_output(self, cb: OutputCallback) -> None:
        self._on_output = cb

    def on_exit(self, cb: ExitCallback) -> None:
        """Set callback for process exit (receives exit code)."""
        self._on_exit = cb

    def set_winsize(self, rows: int, cols: int) -> None:
        """Set PTY window size and notify child process via SIGWINCH."""
        self._apply_winsize(rows, cols)
        self._last_requested_rows = rows
        self._last_requested_cols = cols
        if not self._post_output_resize_done:
            self._post_output_resize_pending = True

    def _apply_child_winsize(self, rows: int, cols: int) -> None:
        """Set initial winsize inside the child process before exec."""
        try:
            winsize = struct.pack("HHHH", rows, cols, 0, 0)
        except Exception:
            return
        try:
            import os
            os.environ["LINES"] = str(rows)
            os.environ["ROWS"] = str(rows)
            os.environ["COLUMNS"] = str(cols)
            os.environ["COLS"] = str(cols)
        except Exception:
            pass
        for stream in (sys.stdin, sys.stdout, sys.stderr):
            try:
                fd = stream.fileno()
                fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)
            except Exception:
                continue

    def get_winsize(self) -> Optional[tuple[int, int]]:
        """Return current PTY winsize as (rows, cols) if available."""
        if self.master_fd is None:
            return None
        try:
            data = fcntl.ioctl(self.master_fd, termios.TIOCGWINSZ, struct.pack('HHHH', 0, 0, 0, 0))
            rows, cols, _, _ = struct.unpack('HHHH', data)
            return rows, cols
        except Exception:
            return None

    def first_output_preview(self, limit: int = 512) -> str:
        if not self._first_output:
            return ""
        return self._first_output[:limit].decode("utf-8", errors="replace")

    def _apply_winsize(self, rows: int, cols: int) -> None:
        if self.master_fd is None:
            return
        try:
            winsize = struct.pack('HHHH', rows, cols, 0, 0)
            fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, winsize)
        except Exception:
            pass
        if self.pid:
            try:
                os.kill(self.pid, signal.SIGWINCH)
            except Exception:
                pass

    def start(self) -> bool:
        """Fork process in PTY and begin background read loop."""
        if self.pid is not None:
            return True

        self._first_output.clear()
        self._post_output_resize_pending = False
        self._post_output_resize_done = False
        if self._pending_scheduled_resize is not None:
            try:
                self._pending_scheduled_resize.cancel()
            except Exception:
                pass
            self._pending_scheduled_resize = None

        pid, master = pty.fork()
        if pid == 0:
            # Child: apply an explicit winsize before exec to avoid 80x24 default
            self._apply_child_winsize(rows=48, cols=240)
            # Child: exec the command; fallback to bash -lc "cmd" if direct exec fails
            try:
                os.execvp(self.command[0], self.command)
            except Exception:
                try:
                    cmd_str = " ".join(shlex.quote(p) for p in self.command)
                    os.execlp("bash", "bash", "-lc", cmd_str)
                except Exception as e:
                    print(f"Failed to exec {self.command}: {e}", file=sys.stderr)
                    os._exit(1)

        # Parent
        self.pid = pid
        self.master_fd = master

        # Start a background reader thread to avoid blocking the UI loop
        self._stop_event.clear()
        self._reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._reader_thread.start()
        # Initialize default window size so child doesn't assume 80x24.
        try:
            self.set_winsize(rows=48, cols=240)
        except Exception:
            pass

        # Disabled: these sequences can cause issues with some programs
        # that echo them back, creating garbled output at startup.
        # The emulator (pyte) handles mouse tracking sequences fine anyway.
        # try:
        #     if self.master_fd is not None:
        #         os.write(self.master_fd, b"\x1B[?9l\x1B[?1000l\x1B[?1001l\x1B[?1002l\x1B[?1003l\x1B[?1006l\x1B[?1015l")
        #         os.write(self.master_fd, b"\x1B[?2004l\x1B[?1004l")
        # except Exception:
        #     pass
        # Quick sanity: detect immediate child exit
        for _ in range(10):
            if not self.is_alive():
                return False
            time.sleep(0.05)
        return True

    def _reader_loop(self) -> None:
        fd = self.master_fd
        if fd is None:
            return
        while not self._stop_event.is_set():
            try:
                r, _, _ = select.select([fd], [], [], 0.05)
                if fd in r:
                    try:
                        data = os.read(fd, 4096)
                        if not data:
                            break
                        if len(self._first_output) < 2048:
                            remaining = 2048 - len(self._first_output)
                            self._first_output.extend(data[:remaining])
                            if self._pending_scheduled_resize is None and self._last_requested_rows and self._last_requested_cols:
                                def _delayed_resize() -> None:
                                    try:
                                        self._apply_winsize(self._last_requested_rows, self._last_requested_cols)
                                    finally:
                                        self._pending_scheduled_resize = None
                                timer = threading.Timer(0.5, _delayed_resize)
                                timer.daemon = True
                                timer.start()
                                self._pending_scheduled_resize = timer

                        if (
                            not self._post_output_resize_done
                            and self._post_output_resize_pending
                            and self._last_requested_rows is not None
                            and self._last_requested_cols is not None
                        ):
                            self._apply_winsize(self._last_requested_rows, self._last_requested_cols)
                            self._post_output_resize_pending = False
                            self._post_output_resize_done = True
                        if self._on_output:
                            # Stream as-is; UI may decide how to render
                            text = data.decode("utf-8", errors="replace")
                            self._on_output(text)
                    except OSError:
                        break
            except Exception:
                break
        # Process exited - get exit status and call callback
        if self.pid is not None and self._on_exit:
            try:
                _, status = os.waitpid(self.pid, os.WNOHANG)
                exit_code = os.WEXITSTATUS(status) if os.WIFEXITED(status) else -1
                self._on_exit(exit_code)
            except Exception:
                pass

    def write(self, data: str) -> None:
        """Write text to the child's stdin (via PTY)."""
        if self.master_fd is None:
            return
        try:
            os.write(self.master_fd, data.encode())
        except Exception:
            pass

    def inject(self, text: str) -> None:
        """Inject a line (presses Enter)."""
        # Use carriage return to simulate Enter reliably across TUIs
        self.write(text + "\r")

    def close(self) -> None:
        # Stop reader loop
        self._stop_event.set()
        try:
            if self._reader_thread:
                self._reader_thread.join(timeout=0.5)
        except Exception:
            pass

        # Close fds and kill child
        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except Exception:
                pass
            self.master_fd = None

        if self.pid is not None:
            try:
                os.kill(self.pid, 9)
                os.waitpid(self.pid, 0)
            except Exception:
                pass
            self.pid = None

    def is_alive(self) -> bool:
        if self.pid is None:
            return False
        try:
            # signal 0 doesn't kill; raises if not running
            os.kill(self.pid, 0)
            return True
        except Exception:
            return False
