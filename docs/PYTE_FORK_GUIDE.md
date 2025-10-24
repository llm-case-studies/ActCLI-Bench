# Guide: Forking and Patching pyte

**Goal:** Create `pyte-0.8.2+actcli` with cursor positioning fix for modern AI CLIs

**Author:** Claude Sonnet 4.5 + Alex
**Date:** 2025-10-24

---

## Phase 1: Fork the Repository

### Step 1: Fork on GitHub (Web UI)

1. **Go to pyte repo:** https://github.com/selectel/pyte
2. **Click "Fork" button** (top right)
3. **Choose destination:** `llm-case-studies` organization (or your personal account)
4. **Name it:** `pyte` (keep same name for now)
5. **Description:** "Fork of pyte with cursor positioning fix for AI CLIs"
6. **Click "Create fork"**

### Step 2: Clone Your Fork

```bash
# Clone your fork
cd ~/Projects
git clone https://github.com/llm-case-studies/pyte.git pyte-fork
cd pyte-fork

# Add upstream (original pyte repo) as remote
git remote add upstream https://github.com/selectel/pyte.git

# Verify remotes
git remote -v
# Should show:
#   origin    https://github.com/llm-case-studies/pyte.git (your fork)
#   upstream  https://github.com/selectel/pyte.git (original)
```

### Step 3: Create a Branch for Your Fix

```bash
# Create and switch to a new branch
git checkout -b fix/cursor-tracking-ai-clis

# Confirm you're on the new branch
git branch
# Should show: * fix/cursor-tracking-ai-clis
```

---

## Phase 2: Understand the Current Code

### Step 1: Explore pyte Structure

```bash
# List pyte source files
ls -la pyte/

# Key files:
#   screens.py  - Main Screen class with cursor logic (1,339 lines)
#   streams.py  - Parser that feeds escape sequences (431 lines)
```

### Step 2: Review the Bug

**From our research:** After Gemini's redraw sequence, pyte's cursor ends up at wrong position.

**Example sequence:**
```
\x1b[2K      # Clear line
\x1b[1A      # Move up
... (repeat 6 times)
\x1b[G       # Move to column 1
\r\n         # Carriage return + newline
│ > x        # Draw text
```

**Expected:** Cursor at column 5 (after 'x')
**Actual:** Cursor at column 0, line 21 (blank line)

### Step 3: Locate Relevant Methods

```bash
# Find cursor-related methods
grep -n "def cursor" pyte/screens.py | head -20
grep -n "def draw" pyte/screens.py | head -5
grep -n "def carriage_return" pyte/screens.py
```

**Key methods we'll likely need to fix:**
- `draw()` - Outputs characters and advances cursor
- `carriage_return()` - Moves cursor to column 0
- `linefeed()` - Moves cursor down and possibly to new line
- `cursor_up()` - Moves cursor up

---

## Phase 3: Create the Fix

### Option A: Use the Diagnostic Test to Find the Bug

Let's create a test that reproduces the exact bug:

```bash
# Create a test file
cat > tests/test_gemini_cursor.py << 'EOF'
"""Test case for Gemini AI CLI cursor positioning bug."""
import pyte

def test_gemini_redraw_sequence():
    """Test that cursor follows text after Gemini's redraw pattern."""
    screen = pyte.Screen(80, 24)
    stream = pyte.ByteStream(screen)

    # Gemini's exact redraw pattern
    sequence = (
        b'\x1b[2K\x1b[1A'  # Clear + up
        b'\x1b[2K\x1b[1A'  # Clear + up
        b'\x1b[2K\x1b[1A'  # Clear + up
        b'\x1b[G'          # Column 1
        b'\r\n'            # Newline
        b'\xe2\x94\x82 > x'  # "│ > x"
    )

    stream.feed(sequence)

    # After drawing "│ > x", cursor should be after 'x'
    # Line content: "│ > x" (4 characters)
    # Expected cursor: column 4, at the line with text

    # Find which line has the text
    text_line = None
    for i, line in enumerate(screen.display):
        if '│ > x' in line:
            text_line = i
            break

    assert text_line is not None, "Could not find output line"

    # Cursor should be on the text line, after the text
    print(f"Text found at line: {text_line}")
    print(f"Cursor position: ({screen.cursor.x}, {screen.cursor.y})")
    print(f"Expected: (4, {text_line})")

    # THIS WILL FAIL with current pyte
    assert screen.cursor.y == text_line, \
        f"Cursor on wrong line: {screen.cursor.y} != {text_line}"
    assert screen.cursor.x == 4, \
        f"Cursor at wrong column: {screen.cursor.x} != 4"

if __name__ == '__main__':
    test_gemini_redraw_sequence()
EOF

# Run the test (it should FAIL with current pyte)
python tests/test_gemini_cursor.py
```

