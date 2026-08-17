# Payment API (`app/`)

The SecurePay payment microservice — the object the platform's security
controls defend

Status: **Phase 1 complete on `main`** (secure reference implementation). The
`vulnerable-demo` branch with planted flaws comes in a later pass.

## Stack

FastAPI (async) · SQLAlchemy 2.0 (async, asyncpg) · Pydantic v2 ·
PostgreSQL · PyJWT · bcrypt · structlog · slowapi · Prometheus instrumentator.

## Endpoints

| Method | Path | Auth | Notes |
| --- | --- | --- | --- |
| POST | `/auth/login` | no | Returns a JWT; rate-limited |
| POST | `/transactions` | yes | Create a transaction |
| GET | `/transactions/{id}` | yes | Owner-scoped; 404 if not owned |
| GET | `/transactions` | yes | Owner-scoped list with filters |
| GET | `/health` | no | Liveness (no DB) |
| GET | `/health/ready` | no | Readiness (DB ping) |
| GET | `/metrics` | no | Prometheus; network-restricted later |

No real PANs are handled anywhere. `card_token` is a UUID reference to a card
stored in an out-of-scope tokenization vault.

## Layout

```text
app/
├── src/
│   ├── main.py            # app factory, middleware, router wiring, lifespan
│   ├── config.py          # settings (pydantic-settings), JWT/currency allowlists
│   ├── database.py        # async engine, session, Base
│   ├── dependencies.py    # current-user guard (Bearer JWT)
│   ├── middleware.py      # security headers + request-context logging
│   ├── ratelimit.py       # shared slowapi limiter
│   ├── logging_config.py  # structlog + sensitive-key redaction
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic request/response schemas
│   ├── security/          # JWT + password hashing
│   ├── services/          # DB access
│   └── routers/           # auth, transactions, health
├── tests/                 # pytest (in-memory SQLite)
├── Dockerfile             # dev image (non-root); hardened in Phase 2
├── docker-compose.yml     # API + PostgreSQL for local dev
├── requirements.txt       # runtime deps (pinned)
├── requirements-dev.txt   # test deps (pinned)
└── .env.example           # config templates
```

## Security defaults applied

- JWT decoded with a fixed algorithm allowlist; `alg=none` and HS/RS confusion
  are structurally impossible. `exp`/`iat`/`sub` required.
- ORM with bound parameters only — no string-built SQL.
- Transactions scoped by `owner_id`; a non-owned id is a 404 (no IDOR leak).
- Login: identical 401 for unknown user and wrong password, bcrypt timing
  parity, per-IP rate limit.
- Money as `Numeric(18,2)`, serialized as a string (no float).
- Structured logs with a redaction processor; `card_token`, passwords and
  tokens never reach the log sink.
- Strict CORS allowlist; security headers (HSTS, strict CSP, nosniff, frame
  deny, no-store); `Server` header stripped.
- Interactive docs and the OpenAPI schema are served in `local` only.

## Run locally

### Docker Compose (API + PostgreSQL)

```bash
cp .env.example .env
docker compose up --build
```

API on `http://127.0.0.1:8000`, docs on `http://127.0.0.1:8000/docs`.
With `SEED_USER`/`SEED_PASSWORD` set, that login user is created on startup.

### Bare metal

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn src.main:app --reload --no-server-header
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Tests use in-memory SQLite via a dependency override, so no external database
is required — the same suite runs unchanged in CI.

## Not here yet

- `vulnerable-demo` branch (planted flaws for the attack demos).
- Hardened multi-stage Dockerfile — Phase 2.
- Secrets from Vault instead of env — Phase 7.
- Schema migrations (Alembic): local dev auto-creates tables; migrations land
  with the persistent environments.
