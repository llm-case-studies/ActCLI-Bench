# Cursor Positioning Research Findings

**Date:** 2025-10-23
**Researcher:** Claude Sonnet 4.5
**Status:** Root cause identified, solution options documented

## Executive Summary

The cursor positioning issue in ActCLI-Bench's terminal emulator has been traced to a **fundamental difference between pyte and real terminal emulators**:

- **Real terminals**: Cursor position automatically follows text output
- **Pyte**: Cursor position after complex escape sequences (clear + up + redraw) doesn't match output location

**Gemini/Claude's rendering strategy** relies on cursor-follows-output behavior that pyte doesn't implement.

---

## Diagnostic Evidence

### Test Results from `tests/pyte_cursor_investigation.py`

**Scenario:** Simulate Gemini's redraw pattern when typing 'x'

```
Input box displayed on line 6: '│ > x                                    │'
Pyte cursor position: y=9, x=0 (blank line, not where 'x' is)
Character 'x' is at string index 4 on line 6
Expected cursor: line 6, column 5 (after 'x')
Actual cursor: line 9, column 0
```

**Conclusion:** After Gemini's upward-clearing redraw sequence, pyte's cursor ends up on a blank line below the actual input, not following the output text.

### Production Evidence from Troubleshooting Snapshots

From `troubleshooting_pack_20251022T222932Z.txt`:

```
[text_with_cursor] pyte cursor position: (x=0, y=21)
[text_with_cursor] line[21] length=175, content='                ' (blank)

Actual Gemini output visible in [gemini] logs:
│ > x                                                                         │
│ > xx                                                                        │
│ > xxx                                                                       │
```

**Observation:** User types 'x' multiple times. Each keypress triggers:
- Escape sequences: `\x1b[2K\x1b[1A` (clear line, move up) repeated
- Full UI redraw with updated text
- Pyte's cursor stays at (0, 21) - never moves

---

## Root Cause Analysis

### How Gemini/Claude Render Their UI

1. **Full Screen Redraw on Every Keystroke:**
   ```
   \x1b[2K     - Clear current line
   \x1b[1A     - Move cursor up
   \x1b[2K     - Clear that line
   \x1b[1A     - Move up again
   ... (repeat)
   \x1b[G      - Move cursor to column 1
   \r\n        - Newline
   [Output the entire UI: box, text, status]
   ```

2. **No Explicit Cursor Positioning:**
   - Gemini does NOT send `\x1b[row;colH` codes to position cursor after redraw
   - Relies on cursor ending up at the correct position naturally

3. **This Works in Real Terminals Because:**
   - When you output "│ > x", the cursor advances as text is printed
   - Final cursor position = end of last printed character
   - Terminal's cursor automatically "follows" the output

### Why Pyte Behaves Differently

**Hypothesis:** After the sequence of "clear line + move up" operations, pyte's internal cursor state becomes disconnected from where text is actually rendered.

**Evidence:**
- Pyte correctly handles simple output (test with explicit `\x1b[4;8H` worked)
- Pyte's `screen.display` shows correct text content
- Pyte's `screen.cursor` position doesn't match where text was last output

