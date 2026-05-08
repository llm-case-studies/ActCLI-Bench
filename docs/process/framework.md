# Sprint-Pack Framework

This is the rule manual for the sprint-pack process. The shape was
proven across `iHomeNerd`, `office-clerk`, and `panel-runner` — see
`example.md` for one concrete completed sprint.

## Folder Shape

```
docs/expert-briefs/
  README.md           ← this framework, in summary form
  INDEX.md            ← initiative table, status vocab
  LESSONS.md          ← cross-initiative running log
  initiatives/<initiative>/
    README.md, INDEX.md, LESSONS.md
    active/<YYYY-MM-DD_slug>/
      00-opencode-kickoff.md
      01-brief.md
      02-result-template.md
      03-merge-note-template.md
      README.md
    queued/, paused/, aborted/, completed/<YYYY-MM>/

testing/initiatives/<initiative>/<slug>/
  request.md
  result.md
  evidence/
```

Use **initiative-first grouping**. A sprint that touches multiple
platforms (Rust core, Python tooling, terminal emulator) belongs under
the initiative whose success condition it advances, not under a
platform folder.

`reference/` (optional) is for sprint packs that grew into reusable
learning examples. `initiatives/` is for real product work.

`LESSONS.md` files are running logs, append-as-you-go. They are NOT
sprint-closure deliverables. Sprint-specific lessons can also be added
to the merge note's "Findings" or "Follow-Up" section.

## Sprint Pack Shape

Every active sprint pack carries these files:

```
00-opencode-kickoff.md     paste-ready prompt for the implementer
01-brief.md                execution fence + success condition
02-result-template.md      shape the implementer fills
03-merge-note-template.md  shape the orchestrator fills at close
README.md                  one-paragraph sprint overview
```

`00-opencode-kickoff.md` should include:

