# Cursor & PTY Improvements (October 2025)

**Date:** 2025-10-26  
**Scope:** Gemini, Claude, Codex terminals inside ActCLI-Bench

## Highlights

- **Visual cursor parity.** Gemini/Claude highlight the active character with SGR reverse-video rather than emitting cursor-positioning escape codes. We now detect those highlighted cells and place the caret there, falling back to prompt heuristics and finally to the raw VT cursor.
- **Device Status Report support.** Codex expects the terminal to answer `ESC[6n` (cursor position) during startup. The terminal manager now responds with the pyte cursor co-ordinates, restoring compatibility.
- **End-to-end logging.** Every keystroke written to a PTY is logged via the debug stream and persisted in `docs/Trouble-Snaps/write_debug.log`, making Enter/Return diagnostics straightforward.

## Key Changes

1. `src/actcli/bench_textual/term_emulator.py`
   - Added reverse-video detection and prompt heuristics to align the caret with modern AI CLIs.
2. `src/actcli/bench_textual/terminal_runner.py`
   - Added optional debug logging for each write, captured in troubleshooting packs.
3. `src/actcli/bench_textual/terminal_manager.py`
   - Reply to Device Status Report requests (`ESC[6n`) using pyte’s cursor state.

## Tooling & Evidence

- Current packs: `docs/Trouble-Snaps/troubleshooting_pack_20251026T060832Z.txt`, `…061414Z.txt`, `…061550Z.txt`.
- Write trace: `docs/Trouble-Snaps/write_debug.log`.
- Screenshots: `docs/screenshots/sr_24c02c2b.png`, `sr_b25a1972.png`, `sr_c02a4fac.png`.

## Lessons Learned

- Real-world CLIs may use visual cues (reverse video) instead of ANSI cursor codes; terminals must interpret those cues for an accurate caret.
- Responding to terminal queries (`ESC[6n`, mouse modes, etc.) is essential even for simple PTY wrappers.
- Having a persistent write log drastically reduces turnaround when validating input handling.

## Forward Plan

- **ActCLI-TE:** bake in reverse-video cursor detection, DSR replies, configurable logging hooks, and a friendlier Python API so others do not repeat this investigation.
- **Instrumentation:** refactor the write/DSR logging into togglable helpers to avoid ad-hoc patches when debugging in the future.
- **Documentation:** keep this page updated as new terminal behaviours appear; move superseded troubleshooting packs to `docs/Trouble-Snaps/Archive/` to keep the workspace tidy.