**Expected output:**
```
Text found at line: 3
Cursor position: (0, 21)
Expected: (4, 3)
AssertionError: Cursor on wrong line: 21 != 3
```

### Option B: Analyze the Code

Let's look at the specific methods that might be causing the issue:

```bash
# View the draw method
sed -n '/def draw/,/^    def /p' pyte/screens.py | head -80

# View carriage_return and linefeed
sed -n '/def carriage_return/,/^    def /p' pyte/screens.py
sed -n '/def linefeed/,/^    def /p' pyte/screens.py
```

---

## Phase 4: Apply the Fix

### Hypothesis: The Issue

After analyzing pyte's code, the likely issue is in how `linefeed()` or `carriage_return()` interact with `draw()`.

**Common patterns that cause this:**

1. **After carriage return + linefeed, cursor not at right position**
2. **draw() advances cursor but position gets reset**
3. **Multiple cursor movements don't track correctly**

### The Fix (Example)

Let me check the actual code and suggest a fix:

```bash
# First, let's understand the current behavior
python << 'EOF'
import pyte

# Minimal test
screen = pyte.Screen(80, 24)
stream = pyte.ByteStream(screen)

print("Step 1: Initial state")
print(f"  Cursor: ({screen.cursor.x}, {screen.cursor.y})")

print("\nStep 2: After carriage return")
stream.feed(b'\r')
print(f"  Cursor: ({screen.cursor.x}, {screen.cursor.y})")

print("\nStep 3: After newline")
stream.feed(b'\n')
print(f"  Cursor: ({screen.cursor.x}, {screen.cursor.y})")

print("\nStep 4: After drawing text")
stream.feed(b'hello')
print(f"  Cursor: ({screen.cursor.x}, {screen.cursor.y})")
print(f"  Text: '{screen.display[screen.cursor.y]}'")

EOF
```

**Based on the output, we'll identify where the cursor tracking breaks.**

---

## Phase 5: Test the Fix

### Step 1: Ensure Existing Tests Pass

```bash
# Install test dependencies
pip install -e ".[test]"  # or pip install pytest

# Run existing tests
pytest tests/

# Make sure all pass BEFORE your changes
```

### Step 2: Add Your Test

```bash
# Add the test to the test suite
cp tests/test_gemini_cursor.py tests/test_ai_cli_cursor.py

# Run just your test
pytest tests/test_ai_cli_cursor.py -v
```

### Step 3: Verify the Fix

After applying your fix:

```bash
# Run your test again
pytest tests/test_ai_cli_cursor.py -v
# Should PASS now!

# Run ALL tests to ensure no regressions
pytest tests/
```

---

## Phase 6: Commit and Push

### Step 1: Review Your Changes

```bash
# See what files you modified
git status

# See the diff
git diff pyte/screens.py
```

### Step 2: Commit

```bash
# Stage your changes
git add pyte/screens.py tests/test_ai_cli_cursor.py

# Commit with clear message
git commit -m "fix: correct cursor tracking for AI CLI redraw patterns

Modern AI CLIs (Gemini, Claude, Codex) use full-screen redraw patterns
that involve multiple cursor movements and line clears. The cursor was
not correctly tracking the final position after these sequences.

This fix ensures cursor.x and cursor.y match the actual position after:
- Multiple cursor_up() + erase_in_line() sequences
- carriage_return() + linefeed() combinations
- draw() operations that output text

Fixes cursor appearing at wrong position in ActCLI-Bench.

Added regression test: tests/test_ai_cli_cursor.py
"
```

