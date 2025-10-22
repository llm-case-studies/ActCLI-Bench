"""Tree sections for Bench navigation.

These sections implement the TreeSection protocol to build
specific parts of the Bench navigation tree.
"""

from typing import Optional, Callable
from textual.widgets.tree import TreeNode
from .terminal_manager import TerminalManager
from ..shell.navigation_tree import add_action_node, add_data_node


class TerminalsSection:
    """Terminals section - shows active terminals with mute status.

    This is a dynamic section that rebuilds when terminals are added/removed.
    """

    label = "Terminals"
    auto_expand = True

    def __init__(self, terminal_manager: TerminalManager):
        """Initialize terminals section.

        Args:
            terminal_manager: Terminal manager to query for terminal list
        """
        self.terminal_manager = terminal_manager

    def build(self, parent: TreeNode) -> TreeNode:
        """Build the terminals section.

        Creates:
        - Terminals (root)
          - + Add… (action)
          - Terminal1 [M/U] (selectable)
          - Terminal2 [M/U] (selectable)
          ...

        Args:
            parent: Parent node (tree root)

        Returns:
            The Terminals section root node
        """
        section_node = parent.add(self.label)

        # Add "+" action node
        add_node = section_node.add("+ Add…")
        add_node.data = {"type": "add_terminal"}

        # Add each terminal with mute indicator
        for name in self.terminal_manager.list_terminals():
            state = self.terminal_manager.get_terminal_state(name)
            if state:
                mark = "[M]" if state.item.muted else "[U]"
                node = section_node.add(f"{name} {mark}")
                node.data = {"type": "terminal", "name": name}

        return section_node


class SessionsSection:
    """Sessions section - session info and connection.

    This is a mostly static section with session management.
    """

    label = "Sessions"
    auto_expand = True

    def build(self, parent: TreeNode) -> TreeNode:
        """Build the sessions section.

        Creates:
        - Sessions (root)
          - Current session (info)
          - Connect… (action)

        Args:
            parent: Parent node (tree root)

        Returns:
            The Sessions section root node
        """
        section_node = parent.add(self.label)

        # Current session info
        cur = section_node.add("Current session")
        cur.data = {"type": "session_info"}

        # Connect action
        connect = section_node.add("Connect…")
        connect.data = {"type": "connect"}

        return section_node


class SettingsSection:
    """Settings section - actions and toggles.

    This section provides various app-level actions.
    """

    label = "Settings"
    auto_expand = True

    def __init__(self, get_mirror_state: Optional[Callable[[], bool]] = None):
        """Initialize settings section.

        Args:
            get_mirror_state: Optional callable to get current mirror checkbox state
        """
        self.get_mirror_state = get_mirror_state

    def build(self, parent: TreeNode) -> TreeNode:
        """Build the settings section.

        Creates:
        - Settings (root)
          - Mute All (action)
          - Unmute All (action)
          - Mirror to viewer [X/  ] (action)
          - Export troubleshooting pack (action)

        Args:
            parent: Parent node (tree root)

        Returns:
            The Settings section root node
        """
        section_node = parent.add(self.label)

        # Mute/Unmute actions
        add_action_node(section_node, "Mute All", "mute_all")
        add_action_node(section_node, "Unmute All", "unmute_all")

        # Mirror toggle with current state
        mirror_checked = False
        if self.get_mirror_state:
            try:
                mirror_checked = self.get_mirror_state()
            except Exception:
                pass

        mirror_label = f"Mirror to viewer {'[X]' if mirror_checked else '[ ]'}"
        add_action_node(section_node, mirror_label, "toggle_mirror")

        # Export troubleshooting pack
        add_action_node(section_node, "Export troubleshooting pack", "export_troubleshooting")

        return section_node


class LogsSection:
    """Logs section - log categories and troubleshooting.

    This is a static section with log view navigation.
    """

    label = "Logs"
    auto_expand = True

    def build(self, parent: TreeNode) -> TreeNode:
        """Build the logs section.

        Creates:
        - Logs (root)
          - Events (log view)
          - Errors (log view)
          - Output (log view)
          - Debug (log view)
          - Troubleshooting Pack (submenu)
            - Save to file (action)

        Args:
            parent: Parent node (tree root)

        Returns:
            The Logs section root node
        """
        section_node = parent.add(self.label)

        # Log category views
        for cat in ("Events", "Errors", "Output", "Debug"):
            n = section_node.add(cat)
            n.data = {"type": "log", "cat": cat.lower()}

        # Troubleshooting pack submenu
        tpack = section_node.add("Troubleshooting Pack")
        tpack.data = {"type": "log", "cat": "troubleshooting"}

        tpack_save = tpack.add("Save to file")
        tpack_save.data = {"type": "action", "id": "export_troubleshooting"}

        # Expand troubleshooting pack submenu
        try:
            tpack.expand()
        except Exception:
            pass

        return section_node
