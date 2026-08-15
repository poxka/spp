# `observability/` — Prometheus / Grafana / Loki / Alertmanager

Security-focused observability, not generic monitoring. The flagship artifact is
the Grafana **"Security Posture"** dashboard.

## What lands here

- Prometheus config + scrape targets (API `/metrics`, Falco, Kyverno, Istio)
- Grafana dashboards (exported JSON, version-controlled) — Security Posture:
  admission denials, Falco alerts by severity, mTLS coverage, CVE trend,
  failed-auth attempts, rate-limit hits
- Loki config — log + audit-log aggregation (K8s audit, Vault audit)
- Alertmanager routing (reused from Phase 9 → Telegram)

## Secure defaults

Grafana/Prometheus/Loki are never exposed to the internet (ingress + auth, RBAC
on dashboards); metrics carry no sensitive data.

> Status: scaffolded in Phase 0. Implementation lands in Phase 11 (partially
> earlier — handy to see demos actually fire).
