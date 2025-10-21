# Terminal Width Sizing Issue in ActCLI-Bench

## Problem Statement

We have a Textual TUI application (`BenchTextualApp`) that displays terminal emulators using `pyte`. The terminal view is being sized incorrectly, making the displayed terminal content much narrower than it should be.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│ Screen (230 cols x 50 rows reported by Textual)     │
│ ┌──────────┬────────────────────────────────────┐  │
│ │ Sidebar  │ Detail Pane (#detail)              │  │
│ │ 30 cols  │ ┌────────────────────────────────┐ │  │
│ │          │ │ Title (1 row)                  │ │  │
│ │          │ ├────────────────────────────────┤ │  │
│ │          │ │ TermView (#terminal-view)      │ │  │
│ │          │ │ - Contains pyte EmulatedTerm   │ │  │
│ │          │ │ - Should display terminal      │ │  │
│ │          │ │ - Height: 1fr (flexible)       │ │  │
│ │          │ ├────────────────────────────────┤ │  │
│ │          │ │ Control (3 rows)               │ │  │
│ │          │ └────────────────────────────────┘ │  │
│ └──────────┴────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## CSS Layout (from themes.tcss)
```css
#sidebar { width: 30; padding: 1 1; }
#detail { padding: 1 2; }  /* 1 top/bottom, 2 left/right */
#terminal-view { height: 1fr; margin: 1 0; border: solid #555; }
```

## Current Behavior

### Debug Output from Textual:
```
view.size = Size(width=194, height=38)
view.region = Region(x=32, y=4, width=196, height=40)
view.content_size = Size(width=194, height=38)
view.container_size = Size(width=194, height=38)
view.virtual_size = Size(width=196, height=40)

Parent container: detail
parent.size = Size(width=196, height=46)
parent.region = Region(x=30, y=1, width=200, height=48)
parent.content_size = Size(width=196, height=46)
parent.container_size = Size(width=196, height=46)
parent.virtual_size = Size(width=196, height=46)

Screen size: 230x50
```

### Current Calculation:
- We resize the pyte emulator to: **196 columns x 40 rows**
- Calculation: `parent.region.width - 4 = 200 - 4 = 196`
- This results in terminal content being squeezed/wrapped at 196 columns

## Expected Behavior

When running the **same terminal application (Gemini)** directly in the terminal without our bench wrapper, it uses the **full terminal width** - appears to be using the entire available horizontal space with no artificial wrapping at 196 columns.

### Visual Comparison:
- **Gemini in bench**: Text wraps at ~196 characters, looks squeezed
- **Gemini standalone**: Text uses full terminal width, looks natural and spacious

## The Mystery

1. **Textual reports screen size as 230x50**, which seems small for a modern terminal
2. **Is this in "cells" or "characters"?** Could Textual be using different units than we think?
3. **Parent region is 200 wide** (230 - 30 sidebar = 200), which makes sense
4. **But the actual terminal display area should be wider** based on how standalone terminals look

## Questions

1. **Units**: Is Textual's `Size` and `Region` in terminal characters/cells, or some other unit?
2. **Border/Padding**: Does the border (`solid` or `thick`) consume additional layout space beyond what we're accounting for?
3. **Why 230?**: User says terminal is maximized/wide, but Textual reports only 230 columns. Is this:
   - The actual terminal size being misreported?
   - A limitation of how Textual measures the terminal?
   - A virtual size that differs from actual display size?
4. **Right approach?**: Should we be:
   - Using `view.region.width` directly instead of parent?
   - Using a different attribute entirely?
   - Not subtracting padding at all?
   - Querying terminal size differently (e.g., via `os.get_terminal_size()`)?

## What We've Tried

1. ✅ Using `view.content_size` → 194 cols (too narrow)
2. ✅ Using `view.region` → 196 cols (too narrow)
3. ✅ Using `screen.size - sidebar - padding` → 196 cols (too narrow)
4. ✅ Using `parent.region.width - padding` → 196 cols (too narrow)

All approaches yield ~194-196 columns, but the standalone terminal appears much wider.

## Code Location

- **Emulator creation**: `src/actcli/bench_textual/term_emulator.py` - `EmulatedTerminal` class wraps `pyte.Screen`
- **Resize logic**: `src/actcli/bench_textual/app.py` - `_resize_emulator_if_needed()` method
- **CSS layout**: `src/actcli/bench_textual/themes.tcss`

## Help Needed

**How do we correctly determine the actual display width in characters/columns that the TermView widget can render, so we can size the pyte emulator to match?**

The pyte emulator needs to be sized to the actual renderable width so terminal applications don't get artificially wrapped.
