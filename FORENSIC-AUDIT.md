> **0.0.1 ongoing release-candidate note:** Subsequent work adds a source-only x402 v2 fixed-price admission lab, documented in `payments/README.md` and tested with a fake facilitator. This does not advance the live-payment, SIP interoperability, or customer-release acceptance gates.

# AI Dial-Tone 0.0.1 — Pre-publication forensic audit

**Audit date:** 10 October 2026
**Target:** `kierknoby/AI-Dial-Tone`, a new, standalone public repository, first development release `0.0.1`.
**Disposition:** **Suitable for publication as an explicitly non-production research source preview, subject to human ownership/licence review and successful GitHub CI. Not suitable for deployment as a telephone calling service.**

This report distinguishes verified local behaviour from plans. A passing test is not proof of carrier interoperability, correct model decisions, or user consent. The repository and live site have not been published by this audit.

## Release defects found and corrected

| Severity | Finding in the prior candidate | Correction / evidence |
| --- | --- | --- |
| Critical credibility | Public docs and OpenAPI described `/v1/calls`, SSE, MCP and a `PBX1` media framing protocol from an **unshipped private lab**. External developers could not execute the claimed contract. | Replaced the published specification, developer quickstart, agent discovery and reference with the actually shipped **localhost Peer Lab**, `/v1/sessions`, one-use WebSocket tickets and `DT01` PCM. Tests now reject a `/v1/calls` contract. |
| High integrity | The browser preview contained a dormant proxy to a private legacy calling API. This could make the static playground appear to have real backend support. | Removed the proxy and related tests. Static playground is now clearly scripted and the actual local Peer Lab is documented separately. |
| High reliability | A disconnect could cancel the departing socket's handler before the other bot received authoritative session termination; session state could be `ended` without prompt peer notification. | Protected disconnect/stop paths from request cancellation; deliver termination to surviving peers without waiting for the departing socket. Added adverse-path tests and repeated the peer test suite three times. |
| Medium availability | Peer-control collections had no explicit limit; repeated requests could grow mandates, sessions or unused tickets until process memory was exhausted. | Bounded the in-memory lab (`MAX_MANDATES=256`, `MAX_SESSIONS=128`, `MAX_TICKETS=256`) and return explicit `429` under pressure. A restart is the recovery mechanism; **not** a production persistence solution. |
| Medium input safety | Malformed Unicode in JSON/event text or an unhashable `mandate_id` could trigger a server error or disrupt hashing. | Input validation and regressions now reject these inputs as client errors. |
| Medium release integrity | The previous deliverable claimed cleaned packaging while the ZIP still contained `.pyc` and `__pycache__`; the README and reports mixed pre-public version numbers. | First release metadata consistently identifies `0.0.1`, with one initial release history. Release archive is assembled from an explicit Git tracked-file list, excluding bytecode, credentials, caches and test output. |
| Medium accuracy | Documentation and homepage risked presenting planned REST/MCP/telephony as existing, and the native security guide said “verified compatibility” although it was only a source review. | Reworded planned interfaces, headings, status, developer references and privacy text. No live native SIP interoperability is claimed. |
| Medium QA quality | Some tests asserted old, unavailable API behaviour instead of validating the release contents. | Replaced assertions with source-backed Peer Lab contracts and added version/manifest/OpenAPI checks. |

## Source and security boundaries checked

- **Original upstream Windows softphone:** entirely separate `EgyptianEyes/Dial-Tone` repository; no native MicroSIP/PJSIP source imported or modified.
- **Public code licence:** GNU GPL **3.0-or-later**, with a complete root `LICENSE`. The native Windows project's GPL **2.0-or-later** licence is unchanged and applies there, not silently to this new tree. Third-party source and assets require their own respective notices.
- **Experimental BYOT adapter added after the initial audit:** a disabled-by-default, single-call Asterisk ARI/RTP adapter is now public under `byot/`. It has actual HTTP/WebSocket/UDP tests against a fake Asterisk, but NO real Asterisk/PSTN acceptance, verified human account, wallet keys, x402, or booking actions.
- **Dev-only control plane:** local loopback binding, separate role credentials, one-time admission tickets, finite maximum session duration, operator revocation and stop. These are **not** Internet-exposure-grade controls.
- **Events and receipts:** a local hash-chained event record detects accidental tampering under a trusted process assumption. It does **not** prove an actual telephone connection, remote consent, booking, payment or provider-originated release.
- **Voice quality:** an actual offline eSpeak → PocketSphinx → model-protocol fixture → eSpeak audio path ran in prior development, but the particular recognition sample had **100% word error rate**. The included adapters are not evidence of reliable production conversation quality.
- **Privacy:** a browser-only scripted playground does not access real microphones or phone services. Privacy text explicitly requires hosting/operator and statutory review before website deployment.

## Local automated verification

See `QA-REPORT.md` and `RELEASE-EVIDENCE.json` for the exact counts and tools. Node tests cover contracts and generated publications, Python tests cover actual localhost HTTP/WebSocket peer traffic and voice fixtures, and Chromium checks desktop/mobile navigation. A clean Git import must leave generated reference files unchanged.

## What remains unverified or blocks actual service launch

