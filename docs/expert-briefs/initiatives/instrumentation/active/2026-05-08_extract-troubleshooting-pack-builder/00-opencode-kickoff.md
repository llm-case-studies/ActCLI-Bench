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

`feature/instrumentation/extract-troubleshooting-pack-builder`

Check it out:

```bash
git checkout feature/instrumentation/extract-troubleshooting-pack-builder
git pull --ff-only
```

This sprint extracts troubleshooting snapshot collection/export from
`DiagnosticsManager` into a reusable `TroubleshootingPackBuilder` helper.
Keep the current user-facing pack content and export behavior stable. Do not
add screenshots, CLI/config toggles, UI changes, or new probe-response
behavior.

Read first:

- `README.md`
- `CLAUDE.md`
- `AGENTS.md` if present locally
- `docs/process/framework.md`
- `docs/process/environment.md`
- `docs/expert-briefs/initiatives/instrumentation/README.md`
- `docs/expert-briefs/initiatives/instrumentation/active/2026-05-08_extract-troubleshooting-pack-builder/README.md`
- `docs/expert-briefs/initiatives/instrumentation/active/2026-05-08_extract-troubleshooting-pack-builder/01-brief.md`
- `testing/initiatives/instrumentation/2026-05-08_extract-troubleshooting-pack-builder/request.md`
- `src/actcli/bench_textual/diagnostics.py`
- `src/actcli/bench_textual/instrumentation/write_trace_logger.py`
- `src/actcli/bench_textual/instrumentation/probe_responder.py`
- `docs/INSTRUMENTATION_REFACTOR.md`
- `docs/POSTMORTEM_CURSOR_PTY.md`

Environment:

- Use a repo-compatible Python, version >=3.10.
- Prefer the shared user env described in `docs/process/environment.md`.
- Do not install project dependencies into system Python.

Before handoff:

1. `python -m pytest tests/bench_textual/test_troubleshooting_pack_builder.py tests/bench_textual/test_diagnostics_manager.py -v`
2. `python -m pytest tests/bench_textual/test_app_integration.py -q`
3. Run the direct export smoke from the validation request with a temporary
   target directory and confirm it writes one pack file.
4. Confirm `src/actcli/bench_textual/diagnostics.py` no longer contains
   `docs/Trouble-Snaps` or `troubleshooting_pack_`.
5. Confirm no generated files under `docs/Trouble-Snaps/` are changed.
6. Fill
   `docs/expert-briefs/initiatives/instrumentation/active/2026-05-08_extract-troubleshooting-pack-builder/02-result-template.md`.
7. Commit and push the branch.
