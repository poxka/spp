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

Copy this block for each new scenario.

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

*No scenarios recorded yet. The first entries land in Phase 3 (CI gates:
hardcoded secret, CVE dependency, SQLi / `alg:none`, image with CVE).*

| #   | Scenario            | Layer | Control | Status | Phase | Evidence |
| --- | ------------------- | ----- | ------- | ------ | ----- | -------- |
| —   | *(pending Phase 3)* | —     | —       | ⏳      | —     | —        |
