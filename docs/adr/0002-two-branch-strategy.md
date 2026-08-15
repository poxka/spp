# ADR-0002: Two-branch strategy — `main` (secure) and `vulnerable-demo`

- **Status:** Accepted
- **Date:** 2026-08-15
- **Deciders:** Project owner (solo)
- **Phase:** Phase 0 — Foundation
- **PCI DSS touchpoints:** Req 6.2/6.3 (secure SDLC, vuln management), Req 11.3 (regular security testing)

## Context

The killer feature of this project is **live attack scenarios**: we
deliberately introduce a vulnerable dependency / hardcoded secret / SQLi /
privileged pod / unsigned image, push it, and record each defense layer
catching it. That requires vulnerable code, manifests, and images to *exist
somewhere in the repo* — while `main` must stay a pristine, green, "this is
prod" reference.

Two constraints collide:

1. **`main` must always pass every gate** (pre-commit green, CI green). It's the
   secure reference implementation and the thing a reviewer trusts.
2. **The vulnerable material must be real**, not hand-waved. A hardcoded AWS key
   has to actually be in a file for gitleaks to catch it — which means the local
   pre-commit secret gate will (correctly) refuse to let us commit it normally.

We need a structure that lets both live in one monorepo (ADR-0001) without the
vulnerable side ever contaminating `main`.

## Decision

We will maintain **two long-lived branches**:

- **`main`** — the hardened reference. Every pre-commit hook passes; the full
  CI pipeline runs green. This is "prod".
- **`vulnerable-demo`** — a parallel branch carrying deliberately planted
  vulnerabilities, each as its own **atomic** conventional commit using the
  custom `demo:` type (see `commitlint.config.js`), e.g.
  `demo: introduce SQLi in GET /transactions`.

**The `--no-verify` agreement.** Commits on `vulnerable-demo` whose *entire
purpose* is to carry material that local hooks are designed to block (a
hardcoded secret, a merge-conflict marker in a fixture, etc.) are made with:

```bash
git commit --no-verify -m "demo: hardcode AWS key to trip gitleaks"
```

`--no-verify` bypasses **local** pre-commit hooks only. It does **not** bypass
CI. That distinction is the entire point of the demo:

> Even when a developer bypasses the local gate, the **server-side CI gate**
> (Phase 3) still catches it. Shift-left is layered, not a single gate.

So on `vulnerable-demo`, a red pipeline is the **expected, desired** outcome —
that failing job *is* the artifact we screencast. `main` stays fail-closed and
green; `vulnerable-demo` is fail-closed and (intentionally) red.

**Hard discipline (non-negotiable):**

- **Fake secrets only.** Every planted credential is a placeholder / invented
  value. Never a real key. A secret in git history is compromised forever, even
  after deletion — so we never let a real one in, not even to "make the demo
  realistic".
- **One vulnerability per commit.** So we can point at exactly one commit → one
  failed job on screen. No dumping five vulns into one commit.
- **Every planted vuln is logged** in `docs/security-chaos.md` (hypothesis,
  steps, expected defense, actual result, screencast link).
- **`vulnerable-demo` is never merged into `main`.** No MR from
  `vulnerable-demo` → `main`, ever. Enforced by branch protection on the host
  (GitHub) once configured.

## Alternatives considered

- **Single branch with feature flags / env toggles to "turn on" vulns.**
  Rejected: muddies the narrative, risks a vuln toggle leaking into the secure
  path, and there's no clean side-by-side secure-vs-vulnerable diff. It also
  defeats the "`main` is always clean" guarantee.
- **A separate repository for the vulnerable version.** Rejected: breaks the
  monorepo narrative (ADR-0001), and you lose the ability to diff
  `main`↔`vulnerable-demo` in one place, which is the most convincing view.
- **Just disable the hooks globally when doing demos.** Rejected: throws away
  the shift-left protection on *everything* while active, and the `--no-verify`
  approach already scopes the bypass to exactly the commits that need it.

## Consequences

**Positive**

- Clean, diffable secure-vs-vulnerable story in one repo.
- The `--no-verify` → red-CI flow is itself a teaching moment about layered
  gates (local hooks are convenience; CI is the enforcement boundary).
- `demo:` commit type makes the attack history self-documenting and greppable.

**Negative / trade-offs**

- `vulnerable-demo` will drift from `main` as `main` evolves. We periodically
  rebase / cherry-pick so the diff stays about the *vulnerabilities*, not
  incidental churn. This is manual upkeep.
- `--no-verify` is a sharp tool. Used anywhere on `main` it would defeat the
  purpose — so the rule is: `--no-verify` is **only** ever used on
  `vulnerable-demo`, and only for commits that intentionally carry blocked
  material.
- Risk of accidental merge to `main`. Mitigated by branch protection and the
  "never open that MR" rule.

**Follow-ups**

- Phase 3: CI must run on `vulnerable-demo` and is *expected* to fail; capture
  those failures as the first screencasts.
- Configure branch protection on GitHub (primary host) to block
  `vulnerable-demo` → `main` merges.

## Interview notes

"There are two branches. `main` is the secure reference — green through every
gate. `vulnerable-demo` carries planted vulns, one per commit. When a vuln is
literally a hardcoded secret, the local pre-commit gate correctly blocks it, so
I commit that one with `--no-verify` — which bypasses *local* hooks but not CI.
That's deliberate: it demonstrates that even if a dev skips the local gate, the
server-side pipeline still catches it. A red pipeline on `vulnerable-demo` is
the demo. And the secrets are always fake — because anything in git history is
there forever."
