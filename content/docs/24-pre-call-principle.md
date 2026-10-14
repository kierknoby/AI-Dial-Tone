# Pre-call qualification: can the agent actually make a call?

**Principle:** test everything that can be tested before committing a human to a call. The user should not be interrupted merely to find out whether an AI agent was assigned a broken SIP path. This is the engineering principle carried forward from the original [Dial-Tone Windows softphone](https://github.com/EgyptianEyes/Dial-Tone).

## Provenance: what native Dial-Tone established

The MicroSIP-derived Windows application added a pre-call readiness control, **local audible dial tone** and **Call Trace**. Its published README documents the selected SIP account, registration, transport, sound devices, codecs, authenticated SIP OPTIONS response, endpoint and round-trip latency. The tone is generated **locally** when readiness is acceptable; it is **not** a tone supplied by the carrier or a guarantee that any particular number can be reached. `READY` in the Windows application is not a PSTN completion certificate. A successful qualification can be associated with a subsequent outgoing call within 60 seconds on the same account.

An autonomous agent should receive the same level of evidence as structured, timestamped observations. An optional echo or test-tone path should be **isolated and non-human**, so audio-path tests need not ring an unsuspecting recipient.

## Proposed qualification stages

| Stage | Before a real call? | Evidence required | Scope and limitation |
| --- | --- | --- | --- |
| 0. Authenticated mandate | Yes | Server-verifiable human permission, destination class, cost and duration constraints | Approval is not proof of network readiness |
| 1. SIP endpoint | Yes | PBX-reported PJSIP endpoint presence, registration/qualify status and observation time | An online trunk or endpoint does not prove its dialplan or PSTN path |
| 2. SIP response | Yes | Recent SIP OPTIONS response bound to the configured account/peer; transport, certificate, round-trip time | OPTIONS 2xx proves that SIP service answered that check, **not** that a particular dialled number can be completed |
| 3. Security and route policy | Yes | TLS/verified peer, mandatory encrypted media policy, codec and approved routing class | A route-policy decision is not evidence that a carrier will accept a later INVITE |
| 4. Controlled media loop | When configured | Isolated echo/tone exchange, RTP observations, timing and loss; never a real person's number | Proves only this test media path at this time |
| 5. Real INVITE and answer | No; this is the attempted call | Asterisk and provider-attributed call state and media observations | Real destination success becomes knowable only during actual call progress |
| 6. Task and release evidence | After connection | Confirmed hangup, measured usage, independently corroborated task status | A model's statement does not prove booking or release |

**No fully non-dialling preflight can guarantee a future call will complete.** The design goal is to eliminate predictable failures **before** placing the call, and ensure remaining uncertainty is visible. A paid managed route should be qualified before settlement where feasible; the project still needs an explicit failure/refund and settlement policy because pre-payment does not guarantee remote answer.

## Available in version 0.0.1

The public BYOT connector now offers **`GET /v1/readiness`**, an operator-authenticated, **read-only** observation of its fixed configured PJSIP endpoint through Asterisk ARI, when connected. It does not originate, place a test call, issue a mandate, validate the dialplan, or claim to observe SIP OPTIONS directly. An ARI `online` value is only an endpoint-state observation. Its output includes a `not_proven` array and `network_call_authorised: false`. The originator must still separately require an authorised mandate and admission.

Other full-fidelity native readiness checkpoints, authenticated OPTIONS, PBX-specific route inspection, isolated echo diagnostics, audible feedback and provider-certified results **are not implemented in the AI version**. See [Native security](16-native-security.md), [BYOT Asterisk](20-byot-asterisk.md), and [Release readiness](13-readiness.md).

## Acceptance criteria for the real service

1. The probe comes from an authenticated, authoritative PBX/SIP observer, not from client-submitted JSON or a model's claim.
2. Observations are fresh, bound to the selected trunk/account and route policy, and invalidated on configuration, endpoint, IP or credential changes.
3. SIP and media security must fail closed on TLS downgrade, certificate mismatch or optional/disabled SRTP when encryption is required.
4. PBX/carrier routing decisions are recorded without inventing a destination response.
5. The service exposes a clear distinction between **route candidate**, **internal media verified**, **call connected**, and **remote conversation verified**.
6. A bot may stop and report the reason before ringing a human. A successful probe alone cannot trigger a billable call.
7. Real hangup and charging limits must be independently enforced and reconciled at the PBX/carrier boundary.

## Why it matters to AI agents

An autonomous agent cannot sensibly ask a human to troubleshoot SIP or ring a recipient speculatively. It needs **machine-readable confidence and a reason code** before committing to an action. An audible local tone and useful Call Trace were powerful for an administrator; a trustworthy preflight receipt and structured call trace should be their agent-facing equivalents.
