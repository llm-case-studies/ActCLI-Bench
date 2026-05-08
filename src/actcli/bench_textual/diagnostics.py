"""Diagnostics and troubleshooting snapshot generation.

This module handles creating diagnostic snapshots for debugging and
troubleshooting. Snapshot formatting and file export are delegated to
TroubleshootingPackBuilder.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Callable, TYPE_CHECKING

from .instrumentation import TroubleshootingPackBuilder

if TYPE_CHECKING:
    from .terminal_manager import TerminalManager
    from .log_manager import LogManager


class DiagnosticsManager:
    """Manages diagnostic snapshot generation and export.

    Responsibilities:
    - Record key events for diagnostics
    - Coordinate snapshot generation via TroubleshootingPackBuilder
    - Update the troubleshooting log buffer
    - Delegate file export to TroubleshootingPackBuilder
    """

    def __init__(
        self,
        terminal_manager: TerminalManager,
        log_manager: LogManager,
        version_info: Dict[str, str],
        get_app_state: Callable[[], Dict[str, any]],
        nav_tree = None
    ):
        self.terminal_manager = terminal_manager
        self.log_manager = log_manager
        self.version_info = version_info
        self.get_app_state = get_app_state
        self.key_events: List[str] = []
        self._builder = TroubleshootingPackBuilder(
            terminal_manager=terminal_manager,
            log_manager=log_manager,
            version_info=version_info,
            get_app_state=get_app_state,
            nav_tree=nav_tree,
        )

    @property
    def nav_tree(self):
        return self._builder.nav_tree

    @nav_tree.setter
    def nav_tree(self, value):
        self._builder.nav_tree = value

    def record_key_event(self, key: str, character: Optional[str], modifiers: set[str]) -> None:
        mods = "+".join(sorted(modifiers)) if modifiers else ""
        char_repr = repr(character) if character else "None"
        entry = f"{key} char={char_repr} mods={mods}"
        self.key_events.append(entry)
        if len(self.key_events) > 100:
            self.key_events = self.key_events[-100:]

    def generate_snapshot(self) -> str:
        return self._builder.build_snapshot(self.key_events)

    def update_troubleshooting_log(self) -> str:
        snapshot = self.generate_snapshot()
        buf = self.log_manager.buffers.get("troubleshooting")
        if buf is not None:
            buf.clear()
        self.log_manager.add("troubleshooting", snapshot)
        return snapshot

    def export_to_file(self, target_dir: Optional[str] = None) -> Optional[str]:
        snapshot = self.update_troubleshooting_log()
        try:
            path = self._builder.export_to_file(
                target_dir=target_dir,
                snapshot_text=snapshot,
            )
            return str(path)
        except Exception:
            return None
