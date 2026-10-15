# AI Dial-Tone 0.0.1

Updated 11 October 2026.

## Project Overview

The project is developing an open-source communications platform that enables autonomous AI agents to make telephone calls over the existing global telephone network.

As artificial intelligence becomes increasingly capable of completing tasks independently, access to traditional telecommunications remains a significant limitation. AI agents can interact with websites, software, and digital services, but making an ordinary telephone call still requires specialist integrations, infrastructure, and human intervention.

The objective is to change that.

An autonomous agent should be able to discover a telephone service, obtain authorisation from its human, pay for calling access where required, establish a connection, conduct a natural conversation, and report the outcome. Whether booking a restaurant, contacting a supplier, arranging an appointment, or communicating with another automated system, the underlying telecommunications should be largely invisible to the agent.

For managed calling, x402 enables autonomous agents to pay for telephone access programmatically, without conventional subscriptions, manual checkout processes, or pre-existing commercial relationships.

The communications architecture is built around established SIP and PJSIP standards, with Asterisk and FreePBX providing the reference telephony environment. It draws on existing softphone engineering principles to incorporate registration, pre-call readiness qualification, secure signalling and media, real-time diagnostics, and reliable call control into an interface designed specifically for autonomous software.

Human authorisation remains central. Calls must operate within defined permissions, destinations, durations, and spending limits, with safeguards that operate independently of the AI agent itself.

The platform is designed to support both self-hosted telecommunications infrastructure and managed calling services through a common agent-facing interface. Developers can bring their own compatible telephone systems, while others can obtain calling access without operating a PBX.

Its open-source approach encourages interoperability, independent development, and adoption across different AI models, agent frameworks, and telecommunications providers.

The initial implementation includes local agent-to-agent audio communication, experimental speech processing, simulated Asterisk connectivity, and x402 payment-admission components. Production telephone calling, live payment settlement, and reliable unscripted conversations remain under development.

The goal is not to build another AI assistant or another softphone. It is to give autonomous AI agents access to the telephone network as a standard, secure, and programmable capability.

## Start here: your first verified local audio session

For the quickest hands-on proof, use Python 3.11+ in an isolated development environment. **This does not dial a number** and does not verify a real booking, model conversation or payment.

```bash
python -m pip install 'aiohttp==3.13.3'
python tools/verify_first_call.py --out demo-output
```

Success prints `PASS: two received-audio WAV files and local session receipt verified.` and creates `demo-output/verification.json`, `demo-output/caller_heard.wav` and `demo-output/peer_heard.wav`. The JSON must show `"status": "PASS"`, `"bidirectional_received_audio_verified": true`, and `"real_pstn_call_verified": false`. For platform notes, troubleshooting and how to read the evidence, see **[FIRST-CALL.md](FIRST-CALL.md)**. Running locally does not require Asterisk, a carrier, a SIP trunk, a wallet or API keys.

## Overview

