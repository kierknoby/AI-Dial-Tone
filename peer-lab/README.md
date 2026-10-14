# AI Dial-Tone Peer Lab · 0.0.1

**Real network communication between two independent agent processes. Local-only development software.**

This laboratory is the first runnable **agent-to-agent interaction service** in the standalone public repository. Two separately authenticated programs connect over real WebSockets, exchange live **16 kHz, mono, PCM16 audio**, exchange text turns and DTMF, request interruption, signal utterance completion, and end the session. A distinct operator role issues and revokes short-lived, single-use mandates.

**It is NOT a SIP telephone, Asterisk integration, x402 service, PSTN gateway, real restaurant booking platform, or hosted AI model.** The new optional audio-first path supports an offline experimental recogniser and external compatible ASR APIs; it remains inappropriate for real bookings. The included demo uses two deterministic agents and text-sidecar dialogue. Audio is synthesised locally (eSpeak when available, tone fallback); it proves that PCM flows correctly, **not** that a model understood incoming speech. MicroSIP's SIP OPTIONS readiness checks are not run by this service.

## Run a full conversation

From the repository root, Python 3.11+ and aiohttp 3.13.x are required. Optional: `espeak` and `ffmpeg` for audible English speech in the proof WAVs.

```sh
python -m pip install 'aiohttp==3.13.3'
python tools/verify_first_call.py --out demo-output
python -m unittest discover -s peer-lab/tests -p 'test_*.py' -v
```

**Outputs:** `demo-output/proof.json`, `caller_heard.wav`, `peer_heard.wav`, and `verification.json`. The final file independently checks the local session evidence and explicitly declines any real PSTN, model, payment or booking claims. The two WAVs contain actual PCM delivered across independent client connections, not audio copied directly from the synthesiser. `proof.json` gives the event hash chain, call termination reason, per-direction frame counts, and transcript assertions. No real restaurant is contacted or reservation made.

To run the admission server independently, from the `peer-lab/` directory (generates *fresh local-only* credentials and prints them to the terminal):

```sh
python peer_lab.py --host 127.0.0.1 --port 8765
```

For this 0.0.1 release, the in-memory service also caps itself at 256 mandates, 128 sessions and 256 outstanding tickets; restart the local lab to discard the data. It is deliberately not a persistent, multi-tenant service.

Do **not** publish this development server on the Internet. Its credentials and in-memory event journal are not designed for production operations.

## Two separate identities and a human authority

Three bearer credentials are generated or supplied at startup, each at least 24 characters:

- **operator**: represents a lab human. Creates, revokes, and stops one bounded experiment; cannot pretend to be either bot.
- **caller**: the requesting AI. Can use an operator-issued mandate and join only its own session.
- **peer**: the other AI. Can see only its own pending inbox and join as the named destination peer.

Example request sequence using placeholder tokens:

```http
POST /v1/mandates
Authorization: Bearer <OPERATOR_TOKEN>
Content-Type: application/json

{"caller_id":"demo-caller","peer_id":"demo-restaurant","task":"Ask a fictional restaurant about a table","max_seconds":40}
```

That produces a `mandate_id`. Then:

```http
POST /v1/sessions
Authorization: Bearer <CALLER_TOKEN>
Idempotency-Key: intent-demo-0000000001
Content-Type: application/json

{"mandate_id":"<mandate_id>"}
```

Both bot clients separately call `POST /v1/sessions/{session_id}/tickets` with their **own** identities, then connect to `/v1/sessions/{session_id}/connect` as a WebSocket. Their **first** message must be `{"type":"admit","ticket":"<ticket>"}` within four seconds. Tickets are single-use, session-bound and expire in 20 seconds. The operator may call `POST /v1/mandates/{mandate_id}/revoke` or `POST /v1/sessions/{session_id}/stop` at any moment.

### Message formats

The WebSocket accepts JSON text messages:

| Sender | JSON | Meaning |
| --- | --- | --- |
| Client | `{"type":"say","text":"..."}` | Agent-asserted transcript text, relayed and logged as unverified speech intent |
| Client | `{"type":"dtmf","digits":"123#"}` | DTMF **event** delivered to the other AI peer, **not** generated tones on a SIP call |
| Client | `{"type":"audio.end"}` | End of that peer's current PCM utterance |
| Client | `{"type":"audio.interrupt"}` | Interruption request; receiving bot must decide how to cancel its TTS playback |
| Client | `{"type":"hangup"}` | End this peer session; both peers see `session.ended` |
| Client | `{"type":"ping"}` | Return `pong` |
| Server | `{"type":"session.connected", ...}` | Both independent participants admitted; session deadline starts |
| Server | `{"type":"session.ended","reason":"..."}` | Authoritative **lab WebSocket session** closure, not carrier hangup evidence |

Binary PCM packets are exactly **656 bytes**:

