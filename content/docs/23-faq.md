# Frequently asked questions

AI Dial-Tone 0.0.1 is an open-source technical preview. **No public PSTN calling, real x402 settlement or hosted MCP service is available.**

These answers are generated from the same question catalogue as the website and machine-readable `/api/faqs.json`.

## What it is

Purpose, audience and present availability.

### What exactly is AI Dial-Tone?

An open-source development project for giving autonomous AI agents controlled telephone communication. The current 0.0.1 code contains a local peer-audio runtime, an experimental Asterisk adapter and a separate x402 admission lab. It does not yet provide a public telephone calling service.

Further reading: [/docs/overview.html](/docs/overview.html)

### Who is it for?

AI-agent developers, operators of FreePBX/Asterisk systems, researchers testing voice-agent interactions and, eventually, humans asking their assistants to make calls. The technical interfaces are agent-first; people should see permissions and outcomes rather than SIP settings.

Further reading: [/humans.html](/humans.html)

### Can I ask my AI to book a restaurant today?

Not through a hosted AI Dial-Tone service. The restaurant example is an illustration and the public browser playground is scripted. Real booking requires live telephony, accurate ASR, task reasoning and independent confirmation; those acceptance gates remain open.

Further reading: [/docs/human-journey.html](/docs/human-journey.html)

### Why version 0.0.1?

It is the initial open-source development preview, not a declaration of production readiness. Earlier internal prototypes were not public releases. The tests cover local contracts and simulations, not commercial end-to-end calling.

Further reading: [/status.html](/status.html)

### How is this related to the Windows Dial-Tone softphone?

The independent AI project draws on the original Dial-Tone/MicroSIP fork for lessons in SIP diagnostics, PJSIP readiness, security and call lifecycle. The native Windows source is not included or ported into this repository. A browser-capable equivalent requires separate WebRTC/SIP integration and real interoperability testing.

Further reading: [/docs/native-security.html](/docs/native-security.html)

### Is the website itself the telephone service?

No. The public pages, discovery manifest and interactive playground are static demonstrations and documentation. Running them does not create an account, settle USDC or dial a telephone number.

Further reading: [/status.html](/status.html)

### Can I contribute before it is production-ready?

Yes. The public code, issue tracker, contracts, tests and roadmap are intended for independent contributors. The repository is GPLv3-or-later and requires appropriate disclosures for AI-assisted changes. Do not submit credentials, real call recordings or private customer data.

Further reading: [/docs/roadmap.html](/docs/roadmap.html)

### Who develops AI Dial-Tone?

AI Dial-Tone is developed by Kieran Knowles-Byrne (@kierknoby) in his personal development space and is being prepared as an Egyptian Eyes project (egyptianeyes.com). This is not yet a live Egyptian Eyes telecommunications service or a claim of completed organisational transfer. Kieran is Head of Product at FreePBX UK and develops FreePBX community modules; neither Sangoma nor FreePBX UK endorses this independent preview. General/privacy enquiries: ai@dial-tone.uk. Abuse reports: dial-tone@egyptianeyes.com.

Further reading: [/about.html](/about.html)

### What experience is behind the project?

Its engineering draws on more than a decade of work with SIP, Asterisk and FreePBX through 20tele and FreePBX UK. The original Windows Dial-Tone fork contributed the guiding pre-call readiness and diagnostic principle. Real Asterisk interoperability for the new AI project still has to be verified.

Further reading: [/about.html](/about.html)

## Autonomous agents

Discovery, models, authorisation and the agent API.

### How does an AI agent discover AI Dial-Tone?

The static site exposes agents.json, llms.txt and a full developer reference. These are project-specific information resources, not a registered MCP endpoint, an A2A Agent Card or proof of an available online calling service. The agent must inspect the availability flags before attempting any action.

Further reading: [/agents.html](/agents.html)

### Is there a public MCP tool I can call?

Not in 0.0.1. A hosted MCP or comparable agent-tool interface is on the roadmap. The existing locally runnable HTTP/WebSocket Peer Lab, self-hosted BYOT connector and payment lab have different contracts and security scopes.

Further reading: [/docs/agents.html](/docs/agents.html)

### Can an agent choose its own telephone number or trunk?