**Implication:** Pyte either:
1. Has a bug in tracking cursor through complex up/clear/redraw sequences, OR
2. Intentionally differs from terminal behavior for these edge cases, OR
3. Requires explicit cursor positioning (which Gemini doesn't provide)

---

## Key Differences: Real Terminal vs Pyte

| Behavior | Real Terminal | Pyte |
|----------|---------------|------|
| Output "text" | Cursor advances to end of text | Cursor may not follow after complex sequences |
| `\x1b[1A` (up) | Cursor moves up one line | ✓ Same |
| `\x1b[2K` (clear line) | Line erased, cursor stays | ✓ Same |
| Multiple up + clear + output | Cursor follows final output | ❌ Cursor disconnected from output |
| Explicit `\x1b[row;colH` | Cursor moves to position | ✓ Same |

---

## Why Previous Attempts Failed

### Attempt 1: Pattern Matching for Input Lines
**Method:** Detect `│ >` pattern, calculate cursor from text length
**Result:** Failed - layouts vary (Gemini box, Claude separators, Codex plain)
**Why:** Can't reliably detect all input patterns across different AI CLIs

### Attempt 2: Trust Pyte When Column ≠ 0
**Method:** Only override cursor when at (0, blank_line)
**Result:** Failed - pyte cursor ALWAYS at column 0 during Gemini sessions
**Why:** Gemini's redraw sequence consistently ends with cursor at column 0

### Attempt 3: ANSI Stripping & Visual Width Calculation
**Method:** Strip escape codes, calculate visual width for cursor position
**Result:** Unnecessary - pyte already strips ANSI from `screen.display`
**Why:** Not a character width problem; cursor position itself is wrong

---

## The Critical Question

**"Why does this work in real terminals?"**

**Possible answers:**

### Theory A: Real Terminals Track "Output Position" Separately
Real terminals may maintain two cursor positions:
- **Displayed cursor**: Where the user sees the cursor
- **Output position**: Where next character will be printed

After Gemini's complex sequence, maybe:
- Output position = correct (follows text)
- Pyte only has one cursor = gets confused

### Theory B: Gemini Sends Hidden Cursor Codes We're Missing
Maybe Gemini DOES send cursor positioning, but:
- It's in a format we're not logging
- It's sent on a different channel (terminal mode switch?)
- Our capture is incomplete

**Test:** We need to capture COMPLETE raw PTY bytes and compare:
- Bytes received by real terminal
- Bytes received by pyte in our emulator

### Theory C: Pyte Bug with Relative Cursor Movement
The sequence "up multiple times + output" might trigger a pyte bug where:
- Cursor tracking becomes misaligned
- Real terminals handle this correctly
- Pyte doesn't

---

## Next Research Steps

### 1. Capture Complete PTY Output
**Goal:** Verify whether Gemini sends cursor positioning codes we're not seeing

**Method:**
```python
# In terminal_runner.py PTY read loop
raw_output = os.read(self._master_fd, 4096)
log_to_file(f"/tmp/pty_capture_{terminal_name}.log", raw_output)
```

**Compare:**
- Run Gemini in real terminal, capture `script` output
- Run Gemini in our bench, capture PTY bytes
- Diff the escape sequences

### 2. Test Other Terminal Emulator Libraries
**Goal:** Determine if this is pyte-specific or general problem

**Alternatives to test:**
- `python-prompt-toolkit`'s VTYTEST
- `blessed` library
- `asciinema`'s term emulator
- `xterm.js` (JavaScript, but reference implementation)

### 3. Minimal Reproduction Case
**Goal:** File bug report with pyte maintainers (if it's a pyte bug)

**Create:**
```python
# Minimal script that reproduces cursor misalignment
# Just the escape sequence that triggers the bug
# No ActCLI-Bench dependencies
```

---

## Solution Options

### Option 1: Local Cursor Tracking
**Description:** Track keypresses ourselves and calculate cursor position

**Pros:**
- Works for simple editing (append, left/right arrow)
- No dependency changes

**Cons:**
- Complex state management
- Desyncs if Gemini modifies text (autocomplete, corrections)
- Doesn't handle mouse clicks
- Arrow key navigation in slash menus breaks

**Effort:** High
**Reliability:** Medium (fragile)

---

### Option 2: Replace Pyte
**Description:** Switch to a terminal emulator library with better cursor tracking

**Candidates:**
- `python-prompt-toolkit` (used by ipython)
- Custom implementation using `asciinema`'s recorder as reference
- JavaScript-based solution (xterm.js) with bridge

**Pros:**
- May fix cursor issue if pyte-specific
- Could improve other aspects (performance, features)

**Cons:**
- Large refactor
- Risk: New library may have different issues
- Need to verify cursor behavior before committing

**Effort:** High
**Reliability:** Unknown until tested

---

### Option 3: Request Gemini/Claude to Send Cursor Codes
**Description:** Ask Google/Anthropic to emit `\x1b[row;colH` after redraws

**Pros:**
- Would definitively fix the issue
- Benefits all terminal emulators, not just ours

**Cons:**
- Requires vendor cooperation
- No guarantee they'll implement it
- Long timeline

**Effort:** Low (just asking)
**Reliability:** Depends on vendor response

---

### Option 4: PTY-Level Cursor Injection
**Description:** Intercept PTY output, detect redraws, inject cursor codes

**Method:**
```python
# After detecting Gemini's redraw pattern:
if b'\x1b[2K\x1b[1A' in pty_output:
    # Gemini is redrawing
    # Find input line in new output
    input_line, col = detect_input_position(pty_output)
    # Inject cursor positioning
    pty_output += f'\x1b[{input_line};{col}H'.encode()
```

**Pros:**
- No pyte replacement needed
- Works for Gemini/Claude specifically

**Cons:**
- Fragile pattern matching
- Breaks if Gemini changes rendering
- May confuse pyte further

**Effort:** Medium
**Reliability:** Low

---

### Option 5: Hide Cursor for AI CLIs
**Description:** Don't show cursor indicator for Gemini/Claude terminals

**Pros:**
- Honest about limitation
- Simple to implement
- No misleading cursor position

**Cons:**
- Poor UX
- Doesn't solve the underlying problem
- Users still can't see where they're typing

**Effort:** Low
**Reliability:** N/A (workaround, not fix)

---

## Recommended Path Forward

### Phase 1: Complete Evidence Gathering (1-2 days)
1. ✅ **Understand pyte behavior** (DONE - see diagnostic results)
2. **Capture raw PTY output** from both real terminal and bench
3. **Compare escape sequences** to see if cursor codes are present
4. **Test alternative libraries** with same Gemini sequences

### Phase 2: Decide on Solution (After Phase 1)
**If cursor codes ARE present in real terminal:**
→ Debug why we're not receiving/processing them (PTY issue)

**If cursor codes NOT present anywhere:**
→ Option 2 (replace pyte) or Option 3 (request vendor change)

**If other libraries have same issue:**
→ Fundamentally impossible without vendor cooperation (Option 3)

### Phase 3: Implementation (Timeline TBD)
Based on Phase 2 decision

---

## Diagnostic Tools Created

### 1. `tests/pyte_cursor_investigation.py`
Simulates Gemini's exact redraw pattern to understand pyte behavior

**Usage:**
```bash
python tests/pyte_cursor_investigation.py
```

**Output:** Shows where pyte's cursor ends up vs. where text appears

### 2. `tests/diagnostic_cursor_mock.py`
Tests cursor positioning logic in isolation with known inputs

### 3. `tests/interactive_cursor_test.py`
Interactive tool to visually test cursor positioning

**Usage:**
```bash
# Run this, then add as terminal in bench
python tests/interactive_cursor_test.py
```

### 4. Enhanced Logging in `term_emulator.py`
Lines 98-104: Logs escape sequences as they're received
Lines 276-293: Logs pyte cursor position and line content

**View logs:** Export troubleshooting pack from bench UI

---

## References

- **Pyte Documentation:** https://github.com/selectel/pyte
- **VT100 Escape Codes:** https://vt100.net/docs/vt100-ug/chapter3.html
- **ANSI Terminal Spec:** https://invisible-island.net/xterm/ctlseqs/ctlseqs.html
- **Previous Research:** `docs/CURSOR_POSITIONING_RESEARCH.md`
- **Troubleshooting Snapshots:** `docs/Trouble-Snaps/troubleshooting_pack_*.txt`

---

## Conclusion

The cursor positioning issue is now well-understood:

1. **Root cause:** Pyte's cursor doesn't follow text output after complex escape sequences
2. **Why it matters:** Gemini/Claude rely on this "cursor-follows-output" behavior
3. **What works:** Bash (simple cursor codes), explicit positioning (`\x1b[row;colH`)
4. **What doesn't:** AI CLIs that use full-screen redraws without explicit positioning

**The fix requires either:**
- Pyte replacement/fix
- Vendor cooperation (Gemini/Claude sending cursor codes)
- Complex workarounds (local tracking, PTY injection)

**Next critical step:** Capture and compare raw PTY bytes from real vs. emulated terminals to confirm whether cursor codes are being sent but not processed.
