# Pyte Patch Plan

This document captures the short-term steps required to ship an ActCLI-flavoured
`pyte` build (`pyte-0.8.2+actcli`) that fixes the Gemini/Claude cursor drift
while we work on ActCLI-TE.

## Goals

- Produce a minimal, well-documented patch that restores accurate cursor visuals
  for AI CLIs inside ActCLI-Bench.
- Keep the code divergence from upstream as small as possible and publish the
  modified source to satisfy LGPL requirements.
- Add automated regression fixtures so we do not reintroduce the bug.

## Work Breakdown

### 1. Repository Setup
- [ ] Fork `github.com/selectel/pyte` into the ActCLI organization.
- [ ] Create `actcli-pyte` branch tracking upstream `0.8.2`.
- [ ] Add CI workflow (pytest + mypy) to catch regressions quickly.

### 2. Reproduce & Capture Fixtures
- [ ] Use `tests/pyte_cursor_investigation.py` and real PTY logs to isolate the
      failing sequence.
- [ ] Store the raw byte fixture and expected cursor position under
      `tests/fixtures/` in the fork.
- [ ] Add a pytest that feeds the sequence and asserts the cursor aligns with
      the visible input line.

### 3. Implement the Fix
- [ ] Focus on `screens.py` (`draw`, `linefeed`, `carriage_return`) where the
      cursor drifts after `ESC[2K ESC[1A …` sequences.
- [ ] Ensure the fix does not break traditional CLIs (bash, vim, htop).
- [ ] Document the rationale inline with concise comments referencing the
      failing sequence.

### 4. Regression Coverage
- [ ] Add parity tests comparing patched pyte vs. xterm.js for the Gemini fix
      and at least one legacy workload.
- [ ] Extend existing tests (if any) to cover multi-line redraw patterns.

### 5. Packaging & Distribution
- [ ] Tag the fork as `0.8.2+actcli.1` (semantic versioning with build suffix).
- [ ] Publish source tarball + wheels to a temporary package index (or internal
      artifactory) for ActCLI-Bench consumption.
- [ ] Update ActCLI-Bench `pyproject.toml` to depend on the new package and add
      release notes explaining the licence.

### 6. Communication & Sync
- [ ] Open a GitHub issue summarising the change for Codex Web / Claude Web.
- [ ] Share test fixtures and documentation so the remote agents can validate
      behaviour in their environments.

## Open Questions

- Should we submit the fix upstream to `selectel/pyte`? (TBD after initial
  stabilization.)
- Do we want to ship pre-built wheels or rely on source installations?
- How often should we rebase the fork against upstream master?

## References

- `docs/CURSOR_RESEARCH_FINDINGS.md`
- `tests/pyte_cursor_investigation.py`
- `docs/CURSOR_POSITIONING_RESEARCH.md`

