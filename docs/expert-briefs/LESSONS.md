# Cross-Initiative Lessons

Append reusable lessons here when a sprint teaches something future
ActCLI-Bench sessions should not rediscover.

## 2026-05-08

- Host-local agent memory is not portable enough for orchestration.
  Sprint state belongs in repo files under `docs/expert-briefs/` and
  `testing/initiatives/`.
- A smoke test of the current terminal runner appends to the tracked
  `docs/Trouble-Snaps/write_debug.log`, which is itself evidence for
  the first instrumentation sprint's env-var toggle.
- Validation prompts should avoid assuming globally installed tools.
  `pytest` now lives in the repo's `test` extra, and validation checks
  should prefer Python standard-library probes over host-specific
  command-line dependencies when either works.
- App integration tests currently try both `asyncio` and `trio`
  backends on iMacDebian, but `trio` is not installed there. Future
  validation requests should either install the full async test backend
  set or explicitly run the supported `asyncio` backend.
- Shared user-level Python envs by stack are a good default for
  validator hosts: they avoid mutating system Python without creating a
  new `.venv` in every repo.
- Evidence paths in validation requests should be full repo-relative
  paths when the testing folder is nested; bare `evidence/...` is too
  easy to interpret as repo-root.
