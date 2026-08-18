# ADR-0003: FastAPI as the API framework

- **Status:** Accepted
- **Date:** 2026-08-17
- **Deciders:** Project owner (solo)
- **Phase:** Phase 1
- **PCI DSS touchpoints:** Req 6.2 (secure coding), Req 6.5 (input validation)

## Context

The payment service needs a Python web framework. The choice is a security
decision as much as an ergonomic one, because the framework shapes how input
validation, authentication, and API surface are handled — all of which are
controls this project has to demonstrate.

Forces at play:

- Strong, declarative input validation is a shift-left security control; the
  framework should make it hard to skip.
- A machine-readable OpenAPI contract is needed later to point OWASP ZAP at in
  Phase 10 — hand-maintained specs drift and defeat DAST coverage.
- The service will sit behind a mesh and talk to a database and secret
  backends concurrently, so async I/O matches the target architecture.
- Attack surface should be proportional to what the service does: no
  framework features I don't use becoming controls I have to reason about.

## Decision

I will use **FastAPI** as the web framework for the payment API.

## Alternatives considered

- **Flask** — minimal and familiar, but validation, serialization, and
  OpenAPI are all bolt-on libraries assembled by hand, and it is WSGI/sync
  by default. Rejected: too much security-relevant plumbing left to me
  instead of the framework.
- **Django REST Framework** — mature, batteries included, but heavier than
  a minimal payment service needs. Sync-first, and brings a large surface
  (admin, ORM, middleware stack) I would not use. Rejected: attack surface
  and scope out of proportion to the service.

## Consequences

**Positive**

- Pydantic validation is a first-class security control, applied to every
  field before business logic sees the request.
- OpenAPI is generated automatically and feeds Phase 10 DAST directly.
- Async matches the rest of the platform; no sync/async rewrite later.
- Small explicit surface — only the endpoints I define exist.

**Negative / trade-offs**

- Async SQLAlchemy is more complex than the sync ORM most tutorials show.
- Smaller ecosystem than Django; things Django gives for free (admin,
  built-in ORM) are assembled explicitly.
- Requires an ASGI server (uvicorn) and ASGI-aware tooling everywhere.

**Follow-ups**

- Phase 10 DAST is wired against the generated OpenAPI spec, not a
  hand-maintained one.
- Phase 3 SAST rules (Semgrep) target the FastAPI + SQLAlchemy patterns
  used here.

## Interview notes

Chose FastAPI because input validation and the OpenAPI contract are
security controls I want the framework to enforce for me, not libraries
I have to remember to add.
