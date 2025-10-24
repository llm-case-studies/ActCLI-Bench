#!/usr/bin/env python3
"""Analyze escape sequences to find cursor positioning codes.

This tool helps you understand what escape sequences are in a captured log
and specifically looks for cursor positioning codes that might explain
why the cursor ends up in the right place in real terminals.

Usage:
    python tools/analyze_escape_sequences.py <log_file>

Or interactively:
    python tools/analyze_escape_sequences.py
    # Paste the byte sequence when prompted
"""

import sys
import re

def parse_escape_sequences(data_bytes):
    """Parse and categorize escape sequences in byte data."""

    if isinstance(data_bytes, str):
        # Try to evaluate if it's a repr() string
        if data_bytes.startswith("b'") or data_bytes.startswith('b"'):
            try:
                data_bytes = eval(data_bytes)
            except:
                data_bytes = data_bytes.encode('utf-8', errors='replace')

    sequences = []
    i = 0

    while i < len(data_bytes):
        if data_bytes[i:i+1] == b'\x1b':  # ESC
            # Found escape sequence
            start = i
            i += 1

            if i < len(data_bytes):
                next_byte = data_bytes[i:i+1]

                if next_byte == b'[':  # CSI (Control Sequence Introducer)
                    i += 1
                    params = b''
                    while i < len(data_bytes) and data_bytes[i:i+1] in b'0123456789;':
                        params += data_bytes[i:i+1]
                        i += 1

                    if i < len(data_bytes):
                        final = data_bytes[i:i+1]
                        i += 1

                        seq_bytes = data_bytes[start:i]
                        sequences.append({
                            'type': 'CSI',
                            'start': start,
                            'end': i,
                            'bytes': seq_bytes,
                            'params': params.decode('ascii', errors='replace'),
                            'final': final.decode('ascii', errors='replace'),
                            'description': describe_csi(params, final)
                        })
                elif next_byte == b']':  # OSC (Operating System Command)
                    i += 1
                    osc_data = b''
                    while i < len(data_bytes) and data_bytes[i:i+1] not in (b'\x07', b'\x1b'):
                        osc_data += data_bytes[i:i+1]
                        i += 1

                    if i < len(data_bytes) and data_bytes[i:i+1] == b'\x1b':
                        i += 1  # Skip ESC in ESC\

                    if i < len(data_bytes):
                        i += 1  # Skip terminator

                    seq_bytes = data_bytes[start:i]
                    sequences.append({
                        'type': 'OSC',
                        'start': start,
                        'end': i,
                        'bytes': seq_bytes,
                        'description': 'Operating System Command'
                    })
                else:
                    # Other escape sequence
                    i += 1
                    seq_bytes = data_bytes[start:i]
                    sequences.append({
                        'type': 'OTHER',
                        'start': start,
                        'end': i,
                        'bytes': seq_bytes,
                        'description': 'Other escape sequence'
                    })
        else:
            i += 1

    return sequences


def describe_csi(params, final):
    """Describe what a CSI sequence does."""

    final_str = final.decode('ascii', errors='replace') if isinstance(final, bytes) else final
    params_str = params.decode('ascii', errors='replace') if isinstance(params, bytes) else params

    descriptions = {
        'A': f'Cursor up {params_str or "1"} lines',
        'B': f'Cursor down {params_str or "1"} lines',
        'C': f'Cursor forward {params_str or "1"} columns',
        'D': f'Cursor back {params_str or "1"} columns',
        'E': f'Cursor next line {params_str or "1"}',
        'F': f'Cursor previous line {params_str or "1"}',
        'G': f'Cursor to column {params_str or "1"}',
        'H': f'Cursor position (row {params_str.split(";")[0] if ";" in params_str else params_str or "1"}, col {params_str.split(";")[1] if ";" in params_str else "1"})',
        'f': f'Cursor position (same as H)',
        'J': f'Erase in display (mode {params_str or "0"})',
        'K': f'Erase in line (mode {params_str or "0"})',
        'm': f'SGR (colors/attributes): {params_str}',
        's': 'Save cursor position',
        'u': 'Restore cursor position',
    }

    return descriptions.get(final_str, f'CSI {params_str}{final_str}')


