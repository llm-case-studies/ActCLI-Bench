# Pyte Forking & Patching Tools

This directory contains tools to help you fork, patch, and publish pyte with cursor tracking fixes.

## 🚀 Quick Start

**Never forked a repo before? Start here:**

```bash
# Step 1: Run the quick start script
cd ~/Projects/ActCLI-Bench
./tools/start_pyte_fork.sh

# Follow the prompts - it will:
#   ✓ Guide you through forking on GitHub
#   ✓ Clone your fork
#   ✓ Set up branches
#   ✓ Run diagnostics
#   ✓ Show you the bug
```

## 📁 Files in This Directory

### 1. **start_pyte_fork.sh** (Quick Start)
Interactive script that sets up your fork workspace.
- Helps you fork on GitHub
- Clones the repo
- Creates fix branch
- Runs diagnostics

**Usage:**
```bash
./tools/start_pyte_fork.sh
```

### 2. **diagnose_pyte_bug.py** (Bug Finder)
Shows exactly where pyte's cursor tracking breaks.
- Step-by-step escape sequence analysis
- Shows cursor position after each step
- Identifies the exact point where cursor becomes wrong

**Usage:**
```bash
# Run BEFORE your fix (shows the bug)
python tools/diagnose_pyte_bug.py

# Run AFTER your fix (should pass)
python tools/diagnose_pyte_bug.py
```

### 3. **example_pyte_fix.py** (Fix Patterns)
Reference guide showing common cursor bug fix patterns.
- Not executable - just reference
- Shows typical bugs and fixes
- Debugging tips

**Usage:**
```bash
# Read it for guidance
cat tools/example_pyte_fix.py
```

### 4. **PYTE_FORK_GUIDE.md** (Complete Manual)
Comprehensive guide covering EVERYTHING:
- Forking process
- Finding the bug
- Applying the fix
- Testing
- Publishing to PyPI
- Integrating into ActCLI-Bench

**Usage:**
```bash
# Read the full guide
less docs/PYTE_FORK_GUIDE.md
```

## 📋 Step-by-Step Process

### Phase 1: Setup (15 minutes)
```bash
# 1. Run quick start
./tools/start_pyte_fork.sh

# 2. You'll see diagnostic output showing the bug
```

### Phase 2: Find the Bug (30-60 minutes)
```bash
# 1. Look at diagnostic output from step_pyte_fork.sh
# 2. Identify which step shows cursor jumping to wrong position
# 3. Read example_pyte_fix.py for common patterns
# 4. Look at pyte/screens.py to find the faulty method
```

### Phase 3: Fix the Bug (1-3 hours)
```bash
cd ~/Projects/pyte-fork

# 1. Edit pyte/screens.py with your fix
# 2. Test your fix
python diagnose_pyte_bug.py  # Should pass now!

# 3. Run full test suite
pytest tests/

# 4. Commit your changes
git add pyte/screens.py
git commit -m "fix: correct cursor tracking for AI CLI patterns"
```

### Phase 4: Publish (30 minutes)
```bash
# Follow the guide in docs/PYTE_FORK_GUIDE.md Phase 8
# Summary:
#   1. Update version to 0.8.2+actcli.1
#   2. Build: python -m build
#   3. Publish: twine upload dist/*
```

### Phase 5: Integrate (15 minutes)
```bash
cd ~/Projects/ActCLI-Bench

# Update pyproject.toml to use your fork
# Test with ActCLI-Bench
pip install pyte-actcli
actcli-bench  # Test with Gemini/Claude
```

## 🆘 Troubleshooting

### "I can't find the bug"
```bash
# Run diagnostic with detailed output
python tools/diagnose_pyte_bug.py

# Look for the step where cursor.y jumps from expected to wrong value
# That escape sequence is processed by a specific method in screens.py
```

### "My fix breaks other tests"
```bash
# You might have fixed the bug but broken something else
# Check which test fails:
pytest tests/ -v

# The failing test might be testing the OLD (buggy) behavior
# You may need to update that test too
```

### "I don't understand Python well enough"
Don't worry! The guide is very detailed:
1. Read `docs/PYTE_FORK_GUIDE.md` Phase 3
2. Look at `tools/example_pyte_fix.py` for patterns
3. Ask for help! Comment in GitHub issue or ping Claude

### "Publishing to PyPI failed"
```bash
# Check package metadata
twine check dist/*

# Verify version format (must follow PEP 440)
# Good: 0.8.2+actcli.1
# Bad:  0.8.2-actcli-1

# Make sure you have API token configured
cat ~/.pypirc  # Should have your token
```

## 📚 Reference Documents

- **Complete Guide:** `docs/PYTE_FORK_GUIDE.md`
- **Roadmap:** `docs/terminal-engine-roadmap.md`
- **Research:** `docs/CURSOR_RESEARCH_FINDINGS.md`
- **Pyte Analysis:** `docs/PYTE_INVESTIGATION_SUMMARY.md`

## 🎯 Success Criteria

Your fix is ready when:
- ✅ `diagnose_pyte_bug.py` passes (shows "SUCCESS")
- ✅ All original pyte tests pass (`pytest tests/`)
- ✅ Gemini terminal in ActCLI-Bench shows cursor correctly
- ✅ Claude terminal in ActCLI-Bench shows cursor correctly
- ✅ Bash terminal still works (no regression)

## 💡 Tips for Success

1. **Take it step by step** - Don't rush
2. **Use the diagnostic tool** - It shows exactly where the bug is
3. **Test frequently** - Run `diagnose_pyte_bug.py` after each change
4. **Keep it simple** - The fix is likely just a few lines
5. **Document your changes** - Add comments explaining WHY

## 🤝 Getting Help

If you get stuck:
1. Check `docs/PYTE_FORK_GUIDE.md` troubleshooting section
2. Look at `example_pyte_fix.py` for patterns
3. Run `diagnose_pyte_bug.py` to see current state
4. Create GitHub issue with diagnostic output

## 🎉 After You Succeed

Once you've published pyte-actcli:
1. Update ActCLI-Bench to use it
2. Test with real AI CLIs
3. Document any issues
4. Start working on ActCLI-TE (long-term solution)!

---

**You've got this! The tools are here to guide you every step of the way.** 🚀
