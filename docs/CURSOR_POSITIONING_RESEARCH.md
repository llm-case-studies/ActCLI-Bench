# Cursor Positioning Research & Findings

**Date:** 2025-10-22
**Issue:** Cursor appears misplaced in hosted terminals (Gemini, Claude)
**Status:** Partial fix implemented, fundamental limitations discovered

## Problem Statement

When running AI CLI tools (Gemini, Claude) through ActCLI-Bench's terminal emulator, the visual cursor indicator (▌) appears in the wrong position:
- Initially appears below the input box on a blank line
- After typing, jumps to beginning of line instead of following typed text
- Arrow key navigation doesn't move the visible cursor
- Makes editing input text effectively impossible

## Root Cause Analysis

### Key Discovery 1: Gemini/Claude Use Full-Screen Redraws

Through extensive diagnostic logging, we discovered that Gemini and Claude use a **full-screen redraw** approach rather than traditional cursor positioning:

1. **They redraw the entire UI** (input box, status line, etc.) on every update
2. **They never send cursor positioning escape codes** to update pyte's cursor
3. **Pyte's cursor remains at (x=0, y=21)** - a blank line below the UI
4. **The actual typing position is tracked internally** by Gemini/Claude, not visible to pyte

Evidence from troubleshooting snapshots:
```
[text_with_cursor] pyte cursor position: (x=0, y=21)
[text_with_cursor] line[25] length=175, content='                    ' (blank)
[text_with_cursor] line[18] content='│ > he  ell   =v='  (actual input)
```

### Key Discovery 2: Input Box Pattern

Gemini and Claude use a distinctive input box pattern:
```
╭────────────────────────────────────────╮
│ > Type your message or @path/to/file  │
╰────────────────────────────────────────╯
```

The prompt pattern `│ >` is consistent and can be detected.

### Key Discovery 3: No Cursor Position Information

When the user:
- Types characters → Screen redraws with new content, cursor stays at (0,21)
- Uses arrow keys → Screen redraws, cursor stays at (0,21)
- Edits in middle → Screen redraws, cursor stays at (0,21)

**Conclusion:** We have NO information about where the cursor actually is when editing.

## Solution Attempts

### Attempt 1: ANSI Escape Code Stripping
**Hypothesis:** ANSI codes in the line were causing cursor position calculation errors.

**Implementation:**
- Added regex pattern to strip ANSI escape sequences
- Enhanced `_index_from_column()` to handle wide characters

**Result:** ❌ FAILED
- Pyte already strips ANSI codes from `screen.display`
- The problem wasn't character width calculation

### Attempt 2: Smart Input Line Detection
**Hypothesis:** Detect the input box and override pyte's cursor position.

**Implementation:**
- Created `_find_input_line()` function to search for `│ >` pattern
- Calculate cursor position as end of typed content
- Override pyte's cursor when on blank line

**Result:** ⚠️ PARTIAL SUCCESS
- ✅ Cursor now appears in the input box (not below it)
- ✅ For simple typing at end, cursor position is reasonable
- ❌ Arrow key navigation doesn't update cursor
- ❌ Editing in middle of text is broken

**Code location:** `src/actcli/bench_textual/term_emulator.py:147-213`

### Attempt 3: Trust Pyte When Column ≠ 0
**Hypothesis:** If pyte shows cursor at column > 0, it's tracking movement.

**Implementation:**
- Only override cursor when at column 0 on blank line
- Trust pyte's position otherwise

**Result:** ❌ FAILED
- Pyte's cursor never moves from (0,21) even when typing
- Column is always 0

## Fundamental Limitations

The current approach **cannot fully solve** the cursor positioning problem because:

1. **Gemini/Claude don't expose cursor position** - They manage it internally
2. **Screen redraws don't include cursor updates** - No escape codes sent
3. **We can't infer position from content alone** - User could be editing anywhere in the line
4. **Arrow keys are processed by Gemini/Claude** - They don't send cursor movement codes back

## What Works

- ✅ Bash terminal (traditional cursor positioning) - **fully working**
- ✅ Gemini/Claude initial prompt - cursor appears in box
- ✅ Gemini/Claude simple appending - cursor appears after typed text
- ⚠️ Gemini/Claude with placeholder text - cursor positioned after prompt

## What Doesn't Work

- ❌ Arrow key navigation in Gemini/Claude - cursor doesn't follow
- ❌ Editing in middle of text - cursor position unknown
- ❌ Backspace/Delete visual feedback - cursor doesn't update
- ❌ Slash command menu navigation - requires arrow keys

## Possible Future Solutions

### Option 1: Track Keypresses Locally
**Approach:** Maintain our own cursor position based on keys we send.

**Pros:**
- Could track left/right/home/end keys
- Would work for simple editing

**Cons:**
- Complex state management
- Would desync if Gemini changes text (autocomplete, etc.)
- Wouldn't handle mouse clicks (if Gemini supports them)

**Effort:** High, fragile

### Option 2: Gemini/Claude Integration
**Approach:** Request Gemini/Claude to send cursor position updates.

**Pros:**
- Would be accurate
- Would handle all cases

**Cons:**
- Requires changes to Gemini/Claude CLIs
- May not be feasible

**Effort:** Depends on vendor cooperation

### Option 3: Alternative Display Mode
**Approach:** For Gemini/Claude, don't show cursor indicator at all.

**Pros:**
- Simple, honest about limitations
- Doesn't mislead user

**Cons:**
- Poor UX
- Doesn't solve the underlying problem

**Effort:** Low

### Option 4: Capture PTY Input/Output Directly
**Approach:** Monitor the actual escape sequences being sent to/from the PTY.

**Pros:**
- Would see if Gemini IS sending cursor codes
- Could detect patterns we're missing

**Cons:**
- Requires low-level PTY interception
- May still not help if codes aren't sent

**Effort:** Medium

## Diagnostic Tools Created

### 1. Enhanced Logging (`term_emulator.py`)
- Logs pyte cursor position
- Logs line content with byte representation
- Logs cursor calculation steps
- Logs input line detection logic

### 2. Diagnostic Mock (`tests/diagnostic_cursor_mock.py`)
- Simulates Gemini-style input box
- Tests cursor positioning in isolation
- Validates our logic against known inputs

### 3. Interactive Test (`tests/interactive_cursor_test.py`)
- Creates interactive input box
- Can be added as terminal to bench
- Useful for visual testing

## Recommendations

1. **Commit current improvements** - They help with the initial cursor placement
2. **Document the limitation** - Be clear that arrow key editing doesn't work in Gemini/Claude
3. **Create sophisticated diagnostic mock** - Build a terminal that reports cursor position
4. **Consider Option 4** - Investigate PTY-level diagnostics to see actual escape sequences
5. **Reach out to Gemini/Claude teams** - Ask if cursor positioning can be improved

## Testing Notes

To reproduce the issue:
1. Start `actcli-bench`
2. Add Gemini terminal
3. Type some text in the input box
4. Try to use arrow keys to move cursor
5. Export troubleshooting snapshot
6. Observe cursor position logs

## References

- **Troubleshooting Snapshots:** `docs/Trouble-Snaps/troubleshooting_pack_20251022T*.txt`
- **Screenshots:** `docs/screenshots/sr_*.png`
- **Pyte Documentation:** https://github.com/selectel/pyte
- **VT100 Escape Codes:** https://vt100.net/docs/vt100-ug/chapter3.html
