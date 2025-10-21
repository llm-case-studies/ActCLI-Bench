# Wrapper Testing Guide

## Prerequisites Check

Before testing, verify:

```bash
# 1. Python version (need 3.11+)
python3 --version

# 2. Virtual environment
ls -la .venv/bin/python*

# 3. AI CLIs installed
which claude codex gemini

# 4. AI CLIs authenticated (test each)
claude --version
codex --version
gemini --version

# 5. Port 8765 available
lsof -i :8765  # Should be empty
```

## Installation

```bash
# If venv doesn't exist or has wrong Python version
python3.11 -m venv .venv  # or python3.12

# Activate and install
source .venv/bin/activate
pip install -e .

# Verify wrapper commands installed
which actcli-facilitator
which actcli-wrap
```

## Quick Test (Echo Test)

**Terminal 1 - Start Facilitator:**
```bash
source .venv/bin/activate
actcli-facilitator serve

# Should see:
# 🚀 Starting facilitator on 0.0.0.0:8765
# INFO: Started server process
```

**Terminal 2 - Wrap Echo (Test 1):**
```bash
source .venv/bin/activate
actcli-wrap --create --name "Echo-1" "cat"

# Should see:
# ✅ Created session: session_abc123
# ✅ Joined as: Echo-1 (participant_xyz)
# ✅ Connected to facilitator
# 🎬 Starting wrapped session: cat
```

Save the session ID from Terminal 2!

**Terminal 3 - Wrap Echo (Test 2):**
```bash
source .venv/bin/activate
actcli-wrap --session session_abc123 --name "Echo-2" "cat"

# Type something in Terminal 2 or 3
# Should see it echoed in both terminals!
```

## Real Test (Claude ↔ Claude)

**Terminal 1 - Facilitator:**
```bash
actcli-facilitator serve
```

**Terminal 2 - Claude Instance 1:**
```bash
actcli-wrap --create --name "Claude-Teacher" --provider anthropic --model claude-sonnet-4 "claude chat"

# Note the session_id!
```

**Terminal 3 - Claude Instance 2:**
```bash
actcli-wrap --session <session_id> --name "Claude-Student" --provider anthropic "claude chat"
```

**Test Interaction:**
1. In Terminal 2 (Teacher): Type a question or instruction
2. Watch it appear in Terminal 3 (Student)
3. Student responds
4. Response appears in Teacher terminal

## Docker Container Test

**Terminal 1 - Facilitator:**
```bash
actcli-facilitator serve
```

**Terminal 2 - Claude in Container:**
```bash
docker run -it \
  -v ~/.claude:/root/.claude \
  -v $(pwd):/workspace \
  --network host \
  claude-container bash

# Inside container:
pip install /workspace  # Install actcli
actcli-wrap --create --name "Claude-Container" "claude chat"
```

**Terminal 3 - Codex on Host:**
```bash
actcli-wrap --session <session_id> --name "Codex-Host" "codex chat"
```

## Troubleshooting

### "Module not found" errors
```bash
# Make sure actcli is installed in venv
pip list | grep actcli
pip install -e .
```

### "Connection refused"
```bash
# Check facilitator is running
curl http://localhost:8765/sessions

# Check firewall
sudo ufw status  # If using UFW
```

### "Permission denied" on PTY
```bash
# Check if terminal supports PTY
python3 -c "import pty; print('PTY OK')"
```

### Rate limits hit during test
- Expected! This validates rate limit detection
- Check facilitator logs for queuing messages
- Messages should be delivered when limit resets

## Expected Output

**Successful Test Shows:**
1. ✅ Facilitator starts on port 8765
2. ✅ Wrappers connect via WebSocket
3. ✅ Messages route between participants
4. ✅ Both terminals show bidirectional communication
5. ✅ No crashes or error messages

**Success Criteria:**
- [ ] Facilitator serves HTTP endpoints
- [ ] WebSocket connections establish
- [ ] Messages appear in both wrapped terminals
- [ ] Can type in either terminal and other sees it
- [ ] Clean shutdown with Ctrl+C

## Machine-Specific Notes (Fill in on MSI)

**MSI Laptop Setup:**
- Python version: _______
- Venv location: _______
- Claude CLI version: _______
- Codex CLI version: _______
- Gemini CLI version: _______
- Docker images built: _______
- Known issues: _______

## Next Steps After Successful Test

1. Record a demo video
2. Test rate limit detection (spam messages)
3. Test provider switching
4. Build web viewer UI
5. Prepare YC demo material
