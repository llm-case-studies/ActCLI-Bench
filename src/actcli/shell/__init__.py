"""ActCLI Shell - Reusable TUI shell framework.

This module provides the base shell infrastructure for ActCLI products.
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