No. A human/operator mandate specifies the permitted destination and call duration. The Asterisk connector uses a preconfigured PJSIP endpoint; the agent token cannot select a trunk, dialplan context or arbitrary destination.

Further reading: [/docs/byot-asterisk.html](/docs/byot-asterisk.html)

### Must I use an OpenAI model?

No. The speech and conversation interfaces are designed to accept independently configured model-compatible providers. The local test fixtures do not establish real-model conversation quality or compatibility with every vendor.

Further reading: [/docs/audio-first-voice.html](/docs/audio-first-voice.html)

### Can two AI agents communicate with each other?

Yes, within the local research Peer Lab: separately authenticated clients exchange sequenced PCM audio, DTMF and control events. This is not yet publicly reachable, and their exchanged text is treated as an assertion unless it was actually recognised from audio.

Further reading: [/docs/peer-lab.html](/docs/peer-lab.html)

### Can an agent speak with an ordinary person?

The necessary audio pipeline and an experimental Asterisk external-media bridge exist, but a complete reliable conversation through a real telephone network has not been independently verified. Test only within isolated and authorised environments.

Further reading: [/docs/audio-first-voice.html](/docs/audio-first-voice.html)

### Can it navigate phone menus using DTMF?

The local peer protocol supports attributed DTMF events and the experimental BYOT agent interface exposes DTMF signalling. Reliable IVR navigation on a real PBX, including timing and error cases, remains an acceptance test.

Further reading: [/docs/media.html](/docs/media.html)

### Can I pass SIP passwords to an AI model to make it call?

Do not. Agent prompts and model context are not credential vaults. SIP accounts, wallet signing, ARI credentials, destination policy and termination controls belong in separately authenticated services outside the model.

Further reading: [/trust.html](/trust.html)

## FreePBX and telecoms

PJSIP topology, readiness, media and bridging.

### Is FreePBX the reference topology?

Yes. FreePBX/Asterisk with PJSIP is the design reference for secure registration, routing, call states and media. Alternative telecom providers may implement the public agent-side contracts, but they must meet equivalent security and evidence requirements.

Further reading: [/docs/provider.html](/docs/provider.html)

### Do I need a Windows computer?

No. The native Windows softphone is a separate inspiration, not a runtime dependency. The agent service is intended for headless or web-compatible deployment, with a browser/WebRTC research lab today and production browser-SIP integration still to be verified.

Further reading: [/docs/native-security.html](/docs/native-security.html)

### Does MicroSIP run directly in the browser?

No. The Windows C++ client cannot simply be loaded into a browser. SIP.js/WebRTC or another browser-compatible engine must implement equivalent policy and diagnostics; calling it a MicroSIP port would be misleading without actual ported code.

Further reading: [/docs/native-security.html](/docs/native-security.html)

### Does successful SIP OPTIONS mean a call will work?

No. It can prove a configured SIP endpoint responded within a measured time. It cannot prove route permission, carrier/PSTN reachability, INVITE success, RTP establishment, audio quality or that a reservation was accepted. These need separate evidence.

Further reading: [/docs/readiness.html](/docs/readiness.html)

### Does AI Dial-Tone already establish SIP registration?

The standalone 0.0.1 project does not supply a verified headless SIP REGISTER client connected to FreePBX. The experimental BYOT bridge uses an existing configured Asterisk PJSIP endpoint and queries its ARI state; that is not a replacement for registration, TLS or media inspection.

Further reading: [/docs/byot-asterisk.html](/docs/byot-asterisk.html)

### Will SIP TLS and SRTP be mandatory?

The intended managed reference topology requires verified SIP TLS and mandatory secure media (SRTP/DTLS-SRTP), with no insecure fallback. The existing experimental external-media RTP connector is deliberately restricted to loopback or isolated private networking; it is not an SRTP gateway.

Further reading: [/docs/native-security.html](/docs/native-security.html)

### Can it handle audio interruptions?

The local voice runtime supports interruption and cancellation tests. Proper barge-in, jitter, endpoint latency, held calls and telecom-network media behaviour still require real PBX and model-provider testing.

Further reading: [/docs/audio-first-voice.html](/docs/audio-first-voice.html)

### Will the agent receive access to the PBX dialplan?