**AI Dial-Tone** is an independent open-source research project for **AI agents making telephone calls**, maintained under [@kierknoby](https://github.com/kierknoby). It takes inspiration from the readiness, SIP diagnostics, and security engineering of the separate [Egyptian Eyes Dial-Tone Windows softphone](https://github.com/EgyptianEyes/Dial-Tone). No native MicroSIP code is included here. It is designed so a human can eventually ask an AI agent to make a telephone call, approve a bounded task, and receive an evidence-based result, without configuring SIP or running a softphone.

**Project home:** AI Dial-Tone is currently developed in Kieran Knowles-Byrne's personal development space and is being prepared as an [Egyptian Eyes](https://egyptianeyes.com) project. The planned association does not mean Egyptian Eyes already operates a live calling service or that this preview has transferred to a commercial operator. General and privacy enquiries: **[ai@dial-tone.uk](mailto:ai@dial-tone.uk)**. Abuse reports: **[dial-tone@egyptianeyes.com](mailto:dial-tone@egyptianeyes.com?subject=AI%20Dial-Tone%20abuse%20report)**. Security vulnerabilities have a separate private reporting route in [SECURITY.md](SECURITY.md).

The project deliberately has two audiences:

- **For Humans:** an understandable task, explicit approval, cost and time limits, cancellation, and an honest outcome. See [the human journey](content/docs/15-human-journey.md) and the [human-facing site](site/humans.html).
- **For Autonomous Agents:** documented capability discovery, structured permissions, model-neutral peer communication, audio transport, and attributed events. Start with [AGENTS.md](AGENTS.md), then see [the agent contract](content/docs/14-peer-contract.md), [agent entry point](site/agents.html), and [reference documentation](site/docs/index.html).

The public project includes [63 substantial frequently asked questions](site/faqs.html), a static technical-preview website, machine-readable documentation, a synthetic playground, a browser/WebRTC research lab, a **runnable local bot-to-bot audio service**, a **local-only x402 v2 payment-admission contract lab**, and an **optional disabled-by-default Asterisk ARI reference connector** for developers bringing their own isolated telecom infrastructure. The local Peer Lab supports independently authenticated agents, 16-kHz PCM audio, bounded sessions, DTMF events, interrupt signalling, an operator stop, and an experimental audio-first ASR/model/TTS pipeline.

**It is not yet a publicly available telephone service.** The target hosted product will permit autonomous agents to discover a calling API, obtain separately verified human authority, pay a disclosed fixed or metered charge through x402, and converse through a secure FreePBX/Asterisk and PJSIP calling service without receiving SIP or carrier credentials. A developer can instead connect their own Asterisk through BYOT, without any obligation to use managed payments. No publicly hosted telephone calling API, booking service, live x402 settlement, or production MCP service is available. The experimental self-hosted Asterisk connector can attempt PJSIP origination only after explicitly enabling live calling and supplying independently authorised PBX configuration; **real Asterisk interoperability and PSTN audio have not been tested**. Audio transport has been tested; useful natural dialogue with a high-quality live model has not. Native Dial-Tone's complete SIP readiness behaviour has been studied, **not integrated into the headless service**; the BYOT connector only observes an ARI PJSIP endpoint state before origination.

## One product, two entry points

**AI Dial-Tone is designed as an end-to-end calling capability**, not a SIP readiness tool, a standalone BYOT adapter, or a collection of unrelated labs. In its intended complete journey, an autonomous agent discovers calling access, obtains a verified and bounded human mandate, meets the provider's independent call-admission rules, makes any required managed x402 payment, connects and carries a conversation, has its call safely terminated by the telecoms operator, and reports a grounded outcome. Managed service and developer-supplied telecoms are two access models for that same agent-facing capability.

- **[ai.dial-tone.uk](https://ai.dial-tone.uk/)** is the product's public-facing website, agent discovery entry point, human explanation, and developer reference. In 0.0.1 it is **static**, including read-only machine-readable specifications and simulations. It is *not* a deployed telephone or payment API.
- **[GitHub: kierknoby/AI-Dial-Tone](https://github.com/kierknoby/AI-Dial-Tone)** is the open-source implementation and contributor/developer workspace: local agent audio, experimental Asterisk BYOT, x402 admission research, code, contracts, tests, and roadmap. It is not a separate product with a smaller promise; neither does it expose managed production telecoms infrastructure.

For an exact, maintained inventory of what is included, planned, excluded and still undecided, read [Product Scope and Decisions](PRODUCT-SCOPE.md). The [machine-readable scope register](content/product-scope.json) is also published as a static document.

The website describes the end-to-end **product being built**. The repository and [development status](site/status.html) show exactly which parts work **today**. Do not describe planned live calling, carrier-enforced teardown, or real payment settlement as available in this first release.

## The people and the engineering

AI Dial-Tone is developed by **[Kieran Knowles-Byrne (`@kierknoby`)](https://github.com/kierknoby)**, Head of Product at [FreePBX UK](https://freepbx.uk/) and an open-source FreePBX community-module developer. Public projects include [Registration Watch](https://github.com/freepbxUK/registrationwatch), [Repeat Caller](https://github.com/kierknoby/repeatcaller) and [Concurrency Count](https://github.com/kierknoby/concurrencycount). [20tele](https://20tele.com/) brings more than a decade of practical FreePBX/Asterisk and telecom engineering experience. The related [Heqet](https://github.com/20telecom/heqet) and [IN1CLICK](https://github.com/20telecom/IN1CLICK) projects demonstrate the installation and provisioning background.

The FreePBX UK partnership designation belongs to that business and **does not constitute an endorsement or certification of AI Dial-Tone**. This is Kieran's independent development project. For independently inspectable references, see [Origins and community engineering](content/docs/25-origins.md).

## The Dial-Tone principle: check before calling

The separate [Windows Dial-Tone](https://github.com/EgyptianEyes/Dial-Tone) project added **pre-call qualification**, locally generated **audible dial tone**, and useful **Call Trace** reporting to its MicroSIP/PJSIP foundation. The important question is: **can a usable call path be established before an AI agent commits to contacting a human?**

The design for AI Dial-Tone is to verify as much as possible **before dialling**: registered endpoint, authenticated SIP OPTIONS response, TLS/SRTP policy, authorised route class, and a non-human tone/echo test where available. A bot should receive structured evidence and a reason to stop if the available path is broken. A person should not need to be interrupted for a speculative SIP failure.

**Critical distinction:** SIP OPTIONS and endpoint status are *not* a guarantee of PSTN delivery, answer or two-way audio. Only a real attempted call can establish those later stages. The current 0.0.1 local BYOT preflight reports only ARI endpoint state; native-level qualification and browser/headless PJSIP interoperability are future acceptance gates. See [Pre-call qualification](content/docs/24-pre-call-principle.md) and [the readiness website page](site/readiness.html).

## Release Status

- **Version:** 0.0.1, the first public development release (no earlier public release history).
- **Repository:** [`kierknoby/AI-Dial-Tone`](https://github.com/kierknoby/AI-Dial-Tone), published standalone repository on `main`.
- **Status:** development / technical preview; not production-ready.
- **Public site:** [`ai.dial-tone.uk`](https://ai.dial-tone.uk) is published as a static information and developer-discovery site. It does not provide live calling or payment services.
- **Private components:** managed carrier access, routing, and commercial billing are not included. A public x402 v2 admission lab and optional self-hosted Asterisk adapter are provided without any proprietary service implementation.

## Compatibility

| Component | Current requirement | What has been verified |
| --- | --- | --- |
| Website and documentation | Static HTTPS hosting | Local site generation and Chromium desktop/mobile smoke checks |
| Public contracts | Node.js 22 or later | GitHub Actions uses Node.js 22 |
| Documentation build | Python 3.11+; `markdown-it-py==4.2.0` | Local reference generation |
| Peer Lab | Python 3.11+; `aiohttp==3.13.3` | Local HTTP/WebSocket and PCM tests |
| Browser softphone lab | Node.js 22+, Python 3.11+, WebRTC-capable browser, `websockets==16.0`; `npm ci` and `npm run build:sipjs` | Mandatory WSS transport integration in CI; optional Chromium browser integration is not run in CI; no real Asterisk call verified |
| Windows Dial-Tone | Separate MicroSIP-derived project; not part of this source tree | [EgyptianEyes/Dial-Tone](https://github.com/EgyptianEyes/Dial-Tone) (reference only) |
| BYOT Asterisk reference connector | Python 3.11+; Asterisk ARI externalMedia (Asterisk 16.6+) | **Local simulated ARI HTTP/WebSocket and UDP tests only; no real PBX validation** |
| Public hosted SIP, UK PSTN, x402 | Not offered | **No hosted service or real settlement**; local x402 challenge/replay tests only |

The Windows softphone has its own README, repository, build, and licence notices. It is not vendored, branched, or modified by this project.

## Requirements

- Git for maintaining a local checkout.
- Node.js 22+ and Python 3.11+ for running public validation.
- The pinned Python dependencies shown below when running the documentation build or Peer Lab.
- `websockets==16.0` from `labs/web-softphone/requirements-test.txt` for the mandatory browser-controller WSS integration test.
- Optional Chromium/Playwright for browser smoke checks.
- Optional eSpeak, PocketSphinx, or compatible speech APIs for audio-first experiments. **Do not use recorded personal conversations or real booking details in the lab.**

No FreePBX, Asterisk, SIP credentials, wallet, USDC balance, or carrier access is required for the ordinary local development demonstrations. The optional BYOT connector requires separate Asterisk and agent credentials, and refuses real calls by default.

## Installing

Clone the published repository:

```bash
git clone https://github.com/kierknoby/AI-Dial-Tone.git
cd AI-Dial-Tone
```

Or use a source archive:

Unzip the release archive into a new directory, then run the local development checks from that directory. It is a standalone source tree; it does not require or modify `EgyptianEyes/Dial-Tone`.

See [PUBLISHING.md](PUBLISHING.md) for repository, CI, dependency, and static-site verification guidance. The public repository and static website already exist; do not upload private calling infrastructure or credentials.

## Running the Public Project

Run from the repository root:

```bash
python -m pip install 'markdown-it-py==4.2.0' -r labs/web-softphone/requirements-test.txt
python tools/build-site.py
python tools/build-reference.py
npm run check
node examples/restaurant-lab.mjs
```

The restaurant example is **synthetic**. Passing it does not mean a telephone rang or a table was booked. `npm start` launches a **local-only development server**, not a production API.

### Local bot-to-bot audio

```bash
python -m pip install 'aiohttp==3.13.3'
python tools/verify_first_call.py --out demo-output
python -m unittest discover -s peer-lab/tests -p 'test_*.py' -v
```

The demonstration creates two independently connected bot clients, transfers actual PCM over localhost WebSockets, and saves `caller_heard.wav`, `peer_heard.wav`, `proof.json`, and the independently checked local-only `verification.json`. Any text supplied by a bot is **an assertion, not a recognised transcript**. The experimental audio-first voice path is described in [Audio-first Voice](content/docs/19-audio-first-voice.md) and [the Peer Lab README](peer-lab/README.md). Its offline recognition accuracy is inadequate for real reservations.

### Bring Your Own Telecoms — experimental Asterisk bridge

**New optional development path:** see [BYOT Asterisk README](byot/README.md) and [Asterisk reference chapter](content/docs/20-byot-asterisk.md). The source now includes an independently tested HTTP/WebSocket ARI control adapter plus real local UDP RTP forwarding at 16 kHz; it has not contacted a live Asterisk or PSTN endpoint. Real origination is **disabled by default**, requires a configured dedicated PJSIP endpoint, a distinct operator bearer and agent bearer, and a one-time mandate specifying the destination and maximum duration.

```bash
npm run test:byot
# After configuring environment variables as described in byot/README.md:
python -m byot.server --check-config
```

Do **not** enable origination on a production or shared PBX. The test suite uses an isolated fake ARI server and actual loopback UDP sockets, not an actual SIP call. Until external Asterisk/PJSIP, network protection, and PBX-side orphan shutdown are verified, this connector is experimental only.

### Agent-first x402 payment-admission lab

This release adds a **non-production x402 v2 contract implementation**, with correct HTTP `402` / `PAYMENT-REQUIRED` challenge shape, a bound `PAYMENT-SIGNATURE` payload, and a single-use permit issued only when an injected facilitator reports successful upfront settlement. The local fixture uses **no wallet and no actual payment**. It does **not** enable real telephone origination and must not be hosted as a production payment gateway.

```bash
npm run test:x402
python -m payments.examples.first_paid_admission
```

A paid permit is not a PBX call authorisation. The managed service must additionally enforce SIP/WSS/TLS/SRTP readiness, destination restrictions, rate and spend limits, and provider-owned termination. See [the payment contract](payments/README.md) and [agent-first topology](content/docs/21-x402-payment-admission.md). BYOT remains usable without commercial payment.

### Operator-side x402 → BYOT handoff (local-only)

The standalone public code now contains an **integrated lab handoff** in [`integration/`](integration/README.md). It consumes an x402 lab permit once and creates a number- and duration-matched BYOT operator mandate, without giving the agent operator credentials. It **refuses to run against any BYOT instance with live origination enabled**; a simulated settlement can never be used to buy a real call. The handoff does not dial, and any ambiguous downstream response must be reconciled rather than retried.

```bash
npm run test:handoff
```

See [the payment-to-telecom integration chapter](content/docs/22-payment-telecom-handoff.md) and [the substantial public FAQs](site/faqs.html).

### Browser softphone research

```bash
cd labs/web-softphone
npm test
npm run test:bot
```

This is a local browser research tool, not a published SIP account service. Do not connect it to chargeable, emergency, or production calling routes.

## Updating AI Dial-Tone

For a published `main` branch, **review local changes first** and update with Git rather than deleting and reinstalling the project:

```bash
git status --short
git fetch origin main
git log --oneline HEAD..origin/main
git merge --ff-only origin/main
```

These commands affect only the standalone `AI-Dial-Tone` checkout. They do not access or modify the Windows softphone repository.

## Communication Architecture

1. A **human** specifies the task and supplies bounded, independently verifiable authority. An agent's self-reported approval is not sufficient.
2. A **bot** discovers the API and its declared capabilities. Documentation or an advertised tool does not imply that live calling is available.
3. The **Peer Lab** authenticates operator, caller, and peer separately; issues expiring, single-use admissions; exchanges attributed events and binary audio; and enforces a local deadline.
4. The **voice runtime** can segment actual received PCM, request transcription, obtain a model response, synthesise speech, and send it back. Real provider quality, latency, and interruption behaviour remain unaccepted.
5. A future **managed x402 gateway** must verify a fixed-price quote and receive independently trusted settlement before issuing one-time call admission. The local `payments/` contract does this against a fake facilitator only; no real USDC moves.
6. Future **Asterisk/PSTN integration** must independently verify SIP registration, TLS/certificate policy, encrypted media, INVITE/answer, metering, and actual channel termination. Native Dial-Tone's OPTIONS checks do not verify that a PSTN destination will connect.
7. An **outcome** distinguishes model-reported claims from network-confirmed events and independently verified reservations or transactions.

See [Architecture](ARCHITECTURE.md), [Roadmap](ROADMAP.md), [Peer Lab](peer-lab/README.md), and the [full machine-readable guide](site/llms-full.txt).

## Security Model

- **No live dialling:** the public repository must not expose production PBX, SBC, ARI, wallet, or settlement credentials.
- **Bounded authority:** an operator-controlled experiment may be stopped independently of the two bots. Lab bearer tokens are not a real human identity/consent solution.
- **Transport isolation:** the Peer Lab binds to loopback, uses separate bot credentials and one-use connection tickets, and is not designed for public Internet exposure.
- **SIP security:** native MicroSIP-derived Dial-Tone offers TLS and SRTP options, including modes that can permit fallback. The future agent calling gateway must require certificate-validated signalling and encrypted media without silent downgrade.
- **Call-state evidence:** local WebSocket session end is not PSTN channel hangup; a model's claimed booking is not a confirmed reservation; an event hash chain is not independent third-party proof.
- **Data handling:** the lab must use fictional data. Do not publish real recordings, transcripts, phone numbers, API keys, or SIP secrets in issues or test artefacts.

See [Native SIP Security](content/docs/16-native-security.md) and [Contributing](CONTRIBUTING.md). Production security controls belong in the **independent telecom service**, not browser prompts or agent assertions.

## User Interface

The public site has deliberately separate **For Humans** and **For Agents** experiences, alongside a simulated playground, reference documentation, roadmap, and trust/status material. The site itself is not an account portal, chargeable telephone service, or live operational dashboard.

Machine-readable discovery is available from generated `/agents.json`, `/agents.txt`, `/llms.txt`, and `/llms-full.txt`. These declare only current capabilities and must be kept in sync with the implementation.

## Deployment

Prepare static files from repository:

```bash
python tools/prepare-release.py --origin https://ai.dial-tone.uk --out ./site-deploy
```

Deploy **the contents of `site-deploy/` only**. Never serve the repository root or run the development peer server publicly. Verify HTTPS, CSP, headers, JSON and text content types, canonical links, and the actual privacy notice before enabling public hosting. See [DEPLOYMENT.md](DEPLOYMENT.md).

## Validation

```bash
npm run check
npm run test:peer
npm run test:byot
npm run test:x402
node examples/restaurant-lab.mjs
```

Optional browser check (requires Playwright and Chromium):

```bash
python tests/browser_smoke.py
```

The browser softphone's mandatory WSS integration runs with `npm test` from `labs/web-softphone/`; install its pinned npm packages with `npm ci` first. The separate full Chromium UI/media test is optional and is not part of the GitHub Actions job.

All checks are local/contract validations. They do not replace real SIP, model-provider, PBX, carrier, or x402 acceptance tests. Evidence and blockers are tracked in [release evidence](RELEASE-EVIDENCE.json), [ROADMAP.md](ROADMAP.md), [CHANGELOG.md](CHANGELOG.md), and `QA-REPORT.md` in the unpacked source package.

## Current Limitations

- No public hosted API, MCP server, or self-service accounts.
- No standalone SIP registration and no **verified live** SIP INVITE, Asterisk external media, or UK PSTN calling. The optional public BYOT module can attempt SIP origination through owner-operated Asterisk but has been network-tested only against a fake ARI server.
- No independent PBX hangup, carrier billing, or real x402 payment settlement. The new payment-admission fixture produces only synthetic facilitator receipts.
- No completed reservation, calendar integration, or verifiable real-world outcome.
- No high-quality, independently tested two-model voice conversation yet.
- Speech-recognition accuracy and barge-in latency are not yet acceptable for real-world tasks.
- The simulated playground, browser softphone lab, and Peer Lab are development tools, not production call services.

## Roadmap

**Original product focus:** autonomous agents making real telephone calls through a secure, FreePBX/PJSIP-centred service, with verified human authority and x402 payment for managed calling. The Windows MicroSIP-derived project supplies the security/readiness design baseline but no native code is included here. The browser and headless agent interfaces must implement those standards independently.


The dated, evidence-gated [roadmap](ROADMAP.md) covers local peer communication, real Asterisk and audio, natural model conversations, independent hangup, x402 reconciliation, restricted UK PSTN calling, and safe public onboarding. A feature remains **unavailable** until its corresponding live integration gate has been independently tested.

## Release History

### 0.0.1, initial public development release candidate, 11 October 2026

First public source release for `kierknoby/AI-Dial-Tone`: the local Peer Lab, experimental BYOT Asterisk adapter, audio-first voice runtime, static human/agent website, browser lab, contracts, executable demonstrations, and independent tests. No hosted telephony or commercial service is available. See [CHANGELOG.md](CHANGELOG.md).

## Support and Feedback

Once the new repository is published, use [AI-Dial-Tone Issues](https://github.com/kierknoby/AI-Dial-Tone/issues) for reproducible defects and requests. Do not open AI-specific issues against the separate Windows softphone. Include the revision, Python/Node/browser versions, reproduction steps, and **redacted** test output. Never include secrets or identifiable telephone recordings.

Report security concerns privately to **[ai@dial-tone.uk](mailto:ai@dial-tone.uk?subject=AI%20Dial-Tone%20security%20report)**. Begin without secrets or exploit details and ask for a secure exchange. See [SECURITY.md](SECURITY.md); GitHub private vulnerability reporting is an additional route only after it is enabled. For suspected abuse or unwanted contact associated with AI Dial-Tone, use **[dial-tone@egyptianeyes.com](mailto:dial-tone@egyptianeyes.com?subject=AI%20Dial-Tone%20abuse%20report)** instead. The 0.0.1 site provides no public calling service.

## Licence

**GPLv3-or-later for original AI Dial-Tone source in this standalone repository.** See [LICENSE](LICENSE) and [LICENSING-NOTE.md](LICENSING-NOTE.md). The separate Windows MicroSIP-derived repository retains its own **GPLv2-or-later** notices. No native Windows source is distributed here. Third-party libraries and non-code assets retain their own terms.

Using an API to communicate with a separately operated commercial service does not, by itself, make that service's independent implementation part of this source release. Assess actual code reuse and linkage before claiming an exception or a licensing obligation. A future standalone agent SDK may be licensed more permissively after an explicit provenance review.

## AI-Assisted Contributions and Disclosure

Code, tests, review, and documentation may use AI assistance, but the human contributor remains responsible. Each AI-assisted commit must disclose the agent and model in the commit message:

```text
Assisted-by: AGENT_NAME:MODEL_VERSION
```

For example, `Assisted-by: ChatGPT:GPT-6`. AI tools must not be listed as co-authors.

## Author

[@kierknoby](https://github.com/kierknoby), Kieran Knowles-Byrne. Developed personally; preparing as an [Egyptian Eyes](https://egyptianeyes.com) project. The separate [Egyptian Eyes code organisation](https://github.com/EgyptianEyes) includes the native Windows Dial-Tone project.
