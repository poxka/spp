# Security Chaos Log

> A running journal of **attack scenarios**: for each control I build, I play
> attacker — push the bad code / image / manifest / API call — and record what
> the defense actually did. Hypothesis → action → expected defense → observed
> result → evidence. If a control *didn't* catch what it claims to, that's a
> finding, and it goes here too.

This is the evidence trail behind the "defense-in-depth actually works" claim.
It pairs with the `vulnerable-demo` branch (see
[ADR-0002](./adr/0002-two-branch-strategy.md)) and the screencasts in
[`docs/demos/`](./demos/).

## How to use this log

- One entry per scenario, newest at the top of the table.
- Every planted vulnerability on `vulnerable-demo` gets an entry here.
- Link the commit that introduced the vuln **and** the evidence (screencast /
  screenshot / failed-job URL).
- "Expected" is what the control *should* do. "Observed" is what it *did*. When
  they differ, note the gap and the follow-up.
- Redact before publishing: no real account IDs, IPs, ARNs, or keys in
  screenshots/GIFs.

## Scenario status legend

- ✅ **Blocked** — control caught it as designed.
- 🟡 **Detected** — not blocked, but alerted/logged (e.g. runtime detection).
- ❌ **Missed** — control failed to catch it (a finding — investigate).
- ⏳ **Planned** — scenario defined, not yet executed.

## Entry template

```markdown
### [#NN] <short scenario name>

- **Phase / layer:** <e.g. Phase 3 / CI — SCA>
- **Date:** YYYY-MM-DD
- **Attacker action:** <what the "attacker" did>
- **Vulnerable commit:** <link/sha on vulnerable-demo, if applicable>
- **Control under test:** <tool / policy expected to catch it>
- **Hypothesis:** <what I expect to happen>
- **Steps to reproduce:**
  1. …
  2. …
- **Expected defense:** <what the control should do>
- **Observed result:** <what actually happened> — status: ✅ / 🟡 / ❌
- **Evidence:** <screencast / screenshot / job URL in docs/demos/>
- **PCI DSS:** <requirement(s) this exercises, or —>
- **Follow-up:** <tuning, gap to fix, or "none">
```

## Log

| #   | Scenario                                  | Layer                | Control    | Status | Phase   | Evidence |
| --- | ------------------------------------------ | --------------------- | ----------- | ------ | ------- | -------- |
| #01 | Gitleaks generic-api-key coverage gaps      | Source (pre-commit)   | Gitleaks    | ✅ | Phase 1 | [screenshots](./demos/secret-detections/) |
| #02 | JWT signature verification disabled       | Source / Auth        | JWT decode logic (app) | ✅ | Phase 1 | [screenshots](./demos/bad-jwt/) |
| #03 | `/debug/env` leaks environment variables   | Source / API surface | none — shouldn't exist | ✅ | Phase 1 | [screenshot](./demos/env_leaks.png) |
| #04 | SQL injection in `GET /transactions` filter | Source / Data access | ORM parameterization | ✅ | Phase 1 | [screenshots](./demos/sqli-transaction-filter/) |
| #05 | Permissive CORS (any origin allowed)       | Source / Edge         | CORS middleware allowlist | ✅ | Phase 1 | [screenshots](./demos/any-cors/) |
| #06 | Dependency with known CVE   | Dependencies (SCA)    | pip-audit (local check; Trivy/Grype land in Phase 3 CI) | ✅ | Phase 1 | [screenshot](./demos/vulnerable-dependency-cve.png) |
| #07 | Vulnerable container image | Container (image scan) | Trivy | ✅ | Phase 2 | [screenshots](./demos/vulnerable-image/) |
| #08 | Unpatched CRITICAL CVEs in runtime base image (real, unplanned) | Dependencies / Image (CI) | Trivy image scan (Phase 3 CI) | ✅ | Phase 3 | [screenshot](./demos/trivy-critical-catch.png) |
| #09 | Gitleaks/TruffleHog CI-layer secret detection  | Source (CI)         | Gitleaks + TruffleHog (GitLab CI) | ✅ | Phase 3 | [screenshot](./demos/vulnerable-demo-ci-run/secret-scan.png) |
| #10 | Semgrep SAST CI-layer catch | Source (CI)       | Semgrep (GitLab CI) | ✅ | Phase 3 | [screenshot](./demos/vulnerable-demo-ci-run/sast.png) |
| #11 | Trivy SCA CI-layer catch | Dependencies (CI)    | Trivy fs (GitLab CI)      | ✅ | Phase 3 | [screenshot](./demos/vulnerable-demo-ci-run/sca.png) |
| #12 | Trivy container-scan CI-layer catch | Image (CI) | Trivy image (GitLab CI) | ✅ | Phase 3 | [screenshot](./demos/vulnerable-demo-ci-run/container-scan.png) |

