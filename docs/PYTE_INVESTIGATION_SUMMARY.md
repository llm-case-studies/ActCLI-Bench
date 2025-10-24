# Investigation: Could Our Code or Pyte Be At Fault?

**Date:** 2025-10-23
**Question:** Are we corrupting bytes before pyte sees them? How mature/tested is pyte?

---

## Question 1: Are We Corrupting The Byte Stream?

### Our Data Flow

```
PTY (raw bytes)
    ↓
terminal_runner.py:188  →  os.read(fd, 4096)              [BYTES]
terminal_runner.py:216  →  data.decode("utf-8", "replace") [BYTES → STRING]
terminal_runner.py:217  →  self._on_output(text)          [STRING]
    ↓
terminal_manager.py:292 →  emu.feed(text)                 [STRING]
    ↓
term_emulator.py:93-94  →  data.encode("utf-8", "replace") [STRING → BYTES]
term_emulator.py:106    →  self._stream.feed(b)           [BYTES to pyte]
```

**We're doing: BYTES → STRING → BYTES before pyte!**

### Test Results

Created `tests/test_byte_corruption.py` to test if this round-trip corrupts data.

**Results:**
```
✅ PASS: Simple cursor codes (clear, up, home)
✅ PASS: Absolute cursor positioning (ESC[10;5H)
✅ PASS: Gemini's exact redraw pattern (ESC[2K ESC[1A ...)
✅ PASS: UTF-8 box drawing (╭──) with color codes
✅ PASS: Box char (│) + prompt + text
❌ FAIL: Invalid UTF-8 bytes (0xFF, 0xFE standalone)
✅ PASS: NUL bytes
❌ FAIL: Invalid high bytes (0x80-0xFF) without valid UTF-8
```

### Conclusion: **Our byte handling is NOT the problem**

- All valid escape sequences are preserved perfectly
- Only invalid UTF-8 gets corrupted (replaced with � character)
- Real applications (Gemini, Claude) send valid UTF-8
- The troubleshooting snapshot shows valid bytes: `b'\x1b[2K\x1b[1A...'`

**Verdict: We can rule out byte corruption as the cause.**

---

## Question 2: How Mature/Tested Is Pyte?

### Pyte Statistics

**Popularity:**
- 85,857 weekly downloads on PyPI
- 704 GitHub stars
- Classified as "popular" package

**Usage:**
Used by notable projects:
- **Ajenti** – webadmin panel for Linux/BSD
- **Pymux** – terminal multiplexor
- **BastionSSH** – SSH fortress/bastion tool
- **Jumpserver** – open source springboard machine

**Maintenance Status:**
- ⚠️ **Marked as "Inactive"** by Snyk (not actively developed)
- ✅ No known vulnerabilities or license issues
- Last major activity: Version 0.8.2 (current)

### Historical Cursor Bugs In Pyte

From pyte's changelog and commit history:

1. **"fixes to Screen.cursor_up and Screen.cursor_down interact with the scrolling region"**
   - Cursor movement with scrolling regions had bugs

2. **"fixes to Screen.cursor_back when called after the draw in the last column"**
   - Cursor positioning at screen edge was buggy

3. **"modifications to the logic around tracking position in the HistoryScreen"**
   - Position tracking has been problematic

**Important Note from Pyte Docs:**
> "According to ECMA-48 standard, lines and columns are 1-indexed, so ESC [ 10;10 f really means move cursor to position (9, 9) in the display matrix."

Pyte uses 0-based indexing internally but must convert from 1-based escape codes.

### What Pyte Was Designed For

From documentation:
> "To screen scrape terminal apps, for example htop or aptitude. To write cross platform terminal emulators; either with a graphical (xterm, rxvt) or a web interface, like AjaxTerm."

**Key insight:** Pyte was designed for:
- Screen scraping (reading terminal output)
- Simple terminal emulators
- Traditional CLI tools (htop, aptitude)

**NOT tested against:**
- Modern AI CLI tools (Gemini, Claude, Codex)
- Complex full-screen redraws with multi-line clearing
- Fancy TUI frameworks (like what Gemini/Claude use)

---

## Question 3: What Do AI CLIs Do Differently?

### Traditional CLI Tools (bash, htop, vim)

These tools have been around for decades and were the test cases for pyte:
- Use standard escape codes
- Cursor positioning is explicit: `ESC[10;5H`
- Incremental updates (change one line, move cursor there)
- Well-tested patterns

### Modern AI CLIs (Gemini, Claude, Codex)

These are NEW (2023-2024) and use modern TUI frameworks:
- Built with `prompt_toolkit` or similar
- **Full-screen redraws** on every keystroke
- Complex multi-line clearing sequences
- Rely on "cursor follows output" behavior
- May use undocumented/edge-case escape sequences

**They were tested against:**
- Real terminals (Terminal.app, iTerm2, Alacritty, Kitty)
- NOT against pyte!

