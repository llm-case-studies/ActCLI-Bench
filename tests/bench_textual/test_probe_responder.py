"""Tests for TerminalProbeResponder -- response computation for DSR and future probes."""

import pytest
from src.actcli.bench_textual.instrumentation.probe_responder import TerminalProbeResponder


class FakeCursor:
    y = 4
    x = 6


class FakeScreen:
    cursor = FakeCursor()


class FakeEmulatorPyte:
    mode = "pyte"
    _screen = FakeScreen()


class FakeEmulatorPlain:
    mode = "plain"
    _screen = FakeScreen()


class FakeEmulatorNoScreen:
    mode = "pyte"
    _screen = None


class FakeEmulatorNoCursor:
    mode = "pyte"
    _screen = type("_Screen", (), {"cursor": None})()


class TestTerminalProbeResponder:
    """Response computation independent of emulator wiring."""

    def test_dsr_with_pyte_cursor_returns_correct_response(self):
        responder = TerminalProbeResponder()
        response = responder.response_for_text("\x1b[6n", FakeEmulatorPyte())
        assert response == "\x1b[5;7R"

    def test_no_query_returns_none(self):
        responder = TerminalProbeResponder()
        response = responder.response_for_text("ordinary output", FakeEmulatorPyte())
        assert response is None

    def test_non_pyte_mode_returns_none(self):
        responder = TerminalProbeResponder()
        response = responder.response_for_text("\x1b[6n", FakeEmulatorPlain())
        assert response is None

    def test_missing_screen_returns_none(self):
        responder = TerminalProbeResponder()
        response = responder.response_for_text("\x1b[6n", FakeEmulatorNoScreen())
        assert response is None

    def test_missing_cursor_returns_none(self):
        responder = TerminalProbeResponder()
        response = responder.response_for_text("\x1b[6n", FakeEmulatorNoCursor())
        assert response is None

    def test_zero_based_cursor_converts_to_one_based(self):
        class ZeroCursor:
            y = 0
            x = 0

        class ZeroScreen:
            cursor = ZeroCursor()

        class ZeroEmulator:
            mode = "pyte"
            _screen = ZeroScreen()

        responder = TerminalProbeResponder()
        response = responder.response_for_text("\x1b[6n", ZeroEmulator())
        assert response == "\x1b[1;1R"

    def test_malformed_emulator_does_not_raise(self):
        class BadEmulator:
            pass

        responder = TerminalProbeResponder()
        response = responder.response_for_text("\x1b[6n", BadEmulator())
        assert response is None

    def test_no_emulator_does_not_raise(self):
        responder = TerminalProbeResponder()
        response = responder.response_for_text("\x1b[6n", None)
        assert response is None
