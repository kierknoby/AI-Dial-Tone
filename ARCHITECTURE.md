# AI Dial-Tone architecture

```text
kierknoby/AI-Dial-Tone (standalone public repository)
├── README.md                 Human and agent overview
├── peer-lab/                 Loopback-only bot audio transport and experimental voice runtime
├── payments/                 x402 v2 call-admission research library and fake-facilitator tests
├── labs/web-softphone/       Local browser/WebRTC/SIP.js research lab
├── lib/ and contracts/       Pure public contract prototypes and schemas
├── content/docs/             Documentation source
├── site/                     Generated static preview at ai.dial-tone.uk (not deployed)
├── tools/ and tests/         Docs/build, security checks, and local test suites
└── .github/workflows/        Standalone CI for this repository

EgyptianEyes/Dial-Tone             Independent Windows C++/MicroSIP project; untouched
PRIVATE telecom service           Independently deployed, not present in this repository
```

## Current runtime status

## Target agent-first calling topology

```text
Human mandate, independent identity and budget authority
    ↓
Autonomous agent → capability discovery → bounded call request
    ↓
Managed path: x402 quote / payment-admission → hosted gateway
        OR
Self-hosted path: BYOT user-managed ARI gateway (x402 optional)
    ↓
Independent readiness + policy gate: FreePBX/PJSIP, TLS/WSS,
certificate validation, DTLS-SRTP/SRTP, SIP OPTIONS, route controls
    ↓
Asterisk media and call state ⇄ secure WebRTC/PCM agent runtime
    ↓
Provider-controlled hangup, usage, receipts, attributed outcome
```

The two deployments share an agent contract, not a hidden dependence on one
provider. The managed service's actual provisioning, account, routing and
settlement implementations are deliberately absent from public source and docs.
The browser is a possible **agent-operated** media surface, not a human dialler.
The native MicroSIP fork is an independent source of SIP/PJSIP readiness design,
not code that this Python/Web project claims to have ported or bundled.

**No real registration, full SIP preflight, managed x402 settlement, or publicly
hosted calling API currently exists.** Those are acceptance gates, not claims.

## Current local services

The Peer Lab supports bounded local WebSocket sessions and experimentally transports PCM between bots. Audio-first ASR/model/TTS integration is unproven against high-quality real model providers. The browser lab is not a live telephone service, and the agent API in public documentation does not represent a hosted endpoint. **No PSTN, x402, live SIP, or verified restaurant booking is delivered by this code.**

## Design inspiration and implementation boundaries

The independent Windows Dial-Tone project implements native registration, SIP OPTIONS readiness, trace and transport/media features. AI Dial-Tone learns from that engineering, but does not inherit the Windows runtime. Its future headless SIP gateway must separately verify TLS, certificate policy, encrypted media, readiness, call answer, and independent channel hangup. See [native security inventory](content/docs/16-native-security.md).

Keep public interface and private telecom implementation separate. Neither a browser destination allowlist nor an asserted human approval authorises real calling. See [REPOSITORY-POLICY.md](REPOSITORY-POLICY.md) and [ROADMAP.md](ROADMAP.md).

## Optional BYOT Asterisk control and media plane (0.0.1 experimental)

`byot/` adds a one-call, loopback-only ARI connector. An operator scopes a one-use mandate to a UK geographic destination and duration. A separately authenticated agent connects before origination. Asterisk (when configured by the deploying owner) controls PJSIP dialling and exposes a mixing bridge plus externalMedia RTP/L16. `byot/rtp.py` translates samples to the existing 16-kHz `DT01` agent framing. This path has only been exercised against a simulated ARI server and UDP sockets, not real SIP equipment. Process-local timeouts do not survive a crash; carrier isolation, PBX-side deadline and orphan reconciliation are mandatory preconditions for production use. See `byot/README.md`.

## Experimental x402 admission contract (0.0.1)

`payments/` now contains an opt-in fixed-price x402 v2 challenge and settlement
admission state machine. It is only a library and fake-facilitator demonstration.
This is separate from `byot/`: developer-owned trunks do not need to purchase
managed calling. A successful synthetic payment returns one single-use permit,
never a raw dial command. SIP preflight, PBX route enforcement, verified media,
independent hangup and durable settlement reconciliation remain mandatory.
See `payments/README.md` and `content/docs/21-x402-payment-admission.md`.
