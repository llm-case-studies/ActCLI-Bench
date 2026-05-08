# Result - Extract Probe Responder

- Implementation host: Acer-HL
- Working branch: feature/instrumentation/extract-probe-responder
- Commit SHA: 91cf3846993dbe8d1116be0ae3ae25fd9806a963

## Changes

- New file: `src/actcli/bench_textual/instrumentation/probe_responder.py`
- Updated: `src/actcli/bench_textual/instrumentation/__init__.py`
- Updated: `src/actcli/bench_textual/terminal_manager.py`
- New file: `tests/bench_textual/test_probe_responder.py`
- New file: `tests/bench_textual/test_terminal_manager_probe_responder.py`

## Helper Design

- Public responder entry point: `TerminalProbeResponder.response_for_text(text, emulator) -> str | None`
- Inputs: `text` (raw terminal output string), `emulator` (duck-typed object with `mode`, `_screen`, and `_screen.cursor`)
- Response cases: `ESC[6n` + pyte mode + cursor → `ESC[{row};{col}R` with 1-based coordinates
- No-op cases: no `ESC[6n` in text, non-"pyte" mode, missing `_screen`, missing `cursor`
- TerminalManager integration: creates a `TerminalProbeResponder` in `__init__`, calls `response_for_text` in `_append_terminal_output`, writes response and logs it from the manager side

## Local Smoke

- `python3 -m pytest tests/bench_textual/test_probe_responder.py tests/bench_textual/test_terminal_manager_probe_responder.py -v`: 12 passed
- `python3 -m pytest tests/bench_textual/test_app_integration.py -q`: 12 passed
- direct helper smoke, DSR pyte cursor: `'\x1b[5;7R'` (confirmed)
- direct helper smoke, no query: `None` (confirmed)
- direct helper smoke, non-pyte: `None` (confirmed)
- static check for `_respond_to_dsr` in `terminal_manager.py`: no matches (exit 0)

## Tests Added

- `tests/bench_textual/test_probe_responder.py`: 8 tests covering DSR response, no-query, non-pyte mode, missing screen, missing cursor, zero→one-based conversion, malformed emulator, None emulator
- `tests/bench_textual/test_terminal_manager_probe_responder.py`: 4 tests covering manager delegation (DSR writes response), no-write-on-no-query, no-write-on-non-pyte, static `_respond_to_dsr` absence check

## Pushback / Findings

- None. The `response_for_text(text, emulator)` interface is clean and supports the existing call site without awkward coupling.

## Blockers / Open Questions

- None.

## Validation Hand-Off

- testing request reviewed: yes
- next host: `iMacDebian`
- product branch pushed: yes
