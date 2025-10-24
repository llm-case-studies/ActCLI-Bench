#!/usr/bin/env python3
"""Investigation: Why doesn't pyte's cursor follow text output?

This test simulates Gemini's exact redraw pattern to understand
where pyte's cursor ends up after the escape sequences.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def main():
    """Test pyte's cursor behavior with Gemini-like sequences."""

    print("="*80)
    print("PYTE CURSOR POSITION INVESTIGATION")
    print("="*80)
    print()

    try:
        import pyte
    except ImportError:
        print("ERROR: pyte not installed. Run: pip install pyte")
        return

    # Create a pyte screen
    screen = pyte.Screen(columns=80, lines=10)
    stream = pyte.ByteStream(screen)

    print("Initial cursor position:")
    print(f"  x={screen.cursor.x}, y={screen.cursor.y}")
    print()

    # Simulate initial Gemini output
    print("Step 1: Output initial box")
    sequence = (
        "Loaded cached credentials.\r\n"
        "\r\n"
        "╭────────────────────────────────────────╮\r\n"
        "│ > Type your message                    │\r\n"
        "╰────────────────────────────────────────╯\r\n"
        "~/Projects/test                          \r\n"
    ).encode('utf-8')
    stream.feed(sequence)

    print(f"After initial draw:")
    print(f"  Cursor: x={screen.cursor.x}, y={screen.cursor.y}")
    print(f"  Line at cursor y={screen.cursor.y}: {repr(screen.display[screen.cursor.y])}")
    print()

    # Now simulate typing 'x' - Gemini's redraw pattern
    print("Step 2: Type 'x' - Gemini redraws screen")

    # Gemini's actual sequence from troubleshooting snapshot:
    # Clear lines upward, move cursor, then redraw
    redraw_sequence = (
        "\x1b[2K"  # Clear current line
        "\x1b[1A\x1b[2K"  # Up and clear
        "\x1b[1A\x1b[2K"  # Up and clear
        "\x1b[1A\x1b[2K"  # Up and clear
        "\x1b[G"  # Move to column 1
        "\r\n"
        " Using: 1 test.md file\r\n"
        "╭────────────────────────────────────────╮\r\n"
        "│ > x                                    │\r\n"  # ← cursor should be after 'x'
        "╰────────────────────────────────────────╯\r\n"
        "~/Projects/test                          \r\n"
    ).encode('utf-8')
    stream.feed(redraw_sequence)

    print(f"After typing 'x' and redraw:")
    print(f"  Cursor: x={screen.cursor.x}, y={screen.cursor.y}")
    print(f"  Line at cursor y={screen.cursor.y}: {repr(screen.display[screen.cursor.y])}")
    print()

    # Check where the input line actually is
    print("Searching for input line...")
    for i, line in enumerate(screen.display):
        if '│ > x' in line:
            print(f"  Found input at line {i}: {repr(line)}")
            # Where is 'x' in this line?
            x_pos = line.index('x')
            print(f"  Character 'x' is at string index {x_pos}")
            print(f"  Cursor should be at column {x_pos + 1} (after 'x')")
            print(f"  But pyte cursor is at y={screen.cursor.y}, x={screen.cursor.x}")
            print()

    # Try typing more characters
    print("Step 3: Type 'y' - another redraw")
    redraw_sequence2 = (
        "\x1b[2K"
        "\x1b[1A\x1b[2K"
        "\x1b[1A\x1b[2K"
        "\x1b[1A\x1b[2K"
        "\x1b[G"
        "\r\n"
        " Using: 1 test.md file\r\n"
        "╭────────────────────────────────────────╮\r\n"
        "│ > xy                                   │\r\n"  # ← cursor should be after 'y'
        "╰────────────────────────────────────────╯\r\n"
        "~/Projects/test                          \r\n"
    ).encode('utf-8')
    stream.feed(redraw_sequence2)

    print(f"After typing 'xy':")
    print(f"  Cursor: x={screen.cursor.x}, y={screen.cursor.y}")
    print(f"  Line at cursor: {repr(screen.display[screen.cursor.y])}")
    print()

    # The key test: what if Gemini sent explicit cursor positioning?
    print("Step 4: What if Gemini sent cursor position code?")
    print("  Testing: ESC[4;8H (move to row 4, col 8 - after 'xy')")

    # Reset and redraw with explicit positioning
    screen_explicit = pyte.Screen(columns=80, lines=10)
    stream_explicit = pyte.ByteStream(screen_explicit)

    sequence_with_pos = (
        "Loaded cached credentials.\r\n"
        "\r\n"
        "╭────────────────────────────────────────╮\r\n"
        "│ > xy                                   │\r\n"
        "╰────────────────────────────────────────╯\r\n"
        "~/Projects/test                          \r\n"
        "\x1b[4;8H"  # EXPLICIT: Move cursor to row 4, col 8 (after 'xy')
    ).encode('utf-8')
    stream_explicit.feed(sequence_with_pos)

    print(f"With explicit positioning:")
    print(f"  Cursor: x={screen_explicit.cursor.x}, y={screen_explicit.cursor.y}")
    print(f"  Line at cursor: {repr(screen_explicit.display[screen_explicit.cursor.y])}")
    print()

    print("="*80)
    print("CONCLUSIONS:")
    print("="*80)
    print()
    print("1. When Gemini outputs text like '│ > xy', pyte's cursor does NOT")
    print("   automatically end up after the text.")
    print()
    print("2. This is different from real terminals, where the cursor follows output.")
    print()
    print("3. Pyte DOES respond to explicit cursor positioning codes (ESC[row;colH).")
    print()
    print("4. Therefore: Gemini either:")
    print("   a) Sends cursor codes that we're not capturing, OR")
    print("   b) Relies on cursor-follows-output behavior that pyte doesn't have, OR")
    print("   c) Uses a different mechanism entirely")
    print()
    print("NEXT STEP: Capture COMPLETE raw PTY output to see if cursor codes are present.")
    print()


if __name__ == "__main__":
    main()
