# Initiative: Instrumentation

Convert ad-hoc PTY and terminal diagnostics into reusable helpers that
ActCLI-Bench can use directly and ActCLI-TE can mirror without copying
private functions.

## Why This Initiative Exists

The cursor and PTY postmortems left three useful but improvised
diagnostic surfaces:

- write tracing in `terminal_runner._append_write_debug`
- Device Status Report replies in `TerminalManager._respond_to_dsr`
- troubleshooting pack collection through hardcoded paths

Those pieces helped close the cursor investigation, but they are not
cleanly toggleable, not packaged as helpers, and not shaped for reuse
by ActCLI-TE.

## Source Plan

The source task list is `docs/INSTRUMENTATION_REFACTOR.md`. This
initiative breaks that list into small sprints so each helper can land
with focused tests and independent validation evidence.

## Roadmap

1. `extract-write-trace-logger` - completed with PASS
2. `extract-probe-responder` - completed with PASS
   probe replies
3. `extract-troubleshooting-pack-builder` - queued now that the first
   two helpers exist
4. `wire-config-toggles` - later config/CLI surface across helpers

## Initiative-Wide Non-Goals

- Replacing pyte or changing terminal emulation semantics
- Expanding the Textual bench UI
- Reworking troubleshooting pack layout before helper extraction lands
- Changing existing write-trace line format
