"""Tests for TroubleshootingPackBuilder - snapshot building and file export."""

import pytest
from pathlib import Path
from datetime import datetime, timezone

from src.actcli.bench_textual.instrumentation.troubleshooting_pack_builder import (
    TroubleshootingPackBuilder,
)


class FakeRunner:
    muted = False
    command = ["python", "-q"]

    def first_output_preview(self, limit):
        return "first output preview"


class FakeEmulator:
    cols = 80
    rows = 24


class FakeTerminalState:
    def __init__(self):
        self.emulator = FakeEmulator()
        self.last_synced_size = (80, 24)
        self.output_buffer = "recent output 1234567890"
        self.item = FakeRunner()
        self.winsize_history = ["80x24"]


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
        "output": ["output one"],
    }


class TestTroubleshootingPackBuilderSnapshot:
    def test_build_snapshot_includes_expected_sections(self):
        builder = TroubleshootingPackBuilder(
            terminal_manager=FakeTerminalManager(),
            log_manager=FakeLogManager(),
            version_info={"bench": "test", "textual": "test", "pyte": "test"},
            get_app_state=lambda: {
                "active_view": "terminal",
                "active_terminal": "demo",
                "writer_attached": True,
            },
            clock=lambda: datetime(2026, 5, 8, 12, 34, 56, tzinfo=timezone.utc),
        )
        snapshot = builder.build_snapshot(key_events=["enter"])
        assert "versions:" in snapshot
        assert "actcli-bench: test" in snapshot
        assert "terminals:" in snapshot
        assert "demo" in snapshot
        assert "---- recent events ----" in snapshot
        assert "event one" in snapshot
        assert "---- recent errors ----" in snapshot
        assert "---- recent debug ----" in snapshot
        assert "debug one" in snapshot
        assert "---- recent output ----" in snapshot
        assert "---- recent key events ----" in snapshot
        assert "enter" in snapshot

    def test_build_snapshot_empty_terminals(self):
        class EmptyTerminalManager:
            def list_terminals(self):
                return []

        builder = TroubleshootingPackBuilder(
            terminal_manager=EmptyTerminalManager(),
            log_manager=FakeLogManager(),
            version_info={"bench": "test", "textual": "test", "pyte": "none"},
            get_app_state=lambda: {
                "active_view": "terminal",
                "active_terminal": None,
                "writer_attached": False,
            },
        )
        snapshot = builder.build_snapshot()
        assert "terminals:" in snapshot
        assert "versions:" in snapshot
        assert "pyte: none" in snapshot

    def test_build_snapshot_missing_nav_tree(self):
        builder = TroubleshootingPackBuilder(
            terminal_manager=FakeTerminalManager(),
            log_manager=FakeLogManager(),
            version_info={"bench": "test", "textual": "test", "pyte": "test"},
            get_app_state=lambda: {
                "active_view": "terminal",
                "active_terminal": "demo",
                "writer_attached": True,
            },
        )
        snapshot = builder.build_snapshot()
        assert "navigation tree rebuild history" not in snapshot

    def test_build_snapshot_with_nav_tree(self):
        class FakeNavTree:
            rebuild_history = [
                {"timestamp": "12:34:56.000", "section_count": 4},
            ]

        builder = TroubleshootingPackBuilder(
            terminal_manager=FakeTerminalManager(),
            log_manager=FakeLogManager(),
            version_info={"bench": "test", "textual": "test", "pyte": "test"},
            get_app_state=lambda: {
                "active_view": "terminal",
                "active_terminal": "demo",
                "writer_attached": True,
            },
            nav_tree=FakeNavTree(),
        )
        snapshot = builder.build_snapshot()
        assert "navigation tree rebuild history" in snapshot
        assert "Total rebuilds: 1" in snapshot
        assert "12:34:56.000 - [4 sections]" in snapshot

    def test_build_snapshot_with_multiple_rebuilds(self):
        class FakeNavTree:
            rebuild_history = [
                {"timestamp": "12:34:56.001", "section_count": 4},
                {"timestamp": "12:34:56.002", "section_count": 4},
            ]

        builder = TroubleshootingPackBuilder(
            terminal_manager=FakeTerminalManager(),
            log_manager=FakeLogManager(),
            version_info={"bench": "test", "textual": "test", "pyte": "test"},
            get_app_state=lambda: {
                "active_view": "terminal",
                "active_terminal": "demo",
                "writer_attached": True,
            },
            nav_tree=FakeNavTree(),
        )
        snapshot = builder.build_snapshot()
        assert "WARNING: Multiple rebuilds detected" in snapshot

    def test_build_snapshot_no_key_events(self):
        builder = TroubleshootingPackBuilder(
            terminal_manager=FakeTerminalManager(),
            log_manager=FakeLogManager(),
            version_info={"bench": "test", "textual": "test", "pyte": "test"},
            get_app_state=lambda: {
                "active_view": "terminal",
                "active_terminal": "demo",
                "writer_attached": True,
            },
        )
        snapshot = builder.build_snapshot()
        assert "---- recent key events ----" not in snapshot

    def test_build_snapshot_missing_terminal_state(self):
        class MissingStateManager:
            def list_terminals(self):
                return ["missing"]

            def get_terminal_state(self, name):
                return None

        builder = TroubleshootingPackBuilder(
            terminal_manager=MissingStateManager(),
            log_manager=FakeLogManager(),
            version_info={"bench": "test", "textual": "test", "pyte": "test"},
            get_app_state=lambda: {
                "active_view": "terminal",
                "active_terminal": None,
                "writer_attached": False,
            },
        )
        snapshot = builder.build_snapshot()
        assert "terminals:" in snapshot
        assert "missing" not in snapshot

    def test_build_snapshot_empty_log_buffers(self):
        class EmptyLogManager:
            buffers = {}

        builder = TroubleshootingPackBuilder(
            terminal_manager=FakeTerminalManager(),
            log_manager=EmptyLogManager(),
            version_info={"bench": "test", "textual": "test", "pyte": "test"},
            get_app_state=lambda: {
                "active_view": "terminal",
                "active_terminal": "demo",
                "writer_attached": True,
            },
        )
        snapshot = builder.build_snapshot()
        assert "(no events)" in snapshot

    def test_build_snapshot_without_first_output_preview(self):
        class SimpleRunner:
            muted = False
            command = ["python"]

        class SimpleState:
            def __init__(self):
                self.emulator = FakeEmulator()
                self.last_synced_size = (80, 24)
                self.output_buffer = "recent output"
                self.item = SimpleRunner()
                self.winsize_history = []

        class SimpleTerminalManager:
            def list_terminals(self):
                return ["simple"]

            def get_terminal_state(self, name):
                return SimpleState()

        builder = TroubleshootingPackBuilder(
            terminal_manager=SimpleTerminalManager(),
            log_manager=FakeLogManager(),
            version_info={"bench": "test", "textual": "test", "pyte": "test"},
            get_app_state=lambda: {
                "active_view": "terminal",
                "active_terminal": "simple",
                "writer_attached": True,
            },
        )
        snapshot = builder.build_snapshot()
        assert "first_output_preview" not in snapshot

    def test_build_snapshot_missing_version_keys(self):
        builder = TroubleshootingPackBuilder(
            terminal_manager=FakeTerminalManager(),
            log_manager=FakeLogManager(),
            version_info={},
            get_app_state=lambda: {
                "active_view": "terminal",
                "active_terminal": "demo",
                "writer_attached": True,
            },
        )
        snapshot = builder.build_snapshot()
        assert "actcli-bench: unknown" in snapshot
        assert "textual: unknown" in snapshot
        assert "pyte: none" in snapshot


