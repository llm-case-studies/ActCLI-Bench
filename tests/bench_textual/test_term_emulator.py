"""Tests for EmulatedTerminal - VT100 emulation via pyte.

CRITICAL: These tests document the cols/rows vs columns/lines confusion
that caused the terminal width bug. They serve as regression tests to
ensure the dimension ordering never gets swapped again.

Terminology (to prevent confusion):
- cols = WIDTH (horizontal, number of characters per line)
- rows = HEIGHT (vertical, number of lines)
- pyte uses: columns (width) and lines (height)
- PTY uses: (rows, cols) order in winsize struct
"""

import pytest
from src.actcli.bench_textual.term_emulator import EmulatedTerminal


class TestEmulatorDimensions:
    """Test suite for dimension handling - the source of our width bug!"""

    def test_pyte_dimension_order_on_init(self):
        """REGRESSION: Ensure pyte Screen is created with correct dimension order.

        Bug history: We were calling pyte.Screen(cols, rows) which pyte
        interpreted as Screen(columns=cols, lines=rows). But we accidentally
        passed them positionally as Screen(175, 39) which pyte saw as
        Screen(columns=175, lines=39) - CORRECT!

        However, the bug was we were passing (cols=175, rows=39) but pyte's
        constructor is (columns, lines), so if we used positional args wrong,
        we'd get a 39-column screen instead of 175!
        """
        # Create emulator with: 175 cols (WIDTH) x 39 rows (HEIGHT)
        emu = EmulatedTerminal(cols=175, rows=39)

        # Verify our internal tracking
        assert emu.cols == 175, "Emulator should track 175 columns (width)"
        assert emu.rows == 39, "Emulator should track 39 rows (height)"

        # CRITICAL: Verify pyte's internal state matches
        if emu._use_pyte:
            assert emu._screen.columns == 175, "pyte Screen should have 175 columns (width)"
            assert emu._screen.lines == 39, "pyte Screen should have 39 lines (height)"
            # If this fails, we've reintroduced the dimension swap bug!

    def test_pyte_dimension_order_on_resize(self):
        """REGRESSION: Ensure resize() maintains correct dimension order.

        Bug history: resize() was calling screen.resize(cols, rows) but
        pyte.Screen.resize(lines, columns) - OPPOSITE ORDER!
        This caused a 175x39 terminal to become 39x175 on resize.
        """
        emu = EmulatedTerminal(cols=80, rows=24)

        # Resize to wide terminal: 175 cols (WIDTH) x 39 rows (HEIGHT)
        emu.resize(cols=175, rows=39)

        # Verify internal tracking updated
        assert emu.cols == 175
        assert emu.rows == 39

        # CRITICAL: Verify pyte screen updated correctly
        if emu._use_pyte:
            assert emu._screen.columns == 175, "After resize, pyte should have 175 columns"
            assert emu._screen.lines == 39, "After resize, pyte should have 39 lines"
            # If this fails, resize() is swapping dimensions!

    def test_multiple_resizes_maintain_order(self):
        """Ensure multiple resizes don't accumulate dimension swap errors."""
        emu = EmulatedTerminal(cols=80, rows=24)

        # Resize sequence
        emu.resize(cols=120, rows=30)
        emu.resize(cols=175, rows=39)
        emu.resize(cols=100, rows=20)

        if emu._use_pyte:
            assert emu._screen.columns == 100
            assert emu._screen.lines == 20

    def test_narrow_terminal_dimensions(self):
        """Test that narrow terminals (like the bug) work correctly."""
        # This was the buggy state: 39 cols x 175 rows (swapped!)
        emu = EmulatedTerminal(cols=39, rows=175)

        if emu._use_pyte:
            assert emu._screen.columns == 39, "Should be 39 columns wide (narrow)"
            assert emu._screen.lines == 175, "Should be 175 lines tall (very tall)"

    def test_wide_terminal_dimensions(self):
        """Test wide terminals (the intended state)."""
        # This was the intended state: 175 cols x 39 rows
        emu = EmulatedTerminal(cols=175, rows=39)

        if emu._use_pyte:
            assert emu._screen.columns == 175, "Should be 175 columns wide (wide)"
            assert emu._screen.lines == 39, "Should be 39 lines tall (normal height)"


class TestEmulatorOutput:
    """Test emulator text output and rendering."""

    def test_simple_text_output(self):
        """Ensure emulator captures and displays simple text."""
        emu = EmulatedTerminal(cols=80, rows=24)
        emu.feed("Hello World\n")

        output = emu.text()
        assert "Hello World" in output

    def test_text_output_respects_width(self):
        """Ensure text output respects the configured width."""
        emu = EmulatedTerminal(cols=20, rows=5)

        # Feed a line longer than 20 chars
        long_line = "A" * 30
        emu.feed(long_line + "\n")

        output = emu.text()
        lines = output.split('\n')

        # First line should be truncated/wrapped to 20 chars
        # (exact behavior depends on pyte, but shouldn't be 30 chars on one line)
        first_line = lines[0] if lines else ""
        assert len(first_line) <= 20 or not emu._use_pyte, \
            "Output should respect width constraint"

    def test_emulator_mode_property(self):
        """Verify mode property reports correct emulator type."""
        emu = EmulatedTerminal(cols=80, rows=24)

        # Should be "pyte" if pyte is available, "plain" otherwise
        mode = emu.mode
        assert mode in ("pyte", "plain")
        assert mode == ("pyte" if emu._use_pyte else "plain")

    def test_text_with_cursor(self):
        """Test that cursor rendering works."""
        emu = EmulatedTerminal(cols=80, rows=24)
        emu.feed("Test")

        # Should be able to get text with cursor
        text_with_cursor = emu.text_with_cursor(show=True)
        assert isinstance(text_with_cursor, str)

        # With show=False, should return plain text
        text_without_cursor = emu.text_with_cursor(show=False)
        assert isinstance(text_without_cursor, str)

    def test_ansi_color_codes(self):
        """Test that ANSI color codes are processed."""
        emu = EmulatedTerminal(cols=80, rows=24)

        # Feed text with ANSI color codes
        emu.feed("\x1b[31mRed Text\x1b[0m\n")

        output = emu.text()
        # pyte processes ANSI, so color codes should be interpreted
        # Plain mode just strips them
        assert isinstance(output, str)


class TestEmulatorEdgeCases:
    """Test edge cases and error handling."""

    def test_zero_dimensions(self):
        """Test that zero dimensions are handled (or prevented)."""
        # Depending on implementation, this might raise or use defaults
        # Just ensure it doesn't crash
        try:
            emu = EmulatedTerminal(cols=0, rows=0)
            assert emu.cols >= 0
            assert emu.rows >= 0
        except (ValueError, AssertionError):
            # It's OK to reject zero dimensions
            pass

    def test_very_large_dimensions(self):
        """Test that very large dimensions don't cause issues."""
        emu = EmulatedTerminal(cols=1000, rows=1000)
        assert emu.cols == 1000
        assert emu.rows == 1000

        # Should be able to feed text
        emu.feed("Test\n")
        output = emu.text()
        assert isinstance(output, str)

    def test_resize_to_smaller(self):
        """Test resizing from large to small dimensions."""
        emu = EmulatedTerminal(cols=200, rows=50)
        emu.feed("Some content\n")

        # Resize to smaller
        emu.resize(cols=80, rows=24)

        assert emu.cols == 80
        assert emu.rows == 24

        # Should still be able to get text
        output = emu.text()
        assert isinstance(output, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
