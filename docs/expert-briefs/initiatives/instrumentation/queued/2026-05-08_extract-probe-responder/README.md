# Queued Sprint: Extract Probe Responder

Move Device Status Report handling and future terminal probe replies
out of `TerminalManager` into a named helper.

## Why It Is Queued

`TerminalManager._respond_to_dsr` currently answers `ESC[6n` inline.
That belongs beside the write-trace helper as instrumentation, but it
should wait until the first sprint proves the helper package layout and
validation flow.

## Likely Scope

- Add `src/actcli/bench_textual/instrumentation/probe_responder.py`.
- Move DSR response construction behind a small helper.
- Keep the current `ESC[{row};{col}R` behavior unchanged.
- Add unit tests for pyte cursor response and non-pyte no-op behavior.
- Leave write tracing and troubleshooting packs untouched.

## Activation Condition

Promote this folder to `active/` after
`2026-05-08_extract-write-trace-logger` closes and its merge note is
committed.
