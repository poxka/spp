# `security/` — Security tooling, rules & automation

The custom security glue: runtime rules, policy-as-code, and Python automation.

## Layout

- `falco/` — Falco rules for attacker TTPs + alerting wiring (Phase 9)
- `scripts/` — Python: boto3 automation, the Falco→Telegram alert bot (Phase 9),
  custom checks
- `policies/` — Semgrep rules, OPA/Rego policies

## Notes

- The Telegram alert bot is where the Python background shows up — a custom
  Falco → Alertmanager → Telegram integration.
- Runtime rules are tuned against alert fatigue on purpose; noisy detection that
  nobody trusts is worse than none (that tuning is itself part of the story).

> Status: scaffolded in Phase 0. Falco + alerting land in Phase 9; Semgrep/OPA
> rules alongside the CI pipeline (Phase 3) and admission (Phase 6).
