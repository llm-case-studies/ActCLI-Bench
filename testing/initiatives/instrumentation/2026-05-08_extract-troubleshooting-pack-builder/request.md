# Test Request - Extract TroubleshootingPackBuilder

**Date issued:** 2026-05-08
**Initiative:** `instrumentation`
**Sprint:** `2026-05-08_extract-troubleshooting-pack-builder`
**Product branch:** `feature/instrumentation/extract-troubleshooting-pack-builder`
**Validation branch:** `validation/instrumentation/extract-troubleshooting-pack-builder`
**Validation host:** `iMacDebian`

## What You Are Validating

That troubleshooting snapshot generation now delegates to
`TroubleshootingPackBuilder` without changing current Bench behavior:

1. Builder unit tests and diagnostics delegation tests pass.
2. App integration tests pass on the repo-supported asyncio backend.
3. A direct export smoke writes one timestamped pack file into a temporary
   directory and includes the expected text sections.
4. `DiagnosticsManager` no longer hardcodes the troubleshooting export path or
   filename prefix.

## Important Host Safety

`iMacDebian` runs the validator's local development environment. Do not disturb
unrelated services or shells.

Specifically:

- do not stop, restart, or kill anything outside this repo's spawned test
  processes
- do not bind to persistent ports
- do not commit host-local paths or agent memory
- do not commit generated changes to `docs/Trouble-Snaps/`
- do not install project dependencies into system Python

Unacceptable command shapes:

- `kill $(...)`
- `ss ... | head -1 | xargs kill`
- `lsof ... | head -1 | xargs kill`
- `pkill -f bash`
- `pkill -f python`

## Product Commit Under Test

```bash
cd ~/Projects/ActCLI-Bench
git fetch origin
git checkout feature/instrumentation/extract-troubleshooting-pack-builder
git pull --ff-only
git rev-parse HEAD
git checkout -b validation/instrumentation/extract-troubleshooting-pack-builder
```

Save as `evidence/00_commit.txt`. If the validation branch already exists
locally, stop and ask the orchestrator whether to reuse it or start fresh.

## Preflight

Use a shared user-level Python env, not system Python. If `python3` on this
host is not Python >=3.10, set `ACTCLI_PYTHON_BIN` first.

```bash
export ACTCLI_PYTHON_BIN="${ACTCLI_PYTHON_BIN:-python3}"
"$ACTCLI_PYTHON_BIN" - <<'PY'
import sys
print(sys.version)
if sys.version_info < (3, 10):
    raise SystemExit("ActCLI-Bench requires Python >=3.10; set ACTCLI_PYTHON_BIN.")
PY

export ACTCLI_PY_ENV="${ACTCLI_PY_ENV:-$HOME/.venvs/actcli-python}"
if [ ! -d "$ACTCLI_PY_ENV" ]; then
  "$ACTCLI_PYTHON_BIN" -m venv "$ACTCLI_PY_ENV"
fi
. "$ACTCLI_PY_ENV/bin/activate"
python -m pip install -e '.[textual,test]'
python -m pip show pytest
python -m pip show anyio
python -m pip show pyte
python -m pip show textual
git diff origin/main...HEAD --stat
git status --short
```

Save as `evidence/01_preflight.txt`.

## Static Checks

```bash
python -m pytest tests/bench_textual/test_troubleshooting_pack_builder.py tests/bench_textual/test_diagnostics_manager.py -v
```

Save as `evidence/02_builder_and_diagnostics_tests.txt`.

```bash
python -m pytest tests/bench_textual/test_app_integration.py -q
```

Save as `evidence/03_app_integration_regression.txt`.

```bash
python - <<'PY'
from pathlib import Path

path = Path("src/actcli/bench_textual/diagnostics.py")
needles = ("docs/Trouble-Snaps", "troubleshooting_pack_")
matches = [
    f"{line_no}:{line.rstrip()}"
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
    if any(needle in line for needle in needles)
]
print("\n".join(matches))
raise SystemExit(1 if matches else 0)
PY
```

Save as `evidence/04_no_diagnostics_hardcoded_export_path.txt`.
Expected: empty output and exit code 0.

## Run And Probe

### Probe 1 - direct builder export

```bash
export TARGET_DIR="$(mktemp -d)"
PYTHONPATH=src python - <<'PY'
from pathlib import Path
from datetime import datetime, timezone
import os

from actcli.bench_textual.instrumentation import TroubleshootingPackBuilder

class FakeRunner:
    muted = False
    command = ["python", "-q"]

    def first_output_preview(self, limit):
        return "first output"[:limit]

class FakeEmulator:
    cols = 80
    rows = 24

class FakeState:
    emulator = FakeEmulator()
    last_synced_size = (80, 24)
    output_buffer = "recent output"
    item = FakeRunner()
    winsize_history = ["80x24"]

class FakeTerminalManager:
    def list_terminals(self):
        return ["demo"]

    def get_terminal_state(self, name):
        return FakeState()

class FakeLogManager:
    buffers = {
        "events": ["event one"],
        "errors": [],
        "debug": ["debug one"],
        "output": ["output one"],
    }

builder = TroubleshootingPackBuilder(
    terminal_manager=FakeTerminalManager(),
    log_manager=FakeLogManager(),
    version_info={"bench": "test", "textual": "test", "pyte": "test"},
    get_app_state=lambda: {
        "active_view": "terminal",
        "active_terminal": "demo",
        "writer_attached": True,
    },
    clock=lambda: datetime(2026, 5, 8, 12, 34, 56, tzinfo=timezone.utc),
)

target_dir = Path(os.environ["TARGET_DIR"])
path = Path(builder.export_to_file(target_dir=target_dir, key_events=["enter"]))
text = path.read_text(encoding="utf-8")
print(path.name)
print(path.exists())
print("versions:" in text)
print("terminals:" in text)
print("---- recent events ----" in text)
assert path.name == "troubleshooting_pack_20260508T123456Z.txt"
assert "versions:" in text
assert "terminals:" in text
assert "---- recent events ----" in text
PY
```

Save as `evidence/05_direct_builder_export.txt`.

### Probe 2 - no generated docs/Trouble-Snaps changes

```bash
git status --short docs/Trouble-Snaps
```

Save as `evidence/06_no_generated_trouble_snaps.txt`. Expected: empty output.

## Cleanup

```bash
git status --short
```

Confirm:

- no generated `docs/Trouble-Snaps/` files changed
- no stray validation process remains
- only `testing/initiatives/instrumentation/2026-05-08_extract-troubleshooting-pack-builder/result.md`
  and `evidence/` files are new or modified on the validation branch

Save as `evidence/07_cleanup.txt`.

## Result

Fill:

```text
testing/initiatives/instrumentation/2026-05-08_extract-troubleshooting-pack-builder/result.md
```

Verdict options: `PASS`, `PASS with findings`, `FAIL`, `BLOCKED`.

Commit result and evidence to:

```text
validation/instrumentation/extract-troubleshooting-pack-builder
```

Push the validation branch.
