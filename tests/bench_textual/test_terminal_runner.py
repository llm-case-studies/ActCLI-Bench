"""Tests for TerminalRunner - PTY management and process lifecycle.

CRITICAL: These tests document the PTY winsize struct ordering which is
OPPOSITE to our internal cols/rows convention:
- We use: (cols, rows) = (WIDTH, HEIGHT)
- PTY uses: (rows, cols) = (HEIGHT, WIDTH) in struct winsize

This is another source of dimension confusion that tests must clarify!
"""

import pytest
import time
import os
from src.actcli.bench_textual.terminal_runner import TerminalRunner


class TestPTYWinsizeOrdering:
    """Tests for PTY winsize - documenting the (rows, cols) ordering."""

    def test_set_winsize_parameter_order(self):
        """CRITICAL: Document that set_winsize takes (rows, cols) order.

        PTY winsize struct is: struct winsize { rows, cols, xpixel, ypixel }
        This is OPPOSITE to our (cols, rows) convention!
        """
        runner = TerminalRunner(name="test", command=["cat"])
        runner.start()

        try:
            # Set size: 39 rows (HEIGHT) x 175 cols (WIDTH)
            runner.set_winsize(rows=39, cols=175)

            # Get it back - should return (rows, cols) tuple
            actual = runner.get_winsize()

            assert actual is not None, "get_winsize should return a tuple"
            assert actual == (39, 175), \
                f"Expected (39, 175) but got {actual}. PTY winsize is (rows, cols)!"

        finally:
            runner.close()

    def test_initial_winsize_in_child(self):
        """Test that child process receives correct initial winsize.

        The child sets winsize before exec to avoid 80x24 default.
        """
        runner = TerminalRunner(name="test", command=["bash", "-c", "stty size"])
        runner.start()

        # Give it time to execute and capture output
        time.sleep(0.3)

        output = runner.first_output_preview()
        runner.close()

        # Should contain "48 240" (the default initial size)
        # Note: stty size outputs "rows cols"
        assert "48" in output or "240" in output, \
            f"Expected initial size in output, got: {output}"

    def test_winsize_after_resize(self):
        """Test that resize updates the PTY correctly."""
        runner = TerminalRunner(name="test", command=["sleep", "10"])
        runner.start()

        try:
            # Initial size
            runner.set_winsize(rows=24, cols=80)
            initial = runner.get_winsize()
            assert initial == (24, 80)

            # Resize
            runner.set_winsize(rows=39, cols=175)
            after_resize = runner.get_winsize()
            assert after_resize == (39, 175), \
                "Winsize should update after resize"

        finally:
            runner.close()

    def test_multiple_resizes(self):
        """Test that multiple resizes work correctly."""
        runner = TerminalRunner(name="test", command=["sleep", "10"])
        runner.start()

        try:
            # Sequence of resizes
            runner.set_winsize(rows=24, cols=80)
            assert runner.get_winsize() == (24, 80)

            runner.set_winsize(rows=30, cols=120)
            assert runner.get_winsize() == (30, 120)

            runner.set_winsize(rows=39, cols=175)
            assert runner.get_winsize() == (39, 175)

        finally:
            runner.close()


