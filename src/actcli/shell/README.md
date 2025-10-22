# ActCLI Shell Framework

A reusable TUI framework for building terminal applications with [Textual](https://textual.textualize.io/).

## Features

- 🎨 **Three built-in themes** (Ledger, Analyst, Seminar)
- 🧩 **Modular widget system** (NavigationTree, DetailView)
- 🔌 **Protocol-based architecture** for easy customization
- 📐 **Pre-configured 3-panel layout** (sidebar, detail, control)
- 🎯 **Section-based navigation** with auto-rebuild
- 🔄 **Dynamic content management** with DetailView

## Quick Start

```python
from actcli.shell import ActCLIShell, NavigationTree
from textual.app import ComposeResult
from textual.widgets import Static

class MyApp(ActCLIShell):
    def get_brand_text(self) -> str:
        return "ActCLI • MyApp"

    def build_navigation_tree(self, tree: NavigationTree) -> None:
        # Your navigation structure here
        pass

    def compose_detail_view(self) -> ComposeResult:
        yield Static("Hello, ActCLI!")

if __name__ == "__main__":
    MyApp().run()
```

## Documentation

See **[docs/shell-framework.md](../../../docs/shell-framework.md)** for complete documentation including:

- Architecture overview
- Widget API reference
- Protocol implementations
- Theming guide
- Full examples
- Best practices

## Widgets

### NavigationTree
Self-contained navigation widget with section-based building.

```python
tree.register_section(MySection())
tree.register_action("action_id", handler)
tree.rebuild()  # Rebuild when data changes
```

### DetailView
Status line + content area widget.

```python
detail_view.update_status("Status text")
await detail_view.set_content(widget)
```

## Layout Structure

```
┌──────────────────────────────────────┐
│ Header                               │
├──────────┬───────────────────────────┤
│ Sidebar  │ DetailView                │
│  Brand   │  ├─ Status line           │
│  NavTree │  ├─ Content area          │
│  Hints   │  └─ (your widgets)        │
│          ├───────────────────────────┤
│          │ Control Panel (optional)  │
└──────────┴───────────────────────────┘
```

## Example Implementation

See `src/actcli/bench_textual/app.py` for a complete real-world example.

## License

Part of the ActCLI-Bench project.