No. Operators configure the permitted PJSIP endpoint and route policy. The agent receives a bounded call capability, not general PBX administration or the ability to alter dialplan configuration.

Further reading: [/docs/byot-asterisk.html](/docs/byot-asterisk.html)

### Can you establish a usable call route before bothering a human?

The design aims to check PBX registration, recent SIP response, approved route policy, secure transport and an isolated tone/echo media path before dialling a person. These checks can remove predictable failures, but they cannot guarantee carrier acceptance, remote answer or two-way PSTN audio.

Further reading: [/readiness.html](/readiness.html)

## Bring your own telecoms

Self-hosting with an existing PBX and SIP service.

### Can I bring my own SIP trunk or provider?

That is a first-class design goal. The repository includes an experimental self-hosted Asterisk ARI adapter with WebSocket agent media and RTP bridging. It has passed simulated Asterisk protocol tests, not real Asterisk/PSTN interoperability tests.

Further reading: [/docs/byot-asterisk.html](/docs/byot-asterisk.html)

### Do I need to pay through x402 for my own Asterisk calls?

No. BYOT is an independently deployable path. Operators bring their own PBX and commercial relationship. The experimental x402 gate is a separate reference for the future managed calling option, not a BYOT licensing requirement.

Further reading: [/docs/x402-payment-admission.html](/docs/x402-payment-admission.html)

### Can I point the connector at my production FreePBX?

Not recommended for 0.0.1. Use an isolated test extension with no chargeable, emergency or external routes. Real PBX testing, credential management and a PBX-side watchdog are still outstanding. Live origination remains disabled unless an operator explicitly opts in.

Further reading: [/docs/byot-asterisk.html](/docs/byot-asterisk.html)

### Why use ARI instead of giving the model a SIP account?

ARI allows an independently authenticated call-control service to own origination and bridge lifecycle while the agent receives only media and bounded call controls. Keeping SIP credentials outside the model reduces privilege and helps enforce a server-owned termination path.

Further reading: [/docs/architecture.html](/docs/architecture.html)

### Does the existing BYOT adapter support all PBXs?

No. Its initial backend is Asterisk ARI externalMedia and a configured PJSIP endpoint. Other PBXs need adapters providing equivalent admission, media, state and forced release semantics. No universal SIP-provider compatibility claim is made.

Further reading: [/docs/byot-asterisk.html](/docs/byot-asterisk.html)

### Will the application install FreePBX for me?

No. Self-hosted administrators provision and protect their own FreePBX/Asterisk installation, endpoint, routes, ARI account and media networking. AI Dial-Tone supplies reference integration, not a PBX installer.

Further reading: [/docs/byot-asterisk.html](/docs/byot-asterisk.html)

### How is the experimental paid-permit handoff related to BYOT?

A local-only development coordinator can consume a one-use x402 lab permit and issue an identical destination/duration BYOT mandate. It explicitly refuses BYOT configurations with live origination enabled. It demonstrates contracts connecting, not real payment or chargeable calling.

Further reading: [/docs/payment-telecom-handoff.html](/docs/payment-telecom-handoff.html)

## x402 and payments

Price, settlement, wallet custody and trust boundaries.

### What is x402?

x402 is a payment protocol built around HTTP 402 responses. AI Dial-Tone models an upfront fixed-price challenge and one-use admission as a way for an agent to obtain a calling capability after separately authorised settlement.

Further reading: [/docs/x402-payment-admission.html](/docs/x402-payment-admission.html)

### Can I pay AI Dial-Tone in USDC today?

No. 0.0.1 includes a local x402 v2 protocol fixture but no live facilitator, merchant wallet, production billing account or hosted checkout. No on-chain transfer has been verified by this project.

Further reading: [/docs/x402-payment-admission.html](/docs/x402-payment-admission.html)

### Which network and token are the planned defaults?

The research contract recognises native USDC on Base mainnet and Base Sepolia. Test fixtures use Base Sepolia values, with fabricated transaction results. Actual network availability, merchant accounts and published GBP pricing must be established before launch.

Further reading: [/docs/x402-payment-admission.html](/docs/x402-payment-admission.html)

### Does a payment allow any number to be dialled?

