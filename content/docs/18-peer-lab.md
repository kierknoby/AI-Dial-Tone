# The First Call: real AI peer laboratory

> **LOCAL NETWORK DEVELOPMENT ONLY. Not live telephony.** This chapter documents source under `peer-lab/` in the independent `kierknoby/AI-Dial-Tone` repository. It does not describe an API running at `ai.dial-tone.uk`.

## Why this exists

The earlier AI Dial-Tone work could describe an autonomous telephone conversation, but did not let two separately authenticated bot processes talk through an independently running service. The **AI Peer Lab** addresses that gap before a real Asterisk channel is introduced.

Two independent AI *clients* connect over WebSockets, using distinct credentials, and exchange actual bidirectional PCM16 frames and text/DTMF/control events. The local backend enforces human-issued scope, single-use admission, monotonic media sequences, and a session deadline. It does **not** place calls, listen to PSTN speech, perform ASR, or claim that a restaurant accepted a reservation.

## Quickstart: run a conversation, not a static fixture

From an extracted public-source package or the `main` branch of the standalone repository:

```bash
python -m pip install 'aiohttp==3.13.3'
python tools/verify_first_call.py --out demo-output
python -m unittest discover -s peer-lab/tests -p 'test_*.py' -v
```

For actual synthesised speech in `caller_heard.wav` and `peer_heard.wav`, install eSpeak and FFmpeg. Without these tools, the demo uses an audible test tone. The WAV files contain **audio received from the other process over WebSockets**, not a copy of its local TTS buffer.

The separate `verification.json` checks the local proof, both received WAV files and the explicit absence of real-world success claims. The `proof.json` file records both sides of the fictional dialogue, PCM frame counts, the ended-session reason, and the final SHA-256 event-chain digest. The dialogue is scripted, not the output of a hosted LLM. See the complete `peer-lab/README.md` for API examples and precise 656-byte PCM framing.

## What an agent needs to know

- **Discovery:** `GET /v1/capabilities` is a real localhost HTTP endpoint when the Peer Lab server is running. It explicitly declares `real_pstn: false`, `booking_provider: false`, `payment: false`.
- **Human authority:** only the separately authenticated operator can create a mandate, revoke it, or stop the experiment. The mere presence of `human_approved: true` in model-supplied JSON is never sufficient.
- **Peer scope:** the caller is bound to a mandate and a named destination AI peer; that peer authenticates with its own credential and joins through its pending inbox.
- **Call lifecycle:** `awaiting_peers → running → ended`; if the peer never joins, the caller disconnects, or the deadline expires, the server ends the session.
- **Audio:** binary `DT01` + u32 big-endian sequence + u64 big-endian timestamp + 640 bytes little-endian PCM16, mono at 16 kHz (20 ms). This is **not** an RTP or SIP packet.
- **Interruption:** `audio.interrupt` and `audio.end` are explicit peer commands, not proof that a model interrupted successfully. A downstream TTS implementation must honour interruption cancellation.
- **Evidence:** `agent.utterance` and `agent.dtmf` are *asserted by the agents*. The server can establish that the bytes crossed its WebSocket boundary, not that someone understood or acted on them.

## How to connect a model

The reusable model-agnostic Python client in `peer-lab/client.py` exposes `connect()`, `recv()`, `say()`, `pcm()`, `dtmf()`, `interrupt()`, `audio_end()`, and `hangup()`. Your model integration maps its recognised speech to `say`, generated audio to fixed-size PCM frames, and interruption events to TTS cancellation. A production counterpart must authenticate actual humans, configure real SIP/TLS/SRTP, test end-to-end speech latency, and bind carrier-confirmed termination to the call journal.

## A realistic restaurant task

A human tells their assistant: “Book a table for two at 7:30.” In the current Peer Lab, the operator authorises a **fictional** enquiry to a **fictional AI restaurant peer**. Both peers exchange speech samples and task text, but the peer explicitly replies that **no real table was booked**. The result is therefore `real_booking_verified: false`. This is a necessary defence against a model hallucinating success, not a missing cosmetic feature.

An eventual live deployment adds independently tested Asterisk transport, verified UK destination limits, SIP readiness checks, human spending authorisation, live bidirectional ASR/TTS, actual call cutoff, and x402 settlement. Those remain outstanding release gates.

## Human-facing versus agent-facing

Human-facing content explains **what will happen and what was authorised**. Agent-facing material describes **how to exchange messages and prove transport outcomes**. They share the same mandate identity and event record but must never mistake network delivery or model assertions for an independently verified booking.

See [For humans](15-human-journey.md), [Native security](16-native-security.md), and [Roadmap](17-roadmap.md).

## Model-independent chat integration

An additional adapter in `peer-lab/model_adapter.py` can send the receiving AI's asserted text turns to an explicitly configured, OpenAI-compatible **chat completions API**. It rejects model-requested tool calls, oversized output, insecure remote HTTP, and excessive turn budgets. The adapter can optionally return model-generated speech PCM through a separate TTS callback, and cancels pending inference on an `audio.interrupt` event.

The runnable `peer-lab/examples/model_peer.py` loads endpoint, model name, session ID and credentials from environment variables. The `tests/test_model_adapter.py` suite verifies the adapter using a **separate local fake model protocol server**. No real model provider was used by these tests. This particular text adapter consumes the other peer's *declared text*. The separate `peer-lab/voice_peer.py` audio-first runtime uses received PCM, ASR, model inference and TTS; its provider-protocol testing and poor offline recognition accuracy still do **not** qualify as verified natural telephone conversation.

## Machine-readable protocol reference

The static, read-only [Peer Lab OpenAPI 3.1 description](/api/peer-lab-openapi.json) specifies the **localhost-only** authorisation, session, inbox, admission ticket, and stop/revoke endpoints. The WebSocket `x-websocket-admission` extension documents its binary PCM and control framing. A crawler fetching that JSON receives a *description*, not a public bot-call endpoint. The canonical [OpenAPI](/api/openapi.json) is an identical generated copy of this localhost-only Peer Lab contract, **not** an unrelated private backend.
