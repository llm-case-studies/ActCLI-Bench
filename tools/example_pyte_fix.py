#!/usr/bin/env python3
"""Example pyte fix - illustrates common cursor tracking fix patterns.

This is NOT the actual fix (you need to find that), but shows you
what a fix typically looks like based on our research.

Common bug patterns and fixes:
1. Cursor position not updated after draw()
2. Carriage return + linefeed leaves cursor in wrong place
3. Multiple cursor_up() calls lose track of position
"""

# Example Fix Pattern 1: Ensure draw() advances cursor correctly
# ----------------------------------------------------------------
# BEFORE (buggy):
"""
def draw(self, data):
    for char in data:
        line[self.cursor.x] = char
        self.cursor.x += 1  # Simple increment
        # BUG: Doesn't handle wrapping or edge cases
"""

# AFTER (fixed):
"""
def draw(self, data):
    for char in data:
        char_width = wcwidth(char)
        line[self.cursor.x] = char

        # Correctly advance cursor
        if char_width > 0:
            self.cursor.x = min(self.cursor.x + char_width, self.columns)

        # FIX: Ensure cursor is marked on the line we just drew
        self.dirty.add(self.cursor.y)  # ← This is crucial!
"""


# Example Fix Pattern 2: Carriage return + linefeed sequence
# -----------------------------------------------------------
# BEFORE (buggy):
"""
def carriage_return(self):
    self.cursor.x = 0

def linefeed(self):
    self.cursor.y += 1
    # BUG: If we're past bottom, cursor.y becomes invalid
"""

# AFTER (fixed):
"""
def carriage_return(self):
    self.cursor.x = 0

def linefeed(self):
    top, bottom = self.margins or Margins(0, self.lines - 1)

    if self.cursor.y == bottom:
        # At bottom, need to scroll
        self.index()  # This handles scrolling correctly
    else:
        # FIX: Ensure cursor stays within bounds
        self.cursor.y = min(self.cursor.y + 1, bottom)
"""


# Example Fix Pattern 3: Cursor position after complex sequence
# --------------------------------------------------------------
# The bug we're fixing likely happens in the INTERACTION between methods.
# After this sequence:
#   1. cursor_up() multiple times
#   2. erase_in_line()
#   3. carriage_return()
#   4. linefeed()
#   5. draw()
#
# One method might be setting cursor.y to a value that another method
# then interprets incorrectly.

# TYPICAL FIX: Add bounds checking after operations
"""
def ensure_cursor_bounds(self):
    '''Ensure cursor is within valid screen bounds.'''
    self.cursor.x = max(0, min(self.cursor.x, self.columns - 1))
    self.cursor.y = max(0, min(self.cursor.y, self.lines - 1))

def cursor_up(self, count=None):
    top, _bottom = self.margins or Margins(0, self.lines - 1)
    self.cursor.y = max(self.cursor.y - (count or 1), top)
    self.ensure_cursor_bounds()  # FIX: Add bounds check

def linefeed(self):
    # ... existing logic ...
    self.ensure_cursor_bounds()  # FIX: Add bounds check
"""


# HOW TO FIND THE ACTUAL BUG:
# ----------------------------
# 1. Run: python3 diagnose_pyte_bug.py
# 2. Look at the step-by-step output
# 3. Find which step shows cursor.y jumping to 21 (or wrong line)
# 4. That escape sequence (e.g., "\n") calls a specific method
# 5. Look at that method in pyte/screens.py
# 6. Check if it's calculating cursor position correctly
# 7. The fix is usually:
#    - Adding bounds checking
#    - Fixing off-by-one errors
#    - Handling edge cases (at top/bottom of screen)


# DEBUGGING TIPS:
# ---------------
"""
# Add print statements to pyte/screens.py methods:

def cursor_up(self, count=None):
    print(f"[DEBUG cursor_up] before: y={self.cursor.y}, count={count}")
    # ... existing code ...
    print(f"[DEBUG cursor_up] after: y={self.cursor.y}")

def linefeed(self):
    print(f"[DEBUG linefeed] before: y={self.cursor.y}")
    # ... existing code ...
    print(f"[DEBUG linefeed] after: y={self.cursor.y}")

# Run diagnose_pyte_bug.py and watch the debug output
# You'll see exactly where cursor.y becomes wrong!
"""


print(__doc__)
print("\nThis file is a reference, not executable code.")
print("Use it as a guide when fixing pyte/screens.py")
print("\nSee: ~/Projects/ActCLI-Bench/docs/PYTE_FORK_GUIDE.md for full guide")
