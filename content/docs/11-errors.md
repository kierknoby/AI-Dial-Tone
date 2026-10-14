# Errors and recovery rules

Most Peer Lab REST errors return an HTTP error status and `{ "error": "UPPERCASE_CODE" }`. WebSocket protocol errors are similarly explicit. **Do not convert an error into a reported booking success.**

## Typical failure cases

| Code | Meaning | Safe response |
| --- | --- | --- |
| `UNAUTHORISED` | Missing/invalid bearer | Stop; obtain legitimate credentials |
| `OPERATOR_ONLY`, `CALLER_ONLY`, `PEER_ONLY` | Wrong role | Stop, do not substitute another principal |
| `MANDATE_EXPIRED`, `MANDATE_REVOKED`, `MANDATE_ALREADY_USED` | No valid mandate | Obtain new operator authorisation |
| `IDEMPOTENCY_KEY_REQUIRED`, `IDEMPOTENCY_CONFLICT` | Missing/reused key | Fix caller transaction; do not dial again automatically |
| `INVALID_OR_REPLAYED_TICKET`, `ADMISSION_TIMEOUT` | Failed one-use WebSocket admission | Re-authenticate only if session is still joinable |
| `INVALID_PCM_FRAME`, `REPLAYED_OR_INVALID_PCM`, `MEDIA_RATE_LIMIT` | Malformed, duplicated or excessive media | Stop/slow source, preserve evidence |
| `EVENT_QUOTA_EXCEEDED`, `MANDATE_CAPACITY_EXCEEDED`, `SESSION_CAPACITY_EXCEEDED`, `TICKET_CAPACITY_EXCEEDED` | Bounded resource exhausted | Restart local laboratory; never bypass limits |
| `HARD_DEADLINE`, `TRANSPORT_DISCONNECTED`, `PEER_JOIN_TIMEOUT` | Local session ended | Treat as laboratory closure only; no carrier evidence |

## Fail closed

The voice runtime must stop or report uncertainty when ASR, model or TTS fails. A remote agent's text is not trusted ASR evidence. Reconnecting on ambiguous state may cause repeated action in a future real network and must wait for authoritative provider reconciliation.

There is no live customer support, SLA, external provider callback or production fraud response process in 0.0.1.
