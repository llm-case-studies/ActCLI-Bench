# Reference Example: panel-runner Sprint 1 Bootstrap

A complete, validated, closed sprint lives in `panel-runner` at:

> `llm-case-studies/panel-runner` →
> `docs/expert-briefs/initiatives/repo-bootstrap/completed/2026-05/2026-05-07_panel-runner-bootstrap/`

(Public org, accessible with the standard `llm-case-studies` token.)

It is the canonical "smallest credible bootstrap sprint" — a tiny HTTP
service skeleton, JSONL store helpers, placeholder UI page, three
endpoint contract tests. Useful as a shape reference because it is:

- short enough to read end-to-end in 10 minutes
- representative of the orchestrator/implementer/validator handoff
- already validated PASS, with the close ritual demonstrated

## What's in that folder

```
00-opencode-kickoff.md     ← paste-ready prompt the implementer used
01-brief.md                ← scope fence, acceptance, host safety
02-result-template.md      ← shape the implementer filled
03-merge-note.md           ← orchestrator's close note (filled)
README.md                  ← sprint overview
```

Plus the paired testing artifacts at:

```
testing/initiatives/repo-bootstrap/2026-05-07_panel-runner-bootstrap/
  request.md     ← validator's prompt
  result.md      ← validator's verdict (PASS)
  evidence/      ← raw probe outputs
```

And the merge note follow-up that became the next sprint:

> `panel-runner/docs/expert-briefs/initiatives/panel-core/completed/2026-05/2026-05-07_ad-hoc-panel-run/`

That second sprint shows the same shape with one extra dimension: a
real product feature with a design pushback recorded in the merge
note that became its own follow-up sprint.

## Why panel-runner specifically

Panel-runner's bootstrap is the cleanest reference because:

- it lives in a NEW repo (so the framework files are visible without
  layers of legacy)
- it produced exactly one commit per phase (orchestrator scaffold,
  orchestrator sprint pack, implementer code, close commit, validator
  evidence) — easy to read in `git log`
- the validation host's protected-service handling pattern is the same
  one you'll likely apply to ActCLI-Bench when a real validation host
  is identified

If you can fetch panel-runner, `git log --oneline origin/main` shows
the whole sprint shape in five commits. Fetch the actual files at:

```
docs/expert-briefs/initiatives/repo-bootstrap/completed/2026-05/2026-05-07_panel-runner-bootstrap/
testing/initiatives/repo-bootstrap/2026-05-07_panel-runner-bootstrap/
```

## Other concrete examples

If panel-runner's bootstrap feels too tiny for the scale of work this
repo will need, look at:

- `panel-runner/docs/expert-briefs/initiatives/panel-core/completed/2026-05/2026-05-07_ad-hoc-panel-run/`
  — first real product feature; shows how scope fence handles a chunkier
  delivery (dispatcher, expert config, HTML form, JSON API) and how the
  merge note records design pushback as a sprint candidate.
- `office-clerk/docs/expert-briefs/initiatives/clerk-core/completed/2026-05/2026-05-07_oc-custom-provider-hookup/`
  — feature sprint that revealed an in-flight blocker; shows the
  follow-up-kickoff pattern (`04-...-kickoff.md`) for closing a blocker
  inside an active sprint instead of cutting a new one.
- `iHomeNerd/docs/expert-briefs/initiatives/iphone-to-mac-brain/completed/2026-05/2026-05-04_mac-launchd-sidecar-service/`
  — mature sprint with PASS-with-findings verdict, validation evidence
  cherry-pick, and a multi-host handoff (Acer-HL coding, iMac-Debian
  validation, mac-mini runtime).

These four together cover the patterns most likely to come up: tiny
bootstrap, first feature, blocker closure, and multi-host with
findings.
