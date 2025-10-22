# ActCLI Shell Framework

The ActCLI Shell provides a reusable TUI (Text User Interface) framework for building terminal-based applications with Textual. It includes pre-built, customizable widgets and a flexible architecture based on protocols.

## Quick Start

```python
from actcli.shell import ActCLIShell, NavigationTree, DetailView
from textual.app import ComposeResult

class MyApp(ActCLIShell):
    """Your custom ActCLI application."""

    def get_brand_text(self) -> str:
        return "ActCLI • MyApp"

    def build_navigation_tree(self, tree: NavigationTree) -> None:
        # Register sections and handlers
        tree.register_section(MySection())
        tree.register_action("my_action", self._handle_my_action)

    def compose_detail_view(self) -> ComposeResult:
        # Yield your main content widgets
        yield MyContentWidget()
```

## Architecture Overview

The shell framework uses a **protocol-based architecture** that allows you to customize different parts of the UI by implementing specific protocols:

- **NavigationProvider**: Build the navigation tree structure
- **DetailViewProvider**: Provide the main content area widgets
- **ControlPanelProvider**: Add control panel widgets at the bottom

### Layout Structure

```
┌─────────────────────────────────────────────────────┐
│ Header (provided by base shell)                    │
├──────────────┬──────────────────────────────────────┤
│  Sidebar     │  Detail Panel (DetailView)          │
│              │  ┌────────────────────────────────┐  │
│  • Brand     │  │ Status Line (auto)             │  │
│  • NavTree   │  ├────────────────────────────────┤  │
│  • Hints     │  │                                │  │
│              │  │ Content Area                   │  │
│              │  │ (from DetailViewProvider)      │  │
│              │  │                                │  │
│              │  └────────────────────────────────┘  │
│              │  ┌────────────────────────────────┐  │
│              │  │ Control Panel                  │  │
│              │  │ (from ControlPanelProvider)    │  │
│              │  └────────────────────────────────┘  │
└──────────────┴──────────────────────────────────────┘
```

## Core Widgets

### 1. NavigationTree

A self-contained navigation tree widget with section-based building and event handling.

#### Features
- Section-based architecture (register sections that build themselves)
- Action handler registration and dispatch
- Node type handlers for custom interactions
- Automatic tree rebuilding

#### Example Usage

```python
from actcli.shell import NavigationTree, TreeSection, add_action_node, add_data_node
from textual.widgets.tree import TreeNode

class MySection:
    """Example tree section."""
    label = "My Section"
    auto_expand = True

    def build(self, parent: TreeNode) -> TreeNode:
        section = parent.add(self.label)

        # Add action nodes (clickable items that trigger handlers)
        add_action_node(section, "Do Something", "my_action")

        # Add data nodes (items with custom data)
        add_data_node(section, "Item 1", "item", item_id="item1")

        return section

# In your app's build_navigation_tree():
tree.register_section(MySection())
tree.register_action("my_action", self._handle_my_action)
tree.register_node_handler("item", self._handle_item_selected)
```

#### Section Protocol

```python
from typing import Protocol
from textual.widgets.tree import TreeNode

class TreeSection(Protocol):
    label: str              # Section label
    auto_expand: bool       # Auto-expand on rebuild

    def build(self, parent: TreeNode) -> TreeNode:
        """Build this section's tree nodes."""
        ...
```

#### Helper Functions

```python
# Add an action node (triggers registered handler)
add_action_node(parent, "Label", "action_id")

# Add a data node (passes data to handler)
add_data_node(parent, "Label", "node_type", custom_key="value")
```

#### Registering Handlers

```python
# Action handlers (no parameters)
tree.register_action("mute_all", self._mute_all_terminals)

# Node type handlers (receives node data dict)
tree.register_node_handler("terminal", self._handle_terminal_click)

def _handle_terminal_click(self, data: Dict[str, Any]) -> None:
    terminal_name = data.get("name")
    # Do something with the terminal
```