1. **No verified real PSTN calling:** the new ARI control and external-media code is verified only against fake Asterisk over local network sockets; no real PBX call, SIP TLS/SRTP, routes, OPTIONS, provider hangup, crash-safe independent cleanup or speech intelligibility are verified.
2. **No real AI acceptance:** two genuinely independent live models, strong ASR accuracy across accents/noise, realistic turn-taking, latency under load, reliable barge-in, hallucination containment, real booking proof.
3. **No production identity:** the in-memory operator bearer token is not a human-account permission system; restart destroys sessions and evidence. No durable transactional state, robust rate-limiting, audit logging or recovery.
4. **No payment or legal review:** no verified x402/USDC/GBP billing, carrier fraud controls, UK telecom/consent/recording compliance, formal threat model or operational incident response.
5. **Website publication blockers:** verify the site's owner/operator identity, legal disclosures, contact and privacy retention practices after hosting is selected. Validate externally reachable HTTPS, CSP and static file MIME types, and review artwork provenance.
6. **CI and dependency review:** GitHub CI runs Python 3.11 and Node 22; local verification uses the versions recorded in `QA-REPORT.md`. Third-party dependency inventory and provenance warrant ongoing review; the browser SIP laboratory uses external development dependencies and is not production-hardened.
7. **Independent security assessment absent:** no professional pentest, adversarial multi-tenant trial, external agent installation test, telecom provider integration or real payment verification.

## Decision

**Proceed only with a `0.0.1` first public development-source release**, using wording such as “local agent-to-agent communication research preview”. Do **not** launch the site as a functioning AI telephone service, market reservation completion, take money, expose the Peer Lab on the Internet, or permit PSTN access.

When the new repository exists, check its initial GitHub Actions run before creating a `v0.0.1` tag. The next engineering acceptance gate is a high-quality two-model audio conversation **and** a real isolated Asterisk/SIP interoperability test, not another README or branding change.

## Continuation audit: self-hosted Asterisk BYOT connector (same first 0.0.1 candidate)

The new `byot/` component changes the public implementation boundary but **does not prove a real telephone call**. It includes one fixed configured PJSIP endpoint, operator-scoped one-use mandates, agent admission before origination, a hard off-by-default origination flag, ARI event and PJSIP endpoint-state checks, `externalMedia` RTP/L16/16kHz, first-packet source and sequence checks, finite queues, a process-local duration, DTMF, best-effort cleanup, and explicit carrier-release uncertainty. The integration suite connects through actual local HTTP, ARI WebSocket and UDP sockets to a **synthetic Asterisk server**, not to Asterisk or any trunk. The existing model-neutral audio runtime can use a `CallClient` adapter; model conversational reliability is still unverified.

**Residual publication/production blockers:** the ARI authentication, endpoint-state and RTP mapping are untested on a real Asterisk version; SIP TLS/SRTP policies cannot be inferred from the connector; RTP in this reference is unencrypted; the agent-side audio pipeline lacks production echo suppression and reliable ASR; process-local hangup enforcement cannot survive a crash; no independent carrier egress limits, billing, consent provenance, secure persistent accounts, recording policy or human-driven acceptance test exists. **Only publication as experimental research code is defensible.** Do not run `AIDT_ENABLE_LIVE_ORIGINATION=YES` on production infrastructure.

## Follow-up pre-publication forensic findings (11 October 2026)

| Severity | Finding | Verified resolution |
| --- | --- | --- |
| High (confidentiality) | Private internal system names appeared literally in two public negative-test assertions, despite being absent from the published website. | Removed those references from test source and separately audited the exported repository. No private routing or billing implementation is included. |
| Medium (onboarding) | Links between Markdown developer chapters pointed to `.html` files that exist only after rendering, so a reader browsing source on GitHub would encounter broken destinations. | Corrected the 23 Markdown source chapters and taught the renderer to emit public `/docs/` URLs for the generated website and machine guide. Added regression tests. |
| Medium (truthfulness) | The roadmap called the future restricted UK x402 calling journey a completed first-release experience. | Replaced that statement with a clear local Peer Lab capability and an unimplemented paid-call acceptance target. |
| Medium (evidence) | An experimental RTP bridge event described a pinned IP:port as a “trusted peer”, which could imply authenticated/encrypted media. | Replaced the claim with `rtp_source_tuple_locked` and `rtp_integrity_verified:false`, and added a regression test. |
| Medium (release testing) | Existing browser smoke loaded site assets locally, rather than navigating the real static HTTP server. | Expanded real HTTP route/asset, MIME and header checks. Browser navigation to loopback was blocked by this environment, so real hosted-browser checking remains required. |
| Low (accuracy) | Documentation compilation retained an earlier edition date and a literal template expression in one page description. | Fixed both in the generator. |
| Design gap | UK caller ID and abuse-reporting expectations were not prominent enough in the public engineering plan. | Added the valid, dialable CLI requirement and scoped abuse-reporting guidance; these controls are not implemented in the lab. |

**Follow-up verdict:** the source is suitable as an explicitly non-production 0.0.1 research release candidate, conditional on maintainer review, first hosted CI, private security reporting configuration and accurate website legal disclosures. It is *not* suitable for public real calling or commercial payment settlement. No outside penetration test or live SIP security audit has been carried out.
