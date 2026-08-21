# ADR-0005: Container base image — distroless runtime, slim for build and dev

- **Status:** Accepted
- **Date:** 2026-08-21
- **Deciders:** Project owner (solo)
- **Phase:** Phase 2
- **PCI DSS touchpoints:** Req 2.2 (secure configuration standards), Req 6.3 (vulnerability management)

## Context

The payment API needs a container base image. The forces at play:

- **Attack surface** — fewer packages and no shell mean fewer CVEs and less for an
  attacker to pivot with after an RCE.
- **Wheel compatibility** — dependencies ship compiled extensions (`asyncpg`,
  `uvloop`/`httptools` from `uvicorn[standard]`, `bcrypt`). They need glibc +
  manylinux wheels; musl (alpine) forces slow source builds and subtle breakage.
- **Debuggability** — a shell in the image is convenient but is itself attack surface.
- **CI scan noise** — a noisy image erodes trust in the Phase 3 gate.

Three realistic candidates: alpine (musl), debian-slim (glibc), distroless (glibc).

## Decision

I will ship the runtime image on `gcr.io/distroless/python3-debian12` (glibc, no shell,
no package manager, non-root), built via a multi-stage Dockerfile from
`python:3.11-slim-bookworm`. Local development and `docker-compose` use a slim-based
`dev` stage for reload and a shell; the distroless `runtime` stage is the last stage,
so it is the default build target and the image that Trivy scans and that ships to EKS.

Python is pinned to **3.11** because distroless-debian12 provides Debian bookworm's
interpreter (3.11). The interpreter version is coupled to the distroless Debian release,
so the builder is matched to it to keep compiled wheels ABI-compatible.

## Alternatives considered

- **alpine (musl libc)** — smallest tag, but musl breaks the manylinux wheel model:
  `asyncpg`, `uvloop`, `bcrypt` fall back to source builds, needing a toolchain and
  producing longer, more fragile builds. Rejected — the well-known musl-plus-Python
  foot-gun with no upside for a service this size.
- **`python:3.x-slim` (debian, glibc)** — easy, keeps a shell for debugging, glibc
  wheels work out of the box. But it retains `apt`, a shell, and a full base userland,
  which is a larger CVE surface and hands an attacker a shell on RCE. Kept as the
  build/dev base, and documented as the runtime fallback if distroless debugging pain
  ever outweighs the benefit (e.g. keeps Python 3.12 without a custom base).
- **distroless (chosen for runtime)** — only the app plus its runtime deps: no shell,
  no `apt`, non-root by default. Smallest realistic attack surface and lowest Trivy
  count. Cons: no in-container shell (debug via `kubectl debug` / ephemeral containers
  or the `:debug` variant) and the Python version is tied to the Debian release.
- **Chainguard `python`** — distroless-style, near-zero CVEs, per-version tags, SBOM
  included; a strong option. Deferred to avoid a registry dependency and because
  `gcr.io/distroless` is the widely recognised baseline for this portfolio.

## Consequences

**Positive**

- Minimal attack surface; no shell for a post-exploitation attacker.
- Non-root runtime; read-only rootfs works because the app writes nothing to disk.
- Smaller image and clean Trivy reports, which strengthen the Phase 3 CI-gate story.

**Negative / trade-offs**

- No in-container shell — debugging needs ephemeral/debug containers.
- Python is pinned to 3.11; moving to 3.12 means leaving distroless-debian12 or
  building a custom base.
- Two runtime paths (distroless prod vs slim dev) — a minor prod/dev parity gap,
  mitigated because Trivy and K8s use the distroless target.

**Follow-ups**

- Digest-pin both bases (done via Dockerfile `ARG`s).
- Hash-pin Python deps (`--require-hashes`) as a supply-chain hardening in Phase 3.
- Cosign-sign the runtime image in Phase 10.
- Document a `kubectl debug` recipe in the Phase 13 runbooks.

## Known residual risk

As of 2026-08-21, the pinned distroless digest carries 18 HIGH-severity Debian
package CVEs (krb5, libssl3, libpython3.11 — full list in `.trivyignore`) with
upstream fixes already released but not yet present in any available distroless
rebuild. None are in application code or Python dependencies — those scan clean.
Tracked via `.trivyignore` with a 2026-09-04 review date: re-resolve the digest,
re-scan, and drop entries once the patched packages appear upstream. This is an
accepted, time-boxed exception, not a permanent suppression.

## Interview notes

Distroless is a base image carrying only the application and its runtime dependencies —
no shell, no package manager, no busybox. It shrinks the attack surface and means an
attacker who lands RCE has no shell to pivot with; the trade-off is debuggability,
solved with ephemeral debug containers. The Python version is tied to the distroless
Debian release, so I match the builder (`slim-bookworm`, 3.11) to the runtime to keep
compiled wheels ABI-compatible.
