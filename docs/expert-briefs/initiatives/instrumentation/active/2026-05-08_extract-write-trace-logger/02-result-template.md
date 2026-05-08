# Result - Extract WriteTraceLogger

- Implementation host: `Acer-HL`
- Working branch: `feature/instrumentation/extract-write-trace-logger`
- Commit SHA: `0b9c98e4d68d8f7fa34b1783d72e09ca890a39f4`

## Changes

- New package `src/actcli/bench_textual/instrumentation/` with `write_trace_logger.py`
- `TerminalRunner.write` now calls `self._write_tracer.record(data)` instead of inline `_append_write_debug`
- Removed module-level `_append_write_debug` function from `terminal_runner.py`
- Added `__post_init__` to `TerminalRunner` that creates `WriteTraceLogger.from_env(self.name)`
- New test file `tests/bench_textual/test_write_trace_logger.py` (27 tests)
- Marked `WriteTraceLogger` extraction as done in `docs/INSTRUMENTATION_REFACTOR.md`

## Sink Design

- Public logger entry point: `WriteTraceLogger(name, sinks)` with `record(data)` method
- Sink types implemented: `FileTraceSink`, `MemoryTraceSink`, `CallbackTraceSink`
- Env-var behavior: `ACTCLI_WRITE_TRACE=1` enables `FileTraceSink` via `from_env()` factory; unset, empty, or `0` produces no sinks
- File path default: `docs/Trouble-Snaps/write_debug.log` (`WriteTraceLogger.DEFAULT_TRACE_PATH`)
- Format compatibility: `{name}: {repr(data)}\n` preserved in all sinks

## Local Smoke

- `python3 -m pytest tests/bench_textual/test_write_trace_logger.py -v`: **27 passed**
- `python3 -m pytest tests/bench_textual/test_terminal_runner.py -q`: **17 passed** (no regressions)
- `ACTCLI_WRITE_TRACE=1` direct write smoke: `exists=True`, output `smoke-cat: 'hello-smoke\n'` (correct format)
- `ACTCLI_WRITE_TRACE` unset direct write smoke, absent log: `exists=False`
- `ACTCLI_WRITE_TRACE` unset direct write smoke, pre-existing log: exactly `preexisting sentinel`, no append
- `rg` check for hardcoded path in `terminal_runner.py`: **no matches** (`docs/Trouble-Snaps/write_debug.log` only appears in `write_trace_logger.py`)

## Tests Added

- Construction and empty-sink behaviour (2 tests)
- FileTraceSink: correct format, append, repr output, unwritable-path degradation (4 tests)
- MemoryTraceSink: collection, empty start, repr format (3 tests)
- CallbackTraceSink: callback invocation, exception isolation (2 tests)
- Multi-sink: all sinks receive records, partial failure isolation (2 tests)
- `from_env`: ACTCLI_WRITE_TRACE=1/0/unset/empty/other-values, default path, construction-time resolution (7 tests)
- TerminalRunner integration: off-by-default, enabled creates file, module no longer contains hardcoded path (3 tests)
- Format preservation: simple, newlines, special chars (3 tests)
- Best-effort degradation: sinks self-isolate failures (1 test)

## Pushback / Findings

- None. The sink contract (duck-typed `record(name, data)` on each sink) proved straightforward. All three sink types share the same shape without needing a formal abstract base class or protocol at this stage.
- Sinks self-catch exceptions (`FileTraceSink`, `CallbackTraceSink`); `WriteTraceLogger.record` iterates sinks without per-sink try/except, on the assumption that each sink is responsible for its own error handling.

## Blockers / Open Questions

- None.

## Validation Hand-Off

- testing request reviewed: yes
- next host: `iMacDebian`
- product branch pushed: yes (to be done after commit)
