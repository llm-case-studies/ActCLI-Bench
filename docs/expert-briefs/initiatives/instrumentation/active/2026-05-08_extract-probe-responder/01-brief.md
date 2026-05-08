# Sprint Brief - Extract Probe Responder

**Initiative:** `instrumentation`
**Sprint:** `2026-05-08_extract-probe-responder`
**Target branch:** `feature/instrumentation/extract-probe-responder`
**Merge target:** `main`
**Validation branch:** `validation/instrumentation/extract-probe-responder`

## Goal

Replace the inline DSR handling in `TerminalManager` with a
`TerminalProbeResponder` helper that detects terminal probe requests
and builds responses without changing current terminal behavior.

When done:

- `TerminalManager` no longer defines `_respond_to_dsr`.
- DSR response construction lives in
  `src/actcli/bench_textual/instrumentation/probe_responder.py`.
- `TerminalProbeResponder.response_for_text(text, emulator)` returns
  `str | None`.
- `ESC[6n` with a pyte emulator and cursor returns
  `ESC[{row};{col}R` using 1-based coordinates.
- No query, non-pyte mode, missing cursor, or malformed emulator state
  returns `None` without raising.

## Why Now

The first instrumentation sprint extracted `WriteTraceLogger` and
closed with PASS. This sprint uses the same package boundary for the
next ad-hoc diagnostic behavior called out in the cursor/PTY
postmortem and `docs/INSTRUMENTATION_REFACTOR.md`.

## Scope Fence

Expected touch set:

- `src/actcli/bench_textual/instrumentation/probe_responder.py` (new)
- `src/actcli/bench_textual/instrumentation/__init__.py`
- `src/actcli/bench_textual/terminal_manager.py`
- `tests/bench_textual/test_probe_responder.py` (new)
- `tests/bench_textual/test_terminal_manager_probe_responder.py` (new,
  or equivalent focused manager delegation tests)
- `docs/INSTRUMENTATION_REFACTOR.md`

Good scope:

- A small helper class with one public method:
  `response_for_text(text, emulator) -> str | None`
- Keeping write/logging side effects in `TerminalManager`
- Focused fake-emulator tests instead of spawning real PTYs
- Manager-level tests that prove DSR output still writes to the runner

Still out of scope:

- Write tracing changes
- Troubleshooting pack export changes
- CLI/config toggles
- Mouse mode replies, terminal identity replies, color queries, or
  other future probes
- pyte replacement, cursor heuristics, PTY sizing, or UI layout
- Changing `ESC[{row};{col}R` response format

## Acceptance Target

- `python3 -m pytest tests/bench_textual/test_probe_responder.py tests/bench_textual/test_terminal_manager_probe_responder.py -v`
  passes.
- `python3 -m pytest tests/bench_textual/test_app_integration.py -q`
  still passes.
- A direct helper smoke returns `'\x1b[5;7R'` for pyte cursor
  `y=4, x=6` and `'\x1b[6n'` input.
- A direct helper smoke returns `None` for no query and for non-pyte
  mode.
- A static check finds no `_respond_to_dsr` definition in
  `terminal_manager.py`.

## Honest-Failure Mode

If `response_for_text(text, emulator)` is too narrow or too coupled to
`EmulatedTerminal`, record the design concern in the result note and
propose the smallest alternative. Do not widen this sprint into mouse
mode support, terminal identity replies, or troubleshooting pack work.

## Hosts

- coding host: `Acer-HL`
- validation host: `iMacDebian`
- orchestration host: local Codex/Claude session on the user's primary
  workstation

## Host Safety

No protected production services are involved in this sprint. Standard
host safety still applies:

- do not commit host-local Claude/Codex memory
- do not commit generated changes to `docs/Trouble-Snaps/`
- do not stop or kill processes outside this repo's spawned test
  process tree
- keep all probes local to the repo checkout
