# ADR-0029: Dependency pinning with pip-tools

- **Status:** Accepted
- **Date:** 2026-08-26
- **Deciders:** Project owner (solo)
- **Phase:** Phase 3
- **PCI DSS touchpoints:** Req 6.4.3 (integrity of scripts and dependencies), Req 6.3

## Context

`requirements.txt` / `requirements-dev.txt` were pinned to exact package
versions (`==`) but had no hash pinning and no fully resolved transitive-
dependency lock. That leaves two problems once a CI SCA gate depends on
these files: the scan result isn't fully reproducible (a fresh resolve
can pick different transitive sub-versions over time), and there's no
integrity check against a compromised or substituted package artifact
being installed under a version string that looks correct.

## Decision

I will migrate to pip-tools. `requirements.in` / `requirements-dev.in`
become the hand-edited source files; `pip-compile --generate-hashes`
produces the fully pinned, hash-locked `requirements.txt` /
`requirements-dev.txt` that the Dockerfile's `builder` stage actually
installs from.

## Alternatives considered

- **Poetry** — a full dependency manager with its own lockfile, but it
  restructures the project around `pyproject.toml` and changes the
  Dockerfile's install step.
- **uv (`uv pip compile`)** — modern, notably faster resolver, also
  supports hash generation. A legitimate alternative; stayed with
  pip-tools as the more widely recognized, lower-risk default that's
  immediately familiar to a reviewer.
- **No change (status quo `==` pinning only)** — rejected: leaves SCA
  scan reproducibility and supply-chain integrity unaddressed, which the
  Phase 3 SCA gate now depends on.

## Consequences

**Positive**

- SCA scan results become a pure function of the commit, not of when
  `pip` happened to resolve transitive dependencies.
- Hash verification blocks a substituted or poisoned package artifact
  from installing even if its version string matches what's pinned.
- CVE diffs between `main` and `vulnerable-demo` are now unambiguous.

**Negative / trade-offs**

- One more tool in the local dev + CI toolchain.
- `--generate-hashes` is all-or-nothing — every dependency must publish
  hashes, which constrains dependency sources to PyPI wheels. Not a
  constraint that affects this stack in practice.

**Follow-ups**

- Re-run `pip-compile` periodically (e.g. monthly, or whenever Trivy
  flags a CRITICAL in a transitive dependency) to pull patched versions
  forward.

## Interview notes

I hash-pin every dependency so a compromised or substituted package
can't silently enter the build even if its version string looks right —
a small, concrete PCI Req 6.4.3 control, not just tidiness.
