# ActCLI-TE Tracking

This document links ActCLI-Bench with the ActCLI-TE project so progress on the
Python-native terminal engine stays visible to bench contributors.

## Milestones (mirror of ActCLI-TE/docs/PLAN.md)

1. **Bootstrapping** – repo scaffolding, API draft, fixture corpus
2. **Core Engine** – Python-native parser, screen model, cursor reporting
3. **Parity & Testing** – comparison harness, AI CLI fixtures, fuzz tests
4. **Integration** – packaging, bench toggle, migration notes

## Coordination Notes

- Upstream plan: https://github.com/llm-case-studies/ActCLI-TE/blob/bootstrap/docs/PLAN.md
- When a milestone completes in ActCLI-TE, reflect it here and adjust the bench
  roadmap accordingly (e.g., removing pyte dependencies).
- Share findings (cursor heuristics, PTY behaviours) via postmortems in this
  repo so both codebases stay aligned.

## Actions

- [ ] Monitor ActCLI-TE issues/milestones monthly
- [ ] Pull latest ActCLI-TE tags when evaluating new bench releases
- [ ] Update bench documentation once a stable ActCLI-TE release replaces pyte
