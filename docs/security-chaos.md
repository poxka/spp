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
