# Initiative: Instrumentation

Convert ad-hoc PTY/terminal logging into reusable helpers that both
ActCLI-Bench and ActCLI-TE can share.

## Why this initiative exists

The cursor/PTY postmortem (`docs/POSTMORTEM_CURSOR_PTY.md`) and the
ActCLI-TE plan both depend on having clean, toggleable instrumentation.
Today the bench has three bundles of ad-hoc code:

1. **Write tracing** — `terminal_runner._append_write_debug` writes
   raw payloads to `docs/Trouble-Snaps/write_debug.log`.
2. **PTY probe replies** — `TerminalManager._respond_to_dsr` answers
   `ESC[6n` cursor-position queries inline; future probes (mouse mode,
   terminal-id) need somewhere to live.
3. **Troubleshooting packs** — the export script collects screenshots,
   logs, and version info via hardcoded paths.

Each works, but none can be reused by ActCLI-TE or toggled cleanly
from config. This initiative extracts them into named helpers with
sink abstractions and env-var toggles.

## Source plan

See `docs/INSTRUMENTATION_REFACTOR.md` for the original task list. This
initiative breaks that list into one sprint per helper so each can
land independently.

## Sprint roadmap

1. **`extract-write-trace-logger`** — first sprint, currently `active/`
2. **`extract-probe-responder`** — wrap DSR + future probes
3. **`extract-troubleshooting-pack-builder`** — replace hardcoded paths
4. **`wire-config-toggles`** — CLI/config surface for all three

Cross-initiative dependency: ActCLI-TE will mirror the helper
interfaces, so each sprint should land a stable signature before the
TE side starts consuming it.

## Out of scope (initiative-wide)

- Changing PTY behaviour or terminal emulation logic
- Switching off pyte; that lives in the `terminal-engine` initiative
  (not yet seeded — will follow ActCLI-TE milestones)
- Replacing the LogManager — these helpers are diagnostics, separate
  from the application log surface
