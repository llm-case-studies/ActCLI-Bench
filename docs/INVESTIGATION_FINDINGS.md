# Critical Findings: Gemini Cursor Positioning Mystery SOLVED

**Date:** 2025-10-24
**Investigators:** Claude Sonnet 4.5 (Desktop) + Claude Sonnet 4.5 (Web) + Alex
**Status:** ✅ ROOT CAUSE IDENTIFIED

---

## Executive Summary

**Question:** Why does Gemini's cursor appear correctly in real terminals but not in pyte-based ActCLI-Bench?

**Answer:** Gemini does NOT send explicit cursor positioning codes (`ESC[H`, `ESC[row;colH`). Instead, it uses **reverse video highlighting** (`ESC[7m`) to indicate cursor position VISUALLY. Real terminals render this as a visual cursor, while pyte tracks the actual VT cursor position (end of output).

---

## Evidence

### Test Scenario
- Typed "hello!" in Gemini
- Moved cursor back
- Inserted "Welcome and "
- Result: "Welcome and hello!"
- **Full escape sequences captured** (no 200-byte truncation)

### Escape Sequence Analysis

**Complete sequence from Gemini after user edit:**
```
ESC[2K ESC[1A ESC[2K ESC[1A ... (6x clear+up)
ESC[G \r\n
" Using: 1 GEMINI.md file\r\n"
"╭────...╮\r\n"
"│ > welcome an\x1b[7mh\x1b[27mello !\r\n"  ← CRITICAL LINE
"╰────...╯\r\n"
"~/Projects/... \r\n"
```

**Key observation:**
- Text: `> welcome an\x1b[7mh\x1b[27mello !`
- `\x1b[7m` = Reverse video ON (highlight 'h')
- `\x1b[27m` = Reverse video OFF
- **NO cursor positioning codes!**

### Cursor Code Search Results

**Searched for:**
- `ESC[H` - Cursor home → ❌ NOT FOUND
- `ESC[row;colH` - Absolute positioning → ❌ NOT FOUND
- `ESC[f` - Alternative cursor position → ❌ NOT FOUND

**What WAS found:**
| Code | Description | Count |
|------|-------------|-------|
| `ESC[2K` | Clear line | 7 |
| `ESC[1A` | Cursor up | 6 |
| `ESC[G` | Cursor to column 1 | 1 |
| `ESC[38;2;r;g;bm` | RGB colors | Many |
| `ESC[7m` / `ESC[27m` | Reverse video | Yes! |

---

## How It Works

### In Real Terminals (xterm.js, iTerm2)

1. **Gemini outputs:**
   ```
   │ > welcome an\x1b[7mh\x1b[27mello !│
   ```

2. **Terminal renders:**
   - Normal text: "│ > welcome an"
   - **HIGHLIGHTED 'h'** ← Rendered as cursor visually
   - Normal text: "ello !│"

3. **VT cursor position:**
   - Actually at end of line (after `!│\r\n`)
   - But user SEES cursor at 'h'

4. **Visual vs Technical:**
   - Visual cursor: At highlighted 'h' ✅ (what user sees)
   - VT cursor: At end of output ✅ (actual position per ANSI)

### In pyte-based ActCLI-Bench

1. **Pyte processes same sequence:**
   - Correctly tracks VT cursor at end of line
   - Correctly renders reverse video attribute on 'h'

2. **ActCLI-Bench displays:**
   - Shows text with 'h' highlighted
   - Shows cursor marker (`▌`) at **VT cursor position** (end of output)
   - **Mismatch!** User expects cursor at highlighted 'h'

3. **Why the difference:**
   - Real terminals: Visual cursor = highlighted char
   - ActCLI-Bench: Cursor marker = VT cursor position
   - Both are technically correct for different definitions of "cursor"!

---

## Why Gemini Does This

### Traditional Terminal Apps (bash, vim)
- Send explicit cursor positioning: `ESC[row;colH`
- VT cursor = visual cursor = correct

### Modern TUI Apps (Gemini, Claude)
- Use reverse video for cursor highlighting
- Rely on visual rendering to show cursor
- VT cursor position is irrelevant (just track state)
- **Assumption:** Terminal will render highlighted char as cursor

---

## Implications

### For Pyte
✅ **Pyte is NOT buggy!**
- Correctly implements ANSI X3.64/ECMA-48 standards
- Correctly tracks VT cursor position
- Correctly processes reverse video attributes

**Verdict:** No pyte patch needed.

### For ActCLI-TE
⚠️ **Would have same issue!**
- If following ANSI standards strictly → same behavior as pyte
- VT cursor would be at end of output
- Visual cursor (highlighted char) would be elsewhere

