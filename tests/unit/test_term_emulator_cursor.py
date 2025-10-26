"""Regression tests for cursor placement heuristics in EmulatedTerminal."""

from __future__ import annotations

import pytest

from actcli.bench_textual.term_emulator import EmulatedTerminal


@pytest.mark.parametrize("cursor_char", ["▌", "|"])
def test_reverse_video_cursor_wins(cursor_char: str) -> None:
    """When reverse-video highlight is present, use it as the cursor."""

    term = EmulatedTerminal(cols=80, rows=4)
    term.feed("│ > welcome an")
    term.feed("\x1b[7mh\x1b[27mello !")

    rendered = term.text_with_cursor(cursor_char=cursor_char)
    first_line = rendered.splitlines()[0]

    assert f"{cursor_char}hello" in first_line
    assert not first_line.rstrip().endswith(cursor_char)


def test_pattern_fallback_when_no_highlight() -> None:
    """If there is no highlight, fall back to prompt pattern detection."""

    term = EmulatedTerminal(cols=80, rows=4)
    term.feed("│ > draft")

    rendered = term.text_with_cursor()
    first_line = rendered.splitlines()[0]

    assert first_line.count("▌") == 1
    assert first_line.rstrip().endswith("▌")


def test_vt_cursor_used_as_last_resort() -> None:
    """Without highlight or patterns, rely on pyte's cursor position."""

    term = EmulatedTerminal(cols=40, rows=3)
    term.feed("hello")

    rendered = term.text_with_cursor()
    first_line = rendered.splitlines()[0]

    assert first_line.strip().endswith("▌")
    # Ensure it is appended directly after the existing text
    assert "hello▌" in first_line
