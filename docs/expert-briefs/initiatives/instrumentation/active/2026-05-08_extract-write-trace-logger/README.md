# Extract WriteTraceLogger

This sprint extracts `terminal_runner._append_write_debug` into a
reusable `WriteTraceLogger` helper with sink abstraction and env-var
toggle.

## Why This Sprint Exists

The cursor/PTY investigation in late October relied on
`docs/Trouble-Snaps/write_debug.log` to see what we wrote into the
PTY. The mechanism works but is hardcoded: the path is a string
literal in `terminal_runner.write`, the sink is always the same file,
and there is no way to disable it without a code change.

ActCLI-TE will need the same tracing capability when it wraps the
Rust vte parser. Keeping the helper in `terminal_runner.py` means TE
either copies the code or re-imports a private function. Extracting
it now — before TE starts consuming it — gives both projects a stable
shape to share.

## Read With It

- `01-brief.md`
- `00-opencode-kickoff.md`
- `testing/initiatives/instrumentation/2026-05-08_extract-write-trace-logger/request.md`
- `docs/INSTRUMENTATION_REFACTOR.md` (source plan)
- `src/actcli/bench_textual/terminal_runner.py` (current implementation)

## Out Of Scope

- Probe responder extraction (next sprint: `extract-probe-responder`)
- Troubleshooting pack builder rewiring
- CLI flag surface — env-var only for this sprint
- Changing the on-disk log format (`{name}: {repr(data)}\n`)

## After This Sprint

- `extract-probe-responder` — wraps `_respond_to_dsr` and future PTY
  probe replies under the same sink/toggle pattern
- `extract-troubleshooting-pack-builder` — rewires the export script
  to pull from the helper instead of hardcoded paths
