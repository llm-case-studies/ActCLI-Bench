# Merge Note - Extract Probe Responder

## Branches

- working branch: `feature/instrumentation/extract-probe-responder`
- merge target: `main`
- validation branch: `validation/instrumentation/extract-probe-responder`

## Validation Outcome

- implementation host: `Acer-HL`
- validation host: `iMacDebian`
- tested product commit: `a5c9c3e`
- implementation commits:
  - `6e55741` - `docs: seed probe responder sprint pack`
  - `a5c9c3e` - `feat: extract probe responder from TerminalManager`
- validation evidence commits:
  - original validation branch: `442e668`
  - normalized evidence commit on feature branch: `acf44c2`
- verdict: **PASS**
- result path:
  `testing/initiatives/instrumentation/2026-05-08_extract-probe-responder/result.md`

## Evidence Summary

- Probe responder and manager delegation tests: 12 passed.
- App integration regression: 9 asyncio variants passed; 9 trio
  variants failed because `trio` is not installed on iMacDebian.
  Validator marked this as pre-existing host dependency debt, not a
  probe responder regression.
- Static check confirmed `_respond_to_dsr` is no longer defined in
  `terminal_manager.py`.
- Direct DSR smoke returned `'\x1b[5;7R'` for pyte cursor
  `y=4, x=6`.
- No-query and non-pyte smokes returned `None`.
- Host safety: no `docs/Trouble-Snaps/` files modified, no unrelated
  services or shells disturbed, no persistent ports bound.

## Findings

- Validation evidence was initially committed under a root `evidence/`
  directory on the validation branch. The orchestrator normalized it
  into
  `testing/initiatives/instrumentation/2026-05-08_extract-probe-responder/evidence/`
  before merging.
- The app-integration test command needs a follow-up cleanup: either
  include `trio` in the repo test dependencies or run only the
  supported asyncio backend in validation.

## Decision

- merge to `main`: yes
- close sprint: yes
- split follow-up: yes

## Follow-Up

- Add a small validation-procedure cleanup for the app-integration
  async backend dependency before relying on that test as a hard gate.
- Next instrumentation sprint candidate:
  `extract-troubleshooting-pack-builder`.
