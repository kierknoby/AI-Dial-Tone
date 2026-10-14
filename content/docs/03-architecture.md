# Architecture

AI Dial-Tone 0.0.1 separates **trusted operator control**, two **untrusted bot peers**, and media/events over localhost. This does not yet connect to a carrier or a PBX.

## Implemented local session

```text
Operator bearer → issue/revoke lab mandate → Peer Lab HTTP control
Caller bearer   → single-use ticket ──────────┐
                                               │
                Peer Lab WebSocket relay       ├── real PCM packets
                                               │
Peer bearer     → single-use ticket ──────────┘
           → scoped event journal + local hard deadline
```

The two bots each authenticate using different bearer tokens. The operator cannot join as a bot. Both must be admitted before the session runs. Media flows between their separate WebSocket connections with role attribution, sequence checks and rate limits. The server tracks only the **lab transport** outcome. A local event hash chain is not independent network evidence.

## Optional model integration

`peer-lab/voice_peer.py` segments **received** PCM. `peer-lab/speech.py` supplies recognition/synthesis adapters; `peer-lab/model_adapter.py` calls a restricted, OpenAI-compatible *chat-completions protocol*. Credentials and model availability are supplied by the developer. The test model is a deterministic fixture, not a verified third-party LLM.

## Not implemented

The future private telephony service must separately enforce SIP TLS/certificate policy, SRTP/DTLS-SRTP, verified PBX and SBC routing, network-level call cutoff, cost policy, recording and human mandates. A JavaScript readiness policy or synthetic WebSocket event cannot substitute for PJSIP observations. See [Native SIP Security](16-native-security.md) and [Roadmap](17-roadmap.md).
