# Expert Briefs

Sprint packs and initiative coordination for ActCLI-Bench.

This folder is the repo-resident memory for multi-agent work. The
process rules live in `docs/process/framework.md`; this tree is where
active briefs, queued sprint notes, completed merge notes, and reusable
lessons land.

## Layout

```text
docs/expert-briefs/
  README.md
  INDEX.md
  LESSONS.md
  initiatives/<initiative>/
    README.md
    INDEX.md
    LESSONS.md
    active/<YYYY-MM-DD_slug>/
    queued/<YYYY-MM-DD_slug>/
    paused/
    aborted/
    completed/<YYYY-MM>/
```

Validation requests, validator results, and evidence mirror the sprint
slugs under `testing/initiatives/`.

## Local Role Split

- Orchestrator: the local human-driven session that writes briefs,
  creates branches, and closes sprints.
- Implementer: Acer-HL unless a sprint says otherwise.
- Validator: iMacDebian unless a sprint says otherwise.

Anything a future session needs to know belongs here or in
`testing/`, not in host-local Claude/Codex memory.
