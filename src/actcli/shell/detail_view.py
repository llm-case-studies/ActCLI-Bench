"""DetailView - Reusable detail panel widget with status line and content area.

This widget encapsulates the upper-right panel that displays:
- Status line (title/current view indicator)
- Main content area (terminals, logs, or other views)
"""

from typing import Optional
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static
from textual.widget import Widget


class DetailView(Vertical):
    """Smart detail panel that manages status line and content area.

    This widget provides:
    - A status line at the top showing current state/view
    - A flexible content area for main widgets
    - Methods to update status and swap content

    Usage:
        detail = DetailView(initial_status="Ready")
        detail.set_content(my_widget)
        detail.update_status("Terminal View")
    """

    def __init__(
        self,
        initial_status: str = "Ready",
        initial_content: Optional[Widget] = None,
        **kwargs
    ):
        """Initialize the detail view.

        Args:
            initial_status: Initial text for the status line
            initial_content: Optional widget to display in content area
            **kwargs: Additional Vertical widget arguments
        """
        # Set default ID if not provided
        if "id" not in kwargs:
            kwargs["id"] = "detail"

        super().__init__(**kwargs)

        self._initial_status = initial_status
        self._initial_content = initial_content

        # References to child widgets (set in compose)
        self.status_line: Optional[Static] = None

    def compose(self) -> ComposeResult:
        """Compose the detail view layout.

        Structure:
        - Status line (Static)
        - Content widgets (yielded directly, no wrapper)
        """
        # Status line at top
        self.status_line = Static(self._initial_status, id="title")
        yield self.status_line

        # Note: Content widgets will be yielded here via context manager in base_shell

    def update_status(self, text: str) -> None:
        """Update the status line text.

        Args:
            text: New status text to display
        """
        if self.status_line:
            self.status_line.update(text)

    async def set_content(self, widget: Widget, clear_existing: bool = True) -> None:
        """Set or add content to the detail view.

        Args:
            widget: Widget to display in the content area
            clear_existing: If True, remove existing content first
        """
        # Remove non-status children if clearing
        if clear_existing:
            for child in list(self.children):
                if child != self.status_line:
                    await child.remove()

        await self.mount(widget)

    async def clear_content(self) -> None:
        """Remove all non-status content from the detail view."""
        for child in list(self.children):
            if child != self.status_line:
                await child.remove()
