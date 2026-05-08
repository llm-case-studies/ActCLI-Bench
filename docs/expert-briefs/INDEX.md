# Initiative Index

Cross-initiative table of work in flight. One row per initiative.

## Status Vocabulary

- `planning` - folder exists, no active sprint issued yet
- `active` - at least one sprint is ready for implementation or in
  implementation
- `paused` - intentionally waiting on a host, dependency, or decision
- `completed` - initiative goal met, no open sprints

## Initiatives

| Initiative | Status | Active sprint | Notes |
|---|---|---|---|
| `instrumentation` | active | `2026-05-08_extract-write-trace-logger` | First helper extraction; establishes the Acer-HL implementation and iMacDebian validation cadence |

## Cross-Cutting Concerns

- ActCLI-TE alignment: helper interfaces extracted here should be
  straightforward for ActCLI-TE to mirror.
- Generated diagnostic files: current tests can mutate
  `docs/Trouble-Snaps/write_debug.log`; keep those changes out of
  commits unless the sprint explicitly updates evidence.
