# `app/` — Payment API (FastAPI)

The **object of defense**, not the star of the project. A minimal but realistic
payment microservice so the security tooling has something real to bite on.
If you're tempted to add a feature here — stop, and invest that time in the
platform around it instead.

## What lives here

- `src/` — FastAPI application (async, OpenAPI out of the box — feeds DAST later)
- `tests/` — minimal tests
- `Dockerfile` — multi-stage, non-root, read-only rootfs, pinned base (Phase 2)
- `docker-compose.yml` — local dev: API + PostgreSQL (Phase 1)

## Scope (and only this)

`POST /auth/login` · `POST /transactions` · `GET /transactions/{id}` ·
`GET /transactions` · `GET /health` · `GET /metrics`

**No real PANs.** `card_token` is a UUID reference to a "stored card" —
tokenization as PCI scope reduction (Req 3).

## Branches

- `main` — secure reference (Pydantic validation, parametrized SQL, strict JWT).
- `vulnerable-demo` — planted vulns for the attack demos (see
  [ADR-0002](../docs/adr/0002-two-branch-strategy.md)).

> Status: scaffolded in Phase 0. Implementation lands in Phase 1.
