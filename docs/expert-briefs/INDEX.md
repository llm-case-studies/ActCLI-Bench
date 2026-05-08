# Initiative Index

Cross-initiative table of work in flight. One row per initiative.

## Status vocabulary

- **planning** — folder exists, no sprint authored yet
- **active** — at least one sprint in `active/`
- **paused** — work intentionally on hold; reason recorded in
  initiative `LESSONS.md`
- **completed** — initiative goal met, no open sprints

## Initiatives

| Initiative | Status | Active sprint | Notes |
|---|---|---|---|
| `instrumentation` | active | `2026-05-08_extract-write-trace-logger` | First helper extraction; sets pattern for probe responder + pack builder follow-ups |

## Cross-cutting concerns

- ActCLI-TE alignment: helpers extracted here should keep interfaces
  the Rust engine can mirror. See `docs/ACTCLI-TE_TRACKING.md`.