def analyze_for_cursor_codes(sequences):
    """Find cursor positioning codes in the sequences."""

    cursor_codes = []

    for seq in sequences:
        if seq['type'] == 'CSI':
            final = seq.get('final', '')

            # Cursor positioning codes
            if final in ('H', 'f'):
                cursor_codes.append({
                    'position': seq['start'],
                    'code': seq['bytes'],
                    'description': seq['description'],
                    'type': 'ABSOLUTE POSITION'
                })
            elif final in ('A', 'B', 'C', 'D', 'E', 'F'):
                cursor_codes.append({
                    'position': seq['start'],
                    'code': seq['bytes'],
                    'description': seq['description'],
                    'type': 'RELATIVE MOVE'
                })
            elif final == 'G':
                cursor_codes.append({
                    'position': seq['start'],
                    'code': seq['bytes'],
                    'description': seq['description'],
                    'type': 'COLUMN POSITION'
                })

    return cursor_codes


def main():
    """Analyze escape sequences from input."""

    print("="*70)
    print("ESCAPE SEQUENCE ANALYZER")
    print("="*70)
    print()

    if len(sys.argv) > 1:
        # Read from file
        file_path = sys.argv[1]
        print(f"Reading from file: {file_path}")
        with open(file_path, 'rb') as f:
            data = f.read()
    else:
        # Interactive mode
        print("Paste the byte sequence (as repr() or raw bytes):")
        print("Example: b'\\x1b[2K\\x1b[1A\\x1b[H'")
        print()
        data_str = input("> ")
        data = data_str

    # Parse sequences
    sequences = parse_escape_sequences(data)

    print()
    print("="*70)
    print(f"FOUND {len(sequences)} ESCAPE SEQUENCES")
    print("="*70)
    print()

    if len(sequences) > 20:
        print("Showing first 20 and last 5...")
        show_sequences = sequences[:20] + sequences[-5:]
    else:
        show_sequences = sequences

    for seq in show_sequences:
        print(f"Byte {seq['start']:4d}: {seq['bytes'][:40]}")
        print(f"           → {seq['description']}")
        print()

    # Analyze for cursor codes
    print()
    print("="*70)
    print("CURSOR POSITIONING CODES")
    print("="*70)
    print()

    cursor_codes = analyze_for_cursor_codes(sequences)

    if cursor_codes:
        print(f"Found {len(cursor_codes)} cursor positioning sequences:")
        print()

        for code in cursor_codes:
            print(f"[{code['type']}] at byte {code['position']}:")
            print(f"  Code: {code['code']}")
            print(f"  Action: {code['description']}")
            print()

        # Check if there are ABSOLUTE positioning codes
        absolute = [c for c in cursor_codes if c['type'] == 'ABSOLUTE POSITION']
        if absolute:
            print("🎯 FOUND ABSOLUTE CURSOR POSITIONING!")
            print()
            print("These codes (ESC[H or ESC[row;colH) explicitly set cursor position.")
            print("If pyte receives these, it should move the cursor correctly.")
            print()
            print("Last absolute position command:")
            last = absolute[-1]
            print(f"  {last['code']} → {last['description']}")
            print()
            print("This might explain why cursor works in real terminals!")
        else:
            print("❌ NO ABSOLUTE CURSOR POSITIONING FOUND")
            print()
            print("Only relative movements (up/down/left/right) were found.")
            print("This means the cursor position depends on where it started.")
            print()

    else:
        print("❌ NO CURSOR POSITIONING CODES FOUND")
        print()
        print("The sequence doesn't contain any cursor movement commands.")
        print("The cursor stays wherever it was before.")
        print()

    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print()
    print(f"Total bytes analyzed: {len(data) if isinstance(data, bytes) else len(data.encode())}")
    print(f"Escape sequences: {len(sequences)}")
    print(f"Cursor codes: {len(cursor_codes)}")
    print()

    if cursor_codes:
        print("✅ This sequence contains cursor positioning")
        print("   → Pyte should be able to track the cursor")
        print("   → If cursor is wrong, might be a pyte bug")
    else:
        print("⚠️  This sequence does NOT contain cursor positioning")
        print("   → Real terminals must infer cursor position")
        print("   → This is the mystery to solve!")


if __name__ == '__main__':
    main()