- host and repo context (paths matter — Linux vs macOS host differs)
- a dirty-worktree check before branch switching
- the exact branch checkout command
- the list of files to read first
- the implementation fence (what is and isn't in scope)
- explicit non-goals
- required smoke level before handoff
- where to write the result note

## Required Execution Fence

Every brief should state explicitly:

- repo
- implementation host
- base branch
- working branch
- merge target
- build/deploy host (if separate)
- validation owner / host

A brief that leaves any of these unstated is not handoff-ready.

## Branch Naming

Use initiative-scoped branch names:

- `feature/<initiative>/<sprint-slug>` — product/code sprints
- `docs/<initiative>/<topic>` — coordination or architecture-only
- `validation/<initiative>/<sprint-slug>` — evidence-only validation
- `fix/<initiative>/<short-bug>` — small corrective branches
- `wip/<host>/<topic>` — local scratch only; not for review

Examples:

```
feature/instrumentation/cursor-position-events
feature/bench-emulator/pty-write-trace
validation/instrumentation/cursor-position-events
docs/process/process-bootstrap
```

## Branch Base Rule

New feature sprint branches are cut from `origin/main` at handoff time.
Do not start a new feature sprint from a stale local branch, a sibling
feature branch (unless dependency is explicit), or a machine branch.

The third Android sprint in `iHomeNerd` exposed this clearly: even a
good implementer can be made to fail by a bad branch base.

## Environment Rule

Host setup is part of the handoff contract. Sprint packs and validation
requests should say which runtime environment to use when dependency setup is
not obvious.

Default to shared, user-level environments by stack. For ActCLI Python work,
that means a reusable env such as `$HOME/.venvs/actcli-python`, refreshed from
the repo's `pyproject.toml`. Do not mutate system Python for normal sprint
work, and do not require every repo to create its own `.venv` unless
dependencies genuinely conflict.

See `environment.md` for the concrete Python and Node policy.

## Reviewer-First Rule

Expert briefs are not assignments to be executed blindly. The useful
framing is:

1. ask the implementer for judgment on the approach
2. define a tight implementation fence if the approach holds up
3. treat pushback as a valid deliverable when the approach is flawed

When a brief calls for, say, a particular config schema, the
implementer should push back if implementing reveals a real wart.
Pushback recorded in the result note often becomes the next sprint's
candidate (this happened with `panel-runner`'s `apiKeyEnv` design
decision).

## Smoke-Before-Testing Rule

Coding work is not ready for the validation lane just because the diff
looks good.

A smoke test is the fastest end-to-end proof that the touched surface
runs in its intended runtime. Pick the smallest smoke level that
honestly exercises the sprint's risk:

- **Focused checks** — unit/narrow tests. Rarely sufficient on their
  own unless the sprint is purely library/internal.
- **Local API smoke** — start the service, hit the changed endpoint
  with representative success and failure inputs.
- **Fake-dependency smoke** — emulate an external dependency to prove
  request/response/error contracts.
- **Real-dependency smoke** — use the real downstream service or
  device. Required when the sprint changes integration with that
  dependency.
- **Real-device smoke** — build, install, launch, probe on actual
  hardware. Required for installer/device/native-runtime sprints.
- **Validation** — independent rerun on a separate host with evidence
  in the repo. Comes AFTER the implementer reaches smoke-ready or
  records the blocker.

The brief should say which smoke level is required before handoff.

## Testing Mirror

Testing artifacts mirror the initiative and sprint slug:

```
testing/initiatives/<initiative>/<sprint-slug>/
  request.md     ← orchestrator's paste-ready validation prompt
  result.md      ← validator fills in
  evidence/      ← raw probe outputs (NN_step.{txt,json})
```

Treat the initial `request.md` as a **minimum validation floor**, not
a closed checklist. If implementation work exposes additional risk,
update the same testing request with the extra cases — do not create a
parallel request unless the validation scope has become a separate
sprint.

## Required Deliverables

Every coding effort should end with:

1. code and doc changes on the named branch
2. a short result note (`02-result-template.md` or
   `testing/.../result.md`)
3. a concrete testing request for the next validator

If the sprint cannot reach smoke-ready, the result note should say so
explicitly and leave the exact blocker plus next commands.

## Validation Discipline

- Validation lives on a separate `validation/...` branch.
- Evidence belongs in the repo, not only in chat transcripts.
- Result notes record both product behavior and host-safety findings
  when shared infrastructure is involved.
- The implementer does not mark their own work PASS.

## Closure Ritual

When validation passes, the orchestrator runs:

1. move the sprint folder `active/<slug>/` → `completed/<YYYY-MM>/<slug>/`
2. rename `03-merge-note-template.md` → `03-merge-note.md` and fill it:
   verdict, evidence commit SHA, decision (merge yes/no), follow-up
   sprint candidates, open risks
3. update the initiative `INDEX.md` (sprint moves from active to
   completed table)
4. update the cross-initiative `INDEX.md` if initiative status changed
5. append to `LESSONS.md` if the sprint taught anything reusable
6. merge the feature branch to `main` and cherry-pick the validation
   evidence commit onto main alongside (so main carries the evidence
   files, validators do not have to chase the validation branch)
7. delete the `feature/<initiative>/<slug>` and
   `validation/<initiative>/<slug>` branches on origin
   - **Exception**: `feature/repo-bootstrap/...` and
     `validation/repo-bootstrap/...` are preserved as orchestrator
     onboarding artifacts. New Claude sessions can read them to come
     up to speed on the repo's first sprint.

This whole ritual typically lands as one commit, message
`docs: close <slug> sprint`.

## Status Vocabulary

For initiative INDEX.md tables:

- `active` — in flight or ready to hand to an agent
- `queued` — planned but not yet issued
- `completed` — shipped, result captured, validation path known
- `paused` — waiting on rate limit, host, hardware, or dependency
- `aborted` — intentionally stopped; result explains why

## Cross-Repo Sprints

When a sprint requires changes in more than one repo (e.g. a contract
between `ActCLI-Bench` and `ActCLI-TE`), two patterns work:

1. **Coordination repo with mirrored sprint packs** — a third repo (or
   a `docs/` corner of one of the participating repos) holds the
   master sprint pack. Each participating repo has its own
   `feature/...` branch with the changes specific to it. The merge
   note in the coordination repo captures the joint validation.
2. **One repo as the lead, others as paired clients** — the lead repo
   carries the sprint pack and merge note; client repos cite the lead
   sprint slug in their own commit messages and keep their own
   `validation/...` evidence.

Pattern 1 is cleaner when the contract is symmetric. Pattern 2 is
cleaner when one side is clearly the producer and the other consumes.

## Reference Implementations

The following completed sprints demonstrate the shape:

- `panel-runner/docs/expert-briefs/initiatives/repo-bootstrap/completed/2026-05/2026-05-07_panel-runner-bootstrap/`
  — boring bootstrap, smallest credible HTTP service skeleton
- `panel-runner/docs/expert-briefs/initiatives/panel-core/completed/2026-05/2026-05-07_ad-hoc-panel-run/`
  — first real product feature with a design pushback recorded
- `office-clerk/docs/expert-briefs/initiatives/clerk-core/completed/2026-05/2026-05-07_oc-custom-provider-hookup/`
  — feature sprint that included an in-flight follow-up to close a
  blocker that surfaced during implementation
- `iHomeNerd/docs/expert-briefs/initiatives/iphone-to-mac-brain/completed/2026-05/2026-05-04_mac-launchd-sidecar-service/`
  — mature feature sprint with PASS-with-findings verdict, validation
  cherry-pick, and a concrete merge note

See `example.md` for a fuller walk-through of one of these.
