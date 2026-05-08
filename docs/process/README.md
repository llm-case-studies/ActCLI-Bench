# ActCLI-Bench Sprint-Pack Process

This folder documents how work moves through this repo when more than
one agent or human is involved.

It is adapted from the same shape used in `llm-case-studies/panel-runner`
and `llm-case-studies/office-clerk`, where it has been validated through
multiple sprints across machines (orchestrator on one host, coding
agent on another, validator on a third).

## When to use it

Use the sprint-pack process when:

- the work spans more than one session, agent, or host
- a reviewer-first framing helps (the brief asks for judgment first,
  not blind execution)
- you want repeatable handoff that does not require rediscovering
  context from chat history
- you want validation evidence to live in the repo, not just chat
  transcripts

For a quick local fix in one terminal, with one agent, in one session,
the process is overkill — just commit and push.

## Folder map

```
docs/process/
├── README.md            ← this file
├── framework.md         ← the rules: branches, hosts, sprint shape, closure
├── environment.md       ← shared host environment policy
├── example.md           ← pointer to a real completed sprint for shape
└── templates/
    ├── sprint-pack/     ← paste-ready files for a new sprint
    │   ├── 00-opencode-kickoff.md
    │   ├── 01-brief.md
    │   ├── 02-result-template.md
    │   ├── 03-merge-note-template.md
    │   └── README.md
    └── testing/         ← paired validation request templates
        ├── request.md
        ├── result.md
        └── evidence/.gitkeep
```

## Three roles

| Role | Typical home | Owns |
|---|---|---|
| Orchestrator | host where the human drives, e.g. a Claude session on a primary workstation | sprint design, git ritual, paste-ready prompts |
| Implementer | a coding agent on a chosen coding host | code/test/doc changes inside the brief's fence |
| Validator | a tester on a separate host with no implementation conflict | independent rerun, evidence capture, verdict |

The same person may fulfill more than one role in a small team — but
keeping the distinctions in writing avoids the failure mode where the
implementer also marks their own work PASS.

## Per-sprint flow

1. **Orchestrator** drafts the sprint pack on a `feature/<initiative>/<slug>`
   branch (or `docs/<initiative>/<topic>` for coordination-only work).
   Pack lives at:
   `docs/expert-briefs/initiatives/<initiative>/active/<YYYY-MM-DD_slug>/`
2. **Orchestrator** drafts the paired testing request at:
   `testing/initiatives/<initiative>/<slug>/request.md`
3. **Implementer** receives the kickoff (the `00-opencode-kickoff.md`
   contents pasted in chat), reads the brief, executes within scope,
   gets to a smoke-ready state, fills the result note, pushes.
4. **Validator** receives the testing request, cuts a
   `validation/<initiative>/<slug>` branch, runs probes, captures
   evidence, fills `result.md` with a verdict, pushes.
5. **Orchestrator** runs the **close ritual**:
   - move sprint folder `active/` → `completed/<YYYY-MM>/`
   - rename `03-merge-note-template.md` → `03-merge-note.md` and fill
     it in (verdict, evidence summary, decision, follow-ups)
   - update `INDEX.md` files
   - append to `LESSONS.md` if the sprint taught anything reusable
   - merge feature branch to `main` and cherry-pick the validation
     evidence commit alongside
   - delete the `feature/...` and `validation/...` branches on origin
     (exception: `feature/repo-bootstrap/...` and
     `validation/repo-bootstrap/...` are preserved as orchestrator
     onboarding artifacts)
6. **Orchestrator** drafts the next sprint, drawing on the merge note's
   `Follow-Up` section and the LESSONS log.

## Key conventions

- **Branch base rule**: feature sprint branches must be cut from
  `origin/main` at handoff time. Don't start a new sprint from a stale
  local branch or a sibling feature branch.
- **Environment rule**: use shared, user-level runtime environments by
  stack unless a sprint explicitly needs tighter isolation. See
  `environment.md`.
- **Reviewer-first rule**: the brief asks the implementer for judgment
  on the approach. Pushback is a valid deliverable when the approach
  is flawed.
- **Smoke-before-testing rule**: an implementation isn't testing-ready
  just because the diff looks good. The brief states what smoke level
  the implementer should reach before handing off (unit, local API,
  fake-dependency, real-dependency, real-device).
- **Testing request as floor**: the initial `request.md` is a minimum
  validation contract. Implementers can extend it when work surfaces
  additional risk; they should not create a parallel request.
- **Validation discipline**: don't mark validation PASS from the
  implementation lane. Validation lives on its own branch with
  evidence in the repo.

See `framework.md` for the full set.

## Adapting to ActCLI-Bench

ActCLI-Bench has its own existing technical structure (Rust/Python,
PTY/cursor work, instrumentation refactor planning). The sprint-pack
process sits ALONGSIDE that structure, not in place of it. Existing
research notes under `docs/*.md` remain the source of technical truth.
The expert-briefs structure is for ORGANIZING WORK, not for replacing
research.

When the first real sprint runs in this repo, the orchestrator should
think about:

- which ActCLI-Bench host is the implementation host (the user's
  primary dev workstation, an OpenCode session, etc.)
- whether validation runs on a separate machine or just in a separate
  worktree
- whether the sprint touches sister repos (`ActCLI-TE`, `ActCLI-RT`)
  and how to coordinate across them — cross-repo sprints typically
  live in a shared coordination repo or are mirrored

See `framework.md`, "Cross-repo sprints", for guidance.
