# `k8s/` — Kubernetes manifests & policies

Kubernetes defense-in-depth. Policies are developed locally in **kind** (free,
fast) and validated on **EKS** in bursts.

## Layout

- `base/` — app workload: Deployment, Service, ServiceAccount, NetworkPolicy
  (every workload ships with a security context — non-root, read-only rootfs,
  drop ALL caps, seccomp RuntimeDefault, resource limits)
- `policies/kyverno/` — admission policies (primary)
- `policies/gatekeeper/` — 2–3 equivalents for the Kyverno-vs-Gatekeeper ADR
- `rbac/` — role split: `dev` / `ops` / `security` / `audit`
- `istio/` — PeerAuthentication (mTLS STRICT), AuthorizationPolicy
- `vault/` — External Secrets Operator, SecretStore

## Defense layers represented here

Network Policies (default-deny microsegmentation) · Pod Security Admission
(`restricted`) · Kyverno admission control · Istio mTLS + AuthZ · RBAC least
privilege.

> Status: scaffolded in Phase 0. Baseline lands in Phase 5; policies/mesh/secrets
> in Phases 6–8.
