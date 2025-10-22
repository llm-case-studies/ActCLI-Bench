# Extraction Inventory Notes

This file summarizes what was copied into `SctCLI-Bench/` and why. See also:
- `INVENTORY.txt` — sorted list of all files
- `INVENTORY.sha256.txt` — file hashes (if available)

## Code
- `src/actcli/facilitator/` — FastAPI service that manages sessions, routes messages, and serves a simple viewer over WebSocket broadcast.
- `src/actcli/wrapper/` — WebSocket/HTTP client, PTY wrapper, and the `actcli-wrap` CLI for wrapping AI CLIs.
- `src/actcli/wrapper_tui/` — PromptToolkit multi‑terminal shell (slash commands, tabbing) that can auto‑start the facilitator and join sessions.
- `src/actcli/bench_textual/` — Textual proof‑of‑concept for theme switching and a branded UI.

## Tests
- `tests/integration/test_websocket_routing.py` — end‑to‑end WS flow between two clients via facilitator.
- `tests/integration/test_pty_wrapper_simple.py` — PTY wrapper creation/sanity.
- `tests/unit/test_wrapper_client.py` — Facilitator client unit tests.

## Docs (copied from submodules)
- `docs/WRAPPER_README.md` — from `src/actcli/wrapper/README.md`
- `docs/WRAPPER_TESTING_GUIDE.md` — from `src/actcli/wrapper/TESTING_GUIDE.md`
- `docs/WRAPPER_TUI_README.md` — from `src/actcli/wrapper_tui/README.md`
- `docs/WRAPPER_TUI_STATUS.md` — from `src/actcli/wrapper_tui/STATUS.md`

## Not Included
- ActCLI core commands (chat/auth/doctor/models/etc.) — purposefully excluded to keep the suite independent.
- Any project‑specific configs unrelated to wrappers/facilitator.

## Follow‑ups After Move
- Create a dedicated `pyproject.toml` using the template in `README.md`.
- Update import/package name if you choose to rename `actcli` to something else.
- Verify console scripts: facilitator, wrap, PTK shell, Textual bench.
- Run tests and adjust CI as needed.

