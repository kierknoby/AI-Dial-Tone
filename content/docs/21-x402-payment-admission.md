# x402 payment admission and agent-first topology

**0.0.1 status:** an **unhosted**, tested Python x402 v2 payment-admission research library exists at `payments/x402.py`. It emits HTTP `402` challenge data and consumes wire-shaped `PAYMENT-SIGNATURE` payloads. **No merchant endpoint, real facilitator, real USDC transfer, or public x402 payment service exists.** No model may initiate real calls through this component.

## Original product intent

The primary AI Dial-Tone product is **a telephone capability for autonomous AI agents**, not a human-operated softphone. The user gives a bounded instruction, an agent discovers the capability, the network qualifies the route, a price is disclosed and paid through x402 where applicable, the service connects to the human recipient through a secure FreePBX/PJSIP network, and the agent returns evidence of what happened.

The original Windows Dial-Tone/MicroSIP work is **an engineering benchmark**, not a C++ dependency embedded in a webpage. Preserve the important behaviours in their appropriate runtime: PJSIP registration health, SIP OPTIONS challenge handling, TLS certificate validation, SRTP/DTLS-SRTP with no silent downgrade, call trace evidence, codec/media state, network-owned stop, and call history. A successful OPTIONS response **does not** prove that an external number exists or that voice media works. This repository contains **no native MicroSIP files**.

The target transport is browser-compatible **SIP over WSS + WebRTC audio**, or an agent-side headless media adapter, backed by a properly configured SIP/PJSIP gateway to Asterisk/FreePBX. The browser is for **an AI agent's communication surface**, not an application that requires a human to press telephone buttons. The existing browser SIP.js lab is not yet a verified production gateway or a port of native PJSIP.

## Two ways to use the same agent contract

- **Managed calling:** the autonomous agent uses a hosted, model-neutral calling API. After independently verified human consent and preflight, an x402 challenge authorises fixed-price access; real telecom routing and account orchestration remain private and replaceable. The agent never receives a PBX password, SIP identity, trunk details or network topology.
- **Bring Your Own Telecoms:** a developer installs a public Asterisk adapter against a PBX and trunk they operate themselves. Self-hosting does not require purchasing managed calling. The agent contract, human mandate and independent safety gates remain identical; use of x402 in BYOT is an optional merchant/operator decision, not a mandatory toll.

Both should eventually support agent-to-human and agent-to-agent conversation. A real call is controlled by network-side Asterisk/PJSIP state, never by the model's claim that it dialled or hung up.

## Proposed payable call-admission sequence

1. **Human mandate:** a separately authenticated operator approves a specific destination, fixed maximum duration, and maximum price. No untrusted agent-generated approval suffices.
2. **Preflight:** the provider checks route policy, registration, signalling TLS/certificate chain, mandatory encrypted media, audio readiness, number category and independently imposed spend caps. A rejected preflight should not charge a user.
3. **Quote and challenge:** HTTP `402` with the canonical base64 `PAYMENT-REQUIRED` header and x402 v2 `exact` terms. The lab supports Base mainnet or Base Sepolia native USDC addresses, but has no actual settlement endpoint. Prices are integer USDC atomic units; a GBP display requires a separately sourced timestamped FX quote.
4. **Payment:** the agent (or its authorised wallet service) supplies `PAYMENT-SIGNATURE`. Terms bind the payment to a unique resource. The service rejects altered recipients, assets, network IDs, amounts or time limits.
5. **Settle, then admit:** because a live call has external effects, the lab uses the x402 v2 `upfront` flow. A trusted facilitator reports durable settlement, then the system creates a **single-use admission**. A permit is not a dial command. Production also needs a transactional ledger and reconciliation for ambiguous payments.
6. **Originate:** the independent telephony service validates the destination, remaining call budget, route, SIP status and PBX-side watchdog **again** immediately before origination. The model does not select a trunk or dial arbitrary URI targets.
7. **Converse and conclude:** PCM streams to an ASR/model/TTS or realtime voice agent; separate provider events confirm answer and hangup. Audio and SIP state must not be inferred from text messages.
8. **Evidence and reconciliation:** report call-state transitions, usage and payment outcome separately. A settled payment does not guarantee a call answered. An agent saying *booked* is never evidence that a reservation was accepted.

## Contract and limitations

The local library provides `operator_approve`, `challenge`, `settle_and_admit`, `redeem`, `operator_revoke`, and `operator_status`. It intentionally **does not** expose a live web service, execute ARI calls, or hold a wallet. The injected facilitator in tests is a fake. Transaction replay checks and permits are currently process-local; production requires a database transaction, trusted payment verification, shared rate limits, settlement-recovery workers and independent safeguards around call starts.

**Upfront exact payment charges a fixed sum** even if the later call cannot connect. Automated refunds are not implemented or promised. The payment decision is only one part of call safety. Legal review of consent, commercial terms, UK automated-calling rules and call recording is required before enabling real customers.

See [`payments/README.md`](https://github.com/kierknoby/AI-Dial-Tone/blob/main/payments/README.md) for the reproducible demonstration and [the x402 v2 specification](https://github.com/x402-foundation/x402/blob/main/specs/x402-specification-v2.md) for the normative wire protocol.