| Offset | Bytes | Meaning |
| --- | --- | --- |
| 0 | 4 | ASCII `DT01` |
| 4 | 4 | Unsigned 32-bit big-endian strictly increasing frame sequence |
| 8 | 8 | Unsigned 64-bit big-endian frame timestamp in milliseconds |
| 16 | 640 | Signed 16-bit little-endian PCM, mono, 16,000 Hz, 20 milliseconds |

**Audio frames and transcript messages are distinct.** A model-generated text assertion is not a trustworthy speech recognition transcript. Production speech bridges need ASR and TTS adapters, speech-to-text timing alignment, interruption cancellation, backpressure, and an independently authenticated signalling plane.

### Session and failure semantics

`awaiting_peers` → `running` → `ended`.

- Both bots must join within 15 seconds; otherwise `PEER_JOIN_TIMEOUT`.
- The server enforces the operator-specified call duration after both bots join, maximum 120 seconds: `HARD_DEADLINE`.
- A peer disconnect ends both sessions: `TRANSPORT_DISCONNECTED`.
- Human revocation and stop are authoritative to this local server: `HUMAN_CANCELLED` and `HUMAN_STOPPED`.
- Replaying an admission ticket, reusing a human mandate, or replaying a PCM frame is rejected.
- `GET /v1/sessions/{id}` returns the in-memory event history to authorised parties, with a SHA-256 hash chain. **The chain detects mutation against a previously retained hash; it is not independent proof of a real-world outcome.**
- No user account, persistence, invoices, charging, or calendar mutation is implemented. Restart destroys all mandates and sessions. Do not test with personal data.

## Integrate any AI model

`client.py` is deliberately model-neutral. Create a `PeerClient` with your HTTP session and bot credential; `await connect()`, then respond to `recv()` with calls to `say()`, `pcm()`, `dtmf()`, `interrupt()`, `audio_end()`, or `hangup()`. Bring your own model, ASR, and TTS.

The optional offline `examples/first_call.py` shows two independent clients without any proprietary AI SDK. **It does not demonstrate actual LLM inference or speech understanding**, but creates a reproducible network boundary and recorded PCM material for those integrations to test against.

## Security and relationship to MicroSIP

The native Windows Dial-Tone retains its MicroSIP/PJSIP stack and supported SIP TLS/SRTP modes. This Peer Lab is **not** a port of MicroSIP and doesn't implement SIP. No browser or bot can claim to inherit TLS, certificate verification, mandatory SRTP, registration, OPTIONS, codec negotiation, or PSTN reachability from it. Those checks belong in the independent Asterisk/provider bridge and must fail closed before any real call.

No production SIP trunk, telephone route, credentials, keys, backend source, or payments are included here.

See `openapi.json` (localhost-only machine-readable schema), `content/docs/18-peer-lab.md`, `ROADMAP.md`, and `REPOSITORY-POLICY.md`.

## Plug in a genuine AI language model

`model_adapter.py` has a tested, generic adapter for HTTP **chat-completions-compatible** endpoints. This is an interoperability profile, not a guarantee that every model provider implements the same API. The adapter rejects HTTP to non-loopback hosts, redirects, model tool calls, malformed output, and excessive turn/output budgets. It can optionally accept a TTS callback that returns fixed-rate PCM16. Its pending completion task is cancelled when the peer requests an interruption. No model is given telephone credentials, spend authority, payment permissions or calendar tools.

Set these variables **in the local terminal**, not in the repository or a prompt:

```sh
export AIDT_PEER_URL=http://127.0.0.1:8765
export AIDT_PEER_SESSION=<session_id_from_approved_mandate>
export AIDT_PEER_TOKEN=<own_agent_or_peer_token>
export AIDT_MODEL_URL=http://127.0.0.1:1234/v1/chat/completions
export AIDT_MODEL_NAME=<your_local_model_identifier>
# Optionally export AIDT_MODEL_KEY via a secure secret manager for an HTTPS-hosted provider.
python examples/model_peer.py
```

The included `tests/test_model_adapter.py` starts a separate HTTP completion fixture and proves that a peer message crosses a WebSocket, triggers a real HTTP chat-completion request, returns the model's text, sends a TTS-provided PCM frame sequence, and never reports a real reservation. This is **an integration test with a fake model service, not a live third-party model run**. A real model endpoint and speech recogniser must still be evaluated separately before public calling.

## Audio-first speech pipeline (0.0.1)

`voice_peer.py` + `speech.py` implement **received PCM → VAD → optional ASR → model → TTS → returned PCM**, including interruption, frame bounds, and operator stop. See `content/docs/19-audio-first-voice.md` and `examples/audio_first_call.py`. Experimental PocketSphinx accuracy was insufficient for bookings. The model side of the local audio demonstration is deterministic; no hosted model has been tested.
