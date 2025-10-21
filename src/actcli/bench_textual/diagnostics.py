"""Diagnostics and troubleshooting snapshot generation.

This module handles creating diagnostic snapshots for debugging and
troubleshooting. It collects system state, terminal state, logs, and
version information.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from .terminal_manager import TerminalManager
    from .log_manager import LogManager


class DiagnosticsManager:
    """Manages diagnostic snapshot generation and export.

    Responsibilities:
    - Generate troubleshooting snapshots
    - Collect version information
    - Export snapshots to files
    - Format diagnostic output
    """

    def __init__(
        self,
        terminal_manager: TerminalManager,
        log_manager: LogManager,
        version_info: Dict[str, str],
        get_app_state: Callable[[], Dict[str, any]]
    ):
        """Initialize diagnostics manager.

        Args:
            terminal_manager: TerminalManager instance for terminal state
            log_manager: LogManager instance for log access
            version_info: Dictionary of version information
            get_app_state: Callback to get current app state (active_view, etc.)
        """
        self.terminal_manager = terminal_manager
        self.log_manager = log_manager
        self.version_info = version_info
        self.get_app_state = get_app_state
        self.key_events: List[str] = []

    def record_key_event(self, key: str, character: Optional[str], modifiers: set[str]) -> None:
        """Record a key event for diagnostics.

        Args:
            key: Key name
            character: Character value (if printable)
            modifiers: Set of modifier keys
        """
        mods = "+".join(sorted(modifiers)) if modifiers else ""
        char_repr = repr(character) if character else "None"
        entry = f"{key} char={char_repr} mods={mods}"
        self.key_events.append(entry)
        # Keep last 100 events
        if len(self.key_events) > 100:
            self.key_events = self.key_events[-100:]

    def generate_snapshot(self) -> str:
        """Generate a complete troubleshooting snapshot.

        Returns:
            Formatted snapshot text
        """
        app_state = self.get_app_state()
        lines: List[str] = []

        # Timestamp and versions
        lines.append(f"timestamp: {datetime.utcnow().isoformat()}Z")
        lines.append("versions:")
        lines.append(f"  actcli-bench: {self.version_info.get('bench', 'unknown')}")
        lines.append(f"  textual: {self.version_info.get('textual', 'unknown')}")
        lines.append(f"  pyte: {self.version_info.get('pyte', 'none')}")

        # App state
        lines.append(f"active_view: {app_state.get('active_view', 'unknown')}")
        lines.append(f"active_terminal: {app_state.get('active_terminal') or '(none)'}")
        lines.append(f"writer_attached: {app_state.get('writer_attached', False)}")

        # Terminal state
        lines.append("terminals:")
        for name in self.terminal_manager.list_terminals():
            state = self.terminal_manager.get_terminal_state(name)
            if not state:
                continue

            emu = state.emulator
            emu_size = f"{emu.cols}x{emu.rows}"
            last_sync = state.last_synced_size
            sync_str = f"{last_sync[0]}x{last_sync[1]}" if last_sync else "n/a"
            tty_preview = state.output_buffer[-120:] if state.output_buffer else ""
            runner = state.item
            first_preview = ""
            if hasattr(runner, "first_output_preview"):
                try:
                    first_preview = runner.first_output_preview(240)
                except Exception:
                    first_preview = ""

            lines.append(
                f"  - {name}: muted={runner.muted} cmd={' '.join(runner.command)} "
                f"emu={emu_size} last_winsize={sync_str}"
            )

            history = state.winsize_history
            if history:
                lines.append("    winsize_history:")
                for entry in history[-10:]:
                    lines.append(f"      • {entry}")

            if tty_preview:
                lines.append("    recent_output_preview:")
                lines.append("      " + tty_preview.replace("\n", "\\n"))

            if first_preview:
                lines.append("    first_output_preview:")
                lines.append("      " + first_preview.replace("\n", "\\n"))

        # Recent logs
        lines.append("---- recent events ----")
        lines.append(self._recent_log_text("events"))
        lines.append("---- recent errors ----")
        lines.append(self._recent_log_text("errors"))
        lines.append("---- recent debug ----")
        lines.append(self._recent_log_text("debug"))
        lines.append("---- recent output ----")
        lines.append(self._recent_log_text("output"))

        # Key events
        if self.key_events:
            lines.append("---- recent key events ----")
            lines.extend(self.key_events[-20:])

        return "\n".join(lines)

    def update_troubleshooting_log(self) -> str:
        """Generate snapshot and update troubleshooting log.

        Returns:
            The generated snapshot text
        """
        snapshot = self.generate_snapshot()
        buf = self.log_manager.buffers.get("troubleshooting")
        if buf is not None:
            buf.clear()
        self.log_manager.add("troubleshooting", snapshot)
        return snapshot

    def export_to_file(self, target_dir: str = "docs/Trouble-Snaps") -> Optional[str]:
        """Export troubleshooting snapshot to file.

        Args:
            target_dir: Directory to save snapshot file

        Returns:
            Path to saved file, or None if export failed
        """
        snapshot = self.update_troubleshooting_log()
        try:
            dir_path = Path(target_dir)
            dir_path.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            target_file = dir_path / f"troubleshooting_pack_{timestamp}.txt"
            target_file.write_text(snapshot, encoding="utf-8")
            return str(target_file)
        except Exception as e:
            # Return None on error - caller can handle logging
            return None

    def _recent_log_text(self, category: str, limit: int = 50) -> str:
        """Get recent log entries from a category.

        Args:
            category: Log category name
            limit: Maximum number of entries to return

        Returns:
            Formatted log text, or "(none)" if empty
        """
        buf = self.log_manager.buffers.get(category, [])
        if not buf:
            return f"(no {category})"
        recent = buf[-limit:]
        return "\n".join(recent)
