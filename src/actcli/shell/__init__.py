"""ActCLI Shell - Reusable TUI shell framework.

This module provides the base shell infrastructure for ActCLI products.
"""

from .base_shell import ActCLIShell, DetailViewProvider, NavigationProvider

__all__ = ["ActCLIShell", "DetailViewProvider", "NavigationProvider"]
