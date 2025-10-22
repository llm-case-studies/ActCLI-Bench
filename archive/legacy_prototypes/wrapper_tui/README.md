# actcli-shell - Multi-Terminal TUI

**Status:** ✅ Core implementation complete, ready for testing

## What It Does

A VSCode-style integrated terminal interface for AI communication with:
- Tab-based navigation between wrapped terminals
- Auto-created local facilitator and session
- Slash commands for control
- Progressive complexity (local → docker → remote)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Session: local_default    Facilitator: localhost:8765  │
├─────────────────────────────────────────────────────────┤
│ [Gemini] [Tree] [Calc] [+]  ← Tab navbar               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ [Active terminal output - PTY passthrough]             │
│ Gemini> What can I help you with?                      │
│                                                         │
│ You: <type here>                                        │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ actcli-wrap>>> /add bc                                  │
└─────────────────────────────────────────────────────────┘
```

## Usage

### Start the shell

```bash
actcli-shell
```

**On startup:**
1. Automatically starts local facilitator on port 8765
2. Creates default session
3. Shows empty navbar with control prompt

### Add terminals

```bash
actcli-wrap>>> /add gemini
actcli-wrap>>> /add tree
actcli-wrap>>> /add bc -l
actcli-wrap>>> /add ssh user@remote
```

Each command appears as a new tab in the navbar.

### Navigate tabs

- **Ctrl+N** - Next tab
- **Ctrl+P** - Previous tab
- **Ctrl+T** - Toggle between control mode and terminal mode

### Input Modes

**Control mode** (`actcli-wrap>>>`):
- Use slash commands (/add, /sessions, /connect, etc.)
- Configure and manage terminals

**Terminal mode** (`[terminal-name]>`):
- Send input directly to the active terminal
- Interact with wrapped applications (Gemini, cat, bc, etc.)

### Slash commands

```bash
/add <command>        # Add wrapped terminal
/sessions             # List available sessions
/connect <id>         # Join existing session
/help                 # Show help
/quit                 # Exit (or Ctrl+C)
```

### Example Workflow

```bash
# Start actcli-shell
actcli-shell

# Add a terminal (control mode)
actcli-wrap>>> /add gemini

# Switch to terminal mode
# Press Ctrl+T (prompt changes to [gemini]>)

# Now interact with Gemini
[gemini]> What is 2+2?

# Switch back to control mode
# Press Ctrl+T (prompt changes back to actcli-wrap>>>)

# Add another terminal
actcli-wrap>>> /add tree

# Navigate between tabs
# Press Ctrl+N to switch to tree tab
```

## Components

### SessionManager (`session_manager.py`)

Handles facilitator and session lifecycle:
- Auto-starts local facilitator if not running
- Creates default session on startup
- Manages connections to remote facilitators
- Lists available sessions

### TerminalManager & TerminalTab (`terminal_tab.py`)

Manages multiple wrapped terminals:
- PTY-based terminal wrapping
- Tab creation and lifecycle
- Output buffering and display
- Input forwarding

### Shell (`shell.py`)

Main TUI application using `prompt_toolkit`:
- Full-screen layout with navbar
- Command input with slash command handling
- Keyboard shortcuts
- Async event loop for responsiveness

## Use Cases

### 1. Local AI Development

```bash
actcli-shell
/add gemini
/add codex
# Both AIs in same session, can communicate
```

### 2. Mixed Tools

```bash
actcli-shell
/add gemini
/add tree
/add bc -l
# AI + regular tools all in same session
```

### 3. Docker Integration

```bash
actcli-shell
/add docker exec -it mycontainer bash
# Work in container, still connected to local session
```

### 4. Remote AI

```bash
actcli-shell
/add ssh user@msi "gemini"
# Remote Gemini joins local session
```

### 5. Multi-Machine Sessions

```bash
# On laptop:
actcli-shell
/add gemini
# Note session ID

# On MSI:
actcli-shell
/connect session_abc123
/add codex
# Now laptop Gemini ↔ MSI Codex
```

## Comparison with actcli-wrap

### actcli-wrap (v1 - explicit wrapper)

```bash
# Terminal 1
actcli-facilitator serve

