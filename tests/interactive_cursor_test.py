#!/usr/bin/env python3
"""Interactive cursor test - mimics Gemini's input box for testing cursor positioning.

This creates an interactive terminal session that draws a Gemini-style input box
and lets you type into it, while the actual Gemini terminal emulation shows
whether the cursor is positioned correctly.
"""

import sys
import time

def clear_screen():
    """Clear screen and home cursor."""
    sys.stdout.write("\x1b[2J\x1b[H")
    sys.stdout.flush()

def draw_input_box(text=""):
    """Draw the input box with current text."""
    # Clear and home
    clear_screen()

    # Header
    print("Cursor Positioning Test - Interactive Input Box")
    print()
    print("Type some text and watch where the cursor appears in the bench UI.")
    print("The cursor should appear RIGHT AFTER your typed text, not below the box.")
    print()

    # Draw the input box
    sys.stdout.write("\x1b[38;2;100;100;100m╭────────────────────────────────────────────────────────────╮\x1b[0m\n")
    sys.stdout.write("\x1b[38;2;100;100;100m│\x1b[0m \x1b[38;2;255;255;255m>\x1b[0m ")
    sys.stdout.write(text)

    # Pad the rest of the line
    padding = 56 - len(text)
    if padding > 0:
        sys.stdout.write(" " * padding)

    sys.stdout.write("\x1b[38;2;100;100;100m│\x1b[0m\n")
    sys.stdout.write("\x1b[38;2;100;100;100m╰────────────────────────────────────────────────────────────╯\x1b[0m\n")
    sys.stdout.flush()

    # Now position cursor back to the input position using absolute positioning
    # Row 7 (0-indexed is 6), Column after "> " and current text
    col = 4 + len(text)  # "│ > " = 4 characters
    sys.stdout.write(f"\x1b[7;{col}H")
    sys.stdout.flush()

def main():
    """Run interactive cursor test."""
    # Disable line buffering
    import os
    os.system('stty -echo')  # Disable terminal echo (we'll echo manually)

    try:
        clear_screen()

        text = ""
        draw_input_box(text)

        print("\n\n")
        print("Instructions:")
        print("- Type characters to add to the input")
        print("- Press Backspace to delete")
        print("- Press Ctrl+C to exit")
        print("\n")
        print(f"Current text: '{text}'")

        while True:
            # Read one character at a time
            import tty
            import termios

            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

            # Handle special characters
            if ch == '\x03':  # Ctrl+C
                break
            elif ch == '\x7f' or ch == '\x08':  # Backspace
                if text:
                    text = text[:-1]
            elif ch == '\r' or ch == '\n':  # Enter
                # Clear and show what was typed
                clear_screen()
                print(f"\nYou typed: '{text}'")
                print("\nPress any key to continue or Ctrl+C to exit...")
                sys.stdin.read(1)
                text = ""
            elif ch.isprintable():
                text += ch

            # Redraw
            draw_input_box(text)

    finally:
        os.system('stty echo')  # Re-enable echo
        clear_screen()
        print("Cursor test complete!")

if __name__ == "__main__":
    main()
