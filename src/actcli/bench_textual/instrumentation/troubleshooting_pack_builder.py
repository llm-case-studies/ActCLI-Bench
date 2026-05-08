"""TroubleshootingPackBuilder -- reusable troubleshooting snapshot collection and export."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..terminal_manager import TerminalManager
    from ..log_manager import LogManager


class TroubleshootingPackBuilder:
    """Builds and exports troubleshooting snapshots.

    Collects system state, terminal state, logs, version information,
    key events, and optional write-trace lines into a formatted text
    snapshot and writes it to a timestamped file.
    """

    DEFAULT_EXPORT_DIR = "docs/Trouble-Snaps"

    def __init__(
        self,
        terminal_manager: TerminalManager,
        log_manager: LogManager,
        version_info: Dict[str, str],
        get_app_state: Callable[[], Dict[str, Any]],
        nav_tree: Any = None,
        clock: Optional[Callable[[], datetime]] = None,
        include_trace: bool = False,
    ):
        self.terminal_manager = terminal_manager
        self.log_manager = log_manager
        self.version_info = version_info
        self.get_app_state = get_app_state
        self.nav_tree = nav_tree
        self._clock = clock or datetime.utcnow
        self.include_trace = include_trace

    def build_snapshot(self, key_events: Optional[List[str]] = None) -> str:
        lines: List[str] = []

        app_state = self.get_app_state()

        lines.append(f"timestamp: {self._clock().isoformat()}Z")
        lines.append("versions:")
        lines.append(f"  actcli-bench: {self.version_info.get('bench', 'unknown')}")
        lines.append(f"  textual: {self.version_info.get('textual', 'unknown')}")
        lines.append(f"  pyte: {self.version_info.get('pyte', 'none')}")

        lines.append(f"active_view: {app_state.get('active_view', 'unknown')}")
        lines.append(f"active_terminal: {app_state.get('active_terminal') or '(none)'}")
        lines.append(f"writer_attached: {app_state.get('writer_attached', False)}")

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

        lines.append("---- recent events ----")
        lines.append(self._recent_log_text("events"))
        lines.append("---- recent errors ----")
        lines.append(self._recent_log_text("errors"))
        lines.append("---- recent debug ----")
        lines.append(self._recent_log_text("debug"))
        lines.append("---- recent output ----")
        lines.append(self._recent_log_text("output"))

        if key_events:
            lines.append("---- recent key events ----")
            lines.extend(key_events[-20:])

        if self.nav_tree and hasattr(self.nav_tree, "rebuild_history"):
            rebuild_history = self.nav_tree.rebuild_history
            if rebuild_history:
                lines.append("---- navigation tree rebuild history ----")
                lines.append(f"Total rebuilds: {len(rebuild_history)}")
                if len(rebuild_history) > 1:
                    lines.append("⚠️  WARNING: Multiple rebuilds detected!")
                lines.append("\nRebuild events:")
                for event in rebuild_history:
                    lines.append(
                        f"  • {event['timestamp']} - [{event['section_count']} sections]"
                    )

        if self.include_trace:
            self._append_trace_section(lines)

        return "\n".join(lines)

    def export_to_file(
        self,
        target_dir: Optional[str | Path] = None,
        key_events: Optional[List[str]] = None,
        snapshot_text: Optional[str] = None,
    ) -> Path:
        dir_path = Path(target_dir if target_dir is not None else self.DEFAULT_EXPORT_DIR)
        dir_path.mkdir(parents=True, exist_ok=True)
        timestamp = self._clock().strftime("%Y%m%dT%H%M%SZ")
        target_file = dir_path / f"troubleshooting_pack_{timestamp}.txt"
        text = snapshot_text if snapshot_text is not None else self.build_snapshot(key_events)
        target_file.write_text(text, encoding="utf-8")
        return target_file

    def _recent_log_text(self, category: str, limit: int = 50) -> str:
        buf = self.log_manager.buffers.get(category, [])
        if not buf:
            return f"(no {category})"
        buf_list = list(buf)
        recent = buf_list[-limit:]
        return "\n".join(recent)

    def _append_trace_section(self, lines: List[str]) -> None:
        try:
            from .write_trace_logger import WriteTraceLogger

            trace_path = Path(WriteTraceLogger.DEFAULT_TRACE_PATH)
            if not trace_path.exists():
                return
            content = trace_path.read_text(encoding="utf-8")
        except Exception:
            return

        trace_lines = content.splitlines()
        last_trace = trace_lines[-200:]
        if last_trace:
            lines.append("---- recent write trace ----")
            lines.extend(last_trace)
