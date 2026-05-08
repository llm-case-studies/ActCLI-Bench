# Merge Note - Extract TroubleshootingPackBuilder

## Branches

- working branch: `feature/instrumentation/extract-troubleshooting-pack-builder`
- merge target: `main`
- validation branch: `validation/instrumentation/extract-troubleshooting-pack-builder`

## Validation Outcome

- implementation host: `Acer-HL`
- validation host: `iMacDebian`
- tested product commit: `ec6a8a9`
- implementation commits:
  - `cf5bee6` - `docs: seed troubleshooting pack builder sprint`
  - `12a04ea` - `feat: extract TroubleshootingPackBuilder from DiagnosticsManager`
  - `ec6a8a9` - `docs: fill commit SHA in result template`
- validation evidence commits:
  - original validation branch: `75d84ea`
  - normalized evidence path commit: `cb3792c`
  - cherry-picked onto feature branch: `dc5a027`, `5625e4a`
- verdict: **PASS**
- result path:
  `testing/initiatives/instrumentation/2026-05-08_extract-troubleshooting-pack-builder/result.md`

## Evidence Summary

- `python -m pytest tests/bench_textual/test_troubleshooting_pack_builder.py tests/bench_textual/test_diagnostics_manager.py -v`:
  27 passed.
- `python -m pytest tests/bench_textual/test_app_integration.py -q`:
  12 passed.
- Static check found no `docs/Trouble-Snaps` or
  `troubleshooting_pack_` strings in `diagnostics.py`.
- Direct builder export smoke produced the expected timestamped pack
  file with required sections.
- `git status --short docs/Trouble-Snaps` was clean.
- Validation ran on iMacDebian with Python 3.13.5 in
  `/home/alex/.venvs/actcli-python`.

## Findings

- `TroubleshootingPackBuilder` now owns snapshot formatting, default
  export directory, timestamped filenames, optional write-trace
  inclusion, and deterministic clock injection for tests.
- `DiagnosticsManager` remains the app-facing coordinator and delegates
  generation/export to the builder without changing its constructor
  contract.
- The validator initially committed evidence under repo-root
  `evidence/`; the orchestrator added a follow-up commit moving those
  files into the sprint's testing evidence directory.

## Decision

- merge to `main`: yes
- close sprint: yes
- split follow-up: yes

## Follow-Up

- Promote `wire-config-toggles` as the next instrumentation sprint.
- Future validation requests should use full repo-relative evidence
  paths or explicitly `cd` into the sprint testing folder before
  writing `evidence/...` files.