class TestTroubleshootingPackBuilderExport:
    def test_export_to_default_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        builder = TroubleshootingPackBuilder(
            terminal_manager=FakeTerminalManager(),
            log_manager=FakeLogManager(),
            version_info={"bench": "test", "textual": "test", "pyte": "test"},
            get_app_state=lambda: {
                "active_view": "terminal",
                "active_terminal": "demo",
                "writer_attached": True,
            },
            clock=lambda: datetime(2026, 5, 8, 12, 34, 56, tzinfo=timezone.utc),
        )
        path = builder.export_to_file(target_dir=str(tmp_path / "out"))
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "versions:" in text

    def test_export_deterministic_filename(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        builder = TroubleshootingPackBuilder(
            terminal_manager=FakeTerminalManager(),
            log_manager=FakeLogManager(),
            version_info={"bench": "test", "textual": "test", "pyte": "test"},
            get_app_state=lambda: {
                "active_view": "terminal",
                "active_terminal": "demo",
                "writer_attached": True,
            },
            clock=lambda: datetime(2026, 5, 8, 12, 34, 56, tzinfo=timezone.utc),
        )
        path = builder.export_to_file(target_dir=str(tmp_path / "out"))
        assert path.name == "troubleshooting_pack_20260508T123456Z.txt"

    def test_export_with_snapshot_text(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        builder = TroubleshootingPackBuilder(
            terminal_manager=FakeTerminalManager(),
            log_manager=FakeLogManager(),
            version_info={"bench": "test", "textual": "test", "pyte": "test"},
            get_app_state=lambda: {
                "active_view": "terminal",
                "active_terminal": "demo",
                "writer_attached": True,
            },
            clock=lambda: datetime(2026, 5, 8, 12, 34, 56, tzinfo=timezone.utc),
        )
        path = builder.export_to_file(
            target_dir=str(tmp_path / "out"),
            snapshot_text="custom snapshot content",
        )
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert text == "custom snapshot content"

    def test_export_creates_missing_dirs(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        builder = TroubleshootingPackBuilder(
            terminal_manager=FakeTerminalManager(),
            log_manager=FakeLogManager(),
            version_info={"bench": "test", "textual": "test", "pyte": "test"},
            get_app_state=lambda: {
                "active_view": "terminal",
                "active_terminal": "demo",
                "writer_attached": True,
            },
        )
        path = builder.export_to_file(target_dir=str(tmp_path / "nested" / "dirs"))
        assert path.exists()

    def test_export_with_key_events(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        builder = TroubleshootingPackBuilder(
            terminal_manager=FakeTerminalManager(),
            log_manager=FakeLogManager(),
            version_info={"bench": "test", "textual": "test", "pyte": "test"},
            get_app_state=lambda: {
                "active_view": "terminal",
                "active_terminal": "demo",
                "writer_attached": True,
            },
        )
        path = builder.export_to_file(
            target_dir=str(tmp_path / "out"),
            key_events=["f1", "f2"],
        )
        text = path.read_text(encoding="utf-8")
        assert "---- recent key events ----" in text
        assert "f1" in text
        assert "f2" in text


class TestTroubleshootingPackBuilderIncludeTrace:
    def test_include_trace_with_missing_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from src.actcli.bench_textual.instrumentation.write_trace_logger import WriteTraceLogger

        monkeypatch.setattr(
            WriteTraceLogger,
            "DEFAULT_TRACE_PATH",
            str(tmp_path / "nonexistent" / "trace.log"),
        )
        builder = TroubleshootingPackBuilder(
            terminal_manager=FakeTerminalManager(),
            log_manager=FakeLogManager(),
            version_info={"bench": "test", "textual": "test", "pyte": "test"},
            get_app_state=lambda: {
                "active_view": "terminal",
                "active_terminal": "demo",
                "writer_attached": True,
            },
            include_trace=True,
        )
        snapshot = builder.build_snapshot()
        assert "---- recent write trace ----" not in snapshot

    def test_include_trace_with_existing_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        trace_file = tmp_path / "write_debug.log"
        trace_file.write_text("runner-1: 'hello\\n'\n", encoding="utf-8")

        from src.actcli.bench_textual.instrumentation.write_trace_logger import WriteTraceLogger

        monkeypatch.setattr(WriteTraceLogger, "DEFAULT_TRACE_PATH", str(trace_file))
        builder = TroubleshootingPackBuilder(
            terminal_manager=FakeTerminalManager(),
            log_manager=FakeLogManager(),
            version_info={"bench": "test", "textual": "test", "pyte": "test"},
            get_app_state=lambda: {
                "active_view": "terminal",
                "active_terminal": "demo",
                "writer_attached": True,
            },
            include_trace=True,
        )
        snapshot = builder.build_snapshot()
        assert "---- recent write trace ----" in snapshot
        assert "runner-1: 'hello\\n'" in snapshot

    def test_include_trace_false_skips_trace(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        trace_file = tmp_path / "write_debug.log"
        trace_file.write_text("runner-1: 'data'\n", encoding="utf-8")

        from src.actcli.bench_textual.instrumentation.write_trace_logger import WriteTraceLogger

        monkeypatch.setattr(WriteTraceLogger, "DEFAULT_TRACE_PATH", str(trace_file))
        builder = TroubleshootingPackBuilder(
            terminal_manager=FakeTerminalManager(),
            log_manager=FakeLogManager(),
            version_info={"bench": "test", "textual": "test", "pyte": "test"},
            get_app_state=lambda: {
                "active_view": "terminal",
                "active_terminal": "demo",
                "writer_attached": True,
            },
            include_trace=False,
        )
        snapshot = builder.build_snapshot()
        assert "---- recent write trace ----" not in snapshot
