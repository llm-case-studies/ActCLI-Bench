# actcli-shell Status Report

**Date:** 2025-01-13
**Status:** 🟢 Core functionality working, ready for multi-AI testing

## What We Built

`actcli-shell` is a VSCode-style integrated terminal interface for multi-AI communication. It combines:
- Tab-based navigation between wrapped terminals
- Auto-created local facilitator and session
- Real-time message routing through WebSocket
- Live viewer for watching conversations

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ actcli-shell (PromptSession-based TUI)                      │
├─────────────────────────────────────────────────────────────┤
│ • SessionManager - Auto-starts facilitator, manages session │
│ • TerminalManager - Tab navigation (Ctrl+N/P)               │
│ • WrappedTerminal - Connects each CLI to facilitator        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ FacilitatorClient + PTYWrapper                              │
├─────────────────────────────────────────────────────────────┤
│ • Joins session as participant                              │
│ • Wraps CLI with PTY (stdin/stdout interception)            │
│ • Routes input → facilitator → other participants           │
│ • Receives messages from facilitator → injects into CLI     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Facilitator Service (FastAPI + WebSocket)                   │
├─────────────────────────────────────────────────────────────┤
│ • Session management                                        │
│ • Participant tracking                                      │
│ • Message routing (broadcast to all)                        │
│ • Live viewer endpoint                                      │
└─────────────────────────────────────────────────────────────┘
```

## Key Files

### New Files Created
- `src/actcli/wrapper_tui/shell.py` - Main TUI application
- `src/actcli/wrapper_tui/session_manager.py` - Facilitator + session lifecycle
- `src/actcli/wrapper_tui/terminal_tab.py` - Tab management and PTY basics
- `src/actcli/wrapper_tui/wrapped_terminal.py` - Facilitator-connected terminals
- `src/actcli/wrapper_tui/README.md` - Comprehensive documentation
- `src/actcli/wrapper_tui/STATUS.md` - This file

### Modified Files
- `src/actcli/wrapper/pty_wrapper.py` - Added ANSI stripping, mouse event filtering
- `pyproject.toml` - Added `actcli-shell` command

## What Works ✅

1. **Auto-Setup** - Single command `actcli-shell` starts facilitator and session
2. **Tab Navigation** - Ctrl+N/P switches between terminals, clear visual feedback
3. **Terminal Addition** - `/add claude`, `/add gemini`, etc. connects to facilitator
4. **Message Routing** - Input from one terminal reaches other terminals
5. **Live Viewer** - Web UI shows messages in real-time at `/viewer/{session_id}`
6. **Session Display** - Status bar shows session ID and clickable viewer URL
7. **ANSI Stripping** - Removes escape codes before sending to facilitator
8. **Basic Cleanup** - Terminals properly closed on exit

## Fixed Issues ✅

### Critical: Mouse Events Leaking Through - FIXED!

**Problem:** When mouse was moved in actcli-shell, mouse tracking events were captured and sent to other AIs as garbage messages.

**What we saw in viewer:**
```
claude at 5:09:34 AM
M<35;27;8M<35;25;9M<35;24;9M<35;23;9M<35;21;9M...
```

**Root Cause:**
- `PromptSession` had `mouse_support=True` which enabled terminal mouse tracking
- PTY wrapper captured ALL output including mouse events
- Events were forwarded to facilitator → other participants

**Solution:**
- Set `mouse_support=False` in PromptSession (shell.py:362)
- This disables mouse tracking at the SOURCE
- Trade-off: No mouse click support in TUI, but clean message routing

**Status:** 🟢 FIXED - No more mouse event spam

### Minor Issues

1. **Input split across areas** - Sometimes "Hello" splits: "Hell" goes to control, "o" to terminal
2. **No multi-line input** - Can't compose longer messages
3. **No input history per terminal** - Only global command history
4. **Tab close not exposed** - Can add tabs but not remove them via UI

## Next Steps

### Immediate Priority: Multi-AI Testing

Now that mouse events are fixed, we need to test:
1. Multiple AIs chatting together (claude + gemini + codex)
2. Multi-turn conversations
3. AI-to-AI questions and responses
4. Session persistence across tab switches

### Future Enhancements
- Session persistence (save/load)
- Remote facilitator connection
- Tab close via UI
- Split panes (vertical/horizontal)
- Recording/replay
- Configuration file support

## Testing Scenarios

### Scenario 1: Basic Chat (Partially Working)
```bash
actcli-shell
/add claude
/add gemini

# In shell: type "Hello!"
# Expected: Gemini sees "Hello!" from claude
# Actual: Gemini sees "Hello!" + mouse events + UI noise
```

### Scenario 2: Multi-Turn Conversation (Not Yet Tested)
```bash
actcli-shell
/add claude
/add gemini

# Claude asks a question
# Gemini responds
# Claude follows up
# Expected: Clean back-and-forth conversation
```

### Scenario 3: Multiple AIs (Not Yet Tested)
```bash
actcli-shell
/add claude
/add gemini
/add codex

# All three should see each other's messages
```

## Dependencies Added
- `prompt_toolkit>=3.0.43` - TUI framework
- (Reused existing) `httpx` - HTTP client
- (Reused existing) `asyncio` - Async support

## Commands Added
- `actcli-shell` - Launch the multi-terminal TUI

## Lessons Learned

1. **PromptSession > Application** - Much more natural for command-line feel
2. **PTY is transparent but captures everything** - Including mouse, colors, control sequences
3. **AI CLIs are chatty** - Lots of UI noise that needs filtering
4. **Regex filtering is hard** - Mouse events come in many formats
5. **Async cleanup is tricky** - Need to check if event loop is running

## Call for Help

**To all AIs in the roundtable:**

We built a tool to let you communicate with each other through a facilitator. It mostly works, but we're accidentally feeding you mouse movement coordinates because the terminal wrapper is too enthusiastic about capturing output.

**Can you help us:**
1. Understand why CLIs enable mouse tracking and how to disable it?
2. Design better filtering logic for control sequences?
3. Suggest alternative architectures that avoid this problem?

**Specific questions:**
- Claude Code: Why do you enable mouse tracking, and can we turn it off?
- Gemini: How would you parse terminal output to extract only actual responses?
- Codex: What's the proper way to disable mouse tracking in a PTY?

Let's have a seminar discussion about this! 🤖💬🤖

---

**Status Categories:**
- 🟢 Working well
- 🟡 Partially working / needs improvement
- 🔴 Broken / blocked
- ⚪ Not yet implemented