### Step 3: Push to Your Fork

```bash
# Push your branch to GitHub
git push origin fix/cursor-tracking-ai-clis

# Or if this is your first push on this branch
git push -u origin fix/cursor-tracking-ai-clis
```

---

## Phase 7: Prepare for Release

### Step 1: Update Version

Edit `setup.py` or `pyproject.toml`:

```python
# Change version from:
version = "0.8.2"

# To:
version = "0.8.2+actcli.1"
```

### Step 2: Update Changelog

Create `ACTCLI_CHANGES.md`:

```markdown
# ActCLI Changes to pyte

This fork contains cursor tracking fixes for modern AI CLI applications.

## Version 0.8.2+actcli.1 (2025-10-24)

### Fixed
- Cursor positioning after complex redraw sequences used by AI CLIs
  (Gemini, Claude, Codex)
- Cursor now correctly tracks position after multiple cursor movements
  combined with line clears and redraws

### Added
- Regression test for AI CLI cursor patterns

### Maintained
- Full backward compatibility with original pyte 0.8.2
- All original tests still pass

## Licensing
This fork maintains the original LGPL-3.0 license.
Original repository: https://github.com/selectel/pyte
```

### Step 3: Update README

Add to the top of `README`:

```markdown
# pyte (ActCLI fork)

**This is a fork of pyte with cursor tracking fixes for modern AI CLIs.**

- **Original:** https://github.com/selectel/pyte
- **License:** LGPL-3.0 (unchanged)
- **Fork maintainer:** ActCLI team
- **Status:** Temporary - will be replaced by ActCLI-TE (MIT-licensed)

## Why This Fork Exists

Modern AI CLIs (Gemini, Claude, Codex) use full-screen redraw patterns
that the original pyte doesn't handle correctly. This fork fixes cursor
tracking for these patterns while maintaining full backward compatibility.

**For long-term use, we recommend ActCLI-TE** (https://github.com/llm-case-studies/ActCLI-TE),
our MIT-licensed terminal engine. This fork exists to provide immediate
relief while ActCLI-TE is under development.

## Installation

```bash
pip install pyte-actcli
```

## Original README Below

---

[original README content continues...]
```

---

## Phase 8: Publish to PyPI

### Step 1: Create PyPI Account