No. Payment is not a calling mandate. It must be bound to a separately authorised purpose, destination, time limit and price, and a fresh SIP/network policy decision must still pass. A paid request can legitimately fail admission.

Further reading: [/docs/x402-payment-admission.html](/docs/x402-payment-admission.html)

### Is pricing per second or fixed upfront?

The current x402 research flow uses a fixed upfront amount and a strict maximum call duration; it does not implement metered per-second settlement or real GBP conversion. Any future variable pricing requires an explicit published contract and separate accounting.

Further reading: [/docs/x402-payment-admission.html](/docs/x402-payment-admission.html)

### What if payment succeeds but the call fails?

That is an unresolved commercial outcome, not proof of a completed service. A real provider needs durable reconciliation, refund/dispute handling and independent call evidence before charging customers. The local lab deliberately does not claim automatic refunds.

Further reading: [/docs/x402-payment-admission.html](/docs/x402-payment-admission.html)

### Does the AI ever hold my wallet keys?

It should not. Wallet signing, settlement proof verification and merchant keys must stay outside the model and beyond any public agent-facing tool. The local payment fixture does not manage wallets or private keys.

Further reading: [/trust.html](/trust.html)

### Why is the local x402 handoff unable to make a real call?

Because a fake settlement fixture must never become a route to chargeable calling. The integrated development handoff refuses an enabled origination backend and returns only a separate local BYOT mandate. Production payment-to-call admission remains future engineering.

Further reading: [/docs/payment-telecom-handoff.html](/docs/payment-telecom-handoff.html)

## Safety and privacy

Human control, legal boundaries and operational limits.

### How does the human approve a call?

The intended service uses authenticated human identity and a server-held, time-limited mandate for a specific task, destination, spending ceiling and duration. Current local prototypes use operator bearer tokens and do not prove actual human identity or consent.

Further reading: [/docs/human-journey.html](/docs/human-journey.html)

### Can the operator stop a call?

The local peer lab has an operator stop. The experimental Asterisk connector can issue ARI hangup and check channel disappearance. That observation is not proof of carrier release, and a watchdog surviving process crashes remains required.

Further reading: [/docs/lifecycle.html](/docs/lifecycle.html)

### What happens if the AI goes offline halfway through?

The local connectors attempt to end sessions on disconnects, errors or deadlines. Production requirements go further: independent PBX-side cutoff, call reconciliation after restarts and never trusting the model to hang up its own call.

Further reading: [/docs/errors.html](/docs/errors.html)

### Can it call emergency, premium-rate or arbitrary international numbers?

The supplied lab policies restrict destinations, with the restaurant-style lab permitting UK geographic numbers only. Emergency, premium, mobile, international and ambiguous routes must remain blocked unless separately designed and legally reviewed; an agent cannot waive policy.

Further reading: [/docs/peer-contract.html](/docs/peer-contract.html)

### Does it record calls by default?

The demonstration can write WAV recordings to local development folders when explicitly run. It does not operate a hosted recording service. Real deployments need consent, retention policy, encryption, regional privacy assessment and clear control over recordings.

Further reading: [/privacy.html](/privacy.html)

### Does an audio transcript prove the person agreed?

No. ASR may be wrong, a model can hallucinate, and an agent can misreport. A stated booking reference is conversation evidence but not independent confirmation. The system must distinguish model claims, recognised speech and provider-confirmed network events.

Further reading: [/docs/events.html](/docs/events.html)

### Can callers use it for marketing or robocalling?

The design is for specifically authorised tasks, not unrestricted bulk calling. Any real deployment must enforce applicable communications, privacy, consent and nuisance-calling rules, with destination and rate restrictions. For UK-originated calling, the network operator must also handle Calling Line Identification correctly: Ofcom’s General Condition C6 guidance requires valid, dialable CLI that uniquely identifies the caller. Providing a routable number with a clear route for complaints or abuse reports is a sensible operating choice, but this preview does not verify CLI policy or supply an abuse-reporting service.

Further reading: [/trust.html](/trust.html)

### Will secrets or internal telecom configuration appear in GitHub?

They must not. The public source contains generic provider interfaces and laboratory configurations, not commercial provisioning credentials, routing databases, ARI secrets or hosted service implementation. Operators must supply their own environment configuration.

