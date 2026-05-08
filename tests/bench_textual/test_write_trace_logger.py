"""Tests for WriteTraceLogger - sinks, env-var toggle, format, and integration."""

import os
import tempfile
import pytest
from pathlib import Path
from src.actcli.bench_textual.instrumentation.write_trace_logger import (
    WriteTraceLogger,
    FileTraceSink,
    MemoryTraceSink,
    CallbackTraceSink,
)
from src.actcli.bench_textual.terminal_runner import TerminalRunner


class TestWriteTraceLoggerConstructor:
    """Construction and no-sink behaviour."""

    def test_empty_logger_does_not_crash(self):
        logger = WriteTraceLogger(name="test")
        logger.record("some data")
        assert logger.name == "test"
        assert logger.sinks == []

    def test_name_is_set(self):
        logger = WriteTraceLogger(name="my-runner")
        assert logger.name == "my-runner"


class TestFileTraceSink:
    """File sink behaviour."""

    def test_writes_correct_format(self, tmp_path):
        path = tmp_path / "trace.log"
        sink = FileTraceSink(str(path))
        sink.record("runner-1", "hello\n")
        sink.record("runner-1", "world\r")
        content = path.read_text(encoding="utf-8")
        assert "runner-1: 'hello\\n'" in content
        assert "runner-1: 'world\\r'" in content

    def test_appends_to_existing_file(self, tmp_path):
        path = tmp_path / "trace.log"
        path.write_text("existing line\n", encoding="utf-8")
        sink = FileTraceSink(str(path))
        sink.record("runner-1", "new data\n")
        content = path.read_text(encoding="utf-8")
        assert content.startswith("existing line\n")
        assert "runner-1: 'new data\\n'" in content

    def test_repr_in_output(self, tmp_path):
        path = tmp_path / "repr.log"
        sink = FileTraceSink(str(path))
        sink.record("test", "hello\tworld")
        content = path.read_text(encoding="utf-8")
        assert "hello\\tworld" in content

    def test_unwritable_path_does_not_crash(self, tmp_path):
        sink = FileTraceSink("/nonexistent/readonly/trace.log")
        sink.record("runner-1", "data")


class TestMemoryTraceSink:
    """Memory sink collects records."""

    def test_collects_records(self):
        sink = MemoryTraceSink()
        sink.record("runner-a", "line 1")
        sink.record("runner-a", "line 2\n")
        assert len(sink.records) == 2
        assert "runner-a: 'line 1'" in sink.records[0]
        assert "runner-a: 'line 2\\n'" in sink.records[1]

    def test_starts_empty(self):
        sink = MemoryTraceSink()
        assert sink.records == []

    def test_repr_format_in_memory(self):
        sink = MemoryTraceSink()
        sink.record("x", "data with\nnewlines")
        assert sink.records[0] == "x: 'data with\\nnewlines'"


class TestCallbackTraceSink:
    """Callback sink forwards formatted lines."""

    def test_calls_callback(self):
        received = []

        def cb(line: str) -> None:
            received.append(line)

        sink = CallbackTraceSink(cb)
        sink.record("runner-b", "hello")
        assert len(received) == 1
        assert received[0] == "runner-b: 'hello'"

    def test_callback_exception_does_not_crash(self):
        def cb(line: str) -> None:
            raise RuntimeError("boom")

        sink = CallbackTraceSink(cb)
        sink.record("runner-b", "data")


class TestWriteTraceLoggerMultiSink:
    """Logger with multiple sinks."""

    def test_all_sinks_receive_record(self, tmp_path):
        path = tmp_path / "multi.log"
        received = []

        logger = WriteTraceLogger(
            name="multi",
            sinks=[
                FileTraceSink(str(path)),
                MemoryTraceSink(),
                CallbackTraceSink(lambda line: received.append(line)),
            ],
        )
        logger.record("payload")

        content = path.read_text(encoding="utf-8")
        assert "payload" in content
        assert len(received) == 1

    def test_partial_failure_does_not_block_others(self, tmp_path):
        path = tmp_path / "partial.log"

        def cb(line: str) -> None:
            raise RuntimeError("fail")

        logger = WriteTraceLogger(
            name="partial",
            sinks=[
                FileTraceSink(str(path)),
                CallbackTraceSink(cb),
            ],
        )
        logger.record("should still write to file")

        content = path.read_text(encoding="utf-8")
        assert "should still write to file" in content


