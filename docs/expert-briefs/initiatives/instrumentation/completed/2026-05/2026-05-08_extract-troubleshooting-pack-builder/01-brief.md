# Sprint Brief - Extract TroubleshootingPackBuilder

**Initiative:** `instrumentation`
**Sprint:** `2026-05-08_extract-troubleshooting-pack-builder`
**Target branch:** `feature/instrumentation/extract-troubleshooting-pack-builder`
**Merge target:** `main`
**Validation branch:** `validation/instrumentation/extract-troubleshooting-pack-builder`

## Goal

Move troubleshooting snapshot collection and file export out of
`DiagnosticsManager` into a reusable
`src/actcli/bench_textual/instrumentation/troubleshooting_pack_builder.py`
helper without changing current Bench behavior.

When done:

- `DiagnosticsManager` remains the app-facing coordinator for key-event
  recording, troubleshooting-log updates, and export calls.
- Snapshot formatting and timestamped file writing live in
  `TroubleshootingPackBuilder`.
- `DiagnosticsManager.export_to_file()` delegates to the builder and no longer
  hardcodes `docs/Trouble-Snaps` or `troubleshooting_pack_`.
- Existing troubleshooting pack sections remain present: timestamp, versions,
  app state, terminals, recent logs, key events, and navigation rebuild history.
- The builder is exported from `src/actcli/bench_textual/instrumentation/__init__.py`.

## Why Now

The first two instrumentation sprints extracted write tracing and DSR probe
response logic into `src/actcli/bench_textual/instrumentation/` and both passed
validation. The remaining ad-hoc diagnostic surface is troubleshooting pack
generation. Extracting it now gives the next sprint a cleaner place to wire
config toggles without making `DiagnosticsManager` a catch-all.

## Scope Fence

Expected touch set:

- `src/actcli/bench_textual/instrumentation/troubleshooting_pack_builder.py`
- `src/actcli/bench_textual/instrumentation/__init__.py`
- `src/actcli/bench_textual/diagnostics.py`
- `tests/bench_textual/test_troubleshooting_pack_builder.py`
- `tests/bench_textual/test_diagnostics_manager.py`
- `docs/INSTRUMENTATION_REFACTOR.md`

Good scope:

- A small helper class with clear public methods for building snapshot text and
  exporting it to a target directory.
- A default export directory constant that lives with the helper, not in
  `DiagnosticsManager`.
- Optional builder support for including recent write-trace lines by reading
  the path exposed by `WriteTraceLogger.DEFAULT_TRACE_PATH`, as long as missing
  files are handled quietly.
- Dependency injection for time/clock in tests so timestamped filenames are
  deterministic.
- Focused tests with fake terminal/log/nav objects.

Still out of scope:

- CLI/config toggles for write tracing or troubleshooting export.
- Screenshots, binary artifacts, zip files, or pack compression.
- UI layout or navigation-tree changes.
- Changing `WriteTraceLogger` behavior or trace format.
- Changing `TerminalProbeResponder` behavior.
- Moving `DiagnosticsManager` itself into the instrumentation package.
- Touching historical files under `docs/Trouble-Snaps/`.

## Acceptance Target

- `python -m pytest tests/bench_textual/test_troubleshooting_pack_builder.py tests/bench_textual/test_diagnostics_manager.py -v`
  passes.
- `python -m pytest tests/bench_textual/test_app_integration.py -q` passes.
- A direct builder smoke writes a timestamped
  `troubleshooting_pack_<YYYYMMDDTHHMMSSZ>.txt` file under a temporary
  directory and the file contains `versions:`, `terminals:`, and
  `---- recent events ----`.
- Static check finds no `docs/Trouble-Snaps` or `troubleshooting_pack_` string
  in `src/actcli/bench_textual/diagnostics.py`.
- `git status --short` shows no generated changes under `docs/Trouble-Snaps/`.
- `docs/INSTRUMENTATION_REFACTOR.md` marks the troubleshooting export checkbox
  complete only if the helper delegation is implemented and tested.

## Honest-Failure Mode

If the proposed builder boundary forces awkward coupling or duplicate state,
record the concern in the result note and propose the smallest alternative.
Do not widen this sprint into config toggles, screenshots, UI changes, or
ActCLI-TE mirroring.

## Hosts

- coding host: `Acer-HL`
- validation host: `iMacDebian`
- orchestration host: local Codex/Claude session on the user's primary
  workstation

## Host Safety

No protected production services are involved in this sprint. Standard host
safety still applies:

- do not commit host-local Claude/Codex memory
- do not commit generated changes to `docs/Trouble-Snaps/`
- do not stop or kill processes outside this repo's spawned test process tree
- keep all probes local to the repo checkout
- use the shared user-level Python environment policy in
  `docs/process/environment.md`; do not install project dependencies into
  system Python
