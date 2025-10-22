"""NavigationTree - Self-contained navigation tree widget with section-based building.

This widget encapsulates both tree structure building and event handling,
keeping navigation logic separate from the main app.
"""

import traceback
from typing import Protocol, Callable, Dict, List, Any, Optional, runtime_checkable
from textual.widgets import Tree
from textual.widgets.tree import TreeNode


@runtime_checkable
class TreeSection(Protocol):
    """Protocol for tree section providers.

    Sections are responsible for building their portion of the navigation tree.
    They can be static (e.g., Settings) or dynamic (e.g., Terminals list).
    """

    label: str
    """Section label displayed in the tree."""

    auto_expand: bool
    """Whether to auto-expand this section on rebuild."""

    def build(self, parent: TreeNode) -> TreeNode:
        """Build this section's tree nodes under the parent.

        Args:
            parent: The parent node (typically tree.root)

        Returns:
            The section's root node (for further manipulation if needed)
        """
        ...


class NavigationTree(Tree):
    """Smart navigation tree that manages sections and handles events.

    This widget encapsulates:
    - Section-based tree building
    - Action handler registration and dispatch
    - Event handling (node selection)
    - Custom message emission for app-level events

    Apps register sections and action handlers, then the tree manages itself.
    """

    def __init__(self, label: str = "Navigation", **kwargs):
        """Initialize the navigation tree.

        Args:
            label: Root label for the tree
            **kwargs: Additional Tree widget arguments
        """
        super().__init__(label, **kwargs)

        # Registered sections (in order)
        self._sections: List[TreeSection] = []

        # Action handlers: action_id -> callable
        self._action_handlers: Dict[str, Callable[[], None]] = {}

        # Node selection handlers: node_type -> callable(node_data)
        self._node_handlers: Dict[str, Callable[[Dict[str, Any]], None]] = {}

        # Diagnostics: track rebuild events to detect duplicates
        self.rebuild_history: List[Dict[str, Any]] = []

    def register_section(self, section: TreeSection) -> None:
        """Register a tree section provider.

        Sections are built in the order they are registered.

        Args:
            section: The section provider to register
        """
        self._sections.append(section)

    def register_action(self, action_id: str, handler: Callable[[], None]) -> None:
        """Register an action handler for tree actions.

        When a node with type="action" and id={action_id} is selected,
        the handler will be called.

        Args:
            action_id: Unique action identifier (e.g., "mute_all")
            handler: Callable to invoke when action is selected
        """
        self._action_handlers[action_id] = handler

    def register_node_handler(self, node_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Register a handler for a specific node type.

        When a node with type={node_type} is selected, the handler
        will be called with the node's data dictionary.

        Args:
            node_type: Node type identifier (e.g., "terminal", "log")
            handler: Callable to invoke with node data
        """
        self._node_handlers[node_type] = handler

    def rebuild(self) -> None:
        """Rebuild the entire tree from registered sections.

        This clears all existing nodes and rebuilds from scratch.
        Call this when dynamic content changes (e.g., terminals added/removed).
        """
        # Track this rebuild for diagnostics (FAST - no traceback extraction)
        from datetime import datetime

        rebuild_event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "section_count": len(self._sections),
        }
        self.rebuild_history.append(rebuild_event)

        # Keep only last 20 rebuild events
        if len(self.rebuild_history) > 20:
            self.rebuild_history = self.rebuild_history[-20:]

        # Clear existing tree - use clear() instead of manual removal
        self.root.remove_children()

        # Build each section
        for section in self._sections:
            section_node = section.build(self.root)

            # Auto-expand if requested
            if section.auto_expand:
                try:
                    section_node.expand()
                except Exception:
                    pass

        # Always expand root
        try:
            self.root.expand()
        except Exception:
            pass

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:  # type: ignore[override]
        """Handle tree node selection.

        This method dispatches to registered handlers based on node type/action.
        Apps don't need to override this - they register handlers instead.

        Args:
            event: Tree node selected event
        """
        # Get node data (safely)
        data = getattr(event.node, "data", None) or {}
        node_type = data.get("type")

        if not node_type:
            return

        # Handle actions
        if node_type == "action":
            action_id = data.get("id")
            handler = self._action_handlers.get(action_id)
            if handler:
                handler()
                return

        # Handle other node types
        handler = self._node_handlers.get(node_type)
        if handler:
            handler(data)


# Utility functions for common tree patterns

def add_action_node(parent: TreeNode, label: str, action_id: str) -> TreeNode:
    """Add an action node to the tree.

    Args:
        parent: Parent node
        label: Node label text
        action_id: Action identifier for handler dispatch

    Returns:
        The created node
    """
    node = parent.add(label)
    node.data = {"type": "action", "id": action_id}
    return node


def add_data_node(parent: TreeNode, label: str, node_type: str, **data) -> TreeNode:
    """Add a node with custom type and data.

    Args:
        parent: Parent node
        label: Node label text
        node_type: Node type for handler dispatch
        **data: Additional data to attach to the node

    Returns:
        The created node
    """
    node = parent.add(label)
    node.data = {"type": node_type, **data}
    return node
