# AI Dial-Tone product scope and decisions

**Version 0.0.1 | 11 October 2026 | product direction, not a production capability claim**

This is the source-of-truth human interpretation of [`content/product-scope.json`](content/product-scope.json), which also generates `/scope.html` and `/api/product-scope.json` for the public website. This is a scope decision register, not a certification, contract, completion report or claim of an exhaustive competitor survey.

## Project stewardship

The preview currently lives in Kieran Knowles-Byrne's personal development space and is being prepared as an [Egyptian Eyes](https://egyptianeyes.com) project. This is a development direction, not a claim that Egyptian Eyes operates a production service, has become the legal controller of website data or has taken ownership of the repository. General/privacy and initial private vulnerability enquiries go to **ai@dial-tone.uk**; abuse reports go to **dial-tone@egyptianeyes.com**. Either address must be tested before publication.

## What AI Dial-Tone is

A standard model-neutral telephone capability for autonomous agents, retaining human mandate and independent telecoms authority.

The website is a **static public discovery and documentation entry point**. The repository is **open-source developer code and local laboratories**. They describe one intended product with managed and BYOT access, not two services that already work end to end.

The requesting agent may propose a task and interact with the media plane. It **cannot** confer human consent, select arbitrary telecoms routes, control carrier identity, or release a live carrier channel solely by claiming it has done so. Payment never substitutes for human permission or telecoms admission.

## Included in the initial development release

- **Local agent audio:** Authenticated, bounded, two-peer WebSocket PCM sessions with local WAV and receipt evidence. Not a telephone call.
- **Operator control in local tests:** Local operator-issued mandates, explicit permission limits, revocation and stop demonstrated in lab tests.
- **Experimental speech pipeline:** Offline ASR/TTS and model-compatible adapters exercised with fixtures; no claim of useful production-grade dialogue.
- **Experimental self-hosted BYOT:** Operator-controlled Asterisk ARI/RTP reference bridge with synthetic HTTP, WebSocket and UDP tests. Origination is disabled by default, with no verified real Asterisk call.
- **Local payment research:** x402 v2 challenge and single-use admission using a fake facilitator. No real settlement or funds.
- **Local handoff proof:** Operator-side payment-to-BYOT mandate handoff with real origination deliberately disabled.
- **Static website and machine discovery:** Human and agent explanations, reproducible fixtures, local-only OpenAPI, documentation and FAQ. No hosted call API.
- **Developer research tooling:** Scripted playground, browser softphone lab, local verifier and automated contract tests.

## Future product direction, subject to acceptance

- **Real, independently authorised telephone calling:** One agent-facing interface for managed and BYOT routes, with separate human mandate and operator admission.
- **Reliable SIP and media:** Isolated live Asterisk/SIP proof, secure signalling and media, independent network cutoff and reconciliation.
- **Useful natural speech:** Low-latency bidirectional speech with interruption, IVR, keypad entry, voicemail and accessible language handling.
- **Verifiable task receipts:** Network facts, conversation claims, payment status and confirmed external actions are separate evidence categories.
- **Interoperability:** Versioned public call contract with optional MCP tool and agent-to-agent adapters only after actual protocol conformance tests.
- **Responsible managed calling:** Explicit prices and call budgets; when applicable, real x402 settlement with durable reconciliation and a restricted compliant pilot.
- **Independent BYOT operator kit:** Documented install, operator-owned routing and termination, conformance tests and recovery without private project knowledge.

## Excluded by product direction

- **Bulk unsolicited or mass marketing dialling:** No campaign engine or mass sales dialler. Any future calling must also satisfy applicable calling, privacy and consent rules.
- **Agent-controlled PBX administration:** Agents cannot configure trunks, routes, carrier accounts, caller identity or firewall controls.
- **Custom foundation speech or language model:** Use replaceable engines rather than build a competing model platform.
- **General-purpose CRM and workflow builder:** Expose safe task interfaces; do not become an all-purpose business automation suite.
- **Bespoke SIP replacement:** Use open telecoms standards instead of inventing a parallel telephone network.
- **Unverified success claims:** A model transcript, payment receipt or local simulation never proves a network call or external booking.
- **Unlimited routing through payment:** Payment is one narrow admission condition, not consent, route permission or a right to unrestricted calls.

## Deferred or not yet approved

- **Inbound reception, campaigns and marketplaces:** Not first-release priorities; inbound may be evaluated independently. Bulk marketing remains excluded.
- **Call transfer and human takeover:** Requires additional destination authority and operator proof before adoption.
- **Managed pricing and unsuccessful-call policy:** Commercial model, refunds, retries, currencies and paying use cases not approved.
- **Privacy and retention policy:** Recording, storage, data residency, deletion and user notices require separate decisions.
- **Delegated human authority:** Organisation and delegate mandate models remain open.
- **Territory and compliance gates:** Permitted destinations, purpose classes, disclosure, operator obligations and lawful caller ID await review.
- **Public v1 compatibility promise:** Schema freeze, versioning and long-term support commitments not made in 0.0.1.

## Questions that must remain open until explicitly decided

1. Can a verified organisational delegate authorise a call, and how is that delegation revoked?
2. How quickly does a mandate expire, and how are individual retries approved?
3. What non-audio records can be kept, and how do deletion requests interact with audit obligations?
4. What price model applies to answered, failed, unanswered and interrupted calls?
5. Where does the public managed API end and private operator control begin?
6. Can a self-hosting developer also act as the telecoms operator, and how is independence enforced?
7. Who authorises a transfer to an additional destination?
8. How do externally hosted agents authenticate and prove their commitments?
9. Which speech processing regions and fully local options are acceptable?
10. What constitutes independent PBX and SBC teardown proof on supported systems?
11. When is verbal agreement evidence, and when is a confirmation reference required?
12. Who handles abuse, complaints, refunds and support for managed versus BYOT calls?
13. Which AI caller disclosures are required for each territory and use case?
14. Which task categories and UK pilot routes, if any, may be allowed for paid calling?
15. What is the first stable API version and its backward-compatibility policy?

## Gate to the next live-capability claim

Prove one isolated operator-authorised real Asterisk call, media and independently verified network teardown with no PSTN egress.

This requires operator-controlled isolated PBX tests, both directions of media, reliable call-state events, and independent teardown evidence. Simulated results, fixture call IDs, model dialogue, SIP endpoint status and payment permits do **not** pass this gate. UK legal, privacy and telecoms requirements must be reviewed before any real customer calling.

## Scope-change rule

Every proposed change must state which section it moves, why, who approved it, its privacy and abuse implications, and the acceptance evidence required. Update the manifest, website, docs, negative tests and release evidence together. New capabilities remain unavailable until verification completes.

## Scope-review basis

The development wishlist and the public 0.0.1 code were compared with independently published engineering patterns in SIP, voice-agent handoffs, agent interoperability, x402 payment admission and UK telephone marketing compliance. These are transferable patterns, not evidence of exclusive functionality. The detailed development wishlist deliberately does not name competitors.
