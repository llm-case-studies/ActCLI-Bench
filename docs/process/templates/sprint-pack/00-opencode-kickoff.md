Work in:

`{{absolute path to the repo on the implementation host}}`.

If the repo is not yet on this machine, clone it first:

```bash
mkdir -p {{parent-dir}}
cd {{parent-dir}}
git clone {{repo SSH URL}}
cd {{repo-name}}
```

If it is already there, fetch and check status:

```bash
cd {{absolute path}}
git fetch origin
git status --short --branch
```

If there are uncommitted changes from another lane, stop and report.

Branch:

`{{feature/initiative/sprint-slug}}` (already exists on `origin`,
cut from `origin/main` by the orchestrator).

Check it out:

```bash
git checkout {{feature/initiative/sprint-slug}}
git pull --ff-only
```

{{One-paragraph framing of the sprint: what it is, what it isn't,
what scope fence applies.}}

Read first:

- `README.md`
- `docs/process/framework.md` — if this is a new implementer / fresh
  session
- `docs/expert-briefs/initiatives/{{initiative}}/README.md`
- `docs/expert-briefs/initiatives/{{initiative}}/active/{{sprint-slug}}/README.md`
- `docs/expert-briefs/initiatives/{{initiative}}/active/{{sprint-slug}}/01-brief.md`
- `testing/initiatives/{{initiative}}/{{sprint-slug}}/request.md`
- {{any relevant prior code/doc files}}

Important context:

- {{key constraint 1, e.g. "bind to 127.0.0.1 only"}}
- {{key constraint 2}}
- {{key constraint 3}}
- if you hit any blocker that needs orchestrator input, record it in
  the result note rather than improvising

Before handoff:

1. {{required smoke step 1}}
2. {{required smoke step 2}}
3. update
   `testing/initiatives/{{initiative}}/{{sprint-slug}}/result.md`
4. commit and push the branch
