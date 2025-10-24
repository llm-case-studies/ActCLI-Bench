#!/usr/bin/env python3
"""Implementation example for reverse video cursor detection.

This shows exactly how to add visual cursor support to ActCLI-Bench
based on the discovery that AI CLIs use reverse video (ESC[7m) to
indicate cursor position.

Usage:
    python tools/implement_visual_cursor.py

This is a reference implementation - copy the functions into the actual
source files as indicated.
"""

# ============================================================================
# ADD TO: src/actcli/bench_textual/term_emulator.py
# ============================================================================

def find_visual_cursor_from_reverse_video(screen):
    """Find cursor position from reverse video attribute.

    Modern AI CLIs (Gemini, Claude, Codex) use reverse video highlighting
    (ESC[7m) to show where the cursor is visually, rather than sending
    explicit cursor positioning codes.

    Real terminals (xterm.js, iTerm2) render the highlighted character as
    the cursor, ignoring the VT cursor position which is often at end of line.

    Args:
        screen: pyte.Screen object

    Returns:
        tuple[int, int]: (x, y) position of visual cursor, or VT cursor if
                         no reverse video character found
    """
    # Scan screen for character with reverse video attribute
    for y in range(screen.lines):
        line = screen.buffer[y]
        for x in range(screen.columns):
            char = line.get(x)
            if char and char.reverse:
                # Found highlighted character - this is the visual cursor!
                return (x, y)

    # No reverse video found - fall back to VT cursor position
    # This handles traditional terminals (bash, vim) that don't use reverse video
    return (screen.cursor.x, screen.cursor.y)


# ============================================================================
# UPDATE IN: src/actcli/bench_textual/term_emulator.py
# Add this method to the EmulatedTerminal class
# ============================================================================

class EmulatedTerminal:
    # ... existing code ...

    def get_visual_cursor_position(self):
        """Get cursor position using visual cues (reverse video).

        Returns:
            tuple[int, int]: (x, y) cursor position
        """
        if self._use_pyte:
            return find_visual_cursor_from_reverse_video(self._screen)
        else:
            # Noop screen doesn't have attributes
            return (0, 0)


# ============================================================================
# EXAMPLE: How to access pyte character attributes
# ============================================================================

def example_access_character_attributes(screen):
    """Example showing how to access pyte character attributes."""
    print("="*70)
    print("ACCESSING PYTE CHARACTER ATTRIBUTES")
    print("="*70)
    print()

    # Get a specific line
    y = 5  # Line number
    line = screen.buffer[y]

    # Get a specific character
    x = 10  # Column number
    char = line.get(x)

    if char:
        print(f"Character at ({x}, {y}): '{char.data}'")
        print(f"  Attributes:")
        print(f"    reverse: {char.reverse}")
        print(f"    bold: {char.bold}")
        print(f"    italics: {char.italics}")
        print(f"    underscore: {char.underscore}")
        print(f"    fg color: {char.fg}")
        print(f"    bg color: {char.bg}")
    else:
        print(f"No character at ({x}, {y})")
    print()

    # Scan for all characters with reverse video
    print("Characters with reverse video:")
    for y in range(screen.lines):
        line = screen.buffer[y]
        for x in range(screen.columns):
            char = line.get(x)
            if char and char.reverse:
                print(f"  ({x:2d}, {y:2d}): '{char.data}'")


# ============================================================================
# TEST: Validate visual cursor detection
# ============================================================================