#### Rebuilding the Tree

```python
# Call this when your data changes
tree.rebuild()  # Clears and rebuilds from registered sections
```

### 2. DetailView

A reusable detail panel widget that manages a status line and content area.

#### Features
- Status line at the top (auto-docked)
- Flexible content area (fill remaining space)
- Methods to update status and swap content

#### Example Usage

```python
from actcli.shell import DetailView
from textual.widgets import Static

# Create detail view
detail_view = DetailView(initial_status="Ready")

# Update status
detail_view.update_status("Processing...")

# Add/replace content (async)
await detail_view.set_content(my_widget)

# Clear all content except status
await detail_view.clear_content()
```

#### API Reference

```python
class DetailView(Vertical):
    def __init__(self, initial_status: str = "Ready", **kwargs):
        """Initialize with a status line message."""

    def update_status(self, text: str) -> None:
        """Update the status line text."""

    async def set_content(self, widget: Widget, clear_existing: bool = True) -> None:
        """Add widget to content area. Clears existing if clear_existing=True."""

    async def clear_content(self) -> None:
        """Remove all content widgets (keeps status line)."""

    # Access the status line widget directly if needed
    status_line: Optional[Static]
```

## Implementing the Protocols

### NavigationProvider

Implement this to customize the navigation tree.

```python
from actcli.shell import ActCLIShell, NavigationTree

class MyApp(ActCLIShell):
    def build_navigation_tree(self, tree: NavigationTree) -> None:
        """Configure navigation tree sections and handlers.

        This is called once during on_mount(). The tree will be
        automatically built after this method returns.
        """
        # Register sections (in display order)
        tree.register_section(MainSection())
        tree.register_section(SettingsSection())

        # Register action handlers
        tree.register_action("refresh", self._refresh)
        tree.register_action("export", self._export_data)

        # Register node type handlers
        tree.register_node_handler("item", self._handle_item)
```

### DetailViewProvider

Implement this to provide the main content widgets.

```python
from actcli.shell import ActCLIShell
from textual.app import ComposeResult

class MyApp(ActCLIShell):
    def compose_detail_view(self) -> ComposeResult:
        """Compose the main content widgets.

        Widgets yielded here will appear in the detail panel
        below the status line.
        """
        self.my_view = MyCustomView()
        yield self.my_view
```

### ControlPanelProvider

Implement this to add a control panel at the bottom.

```python
from actcli.shell import ActCLIShell
from textual.app import ComposeResult
from textual.widgets import Input, Button

class MyApp(ActCLIShell):
    def compose_control_panel(self) -> ComposeResult:
        """Compose control panel widgets.

        Widgets yielded here appear in a horizontal container
        at the bottom of the right panel.
        """
        self.search_input = Input(placeholder="Search...")
        yield self.search_input

        yield Button("Submit", id="submit-btn")
```

## Theming

The shell includes three built-in themes that can be switched with F1/F2/F3:

- **F1**: Ledger theme (blue tones)
- **F2**: Analyst theme (teal/cyan tones)
- **F3**: Seminar theme (slate/brown tones)

### Theme Colors

Each theme defines colors for:
- Screen background
- Header/Footer
- Sidebar background
- Detail panel background
- Brand text
- Status line (title)
- Hints text

### Custom Themes

Override the theme classes in your app:

```python
class MyApp(ActCLIShell):
    THEMES = ["ledger", "analyst", "seminar", "custom"]
    DEFAULT_THEME = "custom"
```

Then add theme CSS in your CSS file:

```css
.theme-custom Screen { background: #1a1a2e; }
.theme-custom #header { background: #16213e; }
.theme-custom #sidebar { background: #0f3460; }
.theme-custom #detail { background: #1a1a2e; }
.theme-custom #brand { color: #e94560; }
.theme-custom #title { color: #e94560; }
```

### Custom CSS

Specify additional CSS for your app:

