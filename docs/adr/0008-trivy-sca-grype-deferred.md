# ADR-0008: Trivy for SCA now, Grype deferred to a follow-up pass

- **Status:** Accepted
- **Date:** 2026-08-26
- **Deciders:** Project owner (solo)
- **Phase:** Phase 3
- **PCI DSS touchpoints:** Req 6.3, 11.3

## Context

The charter calls for dual SCA engines — Trivy and Grype — since
different vulnerability databases and detection logic can surface
different findings. Standing up both in the first pipeline pass adds
scope and CI-minute cost before the core shift-left flow
(`lint → secret-scan → sast → sca → build → container-scan`) is proven
end-to-end even once. Several unrelated jobs in this same phase already
needed debugging (semgrep flag syntax, hadolint false positive, ruff
formatting) — stacking a second SCA engine on top of an unproven
pipeline would have made isolating failures harder.

## Decision

I will ship Trivy alone for both dependency scanning (`trivy fs`) and
container image scanning (`trivy image`) in this Phase 3 pass. Grype
will be added as an explicit second SCA-stage job in a dedicated
follow-up pass once the core pipeline is stable.

## Alternatives considered

- **Trivy + Grype together from the start** — gives immediate redundancy,
  and is a stronger talking point. Doubles the SCA debugging surface on
  the very first pipeline run and makes it harder to tell which scanner's
  config is at fault when something fails.
- **Grype alone** — different vulnerability DB lineage (Anchore) than
  Trivy's aggregated sources, well regarded on its own. Doesn't cover
  container image scanning the way Trivy already does for the
  `container-scan` stage, so it would mean adding a second tool rather
  than reusing one already proven to work.

## Consequences

**Positive**

- One working, well-understood scanner across both the SCA and
  container-scan stages reduces moving parts while the pipeline shape
  itself was still being debugged.
- Trivy's DB mirror and built-in scanning are already wired for
  `container-scan`, so no new tool sprawl in this pass.

**Negative / trade-offs**

- Single point of coverage for dependency vulnerabilities until Grype
  lands — a CVE present only in Grype's database and not Trivy's would
  currently go undetected.

**Follow-ups**

- Dedicated pass to add a `grype-fs` job to the `sca` stage — non-
  blocking at first, promoted to a gate once tuned. Tracked as a Phase 3
  follow-up, not pushed to a later phase.

## Interview notes

I shipped one well-integrated SCA scanner first to get the whole
pipeline shape working end-to-end, then layer in the second engine —
sequencing scope deliberately instead of landing everything in one pass.
