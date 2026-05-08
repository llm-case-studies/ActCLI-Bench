# Instrumentation Lessons

Append initiative-specific lessons here as sprints close.

## 2026-05-08

- Keep write-trace format stable as `{name}: {repr(data)}\n`; existing
  troubleshooting notes and grep recipes assume that shape.
- The first helper should prove the pattern without touching DSR,
  troubleshooting pack export, pyte behavior, or UI layout.
- Declaring `pytest` as a `test` extra kept validation local to the
  repo environment and avoided system package installation on
  iMacDebian.
- The probe responder sprint exposed a pre-existing app-integration
  test dependency gap: asyncio variants pass, while trio variants fail
  when `trio` is not installed. Treat this as validation-procedure
  debt rather than a probe responder regression.
- Shared user-level validation envs work well for this repo: iMacDebian
  reused `/home/alex/.venvs/actcli-python` with Python 3.13.5 and
  repo-declared extras instead of touching system Python.
- Validation requests should avoid ambiguous `evidence/...` paths when
  the testing folder is nested. Use full repo-relative paths or tell
  the validator to `cd` into the sprint testing directory first.