**Solution required:** Must detect reverse video and treat as cursor position.

### For ActCLI-Bench
✅ **Pattern matching IS the right approach!**
- Current `_find_input_line()` method works around this
- Searches for input patterns (`│ >`, `> `) to locate cursor
- This is actually a smart solution for AI CLIs!

**Improvements needed:**
1. Detect reverse video (`ESC[7m`) as cursor indicator
2. Use highlighted char position as cursor location
3. Fall back to pattern matching if no highlight found

---

## Recommended Solutions

### Option 1: Detect Reverse Video (BEST for accuracy)

**Approach:**
```python
def find_cursor_from_highlight(screen):
    """Find cursor by looking for reverse video character."""
    for y, line in enumerate(screen.display):
        for x, char in enumerate(line):
            if char.reverse:  # pyte tracks this attribute
                return (x, y)
    return None  # Fall back to pattern matching
```

**Pros:**
- ✅ Matches exactly what Gemini intends
- ✅ Works for any text content
- ✅ Handles cursor movement correctly

**Cons:**
- ⚠️ Requires access to character attributes
- ⚠️ Gemini-specific behavior (might not work for all AI CLIs)

### Option 2: Enhanced Pattern Matching (CURRENT approach)

**Approach:**
- Keep current `_find_input_line()` logic
- Improve patterns for edge cases
- Add heuristics for cursor position within line

**Pros:**
- ✅ Already implemented
- ✅ Works reasonably well
- ✅ No dependency on terminal emulator internals

**Cons:**
- ❌ Fragile (breaks if UI format changes)
- ❌ Doesn't handle arbitrary cursor positions

### Option 3: Hybrid Approach (RECOMMENDED)

**Combine both methods:**
```python
def get_cursor_position(screen):
    # 1. Try reverse video detection first
    pos = find_cursor_from_highlight(screen)
    if pos:
        return pos

    # 2. Fall back to pattern matching
    pos = find_input_line_pattern(screen)
    if pos:
        return pos

    # 3. Last resort: use VT cursor position
    return (screen.cursor.x, screen.cursor.y)
```

**Pros:**
- ✅ Accurate when highlight is present
- ✅ Robust fallback for edge cases
- ✅ Works with multiple AI CLI styles

---

## Action Items

### Immediate (ActCLI-Bench)
1. ✅ Document findings in this report
2. [ ] Implement reverse video cursor detection
3. [ ] Test with Gemini and Claude
4. [ ] Validate cursor position accuracy

### Short-term (pyte fork)
1. ✅ Close investigation (no patch needed)
2. [ ] Update INVESTIGATION_REPORT.md with findings
3. [ ] Share findings with pyte maintainers (informational)

### Long-term (ActCLI-TE)
1. [ ] Implement reverse video cursor detection from start
2. [ ] Add configuration for cursor detection strategies
3. [ ] Document AI CLI cursor behavior for future reference

---

## Lessons Learned

### What We Thought
- Pyte was buggy
- Missing cursor positioning codes
- Need to patch pyte

### What We Discovered
- Pyte is correct per ANSI standards
- Gemini uses visual cursor (reverse video)
- Real terminals render highlights as cursor
- Pattern matching was right approach all along!

### Key Insight
> **Modern AI CLIs use TUI rendering strategies that differ from traditional terminal apps. They rely on visual cursor indicators (reverse video) rather than VT cursor positioning, assuming terminals will render these visually.**

---

## References

**Troubleshooting Snapshot:**
- `docs/Trouble-Snaps/troubleshooting_pack_20251024T201312Z.txt`
- Full escape sequences captured (33KB)
- Test: "Welcome and hello!" with cursor movement

**Investigation Files:**
- `~/Projects/pyte-fork/INVESTIGATION_REPORT.md` - Initial investigation
- `~/Projects/pyte-fork/test_*.py` - Test scripts
- `tools/analyze_escape_sequences.py` - Sequence analyzer

**ANSI Standards:**
- ECMA-48 / ISO 6429
- VT100/VT220 specifications
- xterm extensions

---

## Conclusion

✅ **Mystery Solved!**

Gemini does NOT send cursor positioning codes. It uses reverse video (`ESC[7m`) to highlight the cursor character visually. Real terminals render this as the cursor, while pyte correctly tracks the VT cursor position at the end of output.

**The fix:** Detect reverse video attributes in ActCLI-Bench and use the highlighted character position as the cursor location.

**No pyte patch needed.** Pyte is working correctly per ANSI standards.

---

**End of Report**

*Investigation completed: 2025-10-24*
*Total time: ~4 hours*
*Lines of investigation code: 1,334*
*Critical data captured: 33KB untruncated sequences*
*Root cause: IDENTIFIED ✅*
