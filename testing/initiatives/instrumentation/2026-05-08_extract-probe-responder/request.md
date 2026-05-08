# Test Request - Extract Probe Responder

**Date issued:** 2026-05-08
**Initiative:** `instrumentation`
**Sprint:** `2026-05-08_extract-probe-responder`
**Product branch:** `feature/instrumentation/extract-probe-responder`
**Validation branch:** `validation/instrumentation/extract-probe-responder`
**Validation host:** `iMacDebian`

## What You Are Validating

That `TerminalProbeResponder` replaces inline DSR response logic
without changing current behavior:

1. `ESC[6n` plus a pyte cursor produces `ESC[{row};{col}R` with
   1-based coordinates.
2. No query, non-pyte mode, and missing cursor return no response.
3. `TerminalManager` still writes the DSR response to the terminal
   runner when output contains a DSR query.
4. `terminal_manager.py` no longer defines `_respond_to_dsr`.

## Important Host Safety

`iMacDebian` runs the validator's local development environment. Do
not disturb unrelated services or shells.

Specifically:

- do not stop, restart, or kill anything outside this repo's spawned
  test processes
- do not bind to persistent ports
- do not commit host-local paths or agent memory
- do not commit generated changes to `docs/Trouble-Snaps/`

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
git checkout feature/instrumentation/extract-probe-responder
git pull --ff-only
git rev-parse HEAD
git checkout -b validation/instrumentation/extract-probe-responder
```

Save as `evidence/00_commit.txt`. If the validation branch already
exists locally, stop and ask the orchestrator whether to reuse it or
start fresh.

## Preflight

```bash
if [ -d .venv ]; then . .venv/bin/activate; fi
python3 --version
python3 -m pip show pytest pyte textual >/dev/null 2>&1 || python3 -m pip install -e '.[textual,test]'
python3 -m pip show pytest
python3 -m pip show pyte
python3 -m pip show textual
git diff origin/main...HEAD --stat
git status --short
```

Save as `evidence/01_preflight.txt`. Install dependencies only into
the active repo virtualenv or user environment used for this
validation; do not install system packages.

## Static Checks

```bash
python3 -m pytest tests/bench_textual/test_probe_responder.py tests/bench_textual/test_terminal_manager_probe_responder.py -v
```

Save as `evidence/02_unit_tests_probe_responder.txt`.

```bash
python3 -m pytest tests/bench_textual/test_app_integration.py -q
```

Save as `evidence/03_app_integration_regression.txt`.

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("src/actcli/bench_textual/terminal_manager.py")
needle = "_respond_to_dsr"
matches = [
    f"{line_no}:{line.rstrip()}"
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
    if needle in line
]
print("\n".join(matches))
raise SystemExit(1 if matches else 0)
PY
```

Save as `evidence/04_no_inline_dsr_helper.txt`. Expected: empty
output and exit code 0.

## Run And Probe

### Probe 1 - DSR response

```bash
PYTHONPATH=src python3 - <<'PY'
from actcli.bench_textual.instrumentation.probe_responder import TerminalProbeResponder

class Cursor:
    y = 4
    x = 6

class Screen:
    cursor = Cursor()

class Emulator:
    mode = "pyte"
    _screen = Screen()

responder = TerminalProbeResponder()
response = responder.response_for_text("\x1b[6n", Emulator())
print(repr(response))
assert response == "\x1b[5;7R"
PY
```

Save as `evidence/05_direct_dsr_response.txt`. Expected:
`'\x1b[5;7R'`.

### Probe 2 - no-query no-op

```bash
PYTHONPATH=src python3 - <<'PY'
from actcli.bench_textual.instrumentation.probe_responder import TerminalProbeResponder

class Emulator:
    mode = "pyte"
    _screen = object()

response = TerminalProbeResponder().response_for_text("ordinary output", Emulator())
print(repr(response))
assert response is None
PY
```

Save as `evidence/06_no_query_noop.txt`. Expected: `None`.

### Probe 3 - non-pyte no-op

```bash
PYTHONPATH=src python3 - <<'PY'
from actcli.bench_textual.instrumentation.probe_responder import TerminalProbeResponder

class Cursor:
    y = 4
    x = 6

class Screen:
    cursor = Cursor()

class Emulator:
    mode = "fallback"
    _screen = Screen()

response = TerminalProbeResponder().response_for_text("\x1b[6n", Emulator())
print(repr(response))
assert response is None
PY
```

Save as `evidence/07_non_pyte_noop.txt`. Expected: `None`.

## Cleanup

```bash
git status --short
```

Confirm:

- no generated `docs/Trouble-Snaps/` files changed
- no stray validation process remains
- only `testing/initiatives/instrumentation/2026-05-08_extract-probe-responder/result.md`
  and `evidence/` files are new or modified on the validation branch

Save as `evidence/08_cleanup.txt`.

## Result

Fill:

```text
testing/initiatives/instrumentation/2026-05-08_extract-probe-responder/result.md
```

Verdict options: `PASS`, `PASS with findings`, `FAIL`, `BLOCKED`.

Commit result and evidence to:

```text
validation/instrumentation/extract-probe-responder
```

Push the validation branch.
