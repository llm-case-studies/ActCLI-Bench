# Sprint Brief - Extract WriteTraceLogger

**Initiative:** `instrumentation`
**Sprint:** `2026-05-08_extract-write-trace-logger`
**Target branch:** `feature/instrumentation/extract-write-trace-logger`
**Merge target:** `main`
**Validation branch:** `validation/instrumentation/extract-write-trace-logger`

## Goal

Replace the inline `_append_write_debug` call inside
`TerminalRunner.write` with a `WriteTraceLogger` helper that owns trace
sinks, can be toggled by environment variable, and exposes a small
interface ActCLI-TE can mirror.

When done:

- `terminal_runner.py` calls a logger object to record writes and no
  longer contains the hardcoded trace path or private open/write helper.
- `WriteTraceLogger` lives under
  `src/actcli/bench_textual/instrumentation/`.
- The helper supports file, in-memory, and debug-callback sinks.
- `ACTCLI_WRITE_TRACE=1` enables the file sink using the existing path
  default. Unset, empty, or `0` disables file writes.
- The on-disk line format stays `{name}: {repr(data)}\n`.

## Why Now

The cursor/PTY postmortem proved that write tracing is valuable, but
the current implementation appends to a tracked file by default. This
is a small first instrumentation sprint that establishes the branch,
handoff, validation, and evidence rhythm for ActCLI-Bench.

## Scope Fence

Expected touch set:

- `src/actcli/bench_textual/instrumentation/__init__.py` (new)
- `src/actcli/bench_textual/instrumentation/write_trace_logger.py` (new)
- `src/actcli/bench_textual/terminal_runner.py`
- `tests/bench_textual/test_write_trace_logger.py` (new)
- `docs/INSTRUMENTATION_REFACTOR.md`

Good scope:

- A simple sink protocol or base class if it keeps the code clearer
- Env-var resolution at construction time
- Best-effort file writes equivalent to today's behavior
- Tests for enabled/disabled behavior, sink behavior, format
  preservation, and unwritable-path degradation

Still out of scope:

- Touching `_respond_to_dsr` or other probe reply code
- Changing `docs/Trouble-Snaps/` layout
- Updating troubleshooting pack export
- Adding CLI flags such as `--trace-writes`
- Changing terminal emulator, pyte, PTY sizing, or cursor behavior
- Replacing `repr()` format with JSON or another structured format

## Acceptance Target

- `python3 -m pytest tests/bench_textual/test_write_trace_logger.py -v`
  passes.
- `python3 -m pytest tests/bench_textual/test_terminal_runner.py -q`
  still passes.
- `rg -n "docs/Trouble-Snaps/write_debug.log" src/actcli/bench_textual/terminal_runner.py`
  returns no matches.
- With `ACTCLI_WRITE_TRACE=1`, a small direct PTY write smoke creates
  `docs/Trouble-Snaps/write_debug.log` with lines matching
  `{name}: {repr(data)}`.
- With `ACTCLI_WRITE_TRACE` unset, the same smoke creates no
  `write_debug.log` and appends nothing to a pre-existing file.

## Honest-Failure Mode

If the file, memory, and debug-callback sinks do not share a clean
contract, record the problem in the result note and implement the
smallest honest subset rather than expanding the sprint. Do not absorb
probe responder extraction or troubleshooting pack work into this
branch.

## Hosts

- coding host: `Acer-HL`
- validation host: `iMacDebian`
- orchestration host: local Codex/Claude session on the user's primary
  workstation

## Host Safety

No protected production services are involved in this sprint. Standard
host safety still applies:

- do not commit host-local Claude/Codex memory
- do not commit generated changes to
  `docs/Trouble-Snaps/write_debug.log`
- do not stop or kill processes outside this repo's spawned test
  process tree
- keep all manual probes local to the repo checkout
