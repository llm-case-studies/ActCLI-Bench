# Extract Probe Responder

Move Device Status Report handling and future terminal probe replies
out of `TerminalManager` into a named helper.

## Why This Sprint Exists

`TerminalManager._respond_to_dsr` currently answers `ESC[6n` inline.
That belongs beside the write-trace helper as instrumentation, but it
was intentionally left out of the first sprint to keep the write-trace
change reviewable. The first helper is now closed with PASS, so the
next piece of ad-hoc instrumentation can move behind the same package
boundary.

## Read With It

- `01-brief.md`
- `00-opencode-kickoff.md`
- `testing/initiatives/instrumentation/2026-05-08_extract-probe-responder/request.md`
- `src/actcli/bench_textual/terminal_manager.py`
- `src/actcli/bench_textual/instrumentation/write_trace_logger.py`
- `docs/POSTMORTEM_CURSOR_PTY.md`
- `docs/INSTRUMENTATION_REFACTOR.md`

## Scope

- Add `src/actcli/bench_textual/instrumentation/probe_responder.py`.
- Move DSR response detection and response construction behind a small
  helper.
- Keep the current `ESC[{row};{col}R` behavior unchanged.
- Add unit tests for pyte cursor response, no-query no-op, non-pyte
  no-op, missing cursor no-op, and `TerminalManager` delegation.
- Leave write tracing and troubleshooting packs untouched.

## After This Sprint

The next likely sprint is `extract-troubleshooting-pack-builder`,
which can start using the helper package after both write tracing and
probe responses have landed.
