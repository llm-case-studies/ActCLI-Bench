"""Tests for TermView - focusable terminal widget with key forwarding.

These tests document the key event handling and ensure keys are properly
forwarded to the PTY.
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.actcli.bench_textual.term_view import TermView


class MockKeyEvent:
    """Mock Textual Key event for testing."""

    def __init__(self, key: str, character: str = None, modifiers: list = None):
        self.key = key
        self.character = character
        self.modifiers = modifiers or []

    def stop(self):
        """Mock event.stop()."""
        pass


class TestTermViewBasics:
    """Test basic TermView functionality."""

    def test_can_focus(self):
        """Test that TermView is focusable."""
        view = TermView()
        assert view.can_focus is True, "TermView should be focusable"

    def test_set_writer(self):
        """Test that writer callback can be set."""
        view = TermView()
        writer = Mock()

        view.set_writer(writer)
        assert view._writer is writer

    def test_set_navigator(self):
        """Test that navigator callback can be set."""
        view = TermView()
        navigator = Mock()

        view.set_navigator(navigator)
        assert view._navigator is navigator

    def test_set_on_focus_callback(self):
        """Test that focus callback can be set."""
        view = TermView()
        callback = Mock()

        view.set_on_focus(callback)
        assert view._on_focus_callback is callback

    def test_on_focus_adds_class(self):
        """Test that on_focus adds focus styling class."""
        view = TermView()
        callback = Mock()
        view.set_on_focus(callback)

        # Mock the add_class method
        view.add_class = Mock()

        view.on_focus()

        view.add_class.assert_called_once_with("has-focus")
        callback.assert_called_once()


class TestKeyForwarding:
    """Test that keys are properly forwarded to PTY."""

    def test_printable_character_forwarding(self):
        """Test that printable characters are forwarded."""
        view = TermView()
        writer = Mock()
        view.set_writer(writer)

        # Send 'a' key
        event = MockKeyEvent(key='a', character='a')
        view.on_key(event)

        writer.assert_called_once_with('a')

    def test_multiple_characters(self):
        """Test forwarding multiple characters."""
        view = TermView()
        writer = Mock()
        view.set_writer(writer)

        for char in "hello":
            event = MockKeyEvent(key=char, character=char)
            view.on_key(event)

        assert writer.call_count == 5
        calls = [call[0][0] for call in writer.call_args_list]
        assert calls == list("hello")

    def test_enter_key_sends_carriage_return(self):
        """Test that Enter key sends \\r."""
        view = TermView()
        writer = Mock()
        view.set_writer(writer)

        event = MockKeyEvent(key='enter', character='\r')
        view.on_key(event)

        writer.assert_called_with('\r')

    def test_backspace_key(self):
        """Test that Backspace sends DEL character."""
        view = TermView()
        writer = Mock()
        view.set_writer(writer)

        event = MockKeyEvent(key='backspace')
        view.on_key(event)

        writer.assert_called_with('\x7f')

    def test_arrow_keys(self):
        """Test that arrow keys send ANSI escape sequences."""
        view = TermView()
        writer = Mock()
        view.set_writer(writer)

        test_cases = [
            ('up', '\x1b[A'),
            ('down', '\x1b[B'),
            ('right', '\x1b[C'),
            ('left', '\x1b[D'),
        ]

        for key, expected_seq in test_cases:
            writer.reset_mock()
            event = MockKeyEvent(key=key)
            view.on_key(event)
            writer.assert_called_with(expected_seq), \
                f"Arrow key '{key}' should send '{repr(expected_seq)}'"

    def test_control_keys(self):
        """Test Ctrl+key combinations."""
        view = TermView()
        writer = Mock()
        view.set_writer(writer)

        # Ctrl+C should send \x03
        event = MockKeyEvent(key='c', modifiers=['ctrl'])
        view.on_key(event)

        writer.assert_called_with('\x03')

    def test_no_writer_attached(self):
        """Test that keys are ignored when no writer is attached."""
        view = TermView()
        # Don't set a writer

        event = MockKeyEvent(key='a', character='a')
        # Should not crash
        view.on_key(event)

    def test_key_fallback_when_no_character(self):
        """Test fallback to event.key when event.character is None."""
        view = TermView()
        writer = Mock()
        view.set_writer(writer)

        # Some keys might not have character attribute
        event = MockKeyEvent(key='x', character=None)
        view.on_key(event)

        # Should use key as fallback
        writer.assert_called_with('x')


class TestScrollbackNavigation:
    """Test scrollback navigation with Ctrl+PageUp/Down."""

    def test_ctrl_pageup_navigates_scrollback(self):
        """Test that Ctrl+PageUp triggers scrollback navigation."""
        view = TermView()
        navigator = Mock(return_value=True)
        view.set_navigator(navigator)

        event = MockKeyEvent(key='pageup', modifiers=['ctrl'])
        event.stop = Mock()
        view.on_key(event)

        navigator.assert_called_once_with('pageup', -20)
        event.stop.assert_called_once()

    def test_ctrl_pagedown_navigates_scrollback(self):
        """Test that Ctrl+PageDown triggers scrollback navigation."""
        view = TermView()
        navigator = Mock(return_value=True)
        view.set_navigator(navigator)

        event = MockKeyEvent(key='pagedown', modifiers=['ctrl'])
        event.stop = Mock()
        view.on_key(event)

        navigator.assert_called_once_with('pagedown', 20)

    def test_ctrl_home_and_end(self):
        """Test Ctrl+Home and Ctrl+End navigation."""
        view = TermView()
        navigator = Mock(return_value=True)
        view.set_navigator(navigator)

        # Ctrl+Home
        event = MockKeyEvent(key='home', modifiers=['ctrl'])
        event.stop = Mock()
        view.on_key(event)
        navigator.assert_called_with('home', 0)

        navigator.reset_mock()

        # Ctrl+End
        event = MockKeyEvent(key='end', modifiers=['ctrl'])
        event.stop = Mock()
        view.on_key(event)
        navigator.assert_called_with('end', 0)

    def test_regular_pageup_without_ctrl(self):
        """Test that PageUp without Ctrl is forwarded as key, not navigation."""
        view = TermView()
        writer = Mock()
        navigator = Mock(return_value=True)
        view.set_writer(writer)
        view.set_navigator(navigator)

        # PageUp without Ctrl modifier
        event = MockKeyEvent(key='pageup', modifiers=[])
        view.on_key(event)

        # Should send escape sequence, not navigate
        writer.assert_called_with('\x1b[5~')
        navigator.assert_not_called()


class TestMouseScrolling:
    """Test mouse wheel scrolling."""

    def test_mouse_scroll_up(self):
        """Test mouse wheel scroll up."""
        view = TermView()
        navigator = Mock(return_value=True)
        view.set_navigator(navigator)

        # Mock scroll event
        event = Mock()
        event.stop = Mock()

        view.on_mouse_scroll_up(event)

        navigator.assert_called_once_with('wheel', -3)
        event.stop.assert_called_once()

    def test_mouse_scroll_down(self):
        """Test mouse wheel scroll down."""
        view = TermView()
        navigator = Mock(return_value=True)
        view.set_navigator(navigator)

        event = Mock()
        event.stop = Mock()

        view.on_mouse_scroll_down(event)

        navigator.assert_called_once_with('wheel', 3)

    def test_scroll_without_navigator(self):
        """Test scroll events when no navigator is set."""
        view = TermView()
        # No navigator set

        event = Mock()
        event.stop = Mock()

        # Should not crash
        view.on_mouse_scroll_up(event)
        view.on_mouse_scroll_down(event)

        # Stop should not be called if navigator not set
        event.stop.assert_not_called()


class TestKeyLogging:
    """Test key event logging for diagnostics."""

    def test_key_logger_called(self):
        """Test that key logger callback is called."""
        view = TermView()
        logger = Mock()
        writer = Mock()

        view.set_key_logger(logger)
        view.set_writer(writer)

        event = MockKeyEvent(key='a', character='a', modifiers=[])
        view.on_key(event)

        logger.assert_called_once_with('a', 'a', set())

    def test_key_logger_with_modifiers(self):
        """Test key logger with modifier keys."""
        view = TermView()
        logger = Mock()
        writer = Mock()

        view.set_key_logger(logger)
        view.set_writer(writer)

        event = MockKeyEvent(key='c', character=None, modifiers=['ctrl'])
        view.on_key(event)

        # Logger should be called with key, character, and modifiers
        assert logger.called
        call_args = logger.call_args[0]
        assert call_args[0] == 'c'
        assert 'ctrl' in call_args[2]


class TestSizeListener:
    """Test resize event listener."""

    def test_size_listener_on_resize(self):
        """Test that size listener is called on resize."""
        view = TermView()
        listener = Mock()
        view.set_size_listener(listener)

        # Mock resize event
        event = Mock()

        view.on_resize(event)

        listener.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
