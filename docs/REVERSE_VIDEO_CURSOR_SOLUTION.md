# SOLUTION: Reverse Video Cursor Detection for ActCLI-Bench

## The Discovery

Modern AI CLIs (Gemini, Claude, Codex) use **reverse video highlighting**
(ESC[7m) to indicate cursor position, not explicit cursor positioning codes.

**Example:**
```
│ > hello wo\x1b[7mr\x1b[27mld
            ^^^^^^^^^^^^
            'r' has reverse video = visual cursor position
```

Real terminals (xterm.js, iTerm2) render the highlighted character as the
cursor, ignoring the VT cursor position which is at end of line.

## Why We Missed This

1. Our debug logs truncated at 200 bytes
2. We assumed Gemini sent cursor codes (it doesn't!)
3. Pyte correctly tracks VT cursor, but we didn't check character attributes

## The Fix

### For ActCLI-Bench (Immediate)

Detect reverse video attribute on characters:

```python
# In term_emulator.py or term_view.py

def find_visual_cursor(pyte_screen):
    """Find cursor position from reverse video attribute.

    Modern AI CLIs use reverse video (ESC[7m) to show cursor visually.
    Real terminals render this as the cursor, ignoring VT cursor position.
    """
    # Check each character for reverse video attribute
    for y in range(pyte_screen.lines):
        line = pyte_screen.buffer[y]
        for x in range(pyte_screen.columns):
            char = line[x]
            if char.reverse:  # Character has reverse video attribute
                return (x, y)

    # Fallback: use VT cursor position (traditional behavior)
    return (pyte_screen.cursor.x, pyte_screen.cursor.y)


def text_with_cursor(self, show=True):
    """Get terminal text with cursor indicator."""
    if not show:
        return self.text()

    # Use visual cursor position (from reverse video)
    cursor_x, cursor_y = find_visual_cursor(self._screen)

    # ... rest of rendering logic ...
```

### For ActCLI-TE (Future)

The Rust VTE-based engine needs to:

1. Track reverse video attribute per character
2. Expose API to query which character(s) have reverse video
3. Python wrapper provides `find_visual_cursor()` method

```rust
// In ActCLI-TE Rust code

pub struct Cell {
    pub character: char,
    pub fg_color: Color,
    pub bg_color: Color,
    pub reverse: bool,  // ← Track reverse video attribute
    pub bold: bool,
    // ... other attributes
}

impl Screen {
    pub fn find_reverse_video_position(&self) -> Option<(u16, u16)> {
        for (y, row) in self.buffer.iter().enumerate() {
            for (x, cell) in row.iter().enumerate() {
                if cell.reverse {
                    return Some((x as u16, y as u16));
                }
            }
        }
        None
    }
}
```

## Testing Strategy

### Test Cases

1. **Gemini:** Type 'x' → Should show cursor after 'x'
2. **Claude:** Type 'hello' → Should show cursor after 'o'
3. **Bash:** No reverse video → Should use VT cursor (end of line)
4. **Vim:** No reverse video → Should use VT cursor

### Expected Behavior

| Terminal | Uses Reverse Video? | Cursor Position |
|----------|---------------------|-----------------|
| Gemini   | ✅ Yes              | At highlighted char |
| Claude   | ✅ Yes              | At highlighted char |
| Codex    | ✅ Yes (likely)     | At highlighted char |
| Bash     | ❌ No               | VT cursor (standard) |
| Vim      | ❌ No               | VT cursor (standard) |

## Why This Is Better Than Pattern Matching

### Pattern Matching (OLD approach - FRAGILE):
```python
# Look for text patterns like "│ >" or "> " or "$ "
if "│ >" in line:
    cursor_x = line.index("│ >") + 4
```

**Problems:**
- ❌ Breaks if UI changes
- ❌ Different for each AI CLI
- ❌ Fails on custom prompts
- ❌ Hard to maintain

### Attribute Matching (NEW approach - ROBUST):
```python
# Look for character with reverse video attribute
if char.reverse:
    cursor_x = x
```

**Benefits:**
- ✅ Works with ANY UI layout
- ✅ Works with ALL AI CLIs
- ✅ Based on ANSI standard (reverse video)
- ✅ Easy to implement
- ✅ No maintenance needed

## Impact on Roadmap

### Short-term (Pyte Fork): NOT NEEDED!
- ❌ No pyte patch required
- ✅ Pyte works correctly as-is
- ✅ Just check character attributes

### Medium-term (ActCLI-TE): UPDATED REQUIREMENTS
- ✅ Track reverse video attribute per character
- ✅ Expose `find_visual_cursor()` API
- ✅ Document AI CLI cursor behavior

### Long-term (Browser): ALREADY SOLVED
- ✅ xterm.js already handles reverse video correctly
- ✅ No changes needed for browser frontend

## Code Changes Needed

### File: `src/actcli/bench_textual/term_emulator.py`

Add method to EmulatedTerminal class:

```python
def find_visual_cursor(self) -> tuple[int, int]:
    """Find visual cursor from reverse video attribute.

    Returns:
        (x, y): Cursor position from reverse video, or VT cursor if none found
    """
    if not self._use_pyte:
        return (0, 0)

    # Check for reverse video character
    for y in range(self._screen.lines):
        line = self._screen.buffer[y]
        for x in range(self._screen.columns):
            char = line[x]
            if char.reverse:
                return (x, y)

    # Fallback to VT cursor
    return (self._screen.cursor.x, self._screen.cursor.y)
```

### File: `src/actcli/bench_textual/term_view.py`

Update cursor rendering to use visual cursor:

```python
def text_with_cursor(self, show: bool = True) -> str:
    """Get terminal text with cursor indicator."""
    if not show:
        return self.emulator.text()

    # Use visual cursor position (from reverse video)
    cursor_x, cursor_y = self.emulator.find_visual_cursor()

    # ... rest of rendering logic using cursor_x, cursor_y ...
```

## Implementation Priority

1. **IMMEDIATE:** Add `find_visual_cursor()` to term_emulator.py
2. **IMMEDIATE:** Update term_view.py to use visual cursor
3. **TEST:** Validate with Gemini, Claude, and Bash
4. **DOCUMENT:** Add to CURSOR_RESEARCH_FINDINGS.md
5. **FUTURE:** Implement in ActCLI-TE

## Validation Checklist

- [ ] Gemini cursor shows at correct position (type 'x')
- [ ] Claude cursor shows at correct position (type 'hello')
- [ ] Bash cursor still works (doesn't use reverse video)
- [ ] Vim cursor still works (doesn't use reverse video)
- [ ] Arrow keys in Gemini (cursor moves with highlighting)
- [ ] Backspace in Gemini (cursor moves back)
- [ ] No regressions in non-AI terminals

## Lessons Learned

1. **Question assumptions:** "Pyte must be buggy" → Pyte is correct!
2. **Get complete data:** 200-byte truncation was hiding the truth
3. **Understand the spec:** VT cursor ≠ visual cursor
4. **Test systematically:** Step-by-step validation revealed the pattern
5. **Collaborate:** Multiple perspectives (CLI + Web Claude) found the answer

## References

- ANSI Escape Code: ESC[7m = Reverse video ON
- ANSI Escape Code: ESC[27m = Reverse video OFF
- VT100 Spec: Reverse video inverts foreground/background colors
- Modern terminals: xterm.js, iTerm2 render reverse video as visual cursor

---

**Status:** READY FOR IMPLEMENTATION ✅
**Priority:** HIGH (unblocks ActCLI-Bench cursor tracking)
**Effort:** 1-2 hours (simple attribute check)
**Risk:** LOW (fallback to VT cursor if no reverse video found)
