"""Base shell class for ActCLI applications.

Provides a reusable 3-panel layout with:
- Sidebar: Brand + Navigation tree + Theme hints
- Detail view: Title + Main content area
- Control panel: Input + Action buttons

Products extend this class and implement the protocols to customize behavior.
"""

from typing import Protocol, Iterator, runtime_checkable
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Static, Tree, Input, Button


@runtime_checkable
class NavigationProvider(Protocol):
    """Protocol for providing navigation tree structure.

    Implementers should build the navigation tree structure
    in the build_navigation_tree method.
    """

    def build_navigation_tree(self, tree: Tree) -> None:
        """Build the navigation tree structure.

        Args:
            tree: The Tree widget to populate with navigation nodes
        """
        ...


@runtime_checkable
class DetailViewProvider(Protocol):
    """Protocol for providing the main detail view widget(s).

    Implementers should yield the main content widgets
    that appear in the detail panel (e.g., terminal view, log view).
    """

    def compose_detail_view(self) -> ComposeResult:
        """Compose the detail view content widgets.

        Yields:
            Widget(s) to display in the detail panel
        """
        ...


@runtime_checkable
class ControlPanelProvider(Protocol):
    """Protocol for providing control panel widgets.

    Implementers should yield control panel widgets
    (input fields, buttons, etc.) for the bottom control area.
    """

    def compose_control_panel(self) -> ComposeResult:
        """Compose the control panel widgets.

        Yields:
            Widget(s) to display in the control panel
        """
        ...


class ActCLIShell(App):
    """Base shell for ActCLI applications.

    Provides a 3-panel layout with theming support.
    Products extend this class and implement the provider protocols
    to customize the navigation, detail view, and control panel.

    Theme switching is built-in via F1/F2/F3 keys.
    """

    # Available themes - subclasses can override
    THEMES = ["ledger", "analyst", "seminar"]

    # Default theme - subclasses can override
    DEFAULT_THEME = "ledger"

    # CSS file path - subclasses can override to add additional styles
    CSS_PATH = None

    BINDINGS = [
        Binding("f1", "switch_theme('ledger')", "Ledger theme"),
        Binding("f2", "switch_theme('analyst')", "Analyst theme"),
        Binding("f3", "switch_theme('seminar')", "Seminar theme"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, *args, **kwargs):
        """Initialize the shell."""
        super().__init__(*args, **kwargs)

        # Track current theme (using CSS classes, not Textual's theme system)
        self._active_theme = self.DEFAULT_THEME

        # Widgets that subclasses can access
        self.nav_tree: Tree | None = None
        self.status_line: Static | None = None
        self.control_input: Input | None = None

    def compose(self) -> ComposeResult:
        """Compose the base shell layout.

        Layout structure:
        - Header
        - Body (horizontal):
          - Sidebar (vertical):
            - Brand
            - Navigation tree
            - Theme hints
          - Detail panel (vertical):
            - Status line
            - Detail view content (from DetailViewProvider)
            - Control panel (from ControlPanelProvider)
        """
        yield Header(id="header")

        with Horizontal(id="body"):
            # Sidebar
            with Vertical(id="sidebar"):
                yield Static(self.get_brand_text(), id="brand")
                self.nav_tree = Tree("Navigation", id="nav-tree")
                yield self.nav_tree
                yield Static(self.get_theme_hints(), id="hint")

            # Detail panel
            with Vertical(id="detail"):
                # Status line
                self.status_line = Static(self.get_initial_status(), id="title")
                yield self.status_line

                # Detail view content (from subclass)
                if isinstance(self, DetailViewProvider):
                    yield from self.compose_detail_view()

                # Control panel (from subclass)
                if isinstance(self, ControlPanelProvider):
                    with Horizontal(id="control"):
                        yield from self.compose_control_panel()

    def on_mount(self) -> None:
        """Called when app is mounted.

        Applies the default theme and builds the navigation tree.
        """
        # Apply default theme class
        self.add_class(f"theme-{self._active_theme}")

        # Build navigation tree if provider implemented
        if isinstance(self, NavigationProvider) and self.nav_tree:
            self.build_navigation_tree(self.nav_tree)

    def get_brand_text(self) -> str:
        """Get the brand text for the sidebar.

        Subclasses should override to customize branding.

        Returns:
            Brand text string (e.g., "ActCLI • ProductName")
        """
        return "ActCLI"

    def get_theme_hints(self) -> str:
        """Get the theme hint text for the sidebar.

        Returns:
            Theme hint string showing available themes
        """
        return "F1: Ledger • F2: Analyst • F3: Seminar"

    def get_initial_status(self) -> str:
        """Get the initial status line text.

        Subclasses can override to customize initial status.

        Returns:
            Initial status text
        """
        return "Ready"

    def action_switch_theme(self, theme_name: str) -> None:
        """Switch to a different theme.

        Args:
            theme_name: Name of the theme (ledger, analyst, seminar)
        """
        # Remove old theme class
        self.remove_class(f"theme-{self._active_theme}")

        # Apply new theme
        self._active_theme = theme_name
        self.add_class(f"theme-{theme_name}")

    def update_status(self, text: str) -> None:
        """Update the status line text.

        Args:
            text: New status text
        """
        if self.status_line:
            self.status_line.update(text)
