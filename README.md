# ActCLI-Bench

> Multi-AI terminal wrapper and bench environment with a modern TUI framework

ActCLI-Bench is a complete system for running and coordinating multiple AI CLI tools (Claude, Gemini, etc.) through a unified interface. It includes a terminal wrapper, facilitator service, and a modern Textual-based bench UI with a reusable shell framework.

## Features

🚀 **Multi-AI Coordination**
- Wrap AI CLI tools (Claude, Gemini, etc.) and connect them through a facilitator
- Real-time message routing and broadcast streaming
- Session management with viewer URL

🎨 **Modern TUI Interface**
- Built with [Textual](https://textual.textualize.io/) for rich terminal UI
- Three built-in themes (Ledger, Analyst, Seminar) with F1/F2/F3 switching
- Terminal emulation with VT100 support via `pyte`
- Navigation tree, status line, and control panel

🧩 **Reusable Shell Framework**
- Protocol-based architecture for easy customization
- Pre-built widgets (NavigationTree, DetailView)
- Section-based navigation system
- Comprehensive documentation for building your own apps

📊 **Observability & Debugging**
- Comprehensive logging (Events, Errors, Debug, Output)
- Troubleshooting snapshot export with timestamps
- Terminal state tracking and diagnostics
- Version info display in status line

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/llm-case-studies/ActCLI-Bench.git
cd ActCLI-Bench

# Install with pip (editable mode)
pip install -e ".[textual]"
```

### Running the Bench

```bash
# Start the bench UI
actcli-bench

# The bench will auto-start the facilitator and create a session
# Add terminals using the navigation tree: Terminals → + Add...
```

### Key Bindings

- **F1/F2/F3**: Switch themes
- **Q**: Quit
- Navigate with arrow keys or mouse
- Type in the terminal view when focused
- Use the broadcast input to send to all unmuted terminals

## Project Structure

```
ActCLI-Bench/
├── src/actcli/
│   ├── bench_textual/       # Textual-based bench UI
│   │   ├── app.py           # Main BenchTextualApp
│   │   ├── term_view.py     # Terminal view widget
│   │   ├── term_emulator.py # VT100 emulation (pyte)
│   │   ├── terminal_runner.py # PTY management
│   │   ├── terminal_manager.py # Terminal state management
│   │   ├── diagnostics.py   # Troubleshooting snapshots
│   │   └── tree_sections.py # Navigation tree sections
│   │
│   ├── shell/               # Reusable TUI shell framework ⭐
│   │   ├── base_shell.py    # ActCLIShell base class
│   │   ├── navigation_tree.py # NavigationTree widget
│   │   ├── detail_view.py   # DetailView widget
│   │   ├── themes.tcss      # CSS themes
│   │   └── README.md        # Framework quick reference
│   │
│   ├── facilitator/         # FastAPI facilitator service
│   │   ├── main.py          # FastAPI app
│   │   ├── models.py        # Data models
│   │   └── session.py       # Session management
│   │
│   └── wrapper/             # CLI wrapper and client
│       ├── wrap_cli.py      # actcli-wrap command
│       ├── client.py        # Facilitator client
│       └── pty_wrapper.py   # PTY wrapper
│
├── docs/
│   ├── shell-framework.md   # Complete shell framework guide ⭐
│   ├── WRAPPER_*.md         # Wrapper documentation
│   └── archive/             # Outdated documentation
│
└── tests/
    ├── integration/         # Integration tests
    └── unit/                # Unit tests
```

## Architecture

### System Overview

```
┌──────────────────────────────────────────────────────┐
│ ActCLI Bench (Textual UI)                            │
│ ┌────────────┬───────────────────────────────────┐   │
│ │ Sidebar    │ Detail View                       │   │
│ │            │ ┌───────────────────────────────┐ │   │
│ │ Navigation │ │ Status: Session | Viewer      │ │   │
│ │ Tree       │ ├───────────────────────────────┤ │   │
│ │            │ │                               │ │   │
│ │ Terminals  │ │ Terminal View (VT100)         │ │   │
│ │ Sessions   │ │ ├─ Emulated PTY output        │ │   │
│ │ Settings   │ │ └─ Scrollback support         │ │   │
│ │ Logs       │ │                               │ │   │
│ │            │ └───────────────────────────────┘ │   │
│ │            │ ┌───────────────────────────────┐ │   │
│ │            │ │ Control: Broadcast input      │ │   │
│ └────────────┴─┴───────────────────────────────┴───┘ │
└──────────────────────────────────────────────────────┘
                       ↕ WebSocket
┌──────────────────────────────────────────────────────┐
│ Facilitator Service (FastAPI)                        │
│ - Session management                                 │
│ - Message routing & broadcast                        │
│ - WebSocket connections                              │
└──────────────────────────────────────────────────────┘
                       ↕ WebSocket
┌──────────────────────────────────────────────────────┐
│ Wrapped AI CLIs                                      │
│ - claude (via actcli-wrap)                           │
│ - gemini (via actcli-wrap)                           │
│ - Any terminal command                               │
└──────────────────────────────────────────────────────┘
```

### Shell Framework Architecture

The bench is built on a reusable shell framework that you can use to build your own TUI apps. See **[docs/shell-framework.md](docs/shell-framework.md)** for complete documentation.

```
ActCLIShell (base class)
├── NavigationTree (widget)
│   ├── Section-based architecture
│   ├── Action handlers
│   └── Auto-rebuild
│
├── DetailView (widget)
│   ├── Status line (docked top)
│   └── Content area (flexible)
│
└── Control Panel (optional)
    └── App-specific controls
```

## Future: Round Table Integration

ActCLI-Bench is designed to serve as the backend for **ActCLI Round Table** - a public AI debate platform where multiple AI agents discuss viewer-submitted topics in scheduled sessions.

**Status:** 🚧 Planning phase

**What Round Table Needs:**
- REST API for session management
- Live transcript streaming (WebSocket/SSE)
- Configurable debate formats (YAML configs)
- Structured artifact export (JSON, MD, PDF)
- Multi-AI orchestration with turn management

**Documentation:**
- [Round Table Integration Spec](docs/round-table-integration.md) - Implementation roadmap
- [OpenAPI Specification](docs/api/round-table-openapi.yaml) - API contract
- [Round Table Vision](../ActCLI-Round-Table/README.md) - Full project overview

See `docs/round-table-integration.md` for details on the planned integration.

## Components

### 1. Bench UI (`actcli-bench`)

Modern Textual-based interface for managing multiple terminals.

**Features:**
- Terminal emulation with VT100 escape sequences
- Navigation tree with sections (Terminals, Sessions, Settings, Logs)
- Status line showing session, viewer URL, and version info
- Broadcast input to send commands to all unmuted terminals
- Troubleshooting snapshot export
- Theme switching (F1/F2/F3)

### 2. Facilitator Service (`actcli-facilitator`)

FastAPI service that routes messages between wrapped terminals.

**Features:**
- Session management
- WebSocket message routing
- Broadcast streaming
- RESTful API for session operations

```bash
# Start the facilitator
actcli-facilitator --port 8765
```

### 3. CLI Wrapper (`actcli-wrap`)

Wraps any CLI tool and connects it to the facilitator.

```bash
# Wrap Claude CLI
actcli-wrap --session SESSION_ID --name claude -- claude chat

# Wrap Gemini
actcli-wrap --session SESSION_ID --name gemini -- gemini chat
```

### 4. Shell Framework

Reusable TUI framework for building Textual apps. Complete docs at **[docs/shell-framework.md](docs/shell-framework.md)**.

```python
from actcli.shell import ActCLIShell, NavigationTree
from textual.app import ComposeResult

class MyApp(ActCLIShell):
    def get_brand_text(self) -> str:
        return "ActCLI • MyApp"

    def build_navigation_tree(self, tree: NavigationTree) -> None:
        tree.register_section(MySection())
        tree.register_action("my_action", self._handler)

    def compose_detail_view(self) -> ComposeResult:
        yield MyContentWidget()
```

## Development

### Setup

```bash
# Install in development mode with all extras
pip install -e ".[textual,tui,dev]"

# Run tests
pytest

# Run specific test
pytest tests/integration/test_websocket_routing.py
```

### Running Components Separately

```bash
# Start facilitator manually
python -m actcli.facilitator.main

# Start bench (auto-starts facilitator)
python -m actcli.bench_textual.app

# Wrap a terminal
python -m actcli.wrapper.wrap_cli --session <SESSION> --name test -- bash
```

## Configuration

The bench can be configured via environment variables or command-line options:

```bash
# Facilitator URL (default: http://localhost:8765)
export ACTCLI_FACILITATOR_URL=http://localhost:8765

# Default theme (ledger, analyst, seminar)
# Change with F1/F2/F3 during runtime
```

## Troubleshooting

### Export Diagnostic Snapshot

In the bench UI:
1. Navigate to Settings → Troubleshooting Pack
2. Select "Export troubleshooting pack"
3. File saved to `docs/Trouble-Snaps/troubleshooting_pack_<timestamp>.txt`

### Investigations & Postmortems

- [Cursor & PTY improvements (Oct 2025)](docs/POSTMORTEM_CURSOR_PTY.md)


The snapshot includes:
- Version information
- Active terminals and their state
- Recent logs (events, errors, debug)
- Window size history
- Navigation tree rebuild history (if multiple rebuilds detected)

### Common Issues

**Terminal not displaying correctly:**
- Check the troubleshooting snapshot for window size mismatches
- Verify `pyte` is installed for VT100 emulation
- Check recent errors in the Logs view

**Facilitator connection failed:**
- Ensure facilitator is running: `actcli-facilitator`
- Check the facilitator URL in the bench status line
- See bench logs for connection errors

**Input not working in terminal:**
- Click the terminal view to focus it
- Check the border color (cyan = focused)
- View debug logs for key event capture

## Documentation

- **[Shell Framework Guide](docs/shell-framework.md)** - Complete guide to using the shell framework
- **[Shell Framework Quick Reference](src/actcli/shell/README.md)** - Quick start and API overview
- **[Wrapper README](docs/WRAPPER_README.md)** - CLI wrapper system documentation
- **[Wrapper Testing Guide](docs/WRAPPER_TESTING_GUIDE.md)** - Testing the wrapper system
- **[ActCLI-TE Tracking](docs/ACTCLI-TE_TRACKING.md)** - Cross-project coordination
- **[Instrumentation Refactor Plan](docs/INSTRUMENTATION_REFACTOR.md)** - Upcoming logging/tooling changes

## Version History

### Current (0.0.3)
- ✅ Extracted DetailView as reusable widget
- ✅ Fixed duplicate navigation tree bug
- ✅ Enhanced troubleshooting snapshots with rebuild tracking
- ✅ Comprehensive shell framework documentation
- ✅ Terminal view fills available space correctly
- ✅ Status line shows full information (session, viewer, versions)

### Previous (0.0.2)
- Terminal width fixes and resize handling
- Observability improvements (version display, troubleshooting pack)
- Emulator mode detection and logging
- Border highlight on startup

## Contributing

This is part of the ActCLI suite. For issues or contributions, please use the GitHub issue tracker.

## License

See LICENSE file for details.

## Links

- **Repository**: https://github.com/llm-case-studies/ActCLI-Bench
- **Shell Framework Docs**: [docs/shell-framework.md](docs/shell-framework.md)
- **Issues**: https://github.com/llm-case-studies/ActCLI-Bench/issues
