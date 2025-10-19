"""Terminal tab - represents a wrapped terminal in the navbar."""

import asyncio
import os
import pty
import select
import sys
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TerminalTab:
    """Represents a wrapped terminal tab."""

    name: str
    command: List[str]
    pid: Optional[int] = None
    master_fd: Optional[int] = None
    output_buffer: str = ""
    is_active: bool = False

    def start(self):
        """Start the terminal process."""
        self.pid, self.master_fd = pty.fork()

        if self.pid == 0:
            # Child process - exec command
            os.execvp(self.command[0], self.command)

        # Parent process
        return True

    def read_output(self, size: int = 4096) -> bytes:
        """Read output from terminal (non-blocking)."""
        if not self.master_fd:
            return b""

        try:
            # Check if data available
            r, _, _ = select.select([self.master_fd], [], [], 0)
            if self.master_fd in r:
                return os.read(self.master_fd, size)
        except OSError:
            pass

        return b""

    def write_input(self, data: bytes):
        """Write input to terminal."""
        if self.master_fd:
            try:
                os.write(self.master_fd, data)
            except OSError:
                pass

    def is_alive(self) -> bool:
        """Check if process is still running."""
        if not self.pid:
            return False

        try:
            # Check if process exists
            os.kill(self.pid, 0)
            return True
        except OSError:
            return False

    def close(self):
        """Close the terminal."""
        if self.master_fd:
            try:
                os.close(self.master_fd)
            except:
                pass

        if self.pid:
            try:
                os.kill(self.pid, 9)
                os.waitpid(self.pid, 0)
            except:
                pass


class TerminalManager:
    """Manages multiple terminal tabs."""

    def __init__(self):
        self.tabs: List[TerminalTab] = []
        self.active_index: int = -1

    def add_tab(self, name: str, command: List[str]) -> TerminalTab:
        """Add a new terminal tab."""
        tab = TerminalTab(name=name, command=command)
        tab.start()
        self.tabs.append(tab)

        # Always switch to the newly added tab
        self.switch_tab(len(self.tabs) - 1)

        return tab

    def get_active_tab(self) -> Optional[TerminalTab]:
        """Get currently active tab."""
        if 0 <= self.active_index < len(self.tabs):
            return self.tabs[self.active_index]
        return None

    def switch_tab(self, index: int):
        """Switch to tab at index."""
        if 0 <= index < len(self.tabs):
            # Deactivate current
            if 0 <= self.active_index < len(self.tabs):
                self.tabs[self.active_index].is_active = False

            # Activate new
            self.active_index = index
            self.tabs[index].is_active = True

    def next_tab(self):
        """Switch to next tab."""
        if self.tabs:
            self.switch_tab((self.active_index + 1) % len(self.tabs))

    def prev_tab(self):
        """Switch to previous tab."""
        if self.tabs:
            self.switch_tab((self.active_index - 1) % len(self.tabs))

    def close_tab(self, index: int):
        """Close tab at index."""
        if 0 <= index < len(self.tabs):
            tab = self.tabs[index]
            tab.close()
            self.tabs.pop(index)

            # Adjust active index
            if self.active_index >= len(self.tabs):
                self.active_index = len(self.tabs) - 1

            # Update active flag
            if self.active_index >= 0:
                self.tabs[self.active_index].is_active = True

    def close_all(self):
        """Close all tabs."""
        for tab in self.tabs:
            tab.close()
        self.tabs.clear()
        self.active_index = -1
