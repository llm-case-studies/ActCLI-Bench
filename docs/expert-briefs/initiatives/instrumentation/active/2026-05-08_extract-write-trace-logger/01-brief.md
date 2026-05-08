# Sprint Brief - Extract WriteTraceLogger

**Initiative:** `instrumentation`
**Sprint:** `2026-05-08_extract-write-trace-logger`
**Target branch:** `feature/instrumentation/extract-write-trace-logger`
**Merge target:** `main`
**Validation branch:** `validation/instrumentation/extract-write-trace-logger`

## Goal

Replace the inline `_append_write_debug` call inside
`TerminalRunner.write` with a `WriteTraceLogger` helper that owns its
sink, can be toggled by environment variable, and exposes an interface
ActCLI-TE can mirror without copy-paste.

When done:

- `terminal_runner.py` calls `WriteTraceLogger.record(name, data)` and
  contains no file-path string or best-effort `try/except open` block
  for tracing.
- `WriteTraceLogger` lives in `src/actcli/bench_textual/instrumentation/`
  and supports at least three sinks: rotating file, in-memory deque,
  and the existing debug-logger callback.
- `ACTCLI_WRITE_TRACE=1` enables the file sink with the existing path
  default. Unset (or `0`) disables file writes entirely. The default
  in tests and CI should be **disabled**.
- The on-disk format stays `{name}: {repr(data)}\n` so existing
  troubleshooting packs and grep recipes still work.
- Unit tests cover: enabled vs disabled, each sink, format
  preservation, and graceful degradation when the file path is
  unwritable.

## Why Now

The cursor/PTY postmortem closed but left the bench depending on
ad-hoc instrumentation. The instrumentation initiative is now seeded
(`docs/INSTRUMENTATION_REFACTOR.md`) and ActCLI-TE bootstrap planning
is starting (`docs/ACTCLI-TE_TRACKING.md`). This sprint sets the
helper shape both projects will use.

This is also the first real sprint exercising the sprint-pack process
in this repo, so deliberately small scope is part of the goal.

## Scope Fence

Expected touch set:

- `src/actcli/bench_textual/instrumentation/__init__.py` (new)
- `src/actcli/bench_textual/instrumentation/write_trace_logger.py` (new)
- `src/actcli/bench_textual/terminal_runner.py` (remove
  `_append_write_debug`, call helper instead)
- `tests/bench_textual/test_write_trace_logger.py` (new)
- `docs/INSTRUMENTATION_REFACTOR.md` (tick the WriteTraceLogger box)

Good scope:

- Defining the sink interface (one Protocol or abc, your call —
  judgment expected, see Honest-Failure Mode)
- Env-var resolution at logger construction, not per-call
- Threading-safety equivalent to today's behaviour (single best-effort
  open per call is fine; do not over-engineer locking)

Still out of scope:

- Touching `_respond_to_dsr` or any probe-reply code
- Changing `docs/Trouble-Snaps/` layout or the export script
- Adding CLI flags (`--trace-writes`) — env var only this sprint
- Replacing `repr()` formatting with structured JSON (would break
  existing tools)
- Touching pyte, the emulator, or PTY sizing logic

## Acceptance Target

- `pytest tests/bench_textual/test_write_trace_logger.py -v` passes
- `pytest tests/bench_textual/test_terminal_manager.py` (existing
  tests) still passes — the runner refactor must not regress them
- `grep -rn "docs/Trouble-Snaps/write_debug.log"
  src/actcli/bench_textual/terminal_runner.py` returns nothing
- With `ACTCLI_WRITE_TRACE=1` and a brief bench session, the resulting
  `docs/Trouble-Snaps/write_debug.log` is byte-equivalent in format to
  the previous file (lines of `{name}: {repr(data)}`)
- With `ACTCLI_WRITE_TRACE` unset, no `write_debug.log` is created or
  appended

## Honest-Failure Mode

If the sink/Protocol design surfaces a real wart — e.g. the in-memory
sink wants a different signature than the file sink, or env-var
resolution clashes with how Textual loads config — push back in the
result note rather than papering over it. A clean two-sink minimum
(file + debug-logger forwarder) is acceptable as a checkpoint; the
in-memory sink can become a follow-up sprint if it materially
complicates the contract.

Do NOT widen scope to also touch `_respond_to_dsr` or the export
script. Those are the next two sprints' jobs and merging them
together would defeat the per-helper review pattern.

## Hosts

- coding host: `Acer-HL`
- validation host: `iMac-Debian`

## Host Safety

`Acer-HL` and `iMac-Debian` carry their respective dev environments;
no protected production services involved in this sprint. Standard
caveats from `docs/process/framework.md`:

- do not commit anything from `~/.claude/` or other host-local
  Claude state
- the `docs/Trouble-Snaps/` directory is in-tree but contents are
  generated; do not commit new generated logs from local runs
