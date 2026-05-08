# AI agent orientation — ActCLI-Bench

Welcome. If you are an AI coding agent (Claude, Codex, Cursor, Aider,
or any other) opening this repo for the first time, read this file
first. The orientation is the same regardless of which agent you are.

## What this repo is

`ActCLI-Bench` is part of the ActCLI group: terminal-native AI tooling
(see `README.md`). Recent work has been on the bench emulator, cursor
positioning correctness, and instrumentation refactor — see
`docs/INSTRUMENTATION_REFACTOR.md` and `docs/POSTMORTEM_CURSOR_PTY.md`
for the most current technical context.

## How work moves through this repo

This repo follows a small **sprint-pack process** lifted from
`llm-case-studies/panel-runner` and `llm-case-studies/office-clerk`.
The process is documented at:

- `docs/process/README.md` — overview and pointers
- `docs/process/framework.md` — the framework manual (rules, branch
  naming, sprint shape, who-does-what)
- `docs/process/environment.md` — host environment policy (Python venvs,
  shared user-level installs, etc.)
- `docs/process/templates/sprint-pack/` — paste-ready templates for a
  new sprint
- `docs/process/templates/testing/` — paired testing-request templates
- `docs/process/example.md` — pointer to a real completed sprint in
  `panel-runner` for shape reference

**Three roles:**

- **Orchestrator** — the agent the human is currently driving from
  their primary workstation. Designs sprints, writes briefs, runs the
  git ritual.
- **Implementer** — a coding agent on a chosen coding host (e.g.
  DeepSeek via OpenCode on `Acer-HL`). Executes inside the brief's
  fence.
- **Validator** — a tester on a separate host with no implementation
  conflict (e.g. `iMacDebian`). Independently reruns probes, captures
  evidence, returns a verdict.

The same person may fulfill more than one role in a small team — but
keeping the distinctions in writing avoids the failure mode where the
implementer also marks their own work PASS.

A new agent arriving cold should NOT start coding before reading the
framework manual and checking
`docs/expert-briefs/initiatives/*/active/` for any in-flight sprint.

## Initiative and sprint folders

Live work lives at:

```
docs/expert-briefs/
  README.md, INDEX.md, LESSONS.md
  initiatives/<initiative>/
    README.md, INDEX.md
    active/<YYYY-MM-DD_slug>/      ← in-flight sprints
    completed/<YYYY-MM>/<slug>/    ← finished sprints + merge notes
    queued/<YYYY-MM-DD_slug>/      ← optional pre-prepared packs

testing/initiatives/<initiative>/<slug>/
  request.md, result.md, evidence/
```

Existing `docs/*.md` files are the source of truth for technical
context, and `docs/process/` is the source of truth for HOW work
should be organized.

## Cross-session memory note

Whatever local agent state your tooling keeps (Claude Code's
`~/.claude/`, Cursor's chat history, agent-specific MCP caches, etc.)
is **not portable** across hosts or sessions and is not visible to
other agents working on the same repo.

Anything future sessions need to know belongs in the repo — under
`docs/process/`, in sprint-pack briefs, in merge notes' `## Findings`,
or in `docs/expert-briefs/LESSONS.md`. Treat the repo as the only
durable shared memory.

## ActCLI group context

Sister repos in `llm-case-studies`:

- `ActCLI` — the actuarial CLI itself
- `ActCLI-TE` — terminal engine (MIT-licensed core)
- `ActCLI-Bench` — this repo, "Inter-AI facilitated sessions"
- `ActCLI-Round-Table` — multi-agent debate format
- `ActCLI-Extensions` — Chrome bridge and test rigs
- `ActCLI-HIC` — hardware insight console
- `ActCLI-Round-Table-V1` — private spike

The sprint-pack process can scale across these repos when shared
concerns (diagnostics interfaces, integration validation) need
coordinated work. Cross-repo sprints belong in a shared coordination
repo or are mirrored — see `docs/process/framework.md` for guidance.

## Sprint readiness checklist (for the orchestrator)

Before handing a sprint to an implementer:

1. Have you read the most recent technical postmortems in `docs/`?
2. Have you checked `docs/expert-briefs/initiatives/*/active/` for any
   in-flight work that conflicts?
3. Does the brief explicitly name the implementation host, validation
   host, working branch, merge target, and validation branch?
4. Is the testing request paste-ready (host safety, exact commands,
   evidence file paths)?
5. Are out-of-scope items called out as explicitly as in-scope?
6. Where possible, are acceptance criteria mechanically checkable
   (`grep`, `git status`, exit codes) rather than judgment calls?

If any of these is missing, the brief is not yet handoff-ready.
