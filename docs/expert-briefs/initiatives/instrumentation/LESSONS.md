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
