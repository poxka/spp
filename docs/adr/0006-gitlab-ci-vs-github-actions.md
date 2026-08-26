# ADR-0006: GitLab CI as the pipeline engine, GitHub as primary repo

- **Status:** Accepted
- **Date:** 2026-08-26
- **Deciders:** Project owner (solo)
- **Phase:** Phase 3
- **PCI DSS touchpoints:** Req 6.2, 6.3, 11.3 (indirect — pipeline platform, not a control itself)

## Context

The project needs a CI platform to run the shift-left security pipeline
(secret scan, SAST, SCA, container scan, and later DAST/signing). Two
natural candidates given the hosting setup: GitHub Actions, native to the
primary repo host, or GitLab CI, which is what the target role's stated
stack calls for.

## Decision

I will run the security pipeline on GitLab CI, with GitHub remaining the
primary/source-of-truth repository and GitLab kept in sync via a push
mirror.

## Alternatives considered

- **GitHub Actions** — native integration, no mirroring required, huge
  action marketplace. Doesn't match the target job's stated stack.
- **GitLab CI (chosen)** — matches the target job's stack directly, has
  native SAST/SCA/DAST templates. Requires cross-host mirroring since
  the primary repo stays on GitHub.

## Consequences

**Positive**

- Directly demonstrates fluency in the exact CI platform named in the
  target job posting.
- The split source-of-truth/CI-runner setup is itself a small, honest
  architecture story to walk through in an interview.

**Negative / trade-offs**

- Added operational complexity: mirror maintenance, a second container
  registry, and a free-tier CI-minute budget.
- GitLab's Security Dashboard and MR security widget are Ultimate-only;
  free tier gives SARIF artifacts and a red/green pipeline graph, not the
  polished aggregated dashboard the original plan assumed.

**Follow-ups**

- Revisit CI-minute pressure if/when a self-hosted GitLab Runner (Pi)
  becomes available — removes the shared-runner minute constraint
  entirely (see charter §4).

## Interview notes

I run the security pipeline on GitLab CI, mirrored from GitHub via push,
specifically because the target role's stack calls for GitLab — even
though the code itself lives on GitHub for visibility.
