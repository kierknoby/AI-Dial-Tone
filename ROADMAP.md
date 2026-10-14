# AI Dial-Tone engineering roadmap

**Current state: R0+ local contracts, real bot-to-bot PCM, and an experimental audio-first ASR/model/TTS peer runtime, 11 October 2026. No live calling, hosted agent tools or payment settlement. A local-only x402 v2 payment admission fixture and disabled-origination BYOT handoff are now included. The website and developer reference contain 63 FAQs.**

The continuously generated website chapter is [`content/docs/17-roadmap.md`](content/docs/17-roadmap.md); this short file is the repository entry point. The release standard is **acceptance evidence**, not elapsed calendar time.

| Gate | Milestone | Current state | Proof needed |
| --- | --- | --- | --- |
| R0 | Native MicroSIP security review, bot task mandate, separate human docs | **Local implementation / source review** | `npm run check`, source provenance, no false hosted claims |
| R0.5 | Authenticated bot-to-bot PCM, operator mandate, human stop, chat-model protocol adapter, audio-first ASR/TTS | **Implemented, network-tested with fixtures** | Actual received PCM drives ASR; model/TTS returns PCM; barge-in and stop tests; no carrier |
| R1 | Isolated real Asterisk WSS/SIP/media test | **Synthetic ARI connector built; real PBX gate blocked** | Actual TLS/SRTP registration, OPTIONS, INVITE, audio and hangup, no PSTN egress |
| R2 | Natural low-latency bot-to-bot conversation | **Blocked (audio path now implemented)** | 30 real AI speech conversations with two independent model implementations and measured ASR accuracy |
| R3 | Crash-safe PBX/SBC provider controls | **Blocked** | 100 real test-channel closures; zero orphans/replays |
| R4 | x402 quotes, receipts and settlement | **Local upfront/`exact` challenge, one-use permit, and BYOT lab handoff implemented; real funds/settlement blocked** | Trusted Base/USDC facilitator, durable payment/mandate ledger, reconciliation, refunds and fraud audit |
| R5 | Restricted approved UK geographic PSTN pilot | **Blocked** | Carrier event and usage evidence, security review, opt-out handling |
| R6 | Public agent tools and human account experience | **Blocked** | Unassisted outside agent demonstrates a permitted, paid call |

The [product scope decision register](PRODUCT-SCOPE.md) separates shipped components, future work, excluded functionality and undecided policy. The full [roadmap](content/docs/17-roadmap.md) defines acceptance criteria and outstanding safety checks. The [MicroSIP security matrix](content/docs/16-native-security.md), [peer protocol](content/docs/14-peer-contract.md) and [human journey](content/docs/15-human-journey.md) are not optional reading.

## Original product continuity

AI Dial-Tone is ultimately a callable, model-neutral telephone service for
**autonomous AI agents**. A real customer supplies a bounded human instruction,
the agent discovers the capability, a managed x402 payment admits a permitted
call, a secure PJSIP/FreePBX gateway places it, and the agent reports a grounded
outcome. The managed network remains implementation-private, and BYOT is an
independent self-hosted alternative using the same agent-facing constraints.

The separate Windows MicroSIP-derived Dial-Tone gives us the SIP registration,
OPTIONS, diagnostics, TLS and encrypted media *engineering standard*. There is
no implication that its Windows code is embedded in a browser. A headless or
WebRTC/WSS agent-side equivalent must be separately implemented and validated.

### x402 local admission evidence, not completion of R4

`payments/` now emits x402 v2 challenges and evaluates settled admission via a
fake injected facilitator. It rejects altered terms, reuse, revocation, and
ambiguous settlement. The payment state is in-memory and there is no wallet or
blockchain connection. R4 is still blocked until payments, GBP quote display,
reconciliation after crashes, refund policy, and safe call billing have been
verified with a real independent facilitator. BYOT does not require x402.

## Change protocol

Each PR affecting an agent capability **must** update the schema/version, machine-readable `/agents.json`, human documentation, representative failure tests and evidence register together. Independent SIP/provider and settlement events must never be synthesized from model output. Hosted claims stay `false` until real endpoint verification has passed. GPL-native source and the proprietary backend are separate by design.

**Next engineering request to telecom owner:** provide a dedicated test Asterisk 22.6+ system and verified WebRTC/SIP loopback extension, with carrier access blocked at dialplan and SBC level. Do not perform testing on a production PBX or route to real destinations until R1–R3 acceptance gates pass.

## Local agent peer lab (initial 0.0.1)

`peer-lab/` is a **runnable development server** and client with two independently authenticated bots and a human operator. Unlike static browser fixtures, it transports PCM and commands through real localhost network sockets and produces WAV recordings plus a hash-chained test receipt. It is not speech recognition, a large language model, SIP registration, or a real telephone conversation. The real-model audio, Asterisk, PSTN, and payment gates remain blocked. See [the peer lab](peer-lab/README.md).

**Model adapter:** A locally testable chat-completions integration now exists in `peer-lab/model_adapter.py` with an optional PCM speech callback. It has only been exercised against a *fake model server*, not an actual hosted model or Asterisk device. Do not advance R2 until at least two real model providers, real speech input and interrupt latency have passed acceptance tests.

## Audio-first laboratory (initial 0.0.1)

The `voice_peer.py` runtime no longer relies on the other bot's asserted text. Actual 16-kHz PCM is segmented and sent to ASR, a compatible model, and then TTS. The new regression suite verifies the entire localhost network path, barge-in cancellation, provider failure, and independent human stop. An **actual** offline eSpeak/PocketSphinx recording reaches a local model HTTP fixture, which replies with genuine synthesised speech. Recognition quality was poor, so this is **not** a completed R2 milestone. Hosted speech providers and two real LLMs have not been tested. See `content/docs/19-audio-first-voice.md`.

## Bring Your Own Telecoms acceptance gate (initial 0.0.1 development)

`byot/` now contains a functional isolated local reference path from operator authorisation through authenticated agent admission, ARI origination, externalMedia bridge, RTP/PCM relay, DTMF, and hangup observation. The synthetic test exercises actual ARI HTTP+event WebSocket, plus UDP RTP, against a fake server. **No real Asterisk acceptance gate has passed.** Before R1 is marked complete, test an isolated Asterisk 22 instance with owned endpoints, confirm the exact `slin16` RTP payload mapping, real audio in both directions, end-to-end timer/orphan reconciliation, and SIP TLS/SRTP/OPTIONS policy on the PBX. BYOT operator credentials, spending/route restrictions, and emergency-stop resilience must be audited before any external customer uses it.

## Operator-side payment-to-telephony handoff and FAQs (0.0.1)

The optional `integration/` proof takes a redeemed lab payment permit and issues an Asterisk operator mandate with **exactly the same authorised destination and maximum duration**, without ever giving an AI agent PBX/operator credentials. An explicit check ensures live origination is **disabled**; the handoff remains test code and cannot itself place a call. A real settlement/payment-to-call integration still needs a trusted facilitator, durable storage, independent consent, SBC/PBX security and provider-owned call cutoff. See [the integration chapter](content/docs/22-payment-telecom-handoff.md).

The website has a substantial searchable [60-question FAQ](site/faqs.html), generated from [`content/faqs.json`](content/faqs.json). The same source feeds a [machine-readable FAQ](site/api/faqs.json) and [developer chapter](content/docs/23-faq.md); every answer states the relevant technical availability boundary.
