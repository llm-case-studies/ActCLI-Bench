#!/bin/bash
# Quick patch to enable full sequence logging in term_emulator.py

set -e

echo "PATCHING term_emulator.py FOR FULL SEQUENCE LOGGING"
echo "="*70
echo ""

FILE="src/actcli/bench_textual/term_emulator.py"

if [ ! -f "$FILE" ]; then
    echo "ERROR: $FILE not found"
    echo "Are you in ActCLI-Bench root directory?"
    exit 1
fi

echo "Creating backup..."
cp "$FILE" "${FILE}.backup"
echo "✓ Backup created: ${FILE}.backup"
echo ""

echo "Applying patch..."

# Use sed to modify line 103
# Before: preview = repr(b[:200]) if len(b) > 200 else repr(b)
# After:  preview = repr(b)  # FULL SEQUENCE - no truncation for investigation

sed -i.bak2 '103s/.*/                        preview = repr(b)  # FULL SEQUENCE - no truncation for investigation/' "$FILE"

echo "✓ Patch applied"
echo ""

echo "Changes:"
echo "  Line 103: Removed 200-byte truncation"
echo "  Now logs FULL escape sequence to debug output"
echo ""

echo "To revert:"
echo "  mv ${FILE}.backup $FILE"
echo ""

echo "Next steps:"
echo "  1. Run actcli-bench"
echo "  2. Add Gemini terminal"
echo "  3. Type 'x'"
echo "  4. Export troubleshooting snapshot"
echo "  5. Look for cursor codes (ESC[row;colH) in the full output"
echo ""
