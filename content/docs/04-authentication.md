# Authentication and permissions

The runnable Peer Lab uses three **distinct** bearer authorities. These are local test credentials, not real customer identities or legally sufficient human consent.

| Authority | Allowed actions |
| --- | --- |
| Operator | Issue a synthetic mandate, revoke it, terminate an existing lab session |
| Caller | Start one session from its assigned mandate, request a ticket, inspect its own events |
| Peer | Inspect only its assigned pending sessions, request its own ticket, inspect its own events |

## Connection admission

Agent clients call `POST /v1/sessions/{sid}/tickets` with their own bearer credentials. They receive a short-lived single-use ticket, then connect to `/v1/sessions/{sid}/connect` by WebSocket. The **first JSON message** must contain `{"type":"admit","ticket":"..."}` within four seconds. Tickets last at most 20 seconds. Replays and cross-role tickets fail.

All REST endpoints except `GET /v1/capabilities` require a bearer. Do not put bearer credentials in query strings, log them or upload terminal transcripts. The development server binds only to `127.0.0.1`, `::1`, or `localhost` from its CLI; it has not undergone public-facing security hardening.

## What approval does not prove

An operator bearer represents a **lab operator**, not a verified human subscriber. Future real calls need a server-held, authenticated human mandate, destination and budget policy, revocation at the provider, independent verification of termination, consent checks and records suitable for audit. An agent saying “the user approved” is not authorisation.
