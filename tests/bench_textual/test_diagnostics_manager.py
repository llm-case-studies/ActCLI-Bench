"""Tests for DiagnosticsManager delegation to TroubleshootingPackBuilder."""

import pytest
from pathlib import Path
from datetime import datetime, timezone

from src.actcli.bench_textual.diagnostics import DiagnosticsManager
from src.actcli.bench_textual.instrumentation.troubleshooting_pack_builder import (
    TroubleshootingPackBuilder,
)


class FakeRunner:
    muted = False
    command = ["python", "-q"]

    def first_output_preview(self, limit):
        return "first output"


class FakeEmulator:
    cols = 80
    rows = 24


class FakeTerminalState:
    def __init__(self):
        self.emulator = FakeEmulator()
        self.last_synced_size = (80, 24)
        self.output_buffer = "recent output"
        self.item = FakeRunner()
        self.winsize_history = []


class FakeTerminalManager:
    def list_terminals(self):
        return ["demo"]

    def get_terminal_state(self, name):
        return FakeTerminalState()


class FakeLogManager:
    buffers = {
        "events": ["event one"],
        "errors": [],
        "debug": ["debug one"],
        "output": [],
        "troubleshooting": [],
    }

    def add(self, category, message):
        for line in message.splitlines() or [message]:
            self.buffers.setdefault(category, []).append(line)


class TestDiagnosticsManagerKeyEvents:
    def test_record_key_event(self):
        mgr = DiagnosticsManager(
            terminal_manager=FakeTerminalManager(),
            log_manager=FakeLogManager(),
            version_info={},
            get_app_state=lambda: {},
        )
        mgr.record_key_event("f1", "F1", set())
        assert len(mgr.key_events) == 1
        assert "f1" in mgr.key_events[0]

    def test_record_key_event_trims_to_100(self):
        mgr = DiagnosticsManager(
            terminal_manager=FakeTerminalManager(),
            log_manager=FakeLogManager(),
            version_info={},
            get_app_state=lambda: {},
        )
        for i in range(150):
            mgr.record_key_event(f"key{i}", "K", set())
        assert len(mgr.key_events) == 100
        assert "key50" in mgr.key_events[0]
        assert "key149" in mgr.key_events[-1]

    def test_record_key_event_with_modifiers(self):
        mgr = DiagnosticsManager(
            terminal_manager=FakeTerminalManager(),
            log_manager=FakeLogManager(),
            version_info={},
            get_app_state=lambda: {},
        )
        mgr.record_key_event("c", "c", {"ctrl"})
        assert "mods=ctrl" in mgr.key_events[0]


class TestDiagnosticsManagerDelegation:
    def test_generate_snapshot_delegates_to_builder(self):
        mgr = DiagnosticsManager(
            terminal_manager=FakeTerminalManager(),
            log_manager=FakeLogManager(),
            version_info={"bench": "1.0", "textual": "2.0", "pyte": "0.8"},
            get_app_state=lambda: {
                "active_view": "terminal",
                "active_terminal": "demo",
                "writer_attached": True,
            },
        )
        snapshot = mgr.generate_snapshot()
        assert "versions:" in snapshot
        assert "actcli-bench: 1.0" in snapshot
        assert "terminals:" in snapshot
        assert "demo" in snapshot

    def test_update_troubleshooting_log_updates_buffer(self):
        mgr = DiagnosticsManager(
            terminal_manager=FakeTerminalManager(),
            log_manager=FakeLogManager(),
            version_info={"bench": "1.0", "textual": "2.0", "pyte": "0.8"},
            get_app_state=lambda: {
                "active_view": "terminal",
                "active_terminal": "demo",
                "writer_attached": True,
            },
        )
        snapshot = mgr.update_troubleshooting_log()
        assert "versions:" in snapshot
        buf = mgr.log_manager.buffers.get("troubleshooting")
        assert buf is not None

    def test_export_to_file_delegates_to_builder(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mgr = DiagnosticsManager(
            terminal_manager=FakeTerminalManager(),
            log_manager=FakeLogManager(),
            version_info={"bench": "1.0", "textual": "2.0", "pyte": "0.8"},
            get_app_state=lambda: {
                "active_view": "terminal",
                "active_terminal": "demo",
                "writer_attached": True,
            },
        )
        result = mgr.export_to_file(target_dir=str(tmp_path / "out"))
        assert result is not None
        assert Path(result).exists()
        text = Path(result).read_text(encoding="utf-8")
        assert "versions:" in text

    def test_export_to_file_no_default_hardcoded_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mgr = DiagnosticsManager(
            terminal_manager=FakeTerminalManager(),
            log_manager=FakeLogManager(),
            version_info={"bench": "1.0", "textual": "2.0", "pyte": "0.8"},
            get_app_state=lambda: {
                "active_view": "terminal",
                "active_terminal": "demo",
                "writer_attached": True,
            },
        )
        source = Path(
            __import__("src.actcli.bench_textual.diagnostics", fromlist=[""]).__file__
        ).read_text(encoding="utf-8")
        assert "docs/Trouble-Snaps" not in source
        assert "troubleshooting_pack_" not in source

    def test_nav_tree_property_propagates_to_builder(self):
        class FakeNavTree:
            rebuild_history = [
                {"timestamp": "12:00:00", "section_count": 3},
            ]

        mgr = DiagnosticsManager(
            terminal_manager=FakeTerminalManager(),
            log_manager=FakeLogManager(),
            version_info={"bench": "1.0", "textual": "2.0", "pyte": "0.8"},
            get_app_state=lambda: {
                "active_view": "terminal",
                "active_terminal": "demo",
                "writer_attached": True,
            },
        )
        mgr.nav_tree = FakeNavTree()
        assert mgr.nav_tree is mgr._builder.nav_tree
        snapshot = mgr.generate_snapshot()
        assert "navigation tree rebuild history" in snapshot

    def test_key_events_in_snapshot(self):
        mgr = DiagnosticsManager(
            terminal_manager=FakeTerminalManager(),
            log_manager=FakeLogManager(),
            version_info={"bench": "1.0", "textual": "2.0", "pyte": "0.8"},
            get_app_state=lambda: {
                "active_view": "terminal",
                "active_terminal": "demo",
                "writer_attached": True,
            },
        )
        mgr.record_key_event("enter", "\r", set())
        mgr.record_key_event("f1", "F1", set())
        snapshot = mgr.generate_snapshot()
        assert "---- recent key events ----" in snapshot
        assert "enter" in snapshot
        assert "f1" in snapshot
