# Events, evidence, and truthful outcomes

The server keeps a bounded **local** event list with a monotonically increasing sequence and a SHA-256 hash chain. Each event identifies the peer role or system; accepted text is explicitly tagged as an **unverified model assertion**.

## Representative events

- `session.created`: a caller consumed a lab mandate.
- `peer.joined`: an assigned agent admitted with a single-use ticket.
- `session.connected`: both assigned parties joined the local relay.
- `agent.utterance`: text the agent **asserted**, not necessarily recognised from PCM.
- `media.frame_batch`: aggregate frame accounting, not independent speech content verification.
- `media.utterance_ended` and `media.interruption_requested`: protocol signals, not guaranteed TTS cancellation.
- `session.ended`: a locally observed terminal event with reason.

`GET /v1/sessions/{sid}` returns the session summary and attributed events to assigned parties. It does **not** return an immutable external audit log, signed PBX CDR, consent proof, restaurant confirmation or payment receipt.

## Event evidence has limits

A hash chain makes tampering detectable only if a trusted observer retained the earlier hash and the generating process itself is trusted. It cannot confirm that a carrier call ended or that a table was booked. **Never mark `booking_verified=true` or `real_phone_call=true` from model dialogue.** The service returns both as false.

The event journal has a fixed safety quota; `session.ended` remains possible even when ordinary event emission is exhausted. The lab has no persistence, backups, retention controls or distributed event replay. See [Release readiness](13-readiness.md).
