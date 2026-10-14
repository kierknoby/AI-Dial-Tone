# HTTP API: runnable local Peer Lab

**Source:** `peer-lab/peer_lab.py`. **Base URL:** `http://127.0.0.1:8765`. This is a local development service, **not** `https://ai.dial-tone.uk/v1/` and **not** a SIP-call API.

## Operations

| Method | Path | Credential | Purpose |
| --- | --- | --- | --- |
| GET | `/v1/capabilities` | None | Verify explicitly non-PSTN capabilities |
| POST | `/v1/mandates` | Operator | Issue bounded local mandate |
| POST | `/v1/mandates/{mid}/revoke` | Operator | Cancel mandate and attached session |
| POST | `/v1/sessions` | Caller | Start one mandate, with `Idempotency-Key` |
| GET | `/v1/peers/inbox` | Peer | List only own waiting sessions |
| GET | `/v1/sessions/{sid}` | Caller or assigned peer | Scoped state and event journal |
| POST | `/v1/sessions/{sid}/stop` | Operator | Force an independent lab stop |
| POST | `/v1/sessions/{sid}/tickets` | Assigned caller or peer | Create one-use WebSocket admission |
| GET WebSocket | `/v1/sessions/{sid}/connect` | Single-use ticket in first frame | Duplex events and PCM |

## Example mandate

```http
POST /v1/mandates HTTP/1.1
Host: 127.0.0.1:8765
Authorization: Bearer <OPERATOR_TOKEN>
Content-Type: application/json

{"caller_id":"demo-caller","peer_id":"demo-restaurant","task":"Ask a fictional restaurant about a table","max_seconds":40}
```

Next, the caller creates a session with `{ "mandate_id": "<mandate_id>" }` and an ASCII `Idempotency-Key` of 12–128 printable characters. The operator may revoke the mandate or stop the session at any point. This is a **simulated task conversation**; no restaurant is contacted.

The [OpenAPI 3.1 specification](/api/openapi.json) is copied from this repository's `peer-lab/openapi.json`. `https://ai.dial-tone.uk/api/openapi.json` is only a **download URL for documentation**, not the service base URL. HTTP errors use `{ "error": "CODE" }`. Never infer a successful real-world booking from local `session.ended`.
