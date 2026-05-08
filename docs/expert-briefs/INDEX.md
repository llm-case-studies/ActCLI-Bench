# Initiative Index

Cross-initiative table of work in flight. One row per initiative.

## Status Vocabulary

- `planning` - folder exists, no active sprint issued yet
- `active` - at least one sprint is ready for implementation or in
  implementation
- `queued` - no active sprint; next sprint candidate is written down
- `paused` - intentionally waiting on a host, dependency, or decision
- `completed` - initiative goal met, no open sprints

## Initiatives

| Initiative | Status | Active sprint | Notes |
|---|---|---|---|
| `instrumentation` | queued | none | First helper extraction completed with PASS; next candidate is `2026-05-08_extract-probe-responder` |

## Cross-Cutting Concerns

- ActCLI-TE alignment: helper interfaces extracted here should be
  straightforward for ActCLI-TE to mirror.
- Generated diagnostic files: current tests can mutate
  `docs/Trouble-Snaps/write_debug.log`; keep those changes out of
  commits unless the sprint explicitly updates evidence.