# Terminal 2
actcli-wrap --create --name "User" "cat"

# Terminal 3
actcli-wrap --session session_xyz --name "AI" "gemini"
```

**Pros:**
- Simple, explicit control
- Good for testing/debugging
- Each terminal is independent

**Cons:**
- Manual session management
- Requires multiple terminal windows
- Not transparent to user

### actcli-shell (v2 - integrated TUI)

```bash
# Single command
actcli-shell

# Then:
/add cat
/add gemini
# Everything auto-connected
```

**Pros:**
- Zero-friction startup (auto facilitator + session)
- Tab-based UI (like VSCode terminals)
- Natural workflow
- Progressive complexity

**Cons:**
- More complex implementation
- Requires TUI library

## Technical Details

### PTY Wrapping

Each tab uses PTY (pseudo-terminal) to wrap commands:
- Transparent to wrapped process
- Full terminal emulation
- Colors, formatting preserved
- Process thinks it's in normal terminal

### Auto-Facilitator

On startup, `actcli-shell`:
1. Checks if facilitator already running (`GET /sessions`)
2. If not, spawns `actcli-facilitator serve` subprocess
3. Waits for it to be ready
4. Creates default session

### Async Architecture

Uses `asyncio` + `prompt_toolkit` for:
- Non-blocking terminal I/O
- Responsive UI updates
- Multiple concurrent terminals
- HTTP requests to facilitator

### Message Flow

```
User types in terminal → PTY input
                      ↓
                   Terminal wraps
                      ↓
                   Facilitator routes
                      ↓
                   Other terminals receive
                      ↓
                   PTY output → User sees
```

## Development

### Add new slash command

Edit `shell.py`:

```python
async def handle_command(self, command: str):
    # ...
    elif cmd == "mynewcmd":
        await self.cmd_mynewcmd(parts[1:])

async def cmd_mynewcmd(self, args):
    """Handle /mynewcmd"""
    # Implementation here
```

### Add keybinding

Edit `create_keybindings()`:

```python
@kb.add("c-x")
def _(event):
    """Custom action on Ctrl+X."""
    # Implementation here
```

### Modify layout

Edit `create_layout()` to change UI structure.

## Testing

### Basic test

```bash
actcli-shell

# Should see:
# - Starting local facilitator...
# - ✅ Facilitator started
# - ✅ Session created
# - Type /help for commands
```

### Add terminal test

```bash
/add echo
# Should see [echo] tab appear
# Type something, should echo back
```

### Multi-terminal test

```bash
/add cat
Ctrl+N  # Switch tabs
/add cat
# Type in one, should appear in other (via facilitator)
```

### AI test

```bash
/add gemini
# Should see Gemini startup
# Interact normally
```

## Roadmap

### Phase 1 (Current)
- ✅ Core TUI with tabs
- ✅ Auto facilitator + session
- ✅ Basic slash commands
- ✅ PTY wrapping

### Phase 2 (Next)
- [ ] Session persistence (save/load)
- [ ] Remote facilitator connection
- [ ] Session discovery (list remote sessions)
- [ ] Tab customization (rename, close)

### Phase 3 (Future)
- [ ] Split panes (vertical/horizontal)
- [ ] Broadcast viewer integration
- [ ] Recording/replay
- [ ] Configuration file support

## Known Issues

- Terminal output buffering needs optimization for large outputs
- Some CLI tools may not work properly in PTY (investigate)
- No session authentication yet
- Tab close functionality not exposed in UI

## Files

```
src/actcli/wrapper_tui/
├── __init__.py           # Package exports
├── shell.py              # Main TUI application
├── session_manager.py    # Facilitator + session management
├── terminal_tab.py       # PTY wrapper and tab management
└── README.md             # This file
```

## Dependencies

- `prompt_toolkit>=3.0.43` - TUI framework
- `httpx` - HTTP client for facilitator API
- `asyncio` - Async event loop

---

**Status:** Ready for testing and feedback!
**Date:** 2025-10-12
