# Test Request - Extract WriteTraceLogger

**Date issued:** 2026-05-08
**Initiative:** `instrumentation`
**Sprint:** `2026-05-08_extract-write-trace-logger`
**Product branch:** `feature/instrumentation/extract-write-trace-logger`
**Validation branch:** `validation/instrumentation/extract-write-trace-logger`
**Validation host:** `iMac-Debian`

## What You Are Validating

That `WriteTraceLogger` correctly replaces the old inline write-trace
code, with no behaviour regression in the bench and a clean env-var
toggle:

1. With `ACTCLI_WRITE_TRACE=1`, a real bench session against `bash`
   produces `docs/Trouble-Snaps/write_debug.log` with the same
   line format the old code produced (`{name}: {repr(data)}`).
2. With `ACTCLI_WRITE_TRACE` unset, the same bench session produces
   no `docs/Trouble-Snaps/write_debug.log` (file is not created).
3. Existing terminal_manager unit tests still pass (no regression
   from the runner refactor).
4. The new `WriteTraceLogger` unit tests pass.

## Important Host Safety

`iMac-Debian` runs the validator's local development environment. It
does not host shared production services, but standard caveats apply:

- do not stop, restart, or kill anything outside this repo's spawn
  tree
- do not bind to ports outside the bench's local-loopback default
- do not commit user-host paths from `~/Projects/...` into the repo
- generated `docs/Trouble-Snaps/write_debug.log` files from this
  validation should NOT be committed; capture only `evidence/`
  artifacts under this sprint's testing folder

Unacceptable command shapes:

- `kill $(...)`
- `ss ... | head -1 | xargs kill`
- `lsof ... | head -1 | xargs kill`
- `pkill -f bash` (would hit the validator's own shell)

## Product Commit Under Test

```bash
cd ~/Projects/ActCLI-Bench
git fetch origin
git checkout feature/instrumentation/extract-write-trace-logger
git pull --ff-only
git rev-parse HEAD
```

Save as `evidence/00_commit.txt`.

## Preflight

```bash
python --version
pip show pyte | grep -E "^(Name|Version):"
git diff origin/main...HEAD --stat
ls -la docs/Trouble-Snaps/ 2>/dev/null
```

Save as `evidence/01_preflight.txt`.

If `docs/Trouble-Snaps/write_debug.log` already exists from a prior
run, move it aside before starting:

```bash
mv docs/Trouble-Snaps/write_debug.log docs/Trouble-Snaps/write_debug.log.pre-test 2>/dev/null
```

## Static Checks

```bash
pytest tests/bench_textual/test_write_trace_logger.py -v 2>&1
```

Save as `evidence/02_unit_tests_logger.txt`.

```bash
pytest tests/bench_textual/test_terminal_manager.py 2>&1
```

Save as `evidence/03_unit_tests_runner_regression.txt`.

```bash
grep -rn "docs/Trouble-Snaps/write_debug.log" \
  src/actcli/bench_textual/terminal_runner.py 2>&1
```

Save as `evidence/04_runner_no_path_string.txt`. Expected: empty
output (the path moved to the helper).

## Run And Probe

### Probe 1 — env var ON

```bash
rm -f docs/Trouble-Snaps/write_debug.log
ACTCLI_WRITE_TRACE=1 python -m actcli.bench_textual.app &
BENCH_PID=$!
sleep 2

# In the bench, add a bash terminal and type:
#   echo hello-validator
# Then press Enter, wait 1s, then Ctrl+Q to exit.

wait $BENCH_PID 2>/dev/null
ls -la docs/Trouble-Snaps/write_debug.log
head -20 docs/Trouble-Snaps/write_debug.log
```

Save as `evidence/05_env_on.txt`. Expected: file exists, lines look
like `bash: 'echo hello-validator\r'` etc.

### Probe 2 — env var OFF

```bash
rm -f docs/Trouble-Snaps/write_debug.log
unset ACTCLI_WRITE_TRACE
python -m actcli.bench_textual.app &
BENCH_PID=$!
sleep 2

# Same input as above: echo hello-validator + Enter, then Ctrl+Q.

wait $BENCH_PID 2>/dev/null
ls -la docs/Trouble-Snaps/write_debug.log 2>&1
```

Save as `evidence/06_env_off.txt`. Expected: file does NOT exist
(`No such file or directory`).

## Cleanup

```bash
# Restore any pre-existing log
mv docs/Trouble-Snaps/write_debug.log.pre-test \
  docs/Trouble-Snaps/write_debug.log 2>/dev/null

# Confirm bench process exited
ps -p $BENCH_PID 2>&1 | tail -1
```

Confirm:

- the bench process is gone
- no stray `python -m actcli.bench_textual.app` processes remain on
  the host
- no files committed accidentally:
  `git status --short`

Save as `evidence/07_cleanup.txt`.

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
