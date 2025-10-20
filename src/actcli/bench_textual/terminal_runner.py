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

    def on_output(self, cb: OutputCallback) -> None:
        self._on_output = cb

    def on_exit(self, cb: ExitCallback) -> None:
        """Set callback for process exit (receives exit code)."""
        self._on_exit = cb

    def set_winsize(self, rows: int, cols: int) -> None:
        """Set PTY window size and notify child process via SIGWINCH."""
        if self.master_fd is None:
            return
        try:
            # Pack window size as: rows, cols, xpixel (0), ypixel (0)
            winsize = struct.pack('HHHH', rows, cols, 0, 0)
            fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, winsize)
        except Exception:
            pass
        # Notify child process that window size changed
        if self.pid:
            try:
                os.kill(self.pid, signal.SIGWINCH)
            except Exception:
                pass

    def start(self) -> bool:
        """Fork process in PTY and begin background read loop."""
        if self.pid is not None:
            return True

        pid, master = pty.fork()
        if pid == 0:
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
            self.set_winsize(rows=40, cols=120)
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
