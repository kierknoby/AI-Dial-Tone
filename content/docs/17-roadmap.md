# Living roadmap: from test lab to an agent telephone service

**Baseline: 11 October 2026. Target host: `ai.dial-tone.uk`. Current public maturity: technical preview, not live calling.** The roadmap is an acceptance register, not a collection of promised dates. A phase is complete only when its evidence has been recorded against a repeatable test in the repository.

## R0 — Source truth, contracts, safety and human separation

**State: documentation and local policy tests implemented in this release.** Preserve native MicroSIP/PJSUA code and GPL notices, document exactly which TLS/SRTP settings exist, publish a native/web/headless interoperability matrix, and separate human product guidance from machine peer contracts. Keep the standalone public repository separate from the private carrier/payment backend. Add runnable fake reservation mandate, SIP readiness and evidence-classification tests. **Exit:** tests pass, publication archive contains no secrets/private code, and all discovery documents say public PSTN and payment are unavailable.

## R1 — Real isolated SIP/WebRTC laboratory

**State: blocked, no connected PBX.** Provision a dedicated Asterisk instance with *no carrier routes* in the test context. Inspect the exact Asterisk and PJProject versions. Create two isolated extensions, an echo/answer test endpoint, WSS, required TLS certificate verification and DTLS-SRTP. Verify registration, authenticated OPTIONS, SIP response timing, real INVITE/answer, full-duplex speech and independent media statistics. **Exit:** documented test logs and authorised audio from at least two user agents, including one browser/AI bridge, with no route to emergency, premium or chargeable numbers.

## R2 — Full-duplex AI voice, interruption and peer testing

**State: not live-tested.** Integrate two independently chosen model/voice stacks, with explicit audio sample-rate conversion, jitter/backpressure handling, interruption flush, 20 ms packet timing, DTMF/IVR, silence handling, reconnection and bounded retries. Cover human receptionist, IVR and agent-to-agent answers. **Exit:** at least 30 authorised live laboratory conversations across two different model implementations, externally observable start/stop and latency/quality reports. No credit for synthetic WebSocket loops.

## R3 — Mandatory safety and failure recovery

**State: lab contract exists, real carrier integration missing.** Signed and tenant-bound mandates, provider channel correlation, independently enforced per-call hard deadline, provider reconciliation after process death, PBX/SBC destination controls, blocked REFER/redirect bypass, verified caller ID (including valid, dialable CLI that uniquely identifies the caller under applicable Ofcom requirements), a working destination for complaints/abuse reporting where appropriate, observability, redaction and rate/concurrency limits. **Exit:** deliberately kill the agent and API during live lab calls; verify 100/100 provider-confirmed channel closures with zero orphan channels. Verify no duplicate calls on retry and no channel escapes from authorised dialplan.

## R4 — x402 and money correctness

**State: not integrated.** Define quote currency and immutable validity window, convert GBP to exact USDC units on the selected Base network with slippage policy, verify payer approval and settlement before chargeable origination, meter provider-confirmed connected time, and reconcile errors, refunds and missing settlement. **Exit:** test payment success, replay, chain mismatch, underpayment, expiry, duplicate retries, provider no-answer, partial use and restart, with ledger consistency. Never take an AI-generated claim as payment proof.

## R5 — Restricted, authorised UK PSTN pilot

**State: not started.** Only approved customers and classified UK geographic numbers. Validate UK call purposes, CLI presentation and return-dialling behaviour, privacy/AI-disclosure obligations, recording policy, recipient opt-outs and abuse-report handling. No emergency, premium, international, automated marketing campaign, transfer or deposit-taking. **Exit:** controlled real PSTN call suite, carrier logs matched to public call IDs, independent hangup, usage/settlement reconciliation, operator incident drills and no unresolved high-severity findings.

## R6 — Public self-service agent service

**State: not started.** Add real hosted authenticated REST/MCP, machine-discoverable capability manifests and actual A2A Agent Card only if supported; a free real-audio challenge; human permissions/dashboard, history, invoices/receipts, key revocation and status/incident communications. Publish SDKs and precise limits. **Exit:** an unfamiliar external agent, without team assistance, completes a free live test and a fully authorised paid call with correct evidence. No manual SIP configuration by the agent.

## Always-on engineering requirements

- Every feature change updates its reference chapter, machine-readable manifest/contract, error semantics and evidence record in the same pull request.
- Reject security downgrades rather than trying insecure signalling/media to improve call connection rates.
- Stamp simulated fixtures, provider facts, model interpretations, settlement and third-party booking confirmations with separate provenance.
- Only tests executed against the real PBX/SBC count as real SIP/PSTN acceptance evidence.
- Review licence provenance before moving any GPL-derived source into the closed service; public interface/SDK work is separate from proprietary routing and commerce.
- Maintain versions for all public schemas and include a deprecation/migration policy before published breaking changes.

## Scope of the first public release

**One runnable development experience, plus a target production journey:** (1) the local, genuinely connected bot-to-bot Peer Lab with operator stop and received-audio evidence; and (2) **future**, restricted human-authorised UK geographic calling with managed x402 prepayment. The second is a design and acceptance target, **not delivered in 0.0.1**. Human cost controls, account-bound approval, recording choices, carrier-confirmed hangup and verified booking outcomes remain future work. Only the local lab has a runnable event journal.

## Evidence register

| Evidence | Current observed result | Blocking next proof |
| --- | --- | --- |
| Native repository review | Source inspected; README states not production-ready | Runtime Windows TLS/cert audit |
| Public Peer Lab 0.0.1 | Authenticated local PCM and voice fixture tests | Real independent speech models and provider control |
| Agent policy exercise in this edition | Run `node --test tests/peer-contract.test.mjs` | Authenticated/signed server-side mandate |
| SIP OPTIONS and secure media | Design validated only | Registered account, SIP 2xx with TLS, audio test |
| Live Asterisk / PSTN | **Zero proven** | Isolated staging PBX and authorised number |
| Real agent reservation | **Zero proven** | Real conversation, external confirmation |
| x402 payment | **Zero proven** | Facilitator, chain verification, reconciliation |

**Do not change a phase to “passed” because a documentation page or mock says so.** Record test command, date, backend revision, Asterisk version, provider evidence and pass/fail in a release evidence file.