class TestFromEnv:
    """from_env factory and ACTCLI_WRITE_TRACE toggle."""

    def test_env_var_set_to_1_creates_file_sink(self, monkeypatch):
        monkeypatch.setenv("ACTCLI_WRITE_TRACE", "1")
        logger = WriteTraceLogger.from_env("runner-c")
        assert len(logger.sinks) == 1
        assert isinstance(logger.sinks[0], FileTraceSink)

    def test_env_var_set_to_0_no_sinks(self, monkeypatch):
        monkeypatch.setenv("ACTCLI_WRITE_TRACE", "0")
        logger = WriteTraceLogger.from_env("runner-c")
        assert logger.sinks == []

    def test_env_var_unset_no_sinks(self, monkeypatch):
        monkeypatch.delenv("ACTCLI_WRITE_TRACE", raising=False)
        logger = WriteTraceLogger.from_env("runner-c")
        assert logger.sinks == []

    def test_env_var_empty_string_no_sinks(self, monkeypatch):
        monkeypatch.setenv("ACTCLI_WRITE_TRACE", "")
        logger = WriteTraceLogger.from_env("runner-c")
        assert logger.sinks == []

    def test_file_sink_uses_default_path(self, monkeypatch):
        monkeypatch.setenv("ACTCLI_WRITE_TRACE", "1")
        logger = WriteTraceLogger.from_env("runner-d")
        assert isinstance(logger.sinks[0], FileTraceSink)
        assert logger.sinks[0]._path == WriteTraceLogger.DEFAULT_TRACE_PATH

    def test_env_resolved_at_construction_time(self, monkeypatch):
        monkeypatch.setenv("ACTCLI_WRITE_TRACE", "1")
        logger = WriteTraceLogger.from_env("runner-e")
        monkeypatch.delenv("ACTCLI_WRITE_TRACE")
        assert len(logger.sinks) == 1

    def test_other_env_values_no_sinks(self, monkeypatch):
        for val in ("true", "on", "yes", "2", "enabled"):
            monkeypatch.setenv("ACTCLI_WRITE_TRACE", val)
            logger = WriteTraceLogger.from_env("runner-f")
            assert logger.sinks == [], f"val={val!r} should produce no sinks"


class TestTerminalRunnerIntegration:
    """TerminalRunner uses WriteTraceLogger correctly."""

    @staticmethod
    def _runner_capture_exit(runner, timeout=0.5):
        import time
        exit_codes = []
        runner.on_exit(lambda code: exit_codes.append(code))
        deadline = time.time() + timeout
        while time.time() < deadline and not exit_codes:
            time.sleep(0.05)
        runner.close()
        return exit_codes

    def test_runner_write_uses_tracer_off_by_default(self, monkeypatch, tmp_path):
        monkeypatch.delenv("ACTCLI_WRITE_TRACE", raising=False)
        runner = TerminalRunner(name="test-int", command=["cat"])
        runner.start()
        try:
            runner.write("integration test\n")
        finally:
            self._runner_capture_exit(runner)

    def test_runner_write_with_tracer_enabled(self, monkeypatch, tmp_path):
        trace_path = tmp_path / "write_debug.log"
        monkeypatch.setenv("ACTCLI_WRITE_TRACE", "1")
        with monkeypatch.context() as m:
            m.setattr(WriteTraceLogger, "DEFAULT_TRACE_PATH", str(trace_path))
            runner = TerminalRunner(name="int-runner", command=["cat"])
            runner.start()
            try:
                runner.write("hello-trace\n")
                import time
                time.sleep(0.2)
            finally:
                self._runner_capture_exit(runner)
        assert trace_path.exists()
        content = trace_path.read_text(encoding="utf-8")
        assert "int-runner: 'hello-trace\\n'" in content

    def test_runner_no_hardcoded_trace_path_in_module(self):
        import src.actcli.bench_textual.terminal_runner as tr_mod
        source = Path(tr_mod.__file__).read_text(encoding="utf-8")
        assert "docs/Trouble-Snaps/write_debug.log" not in source


class TestFormatPreservation:
    """On-disk format is {name}: {repr(data)}\\n."""

    def test_simple_string(self, tmp_path):
        path = tmp_path / "fmt.log"
        sink = FileTraceSink(str(path))
        sink.record("alice", "hello world")
        assert path.read_text(encoding="utf-8") == "alice: 'hello world'\n"

    def test_newlines_repr(self, tmp_path):
        path = tmp_path / "fmt2.log"
        sink = FileTraceSink(str(path))
        sink.record("bob", "line1\nline2\n")
        content = path.read_text(encoding="utf-8")
        assert content == "bob: 'line1\\nline2\\n'\n"

    def test_special_chars_repr(self, tmp_path):
        path = tmp_path / "fmt3.log"
        sink = FileTraceSink(str(path))
        sink.record("carol", "tab\there\rback")
        content = path.read_text(encoding="utf-8")
        assert "\\t" in content
        assert "\\r" in content


class TestBestEffortDegradation:
    """Sinks degrade gracefully on failure."""

    def test_sinks_self_isolate_failures(self, tmp_path):
        path = tmp_path / "partial.log"
        writes = []

        class UnreliableSink(FileTraceSink):
            _fail_count = 0

            def record(self, name, data):
                try:
                    UnreliableSink._fail_count += 1
                    if UnreliableSink._fail_count % 2 == 0:
                        raise OSError("fake write failure")
                    super().record(name, data)
                except Exception:
                    writes.append(("fail", name, data))

        UnreliableSink._fail_count = 0
        sink = UnreliableSink(str(path))
        sink.record("degrade", "first")
        sink.record("degrade", "second")
        sink.record("degrade", "third")
        content = path.read_text(encoding="utf-8")
        assert "first" in content
        assert "third" in content
        assert "second" not in content
