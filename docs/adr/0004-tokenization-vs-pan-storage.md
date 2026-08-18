# ADR-0004: Tokenization instead of storing PANs

- **Status:** Accepted
- **Date:** 2026-08-17
- **Deciders:** Project owner (solo)
- **Phase:** Phase 1
- **PCI DSS touchpoints:** Req 3 (protect stored cardholder data), Req 3.4 (render PAN unreadable)

## Context

The service records payment transactions, each tied to a card. The way card
data is handled decides how much of the system falls under PCI DSS scope.

Under PCI DSS, any component that stores, processes, or transmits a Primary
Account Number (PAN) is in scope for Req 3 and drags a heavy set of controls —
encryption, key management, access control, retention limits, audited
deletion — onto that component and often onto everything it touches.

The cheapest way to satisfy a control is to remove the need for it. If the
service never holds a PAN, it is out of scope for storing one. This is a
classic PCI **scope reduction** pattern and is one of the two or three
decisions a fintech interviewer will actually ask about, so it needs to be
explicit rather than incidental.

## Decision

I will store only a **tokenized reference** (`card_token`, a UUID) on each
transaction. Real card data is assumed to live in a separate tokenization
vault that is out of scope for this repository and that this service has no
access to.

## Alternatives considered

- **Store the raw PAN** — simplest to build, worst possible outcome: full
  PCI scope, maximum blast radius on any breach. Rejected outright.
- **Store an encrypted PAN** — keeps the service in scope for Req 3 (key
  management, rotation, access control) even though the data is encrypted.
  Rejected: pays the compliance cost without removing the underlying data.
- **Store nothing about the card** — not viable; a transaction has to
  reference which card it belongs to.

## Consequences

**Positive**

- The service is **out of PCI scope for cardholder-data storage** (Req 3):
  it holds no PAN to protect.
- **Blast radius is minimized** — a full database compromise leaks
  transaction metadata and opaque tokens, not card numbers.
- Compliance surface and control cost shrink accordingly for everything
  downstream (backups, logs, monitoring).

**Negative / trade-offs**

- Introduces an explicit **assumption**: an external tokenization vault
  exists and is correctly scoped. In this project the vault is notional and
  the assumption is documented in `docs/threat-model.md`.
- The service cannot derive or display card details, which is acceptable
  for its purpose and is in fact the point.

**Follow-ups**

- Log discipline: `card_token` values are treated as sensitive and never
  logged (enforced by the redaction processor in `logging_config.py`).
- Threat model records the vault as an out-of-scope trusted dependency.
- The PCI DSS mapping doc (Phase 13) cites this ADR under Req 3.

## Interview notes

Chose tokenization because the cheapest way to satisfy a PCI control is
to remove the need for it — no PAN in the service means no Req 3 scope
here at all.
