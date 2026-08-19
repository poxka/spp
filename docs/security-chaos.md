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
| #01 | Gitleaks generic-api-key coverage gaps      | Source (pre-commit)   | Gitleaks    | ✅      | Phase 1 | [screenshots](./demos/secret-detections/) |
| #02 | JWT signature verification disabled       | Source / Auth        | JWT decode logic (app) | ✅      | Phase 1 | [screenshots](./demos/bad-jwt/) |

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
