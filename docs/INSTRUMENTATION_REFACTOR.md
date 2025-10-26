# Instrumentation Refactor Plan

## Goals
- Convert ad-hoc logging (PTY write traces, DSR responses, troubleshooting packs)
  into reusable helpers with configuration options.
- Prepare the instrumentation layer for reuse in ActCLI-TE so both projects share
  the same diagnostic tooling.

## Proposed Modules
1. **WriteTraceLogger**
   - Hooks into `TerminalRunner.write` to log payloads conditionally.
   - Supports multiple sinks (debug log, rotating file, in-memory buffer).
   - Toggle via config/env (`ACTCLI_WRITE_TRACE=1`).

2. **TerminalProbeResponder**
   - Centralise responses to PTY probes (`ESC[6n`, mouse modes, etc.).
   - Allow easy extension for future sequence replies.

3. **TroubleshootingPackBuilder**
   - Structured collector for snapshots (versions, terminals, write logs,
     screenshots).
   - Configurable scope (basic vs. extended) to avoid bloated packs.

## Bench Tasks
- [ ] Extract current write logging into `WriteTraceLogger` helper.
- [ ] Wrap DSR reply logic in `TerminalProbeResponder` and use it in
      `TerminalManager`.
- [ ] Update troubleshooting export to pull from the new helpers instead of
      hardcoded file paths.
- [ ] Provide CLI/config toggles so logging can be enabled without code changes.

## ActCLI-TE Alignment
- [ ] Mirror these helpers (or their interfaces) when building the Python-native
      engine so instrumentation works identically in both projects.
- [ ] Ensure ActCLI-TE exposes hooks for the bench to plug in custom sinks.