class TestTerminalLifecycle:
    """Test terminal process lifecycle."""

    def test_start_and_is_alive(self):
        """Test that terminal starts and reports as alive."""
        runner = TerminalRunner(name="test", command=["sleep", "2"])

        assert not runner.is_alive(), "Should not be alive before start"

        success = runner.start()
        assert success, "start() should return True"
        assert runner.is_alive(), "Should be alive after start"
        assert runner.pid is not None, "Should have a PID"

        runner.close()
        time.sleep(0.1)
        assert not runner.is_alive(), "Should not be alive after close"

    def test_simple_command_execution(self):
        """Test executing a simple command and capturing output."""
        output_buffer = []

        def on_output(text):
            output_buffer.append(text)

        runner = TerminalRunner(name="test", command=["echo", "hello"])
        runner.on_output(on_output)
        runner.start()

        # Wait for output
        time.sleep(0.5)

        runner.close()

        # Should have captured "hello"
        all_output = "".join(output_buffer)
        assert "hello" in all_output, f"Expected 'hello' in output, got: {all_output}"

    def test_exit_callback(self):
        """Test that exit callback is called when process exits."""
        exit_codes = []

        def on_exit(code):
            exit_codes.append(code)

        runner = TerminalRunner(name="test", command=["bash", "-c", "exit 42"])
        runner.on_exit(on_exit)
        runner.start()

        # Wait for process to exit
        time.sleep(0.5)

        runner.close()

        # Should have captured exit code 42
        assert 42 in exit_codes, f"Expected exit code 42, got: {exit_codes}"

    def test_write_to_stdin(self):
        """Test writing to terminal's stdin."""
        output_buffer = []

        def on_output(text):
            output_buffer.append(text)

        # Use cat which echoes stdin to stdout
        runner = TerminalRunner(name="test", command=["cat"])
        runner.on_output(on_output)
        runner.start()

        # Give it time to start
        time.sleep(0.2)

        # Write to stdin
        runner.write("test input\n")

        # Wait for echo
        time.sleep(0.3)

        runner.close()

        all_output = "".join(output_buffer)
        assert "test input" in all_output, f"Expected echoed input, got: {all_output}"


class TestFirstOutputCapture:
    """Test first output preview functionality."""

    def test_first_output_preview(self):
        """Test that first output is captured."""
        runner = TerminalRunner(name="test", command=["echo", "first output"])
        runner.start()

        time.sleep(0.3)

        preview = runner.first_output_preview()
        runner.close()

        assert "first output" in preview, f"Expected 'first output', got: {preview}"

    def test_first_output_limit(self):
        """Test that first output preview respects limit."""
        runner = TerminalRunner(name="test", command=["echo", "A" * 1000])
        runner.start()

        time.sleep(0.3)

        # Default limit is 512 bytes
        preview = runner.first_output_preview(limit=100)
        runner.close()

        assert len(preview) <= 100, f"Preview should be limited to 100 chars"

    def test_empty_first_output(self):
        """Test first output when command produces no output."""
        runner = TerminalRunner(name="test", command=["sleep", "0.1"])
        runner.start()

        time.sleep(0.2)

        preview = runner.first_output_preview()
        runner.close()

        # Should return empty string or minimal output
        assert isinstance(preview, str), "Preview should always return a string"


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_command(self):
        """Test that invalid commands are handled gracefully."""
        runner = TerminalRunner(name="test", command=["nonexistent_command_xyz"])

        # start() may succeed (fork succeeds) but child will fail to exec
        success = runner.start()

        # Give it time for exec to fail
        time.sleep(0.5)

        # Process should die after failed exec
        # Note: The process might still be alive briefly due to fallback to bash -lc
        # This is OK - the test just ensures no crash occurs
        runner.close()

    def test_write_to_closed_terminal(self):
        """Test that writing to closed terminal doesn't crash."""
        runner = TerminalRunner(name="test", command=["cat"])

        # Try writing before start - should not crash
        runner.write("test\n")

        # Start, close, then write - should not crash
        runner.start()
        time.sleep(0.1)
        runner.close()
        time.sleep(0.1)

        runner.write("test after close\n")  # Should be no-op

    def test_double_start(self):
        """Test that calling start() twice doesn't cause issues."""
        runner = TerminalRunner(name="test", command=["sleep", "1"])

        runner.start()
        pid1 = runner.pid

        # Second start should be a no-op
        runner.start()
        pid2 = runner.pid

        assert pid1 == pid2, "Second start should not create new process"

        runner.close()

    def test_double_close(self):
        """Test that calling close() twice doesn't crash."""
        runner = TerminalRunner(name="test", command=["sleep", "1"])
        runner.start()

        runner.close()
        runner.close()  # Should not crash


class TestMutedFlag:
    """Test muted flag behavior."""

    def test_muted_default_true(self):
        """Test that terminals default to muted=True."""
        runner = TerminalRunner(name="test", command=["cat"])
        assert runner.muted is True, "Terminals should default to muted"

    def test_muted_can_be_set(self):
        """Test that muted flag can be changed."""
        runner = TerminalRunner(name="test", command=["cat"], muted=False)
        assert runner.muted is False

        runner.muted = True
        assert runner.muted is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
