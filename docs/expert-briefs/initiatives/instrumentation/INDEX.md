# Instrumentation - Sprint Index

## Active

| Sprint | Branch | Status | Coding host | Validation host |
|---|---|---|---|---|
| none | - | - | - | - |

## Queued

| Sprint | Why queued | Depends on |
|---|---|---|
| `2026-05-08_extract-probe-responder` | Move DSR and future terminal probe replies behind a helper | `extract-write-trace-logger` merged |
| `extract-troubleshooting-pack-builder` | Replace hardcoded troubleshooting paths with helper-driven collection | write tracer and probe responder merged |
| `wire-config-toggles` | Expose consistent config/CLI switches for instrumentation | helper set stabilized |

## Completed

| Sprint | Branch | Verdict | Notes |
|---|---|---|---|
| `2026-05-08_extract-write-trace-logger` | `feature/instrumentation/extract-write-trace-logger` | PASS | `WriteTraceLogger` extracted and validated on iMacDebian |
