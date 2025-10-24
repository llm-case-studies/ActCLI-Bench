#!/usr/bin/env python3
"""Capture COMPLETE escape sequences from Gemini (no truncation).

This tool removes the 200-byte logging limit to see the FULL sequence,
including any cursor positioning codes that might appear after the UI.

Usage:
    python tools/capture_full_sequences.py

Then run ActCLI-Bench, interact with Gemini, and check the output file.
"""

import sys
import os

def patch_term_emulator():
    """Show how to patch term_emulator.py to capture full sequences."""

    print("="*70)
    print("CAPTURING FULL ESCAPE SEQUENCES FROM GEMINI")
    print("="*70)
    print()

    file_path = "src/actcli/bench_textual/term_emulator.py"

    print(f"📝 File to modify: {file_path}")
    print()

    print("🔍 Current code (line 103):")
    print("    preview = repr(b[:200]) if len(b) > 200 else repr(b)")
    print()

    print("✏️  Change to (no truncation):")
    print("    preview = repr(b)  # Full sequence, no truncation")
    print()

    print("📊 Or, better yet, log to a file for large sequences:")
    print("""
    # Add at top of file:
    import datetime

    # In feed() method, replace lines 98-104 with:
    if self._debug_logger and b:
        if b'\\x1b[' in b or b'\\x1bM' in b or b'\\x1b' in b:
            # Log to file for complete analysis
            log_file = "/tmp/actcli_term_sequences.log"
            timestamp = datetime.datetime.now().isoformat()

            with open(log_file, "a") as f:
                f.write(f"\\n{'='*70}\\n")
                f.write(f"[{timestamp}] Sequence ({len(b)} bytes)\\n")
                f.write(f"{'='*70}\\n")
                f.write(repr(b))
                f.write("\\n")

                # Also show hex for binary analysis
                f.write("\\nHex dump:\\n")
                f.write(" ".join(f"{byte:02x}" for byte in b[:100]))
                if len(b) > 100:
                    f.write(f" ... ({len(b)-100} more bytes)")
                f.write("\\n")

            # Still log preview to debug logger
            preview = repr(b[:100]) + "..." if len(b) > 100 else repr(b)
            self._debug_logger(f"[feed] Escape sequences ({len(b)} bytes): {preview}")
            self._debug_logger(f"[feed] Full sequence → /tmp/actcli_term_sequences.log")
    """)
    print()

    print("="*70)
    print("ALTERNATIVE: Use strace/script to capture at OS level")
    print("="*70)
    print()
    print("Option 1: Use script command (captures everything)")
    print("    script -f gemini_output.log")
    print("    # Run gemini, type 'x', exit")
    print("    exit")
    print("    # Analyze gemini_output.log")
    print()

    print("Option 2: Use strace (Linux)")
    print("    strace -s 10000 -e write -o gemini.strace gemini")
    print("    # Type 'x'")
    print("    # Check gemini.strace for write() calls")
    print()

    print("="*70)
    print("RECOMMENDED APPROACH")
    print("="*70)
    print()
    print("1. Modify term_emulator.py to log to /tmp/actcli_term_sequences.log")
    print("2. Run ActCLI-Bench")
    print("3. Add Gemini terminal")
    print("4. Type 'x' in Gemini")
    print("5. Export troubleshooting snapshot")
    print("6. Analyze /tmp/actcli_term_sequences.log")
    print()
    print("Look for:")
    print("  - ESC[row;colH  (cursor positioning)")
    print("  - ESC[H         (cursor home)")
    print("  - ESC[f         (cursor position)")
    print()
    print("If these appear AFTER the UI text:")
    print("  → Gemini IS sending cursor codes")
    print("  → Pyte should be processing them")
    print("  → Need to debug why pyte isn't applying them")
    print()
    print("If these DON'T appear:")
    print("  → Gemini is NOT sending cursor codes")
    print("  → Real terminals must infer cursor position somehow")
    print("  → This is the actual mystery to solve!")
    print()


def create_comparison_test():
    """Create a test to compare real terminal vs pyte."""

    print("="*70)
    print("COMPARISON TEST: Real Terminal vs Pyte")
    print("="*70)
    print()

    test_code = '''#!/usr/bin/env python3
"""Compare what a real terminal receives vs what we feed to pyte."""

import subprocess
import sys

def capture_from_real_terminal():
    """Capture output from Gemini in a real terminal using script."""
    print("Step 1: Capturing from real terminal...")
    print("  This will open a new shell. Run: gemini")
    print("  Type: x")
    print("  Press Ctrl+D to exit")
    print()
    input("Press ENTER to start...")

    # Use script to record terminal session
    subprocess.run(["script", "-f", "/tmp/real_terminal.log"])

    print("✓ Saved to /tmp/real_terminal.log")
    return "/tmp/real_terminal.log"


def capture_from_pyte():
    """Get the sequence we're feeding to pyte from ActCLI-Bench logs."""
    print("Step 2: Capturing from ActCLI-Bench/pyte...")
    print("  Run ActCLI-Bench")
    print("  Add Gemini terminal")
    print("  Type: x")
    print("  Export troubleshooting snapshot")
    print()

    snapshot_path = input("Enter path to troubleshooting snapshot: ")
    return snapshot_path


def compare_sequences(real_log, pyte_log):
    """Compare the two logs byte-by-byte."""
    print("Step 3: Comparing sequences...")

    # Read real terminal log
    with open(real_log, 'rb') as f:
        real_data = f.read()

    # Read pyte log (extract from troubleshooting snapshot)
    # This needs to be implemented based on snapshot format

    print(f"Real terminal: {len(real_data)} bytes")
    print(f"First 200 bytes: {repr(real_data[:200])}")
    print()

    # Look for cursor codes
    cursor_codes = [
        (b'\\x1b[', 'CSI sequence'),
        (b'\\x1b[H', 'Cursor home'),
        (b'\\x1b[f', 'Cursor position'),
    ]

    for code, desc in cursor_codes:
        if code in real_data:
            positions = [i for i in range(len(real_data)) if real_data[i:i+len(code)] == code]
            print(f"Found {desc} at byte positions: {positions}")


if __name__ == '__main__':
    print("REAL TERMINAL vs PYTE COMPARISON")
    print("="*70)
    print()

    choice = input("Run comparison? (y/n): ")
    if choice.lower() == 'y':
        real_log = capture_from_real_terminal()
        pyte_log = capture_from_pyte()
        compare_sequences(real_log, pyte_log)
    else:
        print("Showing instructions only (see code above)")
'''

    with open("tools/compare_terminal_output.py", "w") as f:
        f.write(test_code)

    print("✓ Created tools/compare_terminal_output.py")
    print()


if __name__ == '__main__':
    patch_term_emulator()
    print()
    print("="*70)
    print("NEXT STEPS")
    print("="*70)
    print()
    print("Choose your investigation path:")
    print()
    print("  A) Modify term_emulator.py to log full sequences")
    print("     → Quick, shows exactly what pyte receives")
    print()
    print("  B) Use 'script' command to capture real terminal")
    print("     → Shows what Gemini outputs in real terminal")
    print("     → Compare with pyte's input")
    print()
    print("  C) Both!")
    print("     → Most thorough")
    print()
