#!/usr/bin/env python3
"""Test if bytes → string → bytes round-trip corrupts escape sequences.

This tests whether our terminal_runner.py decoding could be breaking pyte.
"""

def test_round_trip(original_bytes: bytes, description: str) -> None:
    """Test bytes → string → bytes round-trip."""
    print(f"\n{'='*70}")
    print(f"Test: {description}")
    print(f"{'='*70}")

    print(f"Original bytes: {original_bytes}")
    print(f"Original repr:  {repr(original_bytes)}")

    # Simulate what terminal_runner.py does
    try:
        decoded_string = original_bytes.decode("utf-8", errors="replace")
        print(f"Decoded string: {repr(decoded_string)}")
    except Exception as e:
        print(f"ERROR decoding: {e}")
        return

    # Simulate what term_emulator.py does
    try:
        re_encoded_bytes = decoded_string.encode("utf-8", errors="replace")
        print(f"Re-encoded:     {re_encoded_bytes}")
        print(f"Re-encoded repr:{repr(re_encoded_bytes)}")
    except Exception as e:
        print(f"ERROR encoding: {e}")
        return

    # Check if they match
    if original_bytes == re_encoded_bytes:
        print("✅ PASS: Round-trip preserved bytes")
    else:
        print("❌ FAIL: Round-trip corrupted bytes!")
        print(f"   Lost: {len(original_bytes) - len(re_encoded_bytes)} bytes")

        # Show differences
        for i, (orig, new) in enumerate(zip(original_bytes, re_encoded_bytes)):
            if orig != new:
                print(f"   Byte {i}: {orig:02x} → {new:02x}")


def main():
    """Run tests on various escape sequences."""

    print("\n" + "="*70)
    print("TESTING BYTE ROUND-TRIP CORRUPTION")
    print("Testing: bytes → decode('utf-8') → encode('utf-8') → bytes")
    print("="*70)

    # Test 1: Simple escape codes
    test_round_trip(
        b"\x1b[2K\x1b[1A\x1b[G",
        "Simple cursor codes (clear, up, home)"
    )

    # Test 2: Cursor positioning
    test_round_trip(
        b"\x1b[10;5H",
        "Absolute cursor positioning"
    )

    # Test 3: Gemini's actual sequence (from troubleshooting snapshot)
    test_round_trip(
        b'\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[G\r\n',
        "Gemini's redraw pattern"
    )

    # Test 4: UTF-8 box drawing with escape codes
    test_round_trip(
        b'\x1b[38;2;137;180;250m\xe2\x95\xad\xe2\x94\x80\xe2\x94\x80\x1b[39m',
        "UTF-8 box drawing (╭──) with color codes"
    )

    # Test 5: Mix of control codes and text
    test_round_trip(
        b'\x1b[38;2;100;100;100m\xe2\x94\x82\x1b[0m > x',
        "Box char (│) + prompt + text"
    )

    # Test 6: Invalid UTF-8 sequences (edge case)
    test_round_trip(
        b'\x1b[2K\xff\xfe\x1b[1A',  # Invalid UTF-8 in middle
        "Invalid UTF-8 bytes (should use replacement char)"
    )

    # Test 7: NUL bytes
    test_round_trip(
        b'\x1b[2K\x00\x1b[1A',
        "NUL byte in sequence"
    )

    # Test 8: High bytes (non-ASCII control codes)
    test_round_trip(
        b'\x1b[2K\x80\x90\xa0\x1b[1A',
        "High bytes (0x80-0xFF) without valid UTF-8"
    )

    print("\n" + "="*70)
    print("CONCLUSION:")
    print("="*70)
    print()
    print("If all tests PASS: Our byte round-trip is safe")
    print("If any test FAILS: We're corrupting escape sequences!")
    print()
    print("If FAIL: We should pass bytes directly to pyte, not strings.")
    print()


if __name__ == "__main__":
    main()
