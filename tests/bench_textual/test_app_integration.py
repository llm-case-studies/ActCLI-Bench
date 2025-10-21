"""Integration tests for BenchTextualApp.

These tests ensure the main app can be instantiated and composed
without errors. They serve as a safety net during refactoring.
"""

import pytest
from textual.widgets import Tree, Input, Button, Static
from src.actcli.bench_textual.app import BenchTextualApp

# Configure pytest-anyio to handle async tests (asyncio backend only)
pytestmark = pytest.mark.anyio(backend="asyncio")


class TestAppInstantiation:
    """Test that the app can be created and composed."""

    def test_app_can_be_instantiated(self):
        """Test that BenchTextualApp can be created."""
        app = BenchTextualApp()
        assert app is not None
        assert app.title == "BenchTextualApp"

    def test_app_has_required_attributes(self):
        """Test that app initializes core attributes."""
        app = BenchTextualApp()

        # Managers should be initialized
        assert hasattr(app, 'log_manager')
        assert hasattr(app, 'terminal_manager')
        assert hasattr(app, 'diagnostics')
        assert hasattr(app, 'session_manager')

        # UI state
        assert hasattr(app, 'active_view')
        assert hasattr(app, 'active_terminal')
        assert app.active_view == "terminal"
        assert app.active_terminal is None

    def test_app_has_theme_bindings(self):
        """Test that theme switching bindings exist."""
        app = BenchTextualApp()

        # Should have F1/F2/F3 bindings for themes
        binding_keys = [b.key for b in app.BINDINGS]
        assert "f1" in binding_keys
        assert "f2" in binding_keys
        assert "f3" in binding_keys

    async def test_app_can_mount(self):
        """Test that app can mount without errors."""
        async with BenchTextualApp().run_test() as pilot:
            app = pilot.app

            # Basic smoke test - app should be running
            assert app.is_running

            # Should have mounted key widgets
            assert app.query_one("#nav-tree", Tree) is not None
            assert app.query_one("#terminal-view") is not None
            assert app.query_one("#control-input", Input) is not None
            assert app.query_one("#brand", Static) is not None


class TestThemeSwitching:
    """Test theme switching functionality."""

    async def test_default_theme_is_ledger(self):
        """Test that app starts with Ledger theme."""
        async with BenchTextualApp().run_test() as pilot:
            app = pilot.app
            assert "theme-ledger" in app.classes

    async def test_can_switch_to_analyst_theme(self):
        """Test switching to Analyst theme."""
        async with BenchTextualApp().run_test() as pilot:
            app = pilot.app

            # Switch theme
            await pilot.press("f2")
            await pilot.pause()

            # Should have analyst theme class
            assert "theme-analyst" in app.classes

    async def test_can_switch_to_seminar_theme(self):
        """Test switching to Seminar theme."""
        async with BenchTextualApp().run_test() as pilot:
            app = pilot.app

            # Switch theme
            await pilot.press("f3")
            await pilot.pause()

            # Should have seminar theme class
            assert "theme-seminar" in app.classes


class TestNavigationTree:
    """Test navigation tree building."""

    async def test_nav_tree_has_root_sections(self):
        """Test that navigation tree builds expected sections."""
        async with BenchTextualApp().run_test() as pilot:
            app = pilot.app
            nav_tree = app.query_one("#nav-tree", Tree)

            # Should have built the tree structure
            # Root should have children: Terminals, Sessions, Settings, Logs
            root_children = list(nav_tree.root.children)
            assert len(root_children) >= 4  # At least 4 sections

            # Check section labels (convert Text objects to string)
            labels = [str(child.label) for child in root_children]
            assert "Terminals" in labels
            assert "Sessions" in labels
            assert "Settings" in labels
            assert "Logs" in labels

    async def test_terminals_section_has_add_node(self):
        """Test that Terminals section has '+ Add…' node."""
        async with BenchTextualApp().run_test() as pilot:
            app = pilot.app
            nav_tree = app.query_one("#nav-tree", Tree)

            # Find Terminals node (convert Text to string for comparison)
            terminals_node = None
            for child in nav_tree.root.children:
                if str(child.label) == "Terminals":
                    terminals_node = child
                    break

            assert terminals_node is not None

            # Should have '+ Add…' child
            children_labels = [str(c.label) for c in terminals_node.children]
            assert any("Add" in label for label in children_labels)


class TestControlPanel:
    """Test control panel functionality."""

    async def test_control_input_exists(self):
        """Test that control input is present."""
        async with BenchTextualApp().run_test() as pilot:
            app = pilot.app
            control_input = app.query_one("#control-input", Input)
            assert control_input is not None
            assert "Broadcast" in control_input.placeholder

    async def test_broadcast_button_exists(self):
        """Test that broadcast button is present."""
        async with BenchTextualApp().run_test() as pilot:
            app = pilot.app
            button = app.query_one("#btn-broadcast", Button)
            assert button is not None


class TestStatusLine:
    """Test status line updates."""

    async def test_status_line_exists(self):
        """Test that status line is present."""
        async with BenchTextualApp().run_test() as pilot:
            app = pilot.app
            status = app.query_one("#title", Static)
            assert status is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