Further reading: [/trust.html](/trust.html)

## Calls and outcomes

Reliability, evidence and errors.

### Does a ringing call count as successful?

No. Ringing, answer, bidirectional audio, a completed task and verified customer outcome are different states. The interface must report which transitions were observed and what remains unknown.

Further reading: [/docs/lifecycle.html](/docs/lifecycle.html)

### Can AI Dial-Tone confirm a restaurant booking?

Not independently in 0.0.1. A model can report what it heard, but that is not necessarily an authoritative booking confirmation. A future integration may verify a reservation reference through a recognised provider where available.

Further reading: [/docs/human-journey.html](/docs/human-journey.html)

### What happens when the destination is busy or unreachable?

The intended lifecycle terminates with a machine-readable reason, usage evidence and no invented success. The current simulator includes failure scenarios; the real telecom failure taxonomy and reconciliation still need live Asterisk testing.

Further reading: [/docs/errors.html](/docs/errors.html)

### Can it call another AI instead of a person?

Yes within the local peer test service. A real PSTN-facing bot peer would require the same mandate, identity, audio and network controls as any other destination, plus separate dialogue-quality testing.

Further reading: [/docs/peer-contract.html](/docs/peer-contract.html)

### How do I distinguish local tests from real calls?

Inspect status and evidence flags. The site says technical preview, the OpenAPI points at localhost, the playground says simulated, and the BYOT health endpoint reports whether live origination is enabled. Do not infer a successful call from an event fixture.

Further reading: [/status.html](/status.html)

### Can I make simultaneous calls?

The experimental BYOT service is intentionally single-active-call. Concurrency, fairness, worker isolation and enterprise rate limits are future requirements. The peer lab also has explicit bounded resource limits.

Further reading: [/docs/byot-asterisk.html](/docs/byot-asterisk.html)

## Development and licensing

Running, deploying, contributing and support.

### Where is the source code supposed to live?

The intended standalone repository is kierknoby/AI-Dial-Tone on its main branch. The Windows Egyptian Eyes Dial-Tone repository is separate and should not be modified when developing this AI project.

Further reading: [/docs/overview.html](/docs/overview.html)

### What licence applies?

The new public AI Dial-Tone source is GPLv3-or-later, subject to third-party dependency notices and separate artwork rights. The native MicroSIP code is not shipped in this repository. Commercial hosting infrastructure is not included.

Further reading: [/docs/overview.html](/docs/overview.html)

### Can I use it commercially?

GPLv3 permits commercial use and redistribution under its conditions. It is not a certification of suitability for handling real calls or payments. Operators remain responsible for telecommunications, privacy, security, and any relevant software licence obligations.

Further reading: [/docs/overview.html](/docs/overview.html)

### Is it an official FreePBX, Asterisk or MicroSIP product?

No. AI Dial-Tone is an independent project with a FreePBX/Asterisk reference design. Its upstream inspirations, dependencies, trade names and trademarks belong to their respective owners; interoperability should not be mistaken for endorsement.

Further reading: [/docs/native-security.html](/docs/native-security.html)

### How do I reproduce the tests?

Install the documented Node.js and Python versions, regenerate the site and docs, run npm run check, npm run test:peer, npm run test:byot, npm run test:x402 and npm run test:handoff. The browser lab and optional Chromium smoke checks have their own scripts.

Further reading: [/docs/quickstart.html](/docs/quickstart.html)

### Can I deploy the static site without the backend?

Yes, it is a documentation and preview site. Hosting it does not expose the local Peer Lab, BYOT connector or x402 fixture. Before public deployment, review DNS, content security policy, privacy disclosures, legal notices and accessibility.

Further reading: [/status.html](/status.html)

### How do I report a security issue?

Use the repository security policy rather than publishing credentials or exploit details in an issue. Until a private disclosure channel is explicitly configured, do not assume a monitored security mailbox or service-level agreement exists.

Further reading: [/trust.html](/trust.html)

### How do I know what is finished next?

Use the engineering roadmap and build-status page. A simulated ARI call does not close the real FreePBX interoperability gate, and a mock settlement does not close the live x402 settlement gate. Only independently tested evidence advances those claims.

Further reading: [/roadmap.html](/roadmap.html)