def test_visual_cursor_detection():
    """Test visual cursor detection with simulated sequences."""
    try:
        import pyte
    except ImportError:
        print("ERROR: pyte not installed")
        return

    print("="*70)
    print("TESTING VISUAL CURSOR DETECTION")
    print("="*70)
    print()

    screen = pyte.Screen(80, 24)
    stream = pyte.ByteStream(screen)

    # Test 1: Gemini-style input with reverse video
    print("Test 1: Gemini-style sequence with reverse video")
    sequence = (
        b'\r\n'                     # Move down
        b'\xe2\x94\x82 > hello w'   # │ > hello w
        b'\x1b[7m'                  # Reverse video ON
        b'o'                        # 'o' (highlighted)
        b'\x1b[27m'                 # Reverse video OFF
        b'rld'                      # rld
    )

    stream.feed(sequence)

    cursor_x, cursor_y = find_visual_cursor_from_reverse_video(screen)
    print(f"  Visual cursor: ({cursor_x}, {cursor_y})")
    print(f"  VT cursor: ({screen.cursor.x}, {screen.cursor.y})")

    # Find the line with content
    for y in range(screen.lines):
        line_text = "".join(screen.buffer[y].get(x).data if screen.buffer[y].get(x) else " "
                           for x in range(screen.columns))
        if "hello" in line_text:
            print(f"  Line {y}: {repr(line_text[:30])}")
            # Check which character has reverse video
            for x in range(screen.columns):
                char = screen.buffer[y].get(x)
                if char and char.reverse:
                    print(f"    Character '{char.data}' at column {x} has reverse video ✓")

    print()

    # Test 2: Traditional terminal (no reverse video)
    print("Test 2: Traditional terminal (no reverse video)")
    screen2 = pyte.Screen(80, 24)
    stream2 = pyte.ByteStream(screen2)

    sequence2 = b'$ ls -la\r\n'
    stream2.feed(sequence2)

    cursor_x2, cursor_y2 = find_visual_cursor_from_reverse_video(screen2)
    print(f"  Visual cursor: ({cursor_x2}, {cursor_y2})")
    print(f"  VT cursor: ({screen2.cursor.x}, {screen2.cursor.y})")
    print(f"  (Should match VT cursor - no reverse video found)")
    print()


# ============================================================================
# IMPLEMENTATION GUIDE
# ============================================================================

def show_implementation_guide():
    """Show step-by-step implementation guide."""
    print("="*70)
    print("IMPLEMENTATION GUIDE")
    print("="*70)
    print()

    print("Step 1: Update term_emulator.py")
    print("-" * 70)
    print("""
1. Add the find_visual_cursor_from_reverse_video() function
2. Add get_visual_cursor_position() method to EmulatedTerminal class

Location: src/actcli/bench_textual/term_emulator.py
Lines to add: ~25 lines (two functions)
""")

    print()
    print("Step 2: Update term_view.py")
    print("-" * 70)
    print("""
1. Find the text_with_cursor() method
2. Change:
     cursor_x = self.emulator._screen.cursor.x
     cursor_y = self.emulator._screen.cursor.y

   To:
     cursor_x, cursor_y = self.emulator.get_visual_cursor_position()

Location: src/actcli/bench_textual/term_view.py
Lines to change: 2 lines
""")

    print()
    print("Step 3: Test")
    print("-" * 70)
    print("""
1. Run actcli-bench
2. Add Gemini terminal
3. Type 'x'
4. Cursor should appear after 'x' (not at end of line)
5. Test with Claude, bash, vim
6. Ensure no regressions
""")

    print()
    print("Step 4: Commit")
    print("-" * 70)
    print("""
git add src/actcli/bench_textual/term_emulator.py
git add src/actcli/bench_textual/term_view.py
git commit -m "fix: use reverse video for cursor detection in AI CLIs

Modern AI CLIs (Gemini, Claude, Codex) use reverse video highlighting
(ESC[7m) to indicate cursor position, not explicit cursor codes.

This change detects the highlighted character and uses its position as
the visual cursor, matching how real terminals (xterm.js, iTerm2) work.

Fixes #X"
""")

    print()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n")
    print("="*70)
    print("VISUAL CURSOR IMPLEMENTATION REFERENCE")
    print("="*70)
    print()

    print("This script shows how to implement reverse video cursor detection")
    print("based on the discovery that AI CLIs use ESC[7m to highlight the")
    print("cursor position rather than sending explicit cursor codes.")
    print()

    choice = input("What would you like to see?\n"
                  "  1) Implementation guide\n"
                  "  2) Run tests\n"
                  "  3) Example code\n"
                  "Enter choice (1-3): ")

    if choice == '1':
        show_implementation_guide()
    elif choice == '2':
        test_visual_cursor_detection()
        print()
        example_access_character_attributes(pyte.Screen(80, 24))
    elif choice == '3':
        print("\nSee the functions at the top of this file!")
        print("Copy them into your source code as indicated.")
    else:
        print("\nRun with:")
        print("  python tools/implement_visual_cursor.py")

    print()
    print("Full solution documented in:")
    print("  docs/REVERSE_VIDEO_CURSOR_SOLUTION.md")
    print()
