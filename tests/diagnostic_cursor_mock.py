#!/usr/bin/env python3
"""Diagnostic mock to test cursor positioning with Gemini-style input box.

This script simulates the terminal output from Gemini's input box and tests
our cursor positioning logic in isolation.

Run from project root with:
    source .venv/bin/activate && python tests/diagnostic_cursor_mock.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from actcli.bench_textual.term_emulator import EmulatedTerminal


def debug_log(msg: str):
    """Print debug messages."""
    print(f"[DEBUG] {msg}")


def simulate_gemini_input_box():
    """Simulate Gemini's input box with ANSI codes and box drawing."""

    # Create emulator with debug logging
    print("\n" + "="*80)
    print("Creating EmulatedTerminal with pyte...")
    print("="*80 + "\n")

    emu = EmulatedTerminal(cols=80, rows=10, debug_logger=debug_log)

    print(f"Emulator mode: {emu.mode}")
    print(f"Pyte version: {emu.pyte_version}")
    print()

    # Simulate the Gemini input sequence
    # This is what Gemini sends when displaying its input box

    # Step 1: Draw the box with ANSI codes
    sequence = ""

    # Line 1: Top of box
    sequence += "\x1b[38;2;100;100;100m╭────────────────────────────────────────╮\x1b[0m\r\n"

    # Line 2: Input line with prompt
    sequence += "\x1b[38;2;100;100;100m│\x1b[0m "
    sequence += "\x1b[38;2;255;255;255m>\x1b[0m "
    sequence += "\x1b[38;2;200;200;200mType your message\x1b[0m"
    # Cursor should be here after "Type your message"
    sequence += " " * 10  # Some padding
    sequence += "\x1b[38;2;100;100;100m│\x1b[0m\r\n"

    # Line 3: Bottom of box
    sequence += "\x1b[38;2;100;100;100m╰────────────────────────────────────────╯\x1b[0m\r\n"

    print("Feeding terminal sequence...")
    emu.feed(sequence)

    print("\n" + "="*80)
    print("RENDERING TEXT WITH CURSOR")
    print("="*80 + "\n")

    # Get the text with cursor
    text_with_cursor = emu.text_with_cursor(show=True)

    print("\n" + "="*80)
    print("FINAL OUTPUT")
    print("="*80)
    print(text_with_cursor)
    print("="*80 + "\n")

    # Show where the cursor should be visually
    print("Expected: Cursor after 'Type your message'")
    print("Visual position should be around column 22")
    print()


def simulate_typing_scenario():
    """Simulate typing 'Hello' in the input box."""

    print("\n" + "="*80)
    print("SIMULATING TYPING: 'Hello'")
    print("="*80 + "\n")

    emu = EmulatedTerminal(cols=80, rows=10, debug_logger=debug_log)

    # Clear screen and set up input box
    emu.feed("\x1b[2J\x1b[H")  # Clear and home

    # Draw box
    emu.feed("\x1b[38;2;100;100;100m╭────────────────────────────────────────╮\x1b[0m\r\n")
    emu.feed("\x1b[38;2;100;100;100m│\x1b[0m \x1b[38;2;255;255;255m>\x1b[0m ")

    # Type each character
    for char in "Hello":
        emu.feed(char)
        print(f"\n--- After typing '{char}' ---")
        text = emu.text_with_cursor(show=True)
        # Show just the relevant line
        lines = text.split('\n')
        if len(lines) > 1:
            print(f"Line with cursor: {repr(lines[1])}")

    print("\n" + "="*80)
    print("FINAL STATE")
    print("="*80)
    print(emu.text_with_cursor(show=True))
    print("="*80 + "\n")


def simulate_gemini_with_absolute_positioning():
    """Simulate Gemini-style box with absolute cursor positioning.

    This is likely how Gemini actually works - it draws the entire box
    and UI, then uses absolute cursor positioning to place the cursor
    in the input field.
    """

    print("\n" + "="*80)
    print("SIMULATING GEMINI WITH ABSOLUTE CURSOR POSITIONING")
    print("="*80 + "\n")

    emu = EmulatedTerminal(cols=80, rows=15, debug_logger=debug_log)

    # Clear and home
    emu.feed("\x1b[2J\x1b[H")

    # Draw some header content
    emu.feed("Loaded cached credentials.\r\n")
    emu.feed("\r\n")
    emu.feed("Tips for getting started:\r\n")
    emu.feed("1. Ask questions, edit files, or run commands.\r\n")
    emu.feed("\r\n")

    # Draw the input box
    emu.feed("\x1b[38;2;100;100;100m╭────────────────────────────────────────────────────────────────╮\x1b[0m\r\n")
    emu.feed("\x1b[38;2;100;100;100m│\x1b[0m \x1b[38;2;255;255;255m>\x1b[0m Type your message or @path/to/file")
    emu.feed(" " * 20)
    emu.feed("\x1b[38;2;100;100;100m│\x1b[0m\r\n")
    emu.feed("\x1b[38;2;100;100;100m╰────────────────────────────────────────────────────────────────╯\x1b[0m\r\n")

    # Draw status line
    emu.feed("~/Projects/ActCLI-Bench                   gemini-2.5-pro (99% context)\r\n")

    # NOW - Gemini uses absolute positioning to move cursor back into the input box!
    # Move cursor to row 7, column 5 (inside the input box after "> ")
    emu.feed("\x1b[7;5H")  # ESC[row;colH - absolute positioning

    print("\n--- After drawing UI and positioning cursor ---")
    text = emu.text_with_cursor(show=True)
    print(text)
    print("\n" + "="*80)

    # Now type "Hello"
    for char in "Hello":
        emu.feed(char)

    print("\n--- After typing 'Hello' ---")
    text = emu.text_with_cursor(show=True)
    print(text)
    print("="*80 + "\n")


def main():
    """Run all diagnostic scenarios."""
    print("\n" + "="*80)
    print("CURSOR POSITIONING DIAGNOSTIC TOOL")
    print("="*80)

    simulate_gemini_input_box()
    simulate_typing_scenario()
    simulate_gemini_with_absolute_positioning()

    print("\n" + "="*80)
    print("DIAGNOSTICS COMPLETE")
    print("="*80)
    print("\nReview the [DEBUG] logs above to see:")
    print("1. What pyte reports as cursor position (x, y)")
    print("2. What the actual line content is (with ANSI codes visible)")
    print("3. Whether ANSI codes are detected and stripped")
    print("4. What string index is calculated")
    print("5. Where the cursor character (▌) is actually inserted")
    print()


if __name__ == "__main__":
    main()
