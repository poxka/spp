# `demo/` — Attack-scenario runners

Scripts and pointers that drive the live attack scenarios, plus links to the
recorded GIFs/screencasts (the recordings themselves live in
[`docs/demos/`](../docs/demos/)).

Each scenario:

1. is a small, atomic commit on `vulnerable-demo` (see
   [ADR-0002](../docs/adr/0002-two-branch-strategy.md)),
2. is pushed through the relevant defense layer,
3. gets its block/detect point captured on video,
4. is logged in [`docs/security-chaos.md`](../docs/security-chaos.md).

See the master scenario table in the project charter §6.

> Status: scaffolded in Phase 0. First runners appear with the CI pipeline
> (Phase 3).
