# Sprint Brief - {{Sprint Name}}

**Initiative:** `{{initiative}}`
**Sprint:** `{{YYYY-MM-DD_sprint-slug}}`
**Target branch:** `feature/{{initiative}}/{{sprint-slug}}`
**Merge target:** `main`
**Validation branch:** `validation/{{initiative}}/{{sprint-slug}}`

## Goal

{{One-paragraph success condition. When done, what is true that wasn't
true before?}}

## Why Now

{{One paragraph on what changed to make this sprint timely. What
upstream sprint just landed? What real consumer is waiting?}}

## Scope Fence

Expected touch set:

- {{file 1}}
- {{file 2}}
- {{file 3}}

Good scope:

- {{thing in scope 1}}
- {{thing in scope 2}}

Still out of scope:

- {{out-of-scope item — name explicitly, don't leave to inference}}
- {{out-of-scope item}}

## Acceptance Target

Prefer mechanically checkable criteria where the answer is
unambiguous (`grep` finds X, `git status` shows Y, an exit code, a
diff against a fixture) over judgment calls. Examples:

- `python -m pytest tests/path/test_thing.py -q` exits 0
- `grep -n 'old_string' src/module.py` returns nothing (the rename
  landed everywhere)
- `git status --short` shows no generated changes under `docs/...`
- {{criterion 1 — runnable check, ideally one line of shell}}
- {{criterion 2}}
- {{criterion 3}}

## Honest-Failure Mode

{{If implementation surfaces a real obstacle, what is the right move?
Usually: record the blocker in the result note and stop. Do NOT invent
workarounds that expand scope.}}

## Hosts

- coding host: `{{host}}`
- validation host: `{{host}}`
- {{other roles, e.g. staging or build host, if applicable}}

## Host Safety

{{Any protected services on the listed hosts? Any blind-kill patterns
to avoid? Any ports off-limits?}}