```python
class MyApp(ActCLIShell):
    CSS_PATH = "path/to/your/custom.tcss"  # Relative to your module
```

## Customization Methods

Override these methods to customize the base shell:

```python
class MyApp(ActCLIShell):
    def get_brand_text(self) -> str:
        """Return brand text shown in sidebar."""
        return "ActCLI • MyProduct"

    def get_theme_hints(self) -> str:
        """Return theme hint text shown in sidebar."""
        return "F1: Ledger • F2: Analyst • F3: Seminar"

    def get_initial_status(self) -> str:
        """Return initial status line text."""
        return "Ready"

    def update_status(self, text: str) -> None:
        """Update the status line (already implemented)."""
        # Use this method to update status from anywhere in your app
        pass
```

## Full Example

Here's a complete minimal app using the shell framework:

```python
from actcli.shell import (
    ActCLIShell,
    NavigationTree,
    TreeSection,
    add_action_node,
)
from textual.app import ComposeResult
from textual.widgets import Static, Input, Button
from textual.widgets.tree import TreeNode


class MainSection:
    label = "Main"
    auto_expand = True

    def build(self, parent: TreeNode) -> TreeNode:
        section = parent.add(self.label)
        add_action_node(section, "Refresh", "refresh")
        add_action_node(section, "Export", "export")
        return section


class MyApp(ActCLIShell):
    """Example ActCLI application."""

    def get_brand_text(self) -> str:
        return "ActCLI • Example"

    def build_navigation_tree(self, tree: NavigationTree) -> None:
        tree.register_section(MainSection())
        tree.register_action("refresh", self._handle_refresh)
        tree.register_action("export", self._handle_export)

    def compose_detail_view(self) -> ComposeResult:
        yield Static("Main content goes here", id="content")

    def compose_control_panel(self) -> ComposeResult:
        yield Input(placeholder="Enter command...")
        yield Button("Execute")

    def _handle_refresh(self) -> None:
        self.update_status("Refreshing...")
        # Do refresh logic
        self.update_status("Ready")

    def _handle_export(self) -> None:
        self.update_status("Exporting...")
        # Do export logic
        self.update_status("Ready")


if __name__ == "__main__":
    app = MyApp()
    app.run()
```

## Best Practices

1. **Keep sections focused**: Each TreeSection should handle one logical group
2. **Use descriptive action IDs**: Make handler registration clear
3. **Rebuild sparingly**: Only call `tree.rebuild()` when data actually changes
4. **Update status frequently**: Keep users informed of app state
5. **Use protocols**: Implement only the protocols you need
6. **Leverage DetailView**: Use its API rather than accessing internals

## Advanced Topics

### Dynamic Sections

Create sections that rebuild based on runtime data:

```python
class DynamicSection:
    def __init__(self, data_source):
        self.data_source = data_source
        self.label = "Dynamic Items"
        self.auto_expand = True

    def build(self, parent: TreeNode) -> TreeNode:
        section = parent.add(self.label)
        for item in self.data_source.get_items():
            add_data_node(section, item.name, "item", item_id=item.id)
        return section
```

### Async Handlers

Action handlers can be async:

```python
async def _handle_async_action(self) -> None:
    self.update_status("Loading...")
    data = await self.fetch_data()
    self.update_status(f"Loaded {len(data)} items")
```

### Custom Status Updates

Access the status line directly for formatting:

```python
from rich.text import Text

status_text = Text()
status_text.append("Status: ", style="bold")
status_text.append("Running", style="green")
self.detail_view.status_line.update(status_text)
```

## API Reference

See the inline documentation in:
- `src/actcli/shell/base_shell.py` - Main shell class and protocols
- `src/actcli/shell/navigation_tree.py` - NavigationTree widget
- `src/actcli/shell/detail_view.py` - DetailView widget

## Examples

See the BenchTextualApp implementation in `src/actcli/bench_textual/app.py` for a real-world example of using all the shell framework features.
