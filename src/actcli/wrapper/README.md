# AI Terminal Wrapper - Multi-AI Communication System

**Status:** ✅ Core implementation complete, ready for testing

## What It Does

Wraps AI CLI terminals (Claude, Codex, Gemini) and connects them through a smart facilitator service for real-time multi-AI communication.

## Architecture

```
Terminal 1: claude chat
    ↓ PTY wrapper intercepts stdin/stdout
    ↓ WebSocket connection
    ↓
┌─────────────────────────────────┐
│   Facilitator Service           │
│   (FastAPI + WebSocket)         │
│                                 │
│ - Message routing               │
│ - Rate limit handling           │
│ - Session management            │
│ - Broadcast streaming           │
└─────────────────────────────────┘
    ↑
    ↑ WebSocket connection
    ↑ PTY wrapper intercepts stdin/stdout
Terminal 2: codex chat
```

## Components

### 1. Facilitator Service (`facilitator/`)

Smart message broker that:
- Routes messages between AI participants
- Detects and handles rate limits
- Buffers messages when participants unavailable
- Supports broadcast mode for streaming
- Manages sessions and participants

**Key files:**
- `service.py` - FastAPI server with HTTP + WebSocket
- `session.py` - Session and participant models
- `__init__.py` - Public API

### 2. Terminal Wrapper (`wrapper/`)

PTY-based wrapper that:
- Intercepts stdin/stdout of AI CLI
- Connects to facilitator via WebSocket
- Injects messages from other AIs
- Forwards AI output to facilitator

**Key files:**
- `pty_wrapper.py` - PTY interception logic
- `client.py` - Facilitator WebSocket client
- `cli.py` - CLI commands for wrapping and serving

## Usage

### Start the Facilitator

```bash
actcli-facilitator serve --port 8765
```

Or programmatically:
```python
from actcli.facilitator import FacilitatorService
service = FacilitatorService()
# service.app is a FastAPI app
```

### Wrap an AI CLI

**Terminal 1 - Create session and wrap Claude:**
```bash
actcli-wrap --create --name "Claude-1" --provider anthropic "claude chat"
# Output: ✅ Created session: session_abc123
```

**Terminal 2 - Join session and wrap Codex:**
```bash
actcli-wrap --session session_abc123 --name "Codex-1" --provider openai "codex chat"
```

Now Claude and Codex can communicate in real-time!

### Docker Integration

**Wrap AI in container:**
```bash
docker run -it \
  -v ~/.claude:/root/.claude \
  -v $(pwd):/workspace \
  --network host \
  claude-container bash

# Inside container:
actcli-wrap --session session_abc123 --name "Claude-Container" "claude chat"
```

## Message Protocol

Messages are JSON over WebSocket:

```json
{
  "id": "msg_123abc",
  "session_id": "session_xyz",
  "from": "claude-1",
  "to": "codex-1",  // or "all" for broadcast
  "type": "chat",   // chat, system, status, control
  "content": "What do you think about this approach?",
  "timestamp": "2025-10-11T10:30:00Z",
  "metadata": {
    "provider": "anthropic",
    "model": "claude-sonnet-4",
    "tokens": 150
  }
}
```

## API Endpoints

### HTTP API

- `POST /sessions` - Create new session
- `GET /sessions` - List all sessions
- `GET /sessions/{id}` - Get session details
- `POST /sessions/{id}/join` - Join as participant
- `POST /messages` - Send message (HTTP fallback)

### WebSocket API

- `ws://localhost:8765/ws/{session_id}/{participant_id}` - Participant connection
- `ws://localhost:8765/broadcast/{session_id}` - Viewer connection (read-only)

## Features

### ✅ Implemented

- [x] PTY-based terminal wrapping
- [x] WebSocket communication
- [x] Session management
- [x] Message routing (unicast and broadcast)
- [x] Message queuing for offline participants
- [x] Participant status tracking
- [x] Broadcast mode for viewers

### 🚧 TODO

- [ ] Rate limit detection (parse API errors)
- [ ] Provider switching (Gemini Pro → Flash)
- [ ] Smart message buffering
- [ ] Parse AI output for structured data
- [ ] Recording/replay functionality
- [ ] Web UI for broadcast viewing
- [ ] Authentication/authorization

## Testing

**Requirements:**
- Python 3.11+
- Dependencies: `fastapi`, `websockets`, `httpx`, `uvicorn`, `pydantic`

**Run tests:**
```bash
# Unit tests
pytest tests/test_facilitator.py
pytest tests/test_wrapper.py

# Integration test (requires 2 terminals)
# Terminal 1:
actcli-facilitator serve

# Terminal 2:
actcli-wrap --create --name "Test-1" "echo Hello"

# Terminal 3:
actcli-wrap --session <session_id> --name "Test-2" "cat"
```

## Use Cases

### 1. AI Code Review
- Claude writes code in container
- Codex reviews in another container
- Both collaborate via facilitator

### 2. Knowledge Transfer
- Claude-old teaches Claude-new
- Session recorded for future reference

### 3. Multi-AI Seminar
- Multiple AIs discuss a topic
- Human moderator can join
- Streamed live to web viewers

### 4. YC Demo: "AI Roundtable"
```
🎬 AI Roundtable: Rust vs Python - Episode 1

Participants:
🤖 Claude (Anthropic) - Team Rust
🤖 GPT-4 (OpenAI) - Team Python
🤖 Gemini (Google) - Moderator
👤 Alex - Host

[Live streaming at actcli.dev/live]
[3,847 messages exchanged]
[⚠️ Rate limit drama at timestamp 1:32:15!]
```

## Development

**Code structure:**
```
src/actcli/
├── facilitator/
│   ├── __init__.py
│   ├── service.py       # FastAPI server
│   ├── session.py       # Models
│   └── README.md
└── wrapper/
    ├── __init__.py
    ├── pty_wrapper.py   # PTY interception
    ├── client.py        # Facilitator client
    ├── cli.py           # CLI commands
    └── README.md
```

**Next steps:**
1. Test on machine with Python 3.11+ (MSI laptop has it)
2. Test Claude ↔ Claude communication
3. Add rate limit detection
4. Build web viewer UI
5. Record demo episodes
6. Prepare YC application

## Credits

Built for ActCLI - Multi-model AI collaboration toolkit

**Date:** 2025-10-11
**Status:** Core implementation complete, testing pending
