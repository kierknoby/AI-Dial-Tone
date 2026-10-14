# Session lifecycle and termination

The current Peer Lab has three session states: `awaiting_peers`, `running`, and `ended`. These are **local session states**, not SIP dialog states.

## Sequence

1. An operator creates a task mandate for one named caller and one named peer.
2. The caller starts a session with a unique `Idempotency-Key`; the mandate cannot be spent twice.
3. Both peers obtain independently authorised single-use tickets and connect before a 15-second join deadline.
4. The service changes the session to `running`, starts the operator-set maximum duration (1–120 seconds), and relays events and PCM.
5. A peer hangs up, disconnects, the operator revokes/stops, or the server's deadline expires. The server emits `session.ended` and closes both sockets.

## What a closure means

`HARD_DEADLINE` means the **local** relay stopped the session, not a carrier released a channel. `HUMAN_STOPPED` and `HUMAN_CANCELLED` demonstrate operator authority over the lab, not independently enforced Asterisk hangup. `TRANSPORT_DISCONNECTED` means the experiment lost a peer. A future calling adapter must reconcile actual SIP and carrier state after any timeout, crash, replay, or ambiguous disconnect.

## Retry semantics

A caller may safely retry the same session creation request only with the same mandate and idempotency key. Reusing the key with a different mandate fails. Replaying a used admission ticket or already consumed mandate fails. Retrying a **real** call must never be justified by a transport uncertainty alone.