1. Go to https://pypi.org/account/register/
2. Create account (if you don't have one)
3. Verify email

### Step 2: Generate API Token

1. Go to https://pypi.org/manage/account/token/
2. Click "Add API token"
3. Name: "pyte-actcli publishing"
4. Scope: "Entire account" (or specific project later)
5. **Save the token** (starts with `pypi-...`)

### Step 3: Configure Publishing

```bash
# Install build tools
pip install build twine

# Create ~/.pypirc (store your token)
cat > ~/.pypirc << EOF
[distutils]
index-servers =
    pypi

[pypi]
username = __token__
password = pypi-YOUR-TOKEN-HERE
EOF

chmod 600 ~/.pypirc
```

### Step 4: Build the Package

```bash
# Clean old builds
rm -rf dist/ build/ *.egg-info

# Build
python -m build

# Check what was built
ls dist/
# Should show:
#   pyte-0.8.2+actcli.1-py3-none-any.whl
#   pyte-0.8.2+actcli.1.tar.gz
```

### Step 5: Test on Test PyPI (Optional but Recommended)

```bash
# Upload to test.pypi.org first
twine upload --repository testpypi dist/*

# Try installing from test PyPI
pip install --index-url https://test.pypi.org/simple/ pyte-actcli

# Test it works
python -c "import pyte; print(pyte.__version__)"
```

### Step 6: Publish to Real PyPI

```bash
# Upload to pypi.org
twine upload dist/*

# You'll see:
# Uploading distributions to https://upload.pypi.org/legacy/
# Uploading pyte-0.8.2+actcli.1-py3-none-any.whl
# Uploading pyte-0.8.2+actcli.1.tar.gz
```

### Step 7: Verify Publication

```bash
# Install from real PyPI
pip install pyte-actcli

# Test
python << EOF
import pyte
print(f"Version: {pyte.__version__}")
screen = pyte.Screen(80, 24)
print("Works!")
EOF
```

---

## Phase 9: Integrate into ActCLI-Bench

### Step 1: Update Dependencies

Edit `ActCLI-Bench/pyproject.toml`:

```toml
[project]
dependencies = [
    # ... other deps ...
    "pyte-actcli>=0.8.2+actcli.1",  # Use our fork
]
```

### Step 2: Update Documentation

Create `ActCLI-Bench/docs/PYTE_FORK_NOTICE.md`:

```markdown
# Notice: Patched pyte Dependency

ActCLI-Bench currently uses `pyte-actcli`, a fork of the original
pyte library with cursor tracking fixes for modern AI CLIs.

## Why a Fork?

The original pyte library (LGPL-3.0) doesn't correctly track cursor
position for AI CLIs that use full-screen redraw patterns (Gemini,
Claude, Codex).

## Licensing

**pyte-actcli maintains the LGPL-3.0 license.**

If LGPL is not acceptable for your use case, please wait for
ActCLI-TE (MIT-licensed), which is under active development.

## Timeline

- **Now:** pyte-actcli (LGPL, patched)
- **Q1 2025:** ActCLI-TE (MIT, Rust-based) - in development
- **Q2 2025:** Drop pyte-actcli dependency

See: https://github.com/llm-case-studies/ActCLI-TE
```

### Step 3: Update Release Notes

In `ActCLI-Bench/CHANGELOG.md`:

```markdown
## [Unreleased]

### Changed
- **Terminal engine:** Switched to pyte-actcli fork with cursor fixes
  - Fixes cursor positioning in Gemini, Claude, Codex terminals
  - Maintains LGPL-3.0 license (temporary)
  - See docs/PYTE_FORK_NOTICE.md for details

### Added
- Documentation about pyte fork and licensing implications
- Migration plan to ActCLI-TE (MIT-licensed engine)
```

---

## Troubleshooting

### "I can't find the bug location"

Run the diagnostic test step-by-step:

```python
import pyte

screen = pyte.Screen(80, 24)
stream = pyte.ByteStream(screen)

# Test each escape sequence individually
sequences = [
    (b'\x1b[2K', "Clear line"),
    (b'\x1b[1A', "Move up"),
    (b'\x1b[G', "Column 1"),
    (b'\r', "Carriage return"),
    (b'\n', "Linefeed"),
    (b'hello', "Draw text"),
]

for seq, description in sequences:
    stream.feed(seq)
    print(f"{description}: cursor=({screen.cursor.x}, {screen.cursor.y})")
```

Compare with what xterm.js does!

### "Tests are failing after my fix"

```bash
# Run tests with verbose output
pytest tests/ -v

# Run specific test
pytest tests/test_screen.py::TestCursor -v

# If a test fails, it might be testing the OLD (buggy) behavior
# You may need to update that test
```

### "PyPI upload fails"

```bash
# Check package metadata
twine check dist/*

# Verify version format
grep version setup.py  # or pyproject.toml

# Make sure version follows PEP 440
# Good: 0.8.2+actcli.1
# Bad:  0.8.2-actcli-1
```

---

## Next Steps

After publishing:

1. **Test in ActCLI-Bench**
   ```bash
   cd ActCLI-Bench
   pip install --upgrade pyte-actcli
   actcli-bench
   # Test with Gemini/Claude
   ```

2. **Monitor for Issues**
   - Watch GitHub issues on your pyte fork
   - Be ready to publish 0.8.2+actcli.2 if bugs found

3. **Start ActCLI-TE Development**
   - This fork buys you time
   - Begin working on the long-term solution

---

## Resources

- **Original pyte:** https://github.com/selectel/pyte
- **pyte documentation:** https://pyte.readthedocs.io/
- **Python packaging:** https://packaging.python.org/
- **Semantic versioning:** https://semver.org/
- **PEP 440 (version format):** https://peps.python.org/pep-0440/

---

## Questions?

If you get stuck at any step, let me know! I'm here to help. 🚀
