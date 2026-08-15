# ADR-0001: Monorepo over polyrepo

- **Status:** Accepted
- **Date:** 2026-08-15
- **Deciders:** Project owner (solo)
- **Phase:** Phase 0 — Foundation
- **PCI DSS touchpoints:** Req 6.2 (secure SDLC — a single, auditable change history)

## Context

SecurePay Platform spans many layers that normally live in separate repos in a
real org: the payment API (`app/`), Terraform infra (`infra/`), Kubernetes
manifests and policies (`k8s/`), security tooling and rules (`security/`),
observability config (`observability/`), CI (`.gitlab-ci.yml`), and docs
(`docs/`).

Two things drive the layout choice here, and they're specific to this being a
**portfolio artifact**, not a production org:

1. The selling point is *defense-in-depth across layers* and *live attack
   scenarios that cut through several layers at once* (e.g. a bad image →
   caught at CI **and** at admission **and** at runtime). A reviewer needs to
   see all of that in one place, as one story.
2. Demo scenarios are atomic across layers: a single `vulnerable-demo` commit
   might touch app code *and* a manifest *and* Terraform. That change should be
   one diff, reviewable side-by-side with its secure counterpart on `main`.

## Decision

We will use a **single monorepo** containing all layers of the platform, with
the directory structure defined in the project charter §3.2.

## Alternatives considered

- **Polyrepo (one repo per layer: app / infra / k8s / security).** How a mature
  org often splits things — independent release cadence, per-repo access
  control, smaller blast radius per repo. Rejected for this project: it
  fragments the narrative (a recruiter would have to clone 5 repos and mentally
  stitch them), makes cross-layer demo commits impossible to show as one diff,
  and adds cross-repo version-pinning overhead that buys us nothing at this
  scale.
- **Monorepo with git submodules for vendored pieces.** Unnecessary complexity;
  we vendor nothing that warrants it. Submodules are a known footgun (detached
  HEADs, forgotten `--recursive`) with no upside here.

## Consequences

**Positive**

- One clone, one `README`, one coherent story — optimized for how a recruiter
  actually reviews the repo.
- Atomic cross-layer commits; `main` vs `vulnerable-demo` diffs are clean and
  reviewable in one place (see ADR-0002).
- One CI pipeline definition, one pre-commit config, one source of truth for
  history — which is itself part of the showcase.

**Negative / trade-offs**

- No per-layer access control or independent release cadence. Irrelevant for a
  solo portfolio, but worth naming: in a real multi-team org I'd likely split
  these, or reach for a monorepo tool (Nx/Bazel) with path-scoped CI.
- CI must be path-aware to avoid rebuilding everything on every push (matters
  for GitLab free-tier CI minutes). We handle this with `rules:`/`changes:` in
  Phase 3, not by splitting repos.

**Follow-ups**

- Phase 3: scope CI jobs with `rules: changes:` so a docs-only commit doesn't
  burn minutes running container scans.

## Interview notes

"It's a monorepo because the *product* here is the end-to-end security story,
and that story is best told as one diffable history. A live attack scenario
touches app, manifest, and pipeline at once — I want that as a single commit
you can read top to bottom. In a real multi-team org I'd weigh polyrepo for
blast-radius and access control, and I can walk through that trade-off."
