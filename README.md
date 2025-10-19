# ActCLI Bench Suite (extraction package)

This folder is a temporary export of the wrappers + facilitator + viewer + bench UIs
from the ActCLI repo so we can verify the suite as a standalone project.

Move `SctCLI-Bench/` to its own repository, then adjust packaging metadata.

## What’s included

- Facilitator (FastAPI + WebSocket routing)
  - `src/actcli/facilitator/`
- Wrapper client + PTY wrapper + wrap CLI
  - `src/actcli/wrapper/`
- PromptToolkit shell (multi‑terminal UI)
  - `src/actcli/wrapper_tui/`
- Textual bench (themeable UI)
  - `src/actcli/bench_textual/`
- Tests
  - `tests/integration/test_websocket_routing.py`
  - `tests/integration/test_pty_wrapper_simple.py`
  - `tests/unit/test_wrapper_client.py`
- Docs copied from submodules
  - See `docs/` folder

Full inventory:
- `INVENTORY.txt` (paths)
- `INVENTORY.sha256.txt` (hashes, if sha256sum available)

## Next steps (standalone repo)

1) Create a new repository (e.g., `ActCLI-Bench`) and move contents of `SctCLI-Bench/` into it.
2) Use the `pyproject.template.toml` below as a starting point for packaging.
3) Verify console scripts:
   - `actcli-facilitator` — start facilitator service
   - `actcli-wrap` — wrap a CLI and join a session
   - `actcli-shell` — multi‑terminal PTK shell
   - `actcli-bench` — Textual bench (theme demo)
4) Run tests under `tests/`.

## Packaging template (edit as needed)

```toml
[project]
name = "actcli-bench"
version = "0.0.0"
description = "Facilitator + wrappers + bench UIs for ActCLI"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
  "typer>=0.12.0",
  "rich>=13.0.0",
  "httpx>=0.27.0",
  "websockets>=12.0",
  "fastapi>=0.112.0",
  "uvicorn>=0.30.0",
]

[project.optional-dependencies]
tui = ["prompt_toolkit>=3.0.43", "pyte>=0.8.1"]
textual = ["textual>=0.50.0"]

auth = [
  "keyring>=25.0.0",
]

[project.scripts]
actcli-wrap = "actcli.wrapper.wrap_cli:app"
actcli-facilitator = "actcli.wrapper.facilitator_cli:app"
actcli-shell = "actcli.wrapper_tui.shell:main"
actcli-bench = "actcli.bench_textual.app:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/actcli"]
```

## Notes

- Package name `actcli-bench` is independent; the import path remains `actcli.*` to avoid refactoring internals during extraction. You may later rename the top‑level package.
- All server/UI code here is optional for ActCLI core; this split keeps the core lean.

