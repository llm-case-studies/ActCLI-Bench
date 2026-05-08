# Result - Extract TroubleshootingPackBuilder

## Summary

Extracted troubleshooting snapshot collection and file export from
`DiagnosticsManager` into a reusable `TroubleshootingPackBuilder` helper in
`src/actcli/bench_textual/instrumentation/`. Snapshot formatting, timestamped
file writing, and the default export directory now live in the builder.
`DiagnosticsManager` remains the app-facing coordinator, delegating snapshot
generation and export to the builder via a clean API. A `nav_tree` property
on DiagnosticsManager propagates runtime assignment to the builder. Optional
write-trace line inclusion is supported via a builder toggle.

## Product Commit

- branch: `feature/instrumentation/extract-troubleshooting-pack-builder`
- commit: (to be filled after push)

## Checks Run

- `python -m pytest tests/bench_textual/test_troubleshooting_pack_builder.py tests/bench_textual/test_diagnostics_manager.py -v`: 27 passed
- `python -m pytest tests/bench_textual/test_app_integration.py -q`: 12 passed
- direct builder export smoke: writes `troubleshooting_pack_20260508T123456Z.txt` with all expected sections
- static diagnostics hardcoded-path check: no `docs/Trouble-Snaps` or `troubleshooting_pack_` in diagnostics.py
- `git status --short docs/Trouble-Snaps/`: empty (no generated changes)

## Behavior Notes

- All existing pack sections preserved: timestamp, versions, app state,
  terminals, recent logs (events/errors/debug/output), key events, navigation
  rebuild history
- Export naming unchanged: `troubleshooting_pack_<YYYYMMDDTHHMMSSZ>.txt`
- `DiagnosticsManager` constructor signature unchanged (compatible with app.py)
- `export_to_file()` default target_dir now `None` — builder supplies
  `DEFAULT_EXPORT_DIR` ("docs/Trouble-Snaps")
- `DiagnosticsManager.nav_tree` is a property that propagates to the builder

## Pushback Or Blockers

None.

## Validation Handoff

Ready for:

`validation/instrumentation/extract-troubleshooting-pack-builder`
