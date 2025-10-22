"""ActCLI Shell - Reusable TUI shell framework.

This module provides a complete TUI framework for building terminal applications
with Textual. It includes pre-built widgets, theming support, and a flexible
protocol-based architecture.

Quick Start
-----------
```python
from actcli.shell import ActCLIShell, NavigationTree, DetailView
from textual.app import ComposeResult

class MyApp(ActCLIShell):
    def get_brand_text(self) -> str:
        return "ActCLI • MyApp"

    def build_navigation_tree(self, tree: NavigationTree) -> None:
        tree.register_section(MySection())
        tree.register_action("action_id", self._handler)

    def compose_detail_view(self) -> ComposeResult:
        yield MyContentWidget()
```

Core Components
---------------
- **ActCLIShell**: Base app class with 3-panel layout
- **NavigationTree**: Self-contained navigation widget with section support
- **DetailView**: Status line + content area widget
- **Protocols**: NavigationProvider, DetailViewProvider, ControlPanelProvider

For detailed documentation, see: docs/shell-framework.md
"""

from .base_shell import ActCLIShell, DetailViewProvider, NavigationProvider
from .navigation_tree import NavigationTree, TreeSection, add_action_node, add_data_node
from .detail_view import DetailView

__all__ = [
    "ActCLIShell",
    "DetailViewProvider",
    "NavigationProvider",
    "NavigationTree",
    "TreeSection",
    "add_action_node",
    "add_data_node",
    "DetailView",
]
