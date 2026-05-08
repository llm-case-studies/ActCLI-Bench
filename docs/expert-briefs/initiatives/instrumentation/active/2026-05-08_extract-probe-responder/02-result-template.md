# Result - Extract Probe Responder

- Implementation host:
- Working branch:
- Commit SHA:

## Changes

-

## Helper Design

- Public responder entry point:
- Inputs:
- Response cases:
- No-op cases:
- TerminalManager integration:

## Local Smoke

- `python3 -m pytest tests/bench_textual/test_probe_responder.py tests/bench_textual/test_terminal_manager_probe_responder.py -v`:
- `python3 -m pytest tests/bench_textual/test_app_integration.py -q`:
- direct helper smoke, DSR pyte cursor:
- direct helper smoke, no query:
- direct helper smoke, non-pyte:
- static check for `_respond_to_dsr` in `terminal_manager.py`:

## Tests Added

-

## Pushback / Findings

-

## Blockers / Open Questions

-

## Validation Hand-Off

- testing request reviewed: yes / no
- next host: `iMacDebian`
- product branch pushed: yes / no
