# Testing Initiatives

Validation requests, results, and evidence live under
`<initiative>/<sprint-slug>/` here, mirroring the sprint slugs used in
`docs/expert-briefs/initiatives/<initiative>/active/<sprint-slug>/`.

Each sprint slug carries:

```text
request.md
result.md
evidence/
```

Validation work commits to `validation/<initiative>/<sprint-slug>` and
pushes that branch. The orchestrator cherry-picks or otherwise brings
accepted validation evidence onto `main` during sprint closure.
