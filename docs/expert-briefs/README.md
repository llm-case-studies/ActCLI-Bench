# Expert Briefs

Sprint packs and initiative coordination for ActCLI-Bench.

This folder is the runtime side of the sprint-pack process. The rules
manual lives at `docs/process/framework.md`; the templates that seed
new sprints live at `docs/process/templates/`.

## Layout

```
docs/expert-briefs/
├── README.md          ← this file
├── INDEX.md           ← all initiatives, status vocab
├── LESSONS.md         ← cross-initiative running log
└── initiatives/<initiative>/
    ├── README.md      ← initiative-level framing
    ├── INDEX.md       ← active / queued / completed sprint table
    ├── LESSONS.md     ← initiative-scoped running log
    ├── active/<YYYY-MM-DD_slug>/
    ├── queued/
    ├── paused/
    ├── aborted/
    └── completed/<YYYY-MM>/
```

Validation evidence mirrors this tree under `testing/` — see
`docs/process/framework.md` for the rules.

## Conventions

- **Initiative-first**: a sprint is grouped by which initiative it
  advances, not by which platform or layer it touches.
- **Active before queued**: only one sprint per initiative should be
  in `active/` at a time. Queue the rest.
- **Move on close**: the closure ritual moves `active/<slug>/` to
  `completed/<YYYY-MM>/<slug>/` and renames `03-merge-note-template.md`
  to `03-merge-note.md`.
