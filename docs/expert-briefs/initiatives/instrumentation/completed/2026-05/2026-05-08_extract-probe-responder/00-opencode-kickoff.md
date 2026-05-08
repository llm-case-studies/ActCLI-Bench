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

`feature/instrumentation/extract-probe-responder`

Check it out:

```bash
git checkout feature/instrumentation/extract-probe-responder
git pull --ff-only
```

This sprint extracts `TerminalManager._respond_to_dsr` into a reusable
`TerminalProbeResponder` helper. Keep the behavior unchanged:
`ESC[6n` in terminal output should still produce
`ESC[{row};{col}R` from pyte cursor coordinates. Do not touch write
tracing, troubleshooting packs, pyte sizing, cursor heuristics, or UI
layout.

Read first:

- `README.md`
- `CLAUDE.md`
- `AGENTS.md` if present locally
- `docs/process/framework.md`
- `docs/expert-briefs/initiatives/instrumentation/README.md`
- `docs/expert-briefs/initiatives/instrumentation/completed/2026-05/2026-05-08_extract-probe-responder/README.md`
- `docs/expert-briefs/initiatives/instrumentation/completed/2026-05/2026-05-08_extract-probe-responder/01-brief.md`
- `testing/initiatives/instrumentation/2026-05-08_extract-probe-responder/request.md`
- `src/actcli/bench_textual/terminal_manager.py`
- `src/actcli/bench_textual/instrumentation/write_trace_logger.py`
- `docs/POSTMORTEM_CURSOR_PTY.md`
- `docs/INSTRUMENTATION_REFACTOR.md`

Important context:

- The helper should compute responses; `TerminalManager` can remain
  responsible for writing responses to the runner and logging them.
- Preserve 1-based cursor conversion: pyte cursor `y=0, x=0` becomes
  `ESC[1;1R`.
- No DSR query, non-pyte emulator mode, or missing cursor should return
  no response.
- Keep the helper package import surface tidy in
  `src/actcli/bench_textual/instrumentation/__init__.py`.
- Pushback is valid if the proposed public method shape is awkward;
  record it in the result note instead of widening scope.

Before handoff:

1. `python3 -m pytest tests/bench_textual/test_probe_responder.py tests/bench_textual/test_terminal_manager_probe_responder.py -v`
2. `python3 -m pytest tests/bench_textual/test_app_integration.py -q`
3. Run the direct helper smoke from the validation request and confirm
   the expected `ESC[5;7R` response.
4. Confirm `terminal_manager.py` no longer defines `_respond_to_dsr`.
5. Fill
   `docs/expert-briefs/initiatives/instrumentation/completed/2026-05/2026-05-08_extract-probe-responder/02-result-template.md`.
6. Commit and push the branch.
