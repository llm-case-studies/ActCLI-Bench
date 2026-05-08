Work in:

`/home/<you>/Projects/ActCLI-Bench` on `Acer-HL`.

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

`feature/instrumentation/extract-write-trace-logger` (cut from
`origin/main` by the orchestrator at handoff).

Check it out:

```bash
git checkout feature/instrumentation/extract-write-trace-logger
git pull --ff-only
```

This sprint extracts the existing inline write-trace logging in
`terminal_runner.py` into a reusable `WriteTraceLogger` helper. It is
deliberately narrow: one helper, one env-var toggle, no probe-reply
work, no CLI flags, no troubleshooting-pack changes. The framework
manual at `docs/process/framework.md` explains the
reviewer-first/pushback model — read it before touching code if this
is your first sprint in this repo.

Read first:

- `README.md` (repo root)
- `CLAUDE.md`
- `docs/process/framework.md` (if first sprint here)
- `docs/expert-briefs/initiatives/instrumentation/README.md`
- `docs/expert-briefs/initiatives/instrumentation/active/2026-05-08_extract-write-trace-logger/README.md`
- `docs/expert-briefs/initiatives/instrumentation/active/2026-05-08_extract-write-trace-logger/01-brief.md`
- `testing/initiatives/instrumentation/2026-05-08_extract-write-trace-logger/request.md`
- `src/actcli/bench_textual/terminal_runner.py` (current
  `_append_write_debug` and `write()` — lines ~35 and ~248)
- `docs/INSTRUMENTATION_REFACTOR.md`

Important context:

- the on-disk format must stay `{name}: {repr(data)}\n` so existing
  troubleshooting tools and grep recipes still work
- file sink default ON only when `ACTCLI_WRITE_TRACE=1` is set;
  current behaviour writes unconditionally — this is an intentional
  behaviour change, document it in the result note
- env-var resolution should happen at logger construction time, not
  per write call (cheap and observable)
- the `instrumentation` package is new — initialize the package
  cleanly so future helpers (probe responder, pack builder) drop in
  beside it
- if you hit any blocker that needs orchestrator input, record it in
  the result note rather than improvising; pushback on the brief is a
  valid deliverable

Before handoff:

1. `pytest tests/bench_textual/test_write_trace_logger.py -v`
2. `pytest tests/bench_textual/test_terminal_manager.py` (regression
   guard on the runner change)
3. with `ACTCLI_WRITE_TRACE=1`, run a short bench session against
   `bash` (a few keystrokes plus Enter) and confirm the resulting
   `docs/Trouble-Snaps/write_debug.log` contains lines in the
   `{name}: {repr(data)}\n` format
4. with `ACTCLI_WRITE_TRACE` unset, repeat the bench session and
   confirm no `docs/Trouble-Snaps/write_debug.log` is created
5. update
   `testing/initiatives/instrumentation/2026-05-08_extract-write-trace-logger/result.md`
6. commit and push the branch
