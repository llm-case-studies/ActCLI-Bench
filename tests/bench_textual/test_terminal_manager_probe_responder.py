"""Tests that TerminalManager delegates DSR response to TermainalProbeResponder."""

import pytest
import inspect
from src.actcli.bench_textual.terminal_manager import TerminalManager, TerminalState


class FakeCursor:
    y = 3
    x = 8


class FakeScreen:
    cursor = FakeCursor()


class FakeEmulator:
    mode = "pyte"
    _screen = FakeScreen()

    def feed(self, data):
        pass


class NoopRunner:
    def write(self, data: str) -> None:
        pass


def test_manager_delegates_dsr_response_and_writes():
    mgr = TerminalManager(debug_logger=lambda msg: None)
    emu = FakeEmulator()
    runner = NoopRunner()
    state = TerminalState(item=runner, emulator=emu)
    mgr.terminals["test"] = state
    mgr.active_terminal = "test"

    writes = []

    def capture_write(data: str):
        writes.append(data)

    runner.write = capture_write

    mgr._append_terminal_output("test", "some output with \x1b[6n inside")

    assert len(writes) == 1
    assert writes[0] == "\x1b[4;9R"


def test_manager_no_write_when_no_query():
    mgr = TerminalManager(debug_logger=lambda msg: None)
    emu = FakeEmulator()
    runner = NoopRunner()
    state = TerminalState(item=runner, emulator=emu)
    mgr.terminals["test"] = state
    mgr.active_terminal = "test"

    writes = []
    runner.write = lambda data: writes.append(data)

    mgr._append_terminal_output("test", "no probe here")

    assert len(writes) == 0


def test_manager_no_write_when_non_pyte():
    class PlainEmulator(FakeEmulator):
        mode = "plain"

    mgr = TerminalManager(debug_logger=lambda msg: None)
    emu = PlainEmulator()
    runner = NoopRunner()
    state = TerminalState(item=runner, emulator=emu)
    mgr.terminals["test"] = state
    mgr.active_terminal = "test"

    writes = []
    runner.write = lambda data: writes.append(data)

    mgr._append_terminal_output("test", "output \x1b[6n query")

    assert len(writes) == 0


def test_manager_no__respond_to_dsr_defined():
    import inspect
    methods = [name for name, _ in inspect.getmembers(TerminalManager, predicate=inspect.isfunction)]
    assert "_respond_to_dsr" not in methods
