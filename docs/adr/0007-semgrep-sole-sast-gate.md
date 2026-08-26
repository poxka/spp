# ADR-0007: Semgrep as the sole SAST gate (GitLab managed SAST dropped)

- **Status:** Accepted
- **Date:** 2026-08-26
- **Deciders:** Project owner (solo)
- **Phase:** Phase 3
- **PCI DSS touchpoints:** Req 6.2, 6.3, 11.3

## Context

The original plan called for running both Semgrep and GitLab's managed
SAST template side by side, for redundancy and to show fluency with
GitLab's native offering. In implementation, GitLab's managed SAST
include (`Jobs/SAST.gitlab-ci.yml`) hardcodes its job into a `test`
stage, which doesn't exist in this pipeline's stage list
(`lint → secret-scan → sast → sca → build → container-scan`) — the
pipeline fails validation outright with that include present. Separately,
GitLab's own SAST analyzer for Python is itself Semgrep-based on current
versions, so the two engines overlap almost entirely in what they'd
actually catch. On the free tier, the managed scanner also can't power
the MR security widget or Security Dashboard (both Ultimate-only) and
can't be tuned to gate on a specific severity — it would only ever
produce a report artifact, never block a merge.

## Decision

I will drop the GitLab managed SAST include and run explicit Semgrep
alone as the SAST gate, with a curated ruleset
(`p/python`, `p/security-audit`, `p/owasp-top-ten`, `p/jwt`), gating on
`--severity=ERROR`.

## Alternatives considered

- **Semgrep + GitLab managed SAST together (original plan)** — shows
  native-tooling fluency and nominal two-engine redundancy. In practice
  the engines overlap almost completely for Python, and free tier strips
  the managed scanner of the one thing that would justify the
  redundancy (dashboard/widget visibility), while its hardcoded stage
  forces either fighting the template or accepting pipeline validation
  errors.
- **GitLab managed SAST alone, no explicit Semgrep** — zero extra config,
  but no control over ruleset (can't add `p/jwt` or anything custom),
  and on free tier it can't gate a merge at all — disqualifying for a
  pipeline that's meant to fail-closed.

## Consequences

**Positive**

- The pipeline validates cleanly against a stage list I fully control.
- One clear, tunable, fail-closed SAST gate instead of two overlapping,
  partially crippled ones.

**Negative / trade-offs**

- Deviates from the original plan — a genuine single point of failure if
  Semgrep's ruleset has a blind spot a differently-sourced scanner might
  have caught.

**Follow-ups**

- Revisit if the project ever moves past free tier, or if GitLab
  improves the managed SAST template's stage-remapping story.

## Interview notes

I evaluated GitLab's managed SAST, hit a real free-tier limitation
(hardcoded stage, no gating capability), and chose one well-tuned Semgrep
gate over two overlapping, partially disabled scanners.
