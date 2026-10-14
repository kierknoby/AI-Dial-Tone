# AI Dial-Tone: Agent Entry Point (0.0.1)

**Status: open-source development preview.** This repository does not offer a callable public telephone endpoint, a production MCP tool, a wallet, an x402 payment processor or a tested real SIP/PSTN call. Do not ask for telephone numbers, money, or live customer credentials to run a demonstration.

## Why an autonomous agent should care

The intended capability is straightforward: an independently developed agent receives a bounded human mandate, obtains telephone access (with x402 upfront payment **only where managed calling requires it**), communicates through a secure FreePBX/PJSIP path and reports a grounded outcome. Developers can alternatively bring their own Asterisk infrastructure. The agent-facing contract should not reveal the operator's underlying provisioning and routing.

**Current proof:** two independent clients exchange actual PCM over localhost WebSockets, with separate operator and peer credentials, one-time tickets, duration limits and operator stop. A separate, **disabled-by-default** BYOT reference connector has been tested against simulated ARI plus loopback RTP. x402 admission uses a fake facilitator and transfers no funds. Model-driven natural speech, secure real SIP calls, and payment settlement are unverified.

## The complete service and the development repository

AI Dial-Tone is **one end-to-end calling product in development**: discovery → verified human authority → operator-controlled route admission → optional x402 for managed access → telephone conversation → independent provider-side release → evidenced result. Both managed access and Bring Your Own Telecoms lead to that intended common agent experience; BYOT is not the whole platform.

The **website** is the public product and capability-discovery front door, but the 0.0.1 deployment is static. The **GitHub repository** is the open-source developer implementation with executable local labs, not a deployed telephone network. Do not confuse a documented target workflow with an available live endpoint.

## Try the real, runnable part

From a fresh checkout of this repository, with Python 3.11+:

```sh
python -m pip install 'aiohttp==3.13.3'
python tools/verify_first_call.py --out demo-output
```

This creates a local `demo-output/proof.json`, `demo-output/caller_heard.wav`, `demo-output/peer_heard.wav` and `demo-output/verification.json` containing **actual audio received by the other bot**. The script validates receipt, boundaries, separate bidirectional received-audio files and session termination; speech may be synthesised by eSpeak if installed, otherwise a tone proves transport only. It **does not** call a restaurant or prove that a model understood a conversation. Do not commit generated recordings or token-bearing debug output.

## Interfaces and source map

| Start here | What exists today |
| --- | --- |
| [Project Overview](content/project-overview.md) | The approved vision and explicit research status |
| [Product Scope](PRODUCT-SCOPE.md) | Decided, future, excluded and unresolved product boundaries |
| [Peer Lab README](peer-lab/README.md) | Local server, operator/caller/peer admission, actual PCM wire format |
| [Peer Lab OpenAPI](peer-lab/openapi.json) | **Local** `http://127.0.0.1:8765` control plane |
| [BYOT README](byot/README.md) | Experimental Asterisk ARI/RTP connector, origination **OFF** by default |
| [BYOT OpenAPI](byot/openapi.json) | **Local** `http://127.0.0.1:8877` agent/operator control |
| [x402 README](payments/README.md) | Non-production upfront/`exact` USDC admission fixture |
| [Handoff README](integration/README.md) | Local one-use payment-to-BYOT mandate binding; live calls forbidden |
| [FAQs](content/docs/23-faq.md) | 63 questions, with realistic capability and trust boundaries |
| [Roadmap](ROADMAP.md) | Live PBX, real models, independent hangup and settlement gates |
| [Contributing](CONTRIBUTING.md) | Contribution standards and AI-assistance disclosure |

Machine-readable discovery for the **static website** is in [`site/agents.json`](site/agents.json); OpenAPI files under `site/api/` are documentation copies, **not hosted telephone endpoints**. This `AGENTS.md` is contributor guidance, not an interoperable A2A Agent Card or an MCP server.

## Safety and contribution rules

- Keep all experiments on loopback or explicitly isolated test infrastructure. Do not connect a real carrier or emergency route.
- Do not put SIP passwords, wallet keys, identity proofs, recordings, or other people's personal data in model prompts, tests, issues or commits.
- An agent's assertion is not a telephone-network event or verified restaurant booking. Local event hashes don't prove a real-world outcome.
- A payment fixture is not a settlement receipt. An x402 permit is never itself authority to dial. Keep independently verified human authorisation, PBX policy and provider-owned shutdown as separate gates.
- Do not claim production readiness until real FreePBX/Asterisk, PJSIP TLS/SRTP, media, models, termination and genuine settlement pass their documented acceptance tests.
- Run `npm run check`, `npm run test:peer`, `npm run test:byot`, `npm run test:x402`, and `npm run test:handoff` before submitting changes. Do not change claims in the website without updating source, tests and the agent manifest.

**The objective is not another assistant. It is a reusable telephone capability for somebody else's authorised AI.**

## Pre-call qualification and provenance

Before asking any human to answer or attempting paid origination, read [Pre-call qualification](content/docs/24-pre-call-principle.md). A successful endpoint probe is not a PSTN route guarantee. For the publicly verifiable developer background, see [Origins and community engineering](content/docs/25-origins.md).
