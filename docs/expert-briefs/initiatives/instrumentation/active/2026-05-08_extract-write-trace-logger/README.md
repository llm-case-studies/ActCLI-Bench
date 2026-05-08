# Extract WriteTraceLogger

This sprint extracts the current write-debug helper from
`terminal_runner.py` into a reusable `WriteTraceLogger` with explicit
sinks and an `ACTCLI_WRITE_TRACE` env-var toggle.

## Why This Sprint Exists

The October cursor/PTY work proved that a persisted write trace is very
useful. Today that trace is hardcoded in `TerminalRunner.write`, writes
to a tracked file by default, and cannot be disabled without code
changes. This sprint makes the behavior intentional and testable.

## Read With It

- `01-brief.md`
- `00-opencode-kickoff.md`
- `testing/initiatives/instrumentation/2026-05-08_extract-write-trace-logger/request.md`
- `docs/INSTRUMENTATION_REFACTOR.md`
- `docs/POSTMORTEM_CURSOR_PTY.md`
- `src/actcli/bench_textual/terminal_runner.py`

## Out Of Scope

- Probe responder extraction
- Troubleshooting pack builder rewiring
- CLI flags or persistent config files
- Changing the on-disk write-trace format
- Terminal emulator, pyte, or PTY sizing changes

## After This Sprint

Promote `queued/2026-05-08_extract-probe-responder/` into `active/`
and reuse this same branch, result, validation, and merge-note rhythm.
