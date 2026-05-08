# Instrumentation — Lessons

Running log of lessons specific to this initiative. Append as sprints
close; do not rewrite earlier entries.

## 2026-05-08 — initiative seeded

- Three-helper plan from `docs/INSTRUMENTATION_REFACTOR.md` sliced into
  four sprints (one per helper, plus a config-wiring sprint at the
  end). Doing all three in one sprint risked a fence too wide for one
  reviewer pass.
- Decision: ship `WriteTraceLogger` first because its current home
  (`terminal_runner._append_write_debug`) has the least entanglement
  and the clearest rotating-file/in-memory sink shape.