### [#01] Gitleaks generic-api-key coverage gaps (stopwords, typed syntax, duplicate findings)

- **Phase / layer:** Phase 1 / Source — pre-commit secret scanning
- **Date:** 2026-08-19
- **Attacker action:** Hardcoded an AWS access key, AWS secret key, and JWT
  signing secret in `app/src/config.py` on `vulnerable-demo`.
- **Vulnerable commit:** `vulnerable-demo`@[`d9ad2a7`](https://github.com/poxka/spp/commit/d9ad2a7)
- **Control under test:** Gitleaks (pre-commit hook, `generic-api-key` +
  `aws-access-token` default rules)
- **Hypothesis:** All three hardcoded values should be caught by gitleaks
  before the commit lands.
- **Steps to reproduce:**
  1. Add three hardcoded secret-like values to `Settings` in
     `app/src/config.py`, Python typed-assignment style
     (`name: type = "value"`).
  2. `git add` the file and run `pre-commit run gitleaks -v`.
- **Expected defense:** Pre-commit blocks the commit, one finding per value.
- **Observed result:** ✅ Achieved, but not on the first try. The default
  gitleaks ruleset missed two of the three secrets initially:

  - A secret written as a readable phrase slipped past undetected — the
    scanner allowlists common dictionary words to cut down on false
    positives, and the phrasing happened to trip that allowlist. Switching
    to a fully random value fixed it immediately.
  - A secret declared with Python's typed-assignment syntax
    (`name: type = "value"`) also went undetected, even when random. The
    default rule's pattern assumes a simpler `name = "value"` shape and
    doesn't handle the extra type annotation in between. Fixed by adding a
    small custom rule scoped to that specific syntax, layered on top of
    the default ruleset rather than replacing it.
  - That fix then over-corrected: it started double-flagging one of the
    secrets that a more specific built-in rule already caught correctly.
    Fixed by teaching the custom rule to back off in exactly the cases the
    built-in rule already owns.

  End state, re-verified: all three secrets caught, no duplicate findings,
  values redacted in the tool's output.
- **Evidence:** `docs/demos/secret-detections/`
- **PCI DSS:** Req 6.2 (secure coding), Req 12.10.1 (process gap found and
  closed before reaching `main`)
- **Follow-up:** Re-check this allowlist behavior on future gitleaks
  upgrades — default rules can change silently between versions.

**Bonus finding:** GitHub's server-side push protection independently
caught the same AWS Access Key and Secret Key on push, blocking the branch
until explicitly allowlisted per-secret. It did NOT flag the JWT secret
(different ruleset — cloud-provider key patterns only). Two independent
layers (local pre-commit + GitHub server-side), two different blind spots,
same demo secrets.

### [#02] JWT signature verification disabled

- **Phase / layer:** Phase 1 / Source — authentication
- **Date:** 2026-08-19
- **Attacker action:** Took a valid, expired-looking access token, corrupted
  its signature, and sent it as-is on `vulnerable-demo`.
- **Vulnerable commit:** `vulnerable-demo`@[`9883c71`](https://github.com/poxka/spp/commit/9883c71)
- **Control under test:** JWT decode logic in `security/jwt.py`
- **Hypothesis:** A token with a tampered signature should be rejected
  with 401, same as on `main`.
- **Steps to reproduce:**
  1. Log in to get a valid token.
  2. Replace everything after the last `.` with garbage (corrupting the
     signature) and call a protected endpoint with it.
- **Expected defense:** 401 Unauthorized — signature mismatch rejected.
- **Observed result:** ✅ Demonstrated correctly. With signature
  verification intentionally disabled for this scenario, the tampered
  token was accepted (200) instead of rejected — confirming that on
  `main`, where verification is enforced, the same forged token would be
  rejected outright. This is the exact class of bug real-world `alg=none`
  / signature-bypass incidents come from: trusting a token's payload
  without actually checking who signed it.
- **Evidence:** `docs/demos/bad-jwt/`
- **PCI DSS:** Req 8.3 (strong authentication), Req 6.2 (secure coding)
- **Follow-up:** None — `main` already enforces a fixed algorithm allowlist
  and mandatory signature verification (see `security/jwt.py`, ADR-covered
  implicitly by the auth design).

### [#03] `/debug/env` leaks environment variables

- **Phase / layer:** Phase 1 / Source — API surface / information disclosure
- **Date:** 2026-08-20
- **Attacker action:** Called an undocumented `/debug/env` endpoint on
  `vulnerable-demo` with no authentication.
- **Vulnerable commit:** `vulnerable-demo`@[`89cc827`](https://github.com/poxka/spp/commit/89cc827)
- **Control under test:** API surface — the endpoint simply shouldn't exist
  outside local debugging, and never in a way reachable without auth.
- **Hypothesis:** Hitting the endpoint returns every environment variable
  in plaintext, including DB credentials and the JWT signing secret.
- **Steps to reproduce:**
  1. `curl http://.../debug/env` — no token, no special access.
- **Expected defense:** Endpoint doesn't exist on `main` — 404.
- **Observed result:** ✅ Demonstrated correctly. On `vulnerable-demo` the
  endpoint returns the full environment unauthenticated, including secrets
  that should never leave the process. This is a reminder that the
  cheapest fix for most information-disclosure bugs is simply not building
  the endpoint in the first place — no scanner catches a debug route that
  was never meant to ship, it has to be caught by discipline and code
  review, not tooling.
- **Evidence:** `docs/demos/debug-env-leak.png`
- **PCI DSS:** Req 6.2 (secure coding), Req 3 (no exposure of secrets/keys
  that protect stored data), Req 7 (no unauthenticated access to sensitive
  data)
- **Follow-up:** None — `main` has no such endpoint. Worth carrying this
  principle into the CI phase: a route/attack-surface review, not just
  vulnerability scanning, catches this class of bug earlier.

### [#04] SQL injection in GET /transactions filter

- **Phase / layer:** Phase 1 / Source — data access layer
- **Date:** 2026-08-18
- **Attacker action:** Passed a classic `' OR '1'='1` payload as the
  `currency` query parameter on `vulnerable-demo`, where the filter query
  was rewritten from ORM parameter binding to raw string-concatenated SQL.
- **Vulnerable commit:** `vulnerable-demo`@[`c622fc3`](https://github.com/poxka/spp/commit/c622fc3)
- **Control under test:** Query construction in `transaction_service.py`
- **Hypothesis:** Filtering by a nonexistent currency with an injected
  `OR` clause should still return no rows if the query is safely
  parameterized, and would return everything if it isn't.
- **Steps to reproduce:**
  1. Log in, create a transaction in a known currency (e.g. MXN).
  2. Query `GET /transactions?currency=USD` — a currency with no data —
     confirm it correctly returns nothing.
  3. Query the same endpoint with `currency=ZZZ' OR '1'='1` — a payload
     that turns the WHERE clause into an always-true condition.
- **Expected defense:** Both queries behave identically — no rows,
  since neither currency exists; the injected condition should have no
  special effect.
- **Observed result:** ✅ Demonstrated correctly. The clean nonexistent-
  currency query returned nothing as expected, but the injected payload
  returned data regardless of the filter — confirming raw string-built
  SQL is exploitable exactly the way the ORM's parameter binding on `main`
  is designed to prevent. Same mechanism that would let an attacker read
  other users' data past the owner-scoping the service is supposed to
  enforce.
- **Evidence:** `docs/demos/sqli-transaction-filter/`
- **PCI DSS:** Req 6.2 (secure coding — injection prevention), Req 6.5.1
  (injection flaws)
- **Follow-up:** None — `main` uses SQLAlchemy ORM with bound parameters
  throughout; this class of bug requires deliberately bypassing that, as
  done here for the demo.

### [#05] Permissive CORS (any origin allowed)

- **Phase / layer:** Phase 1 / Source — CORS policy
- **Date:** 2026-08-20
- **Attacker action:** Sent a request with `Origin: https://evil.example.com`
  on `vulnerable-demo`, where the CORS middleware was switched from a
  strict allowlist to wildcard origins.
- **Vulnerable commit:** `vulnerable-demo`@[`2b7e796`](https://github.com/poxka/spp/commit/2b7e796)
- **Control under test:** CORS middleware configuration in `main.py`
- **Hypothesis:** A request from an origin not on the allowlist should not
  receive an `Access-Control-Allow-Origin` header back.
- **Steps to reproduce:**
  1. `curl` any endpoint with `Origin: https://evil.example.com` set.
  2. Inspect the response for `Access-Control-Allow-Origin`.
- **Expected defense:** No `Access-Control-Allow-Origin` header for an
  origin outside the allowlist.
- **Observed result:** ✅ Demonstrated correctly. On `main`, the header is
  absent for the untrusted origin — the browser would block the response
  from being read by that origin's JavaScript. On `vulnerable-demo`, the
  header reflected the attacker's origin back exactly, meaning any website
  on the internet could make authenticated, credentialed requests to the
  API from a victim's browser and read the response.
- **Evidence:** `docs/demos/any-cors/`
- **PCI DSS:** Req 6.2 (secure coding), Req 4 (unauthorized data exposure
  in transit to untrusted origins)
- **Follow-up:** None — `main` uses a strict, env-driven origin allowlist
  (`CORS_ALLOWED_ORIGINS`), verified above.

### [#06] Dependency with known CVE (pyyaml 5.3.1)

- **Phase / layer:** Phase 1 / Dependencies — SCA
- **Date:** 2026-08-20
- **Attacker action:** N/A — this scenario doesn't require an active
  attacker action, it demonstrates that a known-vulnerable dependency
  pinned in `requirements.txt` is discoverable by dependency scanning
  before it ever reaches a container image.
- **Vulnerable commit:** `vulnerable-demo`@[`c02f93b`](https://github.com/poxka/spp/commit/c02f93b)
- **Control under test:** Software composition analysis (`pip-audit`
  locally for now; Trivy/Grype in CI arrive in Phase 3)
- **Hypothesis:** Pinning `pyyaml==5.3.1`, a version with a known public
  CVE, should be flagged by a dependency scan.
- **Steps to reproduce:**
  1. Add `pyyaml==5.3.1` to `requirements.txt`.
  2. Run `pip-audit -r requirements.txt`.
- **Expected defense:** Scanner reports the CVE and a fixed version.
- **Observed result:** ✅ Demonstrated correctly. `pip-audit` flagged
  `pyyaml 5.3.1` against a known advisory and recommended upgrading to
  5.4. This is the same class of check Trivy/Grype will run automatically
  in the CI pipeline in Phase 3 — this entry proves the underlying problem
  is real and catchable before that automation exists.
- **Evidence:** `docs/demos/vulnerable-dependency-cve.png`
- **PCI DSS:** Req 6.3 (vulnerability management), Req 6.3.2 (component
  inventory / known-vulnerability tracking)
- **Follow-up:** Re-run this scenario once Trivy/Grype are wired into
  GitLab CI (Phase 3) to confirm the same finding surfaces automatically
  as a failed pipeline job, not just a manual local check.

### [#07] Vulnerable container image (latest tag, root, CVE dependencies, bloated packages, baked-in secret)

- **Phase / layer:** Phase 2 / Container — image build & scan
- **Date:** 2026-08-21
- **Attacker action:** N/A — this scenario demonstrates that a container
  built without hardening (unpinned base, root user, vulnerable Python
  dependency, unnecessary packages) is caught by image scanning before it
  reaches a registry or cluster.
- **Vulnerable commit:** `vulnerable-demo`@[2dce733](https://github.com/poxka/spp/commit/2dce733)
- **Control under test:** Trivy image scan (`trivy image`, local for now;
  same check runs as a CI gate starting Phase 3)
- **Hypothesis:** An image built from `python:latest`, running as root, with
  `pyyaml==5.3` and unnecessary packages (`vim`, `net-tools`,
  `iputils-ping`, `openssh-client`) should surface multiple HIGH/CRITICAL
  findings, in contrast to the hardened `main` image.
- **Steps to reproduce:**
  1. `docker build -t securepay-api:vulnerable app/` (`vulnerable-demo`
     Dockerfile)
  2. `trivy image securepay-api:vulnerable`
  3. Compare against `main`: `trivy image --severity HIGH,CRITICAL
     --ignore-unfixed --ignorefile app/.trivyignore securepay-api:local`
- **Expected defense:** Scanner reports CVE-2020-14343 plus additional
  findings from the unpinned base and extra packages; `main` stays clean.
- **Observed result:** ✅ Far more than expected. `python:latest` resolved
  to **Debian 13.6 (trixie) with Python 3.14** at build time — not the
  Debian 12 / Python 3.11–3.12 range assumed when writing the Dockerfile.
  That alone produced **557 OS-level HIGH/CRITICAL findings**, most traced
  back to the extra packages pulled in (`vim` alone accounts for a cluster
  of RCE-class CVEs: CVE-2026-59856, -59858, -73072, -73076, -73077,
  -73078). At the Python-dependency layer: **4 findings (2 HIGH, 2
  CRITICAL)** — `pyyaml 5.3` hit both CVE-2020-14343 (CRITICAL) and
  CVE-2020-1747 (bundled), plus two unplanted transitive findings,
  `msgpack` (HIGH, GHSA-6v7p-g79w-8964) and `setuptools` (HIGH,
  CVE-2025-47273, path traversal) — neither was deliberately introduced,
  both came in as dependencies of dependencies. **Bonus cross-layer
  finding:** Trivy's secret scanner independently caught the hardcoded AWS
  access key from `config.py` (see `#01`) baked into the image layer —
  proof that even if a secret slipped past pre-commit, image scanning is a
  second independent rubezh catching the same class of leak.
- **Evidence:** `docs/demos/vulnerable-image/`
- **PCI DSS:** Req 6.3 (vulnerability management), Req 2.2 (secure
  configuration standards — unpinned base, root user), Req 3 (exposed
  credentials in a build artifact)
- **Follow-up:** The `latest`-tag non-determinism (trixie instead of the
  assumed bookworm) is itself a finding worth calling out at interview —
  it's the exact failure mode digest-pinning in `main`'s Dockerfile
  (ADR-0005) exists to prevent: without a pin, the "same" build can
  silently shift its entire base OS and CVE surface between two runs.
  Re-run this scenario once wired into the GitLab CI container-scan job
  (Phase 3) to confirm automatic failure, same as `#06`.

### [#08] Unpatched CRITICAL CVEs surfaced in the runtime base image (real, unplanned)

- **Phase / layer:** Phase 3 / Dependencies & Image — container scan
- **Date:** 2026-08-26
- **Attacker action:** N/A — this wasn't a planted `vulnerable-demo`
  scenario. It's a real finding the `trivy-image` CI job produced against
  `main` while the Phase 3 pipeline was still being wired up, before any
  vulnerable-demo work touched this stage.
- **Vulnerable commit:** `main`@[5d11e80c](https://github.com/poxka/spp/commit/5d11e80c)
- **Control under test:** `trivy image` in the `container-scan` stage,
  CRITICAL-only gate (`--severity CRITICAL --exit-code 1`)
- **Hypothesis:** The pinned, digest-locked distroless runtime image
  should be clean of CRITICAL CVEs, since Phase 2's `.trivyignore`
  (see `#07`) was written and reviewed against the same base image.
- **Steps to reproduce:**
  1. Push a commit to `main` and let the GitLab CI `container-scan` stage
     run against the built runtime image.
- **Expected defense:** Job passes if the image has no CRITICAL findings
  not already covered by `.trivyignore`.
- **Observed result:** ✅ Missed then caught.The gate correctly failed
  with two CRITICAL findings not covered by the existing `.trivyignore`:
  - `CVE-2025-7458` (`libsqlite3-0`, installed `3.40.1-2+deb12u2`) — a
    real, still-unpatched integer overflow in SQLite's
    `sqlite3KeyInfoFromExprList`. Upstream fixed it in SQLite ≥3.41.2;
    Debian's bookworm point release hadn't backported the fix yet at
    scan time. Exploitation requires the ability to already execute
    arbitrary SQL — with SQLAlchemy's parameterized queries on `main`,
    there's no direct injection path to this, but the CVE itself
    remains open at the OS-package level.
  - `CVE-2023-45853` (`zlib1g`) — a well-documented false positive.
    The CVE only affects MiniZip code inside zlib's source tree; Debian
    doesn't build MiniZip into the `zlib1g` binary package at all
    (bookworm marks the CVE `<ignored>` upstream), so this package is
    not actually affected despite matching on version.
  Both were added to `.trivyignore` with justification and a review-by
  date, following the same pattern as the Phase 2 entries — the SQLite
  one flagged for re-check once Debian backports the patch, not
  suppressed indefinitely.
- **Evidence:** `docs/demos/trivy-critical-catch.png`
- **PCI DSS:** Req 6.3 (vulnerability management), Req 6.3.2 (component
  inventory / known-vulnerability tracking)
- **Follow-up:** Re-check `CVE-2025-7458` against future distroless
  digest bumps — drop the ignore entry as soon as Debian ships the
  patched `libsqlite3-0` build.

**Why this entry matters more than a planted one:** every other entry in
this log is a deliberately staged scenario on `vulnerable-demo`. This one
wasn't staged — it's the same class of control as `#07`
(image-layer scanning) catching something real on `main` during its own
CI construction, which is a stronger proof point than a scripted demo:
the gate did its job before the project had even asked it to yet.

### [#09] Gitleaks/TruffleHog CI-layer secret detection

- **Phase / layer:** Phase 3 / Source — secret detection
- **Date:** 2026-09-27
- **Attacker action:** Push code with hardcoded AWS credentials and a JWT
  signing secret directly in source (`app/src/config.py`).
- **Vulnerable commit:** `vulnerable-demo`@[e59dd1d](https://github.com/poxka/spp/commit/e59dd1d)
- **Control under test:** `gitleaks` and `trufflehog` jobs in the
  `secret-scan` stage, both fail-closed on any finding
- **Hypothesis:** A secret committed to the vulnerable-demo branch
  should be caught automatically the moment CI runs against it, without
  needing a local pre-commit hook.
- **Steps to reproduce:**
  1. Push `vulnerable-demo` (containing commit `e59dd1d`) to GitLab.
  2. Observe the `secret-scan` stage.
- **Expected defense:** Both jobs fail with a redacted finding pointing
  at the exact file/line.
- **Observed result:** ✅ Caught by both scanners independently:
  - Gitleaks: `aws-access-token` rule at `app/src/config.py:41`, plus a
    `python-typed-secret-assignment` match on the JWT secret at line 43.
  - TruffleHog: same AWS key, flagged `unverified`.
- **Evidence:** `docs/demos/vulnerable-demo-ci-run/secret-scan.png`
- **PCI DSS:** Req 6.2, 6.3 (secure SDLC), Req 8 (credential management)
- **Follow-up:** none — this control is fully proven end-to-end.

### [#10] Semgrep SAST CI-layer catch (JWT bypass, SQL injection, and root Dockerfile)

- **Phase / layer:** Phase 3 / Source — SAST
- **Date:** 2026-08-27
- **Attacker action:** Disable JWT signature verification, allow the
  `none` algorithm, build a raw SQL query with `sqlalchemy.text()`
  instead of parameterized ORM calls, and ship a Dockerfile with no
  `USER` instruction.
- **Vulnerable commit:** `vulnerable-demo`@[09569dc8](https://github.com/poxka/spp/commit/09569dc8)
- **Control under test:** `semgrep` job in the `sast` stage, gated on
  `--severity=ERROR`
- **Hypothesis:** Ruleset `p/security-audit` + `p/jwt` should flag both
  the JWT and SQL injection classes of vulnerability without any
  custom rules.
- **Steps to reproduce:**
  1. Push `vulnerable-demo` to GitLab.
  2. Observe the `semgrep` job.
- **Expected defense:** Job fails with findings for each planted issue.
- **Observed result:** ✅ 4 findings, all correctly classified:
  - `python.jwt.security.jwt-none-alg` — `none` algorithm allowed
  - `python.jwt.security.unverified-jwt-decode` — signature verification
    disabled
  - `python.sqlalchemy.security.audit.avoid-sqlalchemy-text` — raw SQL
    injection surface via `text(query)`
  - `dockerfile.security.missing-user.missing-user` — no non-root `USER`
- **Evidence:** `docs/demos/vulnerable-demo-ci-run/sast.png`
- **PCI DSS:** Req 6.2, 6.3 (secure coding — injection, auth bypass),
  Req 8 (authentication)
- **Follow-up:** none — control fully proven end-to-end.

### [#11] Trivy SCA CI-layer catch (Known-CVE dependency, dependency scan)

- **Phase / layer:** Phase 3 / Dependencies — SCA
- **Date:** 2026-08-27
- **Attacker action:** Pin `pyyaml==5.3.1`, a version with a known
  incomplete-fix CVE, as a direct dependency.
- **Vulnerable commit:** `vulnerable-demo`@[09569dc8](https://github.com/poxka/spp/commit/09569dc8)
- **Control under test:** `trivy-fs` job in the `sca` stage, gated on
  `--severity CRITICAL`
- **Hypothesis:** Trivy's filesystem scanner should flag the pinned
  version against its vulnerability DB from `requirements.txt` alone,
  before any image is even built.
- **Steps to reproduce:**
  1. Push `vulnerable-demo` to GitLab.
  2. Observe the `trivy-fs` job.
- **Expected defense:** Job fails, CRITICAL finding on `pyyaml`.
- **Observed result:** ✅ `CVE-2020-14343` (CRITICAL) flagged directly
  against `requirements.txt`, installed version `5.3.1`, fixed version
  `5.4`.
- **Evidence:** `docs/demos/vulnerable-demo-ci-run/sca.png`
- **PCI DSS:** Req 6.3 (vulnerability management)
- **Follow-up:** none — control fully proven end-to-end. Note for
  `#12`: the image-layer scan against the same dependency surfaced a
  second, related CVE that the filesystem scan didn't — see below.

### [#12] Trivy container-scan CI-layer catch (Known-CVE dependency and hardcoded secret, container scan)

- **Phase / layer:** Phase 3 / Image — container scan
- **Date:** 2026-09-01
- **Attacker action:** Same as `#09` and `#11`, now observed against the
  actually built container image rather than source or dependency
  manifest.
- **Vulnerable commit:** `vulnerable-demo`@[985a2158](https://github.com/poxka/spp/commit/985a2158)
- **Control under test:** `trivy-image` job in the `container-scan`
  stage, gated on `--severity CRITICAL`
- **Hypothesis:** Scanning the built image should independently confirm
  both the dependency CVE and the hardcoded secret, this time at the
  image-layer level rather than the source/manifest level — proving the
  same class of vulnerability gets caught redundantly at multiple
  points in the pipeline, not just once.
- **Steps to reproduce:**
  1. Push `vulnerable-demo` to GitLab, let `build` produce an image.
  2. Observe the `trivy-image` job.
- **Expected defense:** Job fails with CRITICAL findings on both the
  dependency and the embedded secret.
- **Observed result:** ✅ Caught, with a bonus finding the filesystem
  scan didn't surface:
  - `PyYAML` CRITICAL — `CVE-2020-14343` (same as `#11`) **and**
    `CVE-2020-1747` (arbitrary command execution via
    `python/object/new` when `FullLoader` is used) — the image-layer
    scan resolved a second, related CVE against the installed package
    metadata that the requirements-file scan alone didn't surface.
  - Secret scanning caught the same AWS access key from `#09`, this
    time flagged directly against the image layer added by
    `COPY src ./src` in `/app/src/config.py` — independent confirmation
    that the secret is live in the shipped artifact, not just in git
    history.
  - A large tail of OS-package CRITICALs from the unpinned `python:latest`
    base image.
- **Evidence:** `docs/demos/vulnerable-demo-ci-run/container-scan.png`
- **PCI DSS:** Req 6.3 (vulnerability management), Req 2 (secure
  configuration — unhardened base image), Req 8 (credential exposure)
- **Follow-up:** none — this closes out the full set of Phase 3 CI-layer
  demo scenarios. Worth noting in the interview: `#11` and `#12` together
  demonstrate that dependency scanning at the manifest level and at the
  image level aren't fully redundant — the image scan found a CVE the
  filesystem scan missed, which is itself a small argument for running
  both layers rather than treating one as a superset of the other.
