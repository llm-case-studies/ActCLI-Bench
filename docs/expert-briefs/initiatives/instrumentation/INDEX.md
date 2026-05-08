# Instrumentation - Sprint Index

## Active

| Sprint | Branch | Status | Coding host | Validation host |
|---|---|---|---|---|
| `2026-05-08_extract-write-trace-logger` | `feature/instrumentation/extract-write-trace-logger` | ready for Acer-HL | Acer-HL | iMacDebian |

## Queued

| Sprint | Why queued | Depends on |
|---|---|---|
| `2026-05-08_extract-probe-responder` | Move DSR and future terminal probe replies behind a helper | `extract-write-trace-logger` merged |
| `extract-troubleshooting-pack-builder` | Replace hardcoded troubleshooting paths with helper-driven collection | write tracer and probe responder merged |
| `wire-config-toggles` | Expose consistent config/CLI switches for instrumentation | helper set stabilized |

## Completed

(none yet)
