# Release readiness and validation gates

**Version 0.0.1: local-only technical preview.** The existence of tests, a static site or a hash-chained session receipt does not prove a live phone service. Current evidence is entirely local and fixture-based.

## Pre-call qualification is central to the design

The original Windows Dial-Tone uses registered account, OPTIONS, audio and codec checks, a local audible tone, and Call Trace. AI Dial-Tone aims to bring that principle to autonomous agents as authenticated, machine-readable readiness evidence. The optional BYOT connector currently provides only an operator-authenticated, non-dialling **PJSIP endpoint-state observation** through ARI. `online` cannot establish routing, remote audio or PSTN reachability. See [Pre-call qualification](24-pre-call-principle.md).

## What is checked

- Node.js public-contract checks (`npm run check`), including synthetic site links and capability claims.
- Python Peer Lab tests (`npm run test:peer`), including authentication, media sequence, deadlines and interruption behaviour.
- Browser laboratory unit/contract tests (`cd labs/web-softphone && npm test`), plus Python bot tests.
- Documentation regeneration and clean Git diff of generated files.

## What must be independently accepted

- Genuine two-model natural speech conversations with measured accuracy, latency, interruptions and failure recovery.
- Isolated Asterisk SIP TLS/certificate policy, authenticated OPTIONS, mandatory encrypted media, real INVITE, RTP and confirmed hangup.
- Operator-verified and provider-enforced hard cutoff, consent, destination allowlisting, fraud controls, and orphan reconciliation.
- UK PSTN and regulatory review, real commercial billing, x402 settlement accounting and refund policy.
- Published operations, customer support, telemetry, privacy/retention and incident response.

**Publication of 0.0.1 as research source** is different from **launching a production calling service**. Real telephony remains blocked by all of the above. See [Roadmap](17-roadmap.md) and the repository's `QA-REPORT.md`.
