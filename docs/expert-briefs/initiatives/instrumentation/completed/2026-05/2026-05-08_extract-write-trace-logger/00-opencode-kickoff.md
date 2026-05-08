Work in:

`/home/alex/Projects/ActCLI-Bench` on `Acer-HL`.

If the repo is not yet on this machine, clone it first:

```bash
mkdir -p ~/Projects
cd ~/Projects
git clone git@github.com:llm-case-studies/ActCLI-Bench.git
cd ActCLI-Bench
```

If it is already there, fetch and check status:

```bash
cd ~/Projects/ActCLI-Bench
git fetch origin
git status --short --branch
```

If there are uncommitted changes from another lane, stop and report.

Branch:

`feature/instrumentation/extract-write-trace-logger`

Check it out:

```bash
git checkout feature/instrumentation/extract-write-trace-logger
git pull --ff-only
```

This sprint extracts the inline write-trace logging in
`terminal_runner.py` into a reusable `WriteTraceLogger` helper. It is
deliberately narrow: one helper, explicit sink classes, one env-var
toggle, no DSR/probe work, no CLI flags, and no troubleshooting pack
changes.

Read first:

- `README.md`
- `CLAUDE.md`
- `AGENTS.md` if present locally
- `docs/process/framework.md`
- `docs/expert-briefs/initiatives/instrumentation/README.md`
- `docs/expert-briefs/initiatives/instrumentation/completed/2026-05/2026-05-08_extract-write-trace-logger/README.md`
- `docs/expert-briefs/initiatives/instrumentation/completed/2026-05/2026-05-08_extract-write-trace-logger/01-brief.md`
- `testing/initiatives/instrumentation/2026-05-08_extract-write-trace-logger/request.md`
- `src/actcli/bench_textual/terminal_runner.py`
- `tests/bench_textual/test_terminal_runner.py`
- `docs/INSTRUMENTATION_REFACTOR.md`
- `docs/POSTMORTEM_CURSOR_PTY.md`

Important context:

- The on-disk format must remain `{name}: {repr(data)}\n`.
- `ACTCLI_WRITE_TRACE=1` enables file tracing. Unset, empty, or `0`
  disables file writes.
- Env-var resolution should happen when constructing the logger, not on
  every `record()` call.
- The default test and CI behavior should not append to
  `docs/Trouble-Snaps/write_debug.log`.
- Do not commit generated changes to `docs/Trouble-Snaps/write_debug.log`.
- Pushback is a valid deliverable if the requested sink contract proves
  awkward; record it in the result note instead of widening scope.

Before handoff:

1. `python3 -m pytest tests/bench_textual/test_write_trace_logger.py -v`
2. `python3 -m pytest tests/bench_textual/test_terminal_runner.py -q`
3. Run a small direct smoke with `ACTCLI_WRITE_TRACE=1` and confirm
   `docs/Trouble-Snaps/write_debug.log` uses the existing line format.
4. Repeat with `ACTCLI_WRITE_TRACE` unset and confirm the log is not
   created or appended.
5. Fill
   `docs/expert-briefs/initiatives/instrumentation/completed/2026-05/2026-05-08_extract-write-trace-logger/02-result-template.md`.
6. Commit and push the branch.