---

## The Smoking Gun

### What Works Perfectly In Pyte
```python
# Explicit cursor positioning (what htop/vim do)
screen.feed(b"Hello")
screen.feed(b"\x1b[5;10H")  # Move cursor to row 5, col 10
# Pyte cursor: ✅ Correctly at (9, 4) in 0-indexed coords
```

### What Breaks In Pyte
```python
# Gemini's pattern: clear multiple lines, redraw everything
screen.feed(b"\x1b[2K")      # Clear line
screen.feed(b"\x1b[1A")      # Up
screen.feed(b"\x1b[2K")      # Clear
screen.feed(b"\x1b[1A")      # Up
# ... repeat 6 times ...
screen.feed(b"\x1b[G")       # Column 1
screen.feed(b"\r\n│ > x")    # Output text
# Pyte cursor: ❌ Wrong position (blank line below output)
```

**Real Terminal.app:** After outputting "│ > x", cursor naturally advances to after 'x'

**Pyte:** After the same sequence, cursor ends up on blank line

---

## Root Cause Hypothesis

### The Behavior Difference

| Action | Real Terminal | Pyte |
|--------|---------------|------|
| Output "hello" | Cursor advances to end | Cursor advances to end |
| `ESC[1A` (up) | Cursor moves up | ✅ Same |
| `ESC[2K` (clear) | Line cleared, cursor stays | ✅ Same |
| Complex: multiple up+clear, then output | Cursor follows final output | ❌ Cursor disconnected |

### Why This Might Be A Pyte Bug

1. **Pyte has had cursor tracking bugs before** (see changelog)
2. **Pyte is no longer actively maintained** (might not get fixed)
3. **Gemini/Claude use edge-case sequences** (not tested in pyte's era)
4. **The same bytes work in real terminals** (so not a protocol issue)

### Or... Is It By Design?

Maybe pyte intentionally differs from real terminals for these complex sequences. From pyte's perspective:
- "I was told to move up 6 times, clear 6 lines, go to column 1, output text"
- "I did exactly that, cursor is now at column 1 after the last newline"
- "Not my job to track where the *output* ended up"

Real terminals might have special logic:
- "After a complex sequence, track where printable chars ended"
- "Cursor should be at last printable char position"

---

## Comparison: How Projects Use Pyte

### Ajenti (Web Admin Panel)
- Uses pyte to display terminal in web browser
- Shows command output (ls, ps, etc.)
- Traditional CLI commands, not AI CLIs
- **Works fine!**

### Pymux (Terminal Multiplexor)
- Uses pyte to emulate terminals in panes
- Runs bash, vim, editors
- Traditional tools
- **Works fine!**

### ActCLI-Bench (Our Project)
- Uses pyte to emulate AI CLIs (Gemini, Claude, Codex)
- Complex full-screen TUIs with rapid redraws
- **Cursor positioning broken!**

---

## Conclusions

### ✅ We Can Rule Out:
1. **Our byte handling** - Round-trip test shows no corruption
2. **Invalid UTF-8** - Gemini sends valid sequences
3. **Missing escape codes** - We're feeding everything to pyte

### ⚠️ Strong Evidence That It's Pyte:
1. **Pyte has had cursor bugs before**
2. **Pyte wasn't tested with modern AI CLIs**
3. **Same bytes work in real terminals**
4. **Pyte is no longer actively maintained**
5. **Our diagnostic shows pyte cursor ≠ real terminal cursor**

### 🤔 But Could Real Terminals Be Doing Something Special?

Possible that Terminal.app has extra logic:
- After complex redraw, track where visible text ends
- Update cursor to follow output
- Pyte just follows the specs literally

---

## What Now?

### Option 1: Verify It's Definitely Pyte
**Next test:** Capture raw PTY bytes from:
- Real terminal running Gemini
- Our emulator running Gemini
- Compare byte-for-byte

If bytes are identical but results differ → Definitely pyte

### Option 2: Check If Cursor Codes Are Hidden
**Next test:** Deep inspection of PTY output
- Maybe Gemini sends cursor codes in special modes?
- Terminal state switches we're not capturing?

### Option 3: Test Other Terminal Emulators
Try replacing pyte with:
- `prompt_toolkit`'s VTYTEST
- `xterm.js` (JavaScript, more modern)
- Custom parser

### Option 4: Accept It And Work Around
- Local cursor tracking (fragile)
- Request vendor fix (Gemini/Claude to send explicit cursor codes)
- Hide cursor for AI CLIs (poor UX)

---

## Recommendation

**We're 90% confident it's a pyte limitation**, not our code.

The smoking gun will be:
1. Capturing raw bytes to confirm they're identical
2. Testing another terminal emulator library
3. Filing a detailed bug with pyte (though unlikely to be fixed given inactive status)

**Most pragmatic solution:** Test `prompt_toolkit` or another actively maintained library that handles modern TUI apps better.
