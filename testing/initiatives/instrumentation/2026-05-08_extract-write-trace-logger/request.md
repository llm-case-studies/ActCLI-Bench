# Test Request - Extract WriteTraceLogger

**Date issued:** 2026-05-08
**Initiative:** `instrumentation`
**Sprint:** `2026-05-08_extract-write-trace-logger`
**Product branch:** `feature/instrumentation/extract-write-trace-logger`
**Validation branch:** `validation/instrumentation/extract-write-trace-logger`
**Validation host:** `iMacDebian`

## What You Are Validating

That `WriteTraceLogger` replaces the old inline write-trace code
without regressing PTY writes:

1. `ACTCLI_WRITE_TRACE=1` creates `docs/Trouble-Snaps/write_debug.log`
   using the existing `{name}: {repr(data)}` line format.
2. `ACTCLI_WRITE_TRACE` unset creates no log and appends nothing to a
   pre-existing log.
3. The new logger tests and existing terminal runner tests pass.
4. `terminal_runner.py` no longer contains the hardcoded trace path.

## Important Host Safety

`iMacDebian` runs the validator's local development environment. Do
not disturb unrelated services or shells.

Specifically:

- do not stop, restart, or kill anything outside this repo's spawned
  test processes
- do not bind to persistent ports
- do not commit host-local paths or agent memory
- do not commit generated changes to `docs/Trouble-Snaps/write_debug.log`

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
git checkout feature/instrumentation/extract-write-trace-logger
git pull --ff-only
git rev-parse HEAD
git checkout -b validation/instrumentation/extract-write-trace-logger
```

Save as `evidence/00_commit.txt`. If the validation branch already
exists locally, stop and ask the orchestrator whether to reuse it or
start fresh.

## Preflight

```bash
python3 --version
python3 -m pip show pytest
python3 -m pip show pyte
python3 -m pip show textual
git diff origin/main...HEAD --stat
git status --short
```

Save as `evidence/01_preflight.txt`.

If `docs/Trouble-Snaps/write_debug.log` exists before validation,
move it aside and restore it during cleanup:

```bash
mv docs/Trouble-Snaps/write_debug.log docs/Trouble-Snaps/write_debug.log.pre-test 2>/dev/null || true
```

## Static Checks

```bash
python3 -m pytest tests/bench_textual/test_write_trace_logger.py -v
```

Save as `evidence/02_unit_tests_logger.txt`.

```bash
python3 -m pytest tests/bench_textual/test_terminal_runner.py -q
```

Save as `evidence/03_unit_tests_runner_regression.txt`.

```bash
rg -n "docs/Trouble-Snaps/write_debug.log" src/actcli/bench_textual/terminal_runner.py
```

Save as `evidence/04_runner_no_path_string.txt`. Expected: empty
output and exit code 1 from `rg` because there are no matches.

## Run And Probe

### Probe 1 - env var ON

```bash
rm -f docs/Trouble-Snaps/write_debug.log
PYTHONPATH=src ACTCLI_WRITE_TRACE=1 python3 - <<'PY'
import time
from pathlib import Path
from actcli.bench_textual.terminal_runner import TerminalRunner

runner = TerminalRunner(name="validator-cat", command=["cat"])
runner.start()
time.sleep(0.2)
runner.write("hello-validator\n")
time.sleep(0.3)
runner.close()

log = Path("docs/Trouble-Snaps/write_debug.log")
print(f"exists={log.exists()}")
if log.exists():
    print(log.read_text(encoding="utf-8")[-200:])
PY
```

Save as `evidence/05_env_on.txt`. Expected: `exists=True` and a line
like `validator-cat: 'hello-validator\n'`.

### Probe 2 - env var OFF, no pre-existing log

```bash
rm -f docs/Trouble-Snaps/write_debug.log
PYTHONPATH=src python3 - <<'PY'
import time
from pathlib import Path
from actcli.bench_textual.terminal_runner import TerminalRunner

runner = TerminalRunner(name="validator-cat", command=["cat"])
runner.start()
time.sleep(0.2)
runner.write("hello-validator\n")
time.sleep(0.3)
runner.close()

log = Path("docs/Trouble-Snaps/write_debug.log")
print(f"exists={log.exists()}")
if log.exists():
    print(log.read_text(encoding="utf-8")[-200:])
PY
```

Save as `evidence/06_env_off.txt`. Expected: `exists=False`.

### Probe 3 - env var OFF, pre-existing log

```bash
printf "preexisting sentinel\n" > docs/Trouble-Snaps/write_debug.log
PYTHONPATH=src python3 - <<'PY'
import time
from pathlib import Path
from actcli.bench_textual.terminal_runner import TerminalRunner

runner = TerminalRunner(name="validator-cat", command=["cat"])
runner.start()
time.sleep(0.2)
runner.write("hello-validator\n")
time.sleep(0.3)
runner.close()

log = Path("docs/Trouble-Snaps/write_debug.log")
print(log.read_text(encoding="utf-8"))
PY
```

Save as `evidence/07_env_off_preexisting.txt`. Expected: exactly
`preexisting sentinel` and no appended `validator-cat` line.

## Cleanup

```bash
rm -f docs/Trouble-Snaps/write_debug.log
mv docs/Trouble-Snaps/write_debug.log.pre-test docs/Trouble-Snaps/write_debug.log 2>/dev/null || true
git status --short
```

Confirm:

- no generated `write_debug.log` change is staged or committed
- no stray validation process remains
- only `testing/initiatives/instrumentation/2026-05-08_extract-write-trace-logger/result.md`
  and `evidence/` files are new or modified on the validation branch

Save as `evidence/08_cleanup.txt`.

## Result

Fill:

```text
testing/initiatives/instrumentation/2026-05-08_extract-write-trace-logger/result.md
```

Verdict options: `PASS`, `PASS with findings`, `FAIL`, `BLOCKED`.

Commit result and evidence to:

```text
validation/instrumentation/extract-write-trace-logger
```

Push the validation branch.
