# Test Request - {{Sprint Name}}

**Date issued:** {{YYYY-MM-DD}}
**Initiative:** `{{initiative}}`
**Sprint:** `{{sprint-slug}}`
**Product branch:** `feature/{{initiative}}/{{sprint-slug}}`
**Validation branch:** `validation/{{initiative}}/{{sprint-slug}}`
**Validation host:** `{{host}}`

## What You Are Validating

That {{the goal of this sprint}}:

1.
2.
3.

## Important Host Safety

`{{validation host}}` carries protected local infrastructure:

- {{service / port / resource}}

Do not disturb that. Specifically:

- do not stop, restart, or kill {{the protected service}}
- do not bind to {{protected port}}
- {{other protections}}

Unacceptable command shapes:

- `kill $(...)`
- `ss ... | head -1 | xargs kill`
- `lsof ... | head -1 | xargs kill`
- `pkill -f {{service-name}}`

## Product Commit Under Test

```bash
cd {{absolute path on validation host}}
git fetch origin
git checkout feature/{{initiative}}/{{sprint-slug}}
git pull --ff-only
git rev-parse HEAD
```

Save as `evidence/00_commit.txt`.

## Preflight

```bash
{{preflight check 1}}
{{preflight check 2}}
```

Save as `evidence/01_preflight.txt`.

## Static Checks

```bash
{{test command 1, e.g. node --test, cargo test, pytest}}
```

Save as `evidence/02_static_checks.txt`.

## Run And Probe

{{instructions to start whatever the sprint produced}}

```bash
{{startup command, with tracked PID}}
```

```bash
{{probe command 1}}
{{probe command 2}}
```

Save as `evidence/03_*.{txt,json}`.

## Cleanup

```bash
{{cleanup command, using the tracked PID}}
```

Confirm:

- {{post-cleanup invariant 1, e.g. "the test process is gone"}}
- {{post-cleanup invariant 2, e.g. "protected service still active"}}

Save as `evidence/NN_cleanup.txt`.

## Result

Fill:

```text
testing/initiatives/{{initiative}}/{{sprint-slug}}/result.md
```

Verdict options: `PASS`, `PASS with findings`, `FAIL`, `BLOCKED`.

Commit result and evidence to:

```text
validation/{{initiative}}/{{sprint-slug}}
```

Push the validation branch.
