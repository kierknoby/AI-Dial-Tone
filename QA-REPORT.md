# AI Dial-Tone 0.0.1 — Initial public development release QA

**Date:** 11 October 2026. **Repository:** proposed `kierknoby/AI-Dial-Tone` (`main`). **Disposition:** local research software, not an Internet service or production telephony.

## Test results

| Test | Local result | Scope |
| --- | --- | --- |
| `npm run check` | **75/75 passed** | Source-backed API/manifest/docs consistency, security boundaries, static website links |
| `npm run test:peer` | **39/39 passed** | Actual localhost HTTP/WebSocket, PCM, ASR/model/TTS fixtures, stop/disconnect, malformed input, capacity |
| `npm run test:x402` | **20/20 passed** | Local x402 v2 HTTP challenge and fixed-price admission contract; fake facilitator, tamper/replay/timeout/revoke checks only |
| `npm run test:byot` | **22/22 passed** | Real local HTTP/WebSocket ARI protocol + UDP RTP against a synthetic Asterisk server; whitelists, tokens, PJSIP-online gate, admission, agent adapter, stop, hangup uncertainty |
| `npm run test:handoff` | **12/12 passed** | Real x402 lab permit + actual local BYOT HTTP/WebSocket integration, call refused when origination disabled, tamper/replay/uncertainty tests |
| `cd labs/web-softphone && npm test` | **33/33 passed** | Browser softphone research unit/contract tests (not live PBX) |
| `cd labs/web-softphone && npm run test:bot` | **3/3 passed** | Python scripted bot tests |
| `python tests/browser_smoke.py` | **Passed** | Chromium desktop and mobile static-site journeys; not real SIP |
| `node tools/audit.mjs` | **Passed** | Static publication structure and internal links |
| Site generation | **Reproducible** | `python tools/build-site.py && python tools/build-reference.py` |
| Source archive audit | **Rechecked at final packaging** | Version `0.0.1`, no generated caches or bundled credentials; GitHub initial commit and first hosted CI remain the owner's responsibility |

The latest local automated test total is **209 tests** (80 public + 39 peer + 22 BYOT + 20 x402 + 12 handoff + 33 browser + 3 Python bot). The peer transport suite was also repeated successfully across three consecutive runs after the disconnect termination fix. Results are generated on local development tools, **not** from hosted CI or a production system. The repository's first hosted GitHub Actions run remains outstanding.

## Explicitly not verified

The new BYOT connector passed real local protocol tests against a **synthetic Asterisk ARI server**. No real Asterisk authentication/media/DTMF behaviour has been verified.

The x402 lab executes **no real USDC payment** and contains **no production facilitator**. The test double only reports a synthetic settlement. No actual model-to-model unscripted service quality, real-time high-accuracy ASR, **real Asterisk/PJSIP interoperability**, carrier call, real SIP/TLS/SRTP gateway, independently verified PSTN hangup, verified human consent, booking, x402 settlement, production multi-tenant security, legal/privacy compliance or public service availability.

See [FORENSIC-AUDIT.md](FORENSIC-AUDIT.md) for discovered defects and the publication verdict, and [RELEASE-EVIDENCE.json](RELEASE-EVIDENCE.json) for machine-readable disclosure. **The BYOT, payment handoff, and 63-question FAQ were added before the first public release**, without changing the 0.0.1 version. Version 0.0.1 is the first public source candidate; prior internal prototypes are not public releases.

## 11 October review: FAQ and integrated admission contracts

- New operator-only `integration/handoff.py` binds one already-consumed x402 lab permit to an identical destination and duration on the real local BYOT operator HTTP API. **It refuses any service with origination enabled.** It does not place a call, verify real payment or give the agent operator credentials.
- Adversarial tests reject replayed permits, simultaneous double redemption, remote targets, enabled live calls, mismatched backend details, and ambiguous post-redemption outcomes. The real BYOT service test additionally exercises agent join/start and confirms `LIVE_ORIGINATION_DISABLED`.
- One content source (`content/faqs.json`) now creates 63 FAQ answers on a searchable accessible `/faqs.html` page, a `/api/faqs.json` resource, and a developer reference chapter. Eight subject areas cover purpose, agent protocols, SIP/FreePBX, BYOT, x402, privacy, call evidence and licensing.
- 25 reference chapters build; public docs still declare no hosted telephony, real x402 settlement, or verified human identity.
- The static-site privacy preview and architecture documentation no longer unnecessarily identify private telecom implementations.
- Release candidate was independently re-reviewed on 11 October: added GitHub-source documentation link verification, a runnable contributor-agent entrypoint, HTTP/MIME/CSP crawling, and an explicit RTP-integrity boundary.
- The source-only security review detected commercially sensitive system names inside *negative tests*. Those literal names have been removed from the public tests. The final archive is also checked separately for unwanted internal references.
- Automated Chromium tests render the actual site HTML/CSS/JS locally; direct Chromium navigation to localhost was blocked by this execution environment. An independent HTTP test now fetches the real static server routes and checks headers/MIME. A deployed website must pass real browser navigation and accessibility testing before hosting.

These additions are **development-contract proof only**. The end-to-end hosted product, genuine facilitator, real Asterisk interoperability, secure SIP/WSS/SRTP readiness and crash-resilient PBX termination remain unverified.

## Project Overview publication review

- The user-approved **Project Overview** is reproduced verbatim near the beginning of `README.md`.
- `content/project-overview.md` is the canonical text, rendered in full at `/overview.html` and excerpted on the homepage. The same page is linked from site navigation, the sitemap, and agent-readable discovery.
- Three new source-contract tests assert exact README wording, all 11 website paragraphs, page navigation and machine-discoverability.
- Desktop and mobile Chromium runs verified the overview layout, readability, and absence of horizontal overflow.
- No changes to original Windows softphone source, calling protocols, payment admission, or telephony runtime were made for this editorial update.
- Version remains **0.0.1**. The project is not yet deployed.

## Independent pre-publication follow-up (11 October 2026)

- Verified the actual documented first-call command, which created two genuine received-audio WAVs plus a hash-chained local session receipt; it did **not** establish any real-world calling or language-model competence.
- Repaired GitHub Markdown chapter links and preserved working `/docs/` web links in the generated HTML and `llms-full.txt`. Added a regression that checks all 25 source chapters against both renderings.
- Removed references to the operator's private internal systems from the released test source itself. Nothing in the public package needs to name the private orchestration or billing architecture.
- Added agent contributor entrypoint `AGENTS.md` with runnable local commands, explicit capabilities, safety boundaries, and links to genuine API documents. It is not an A2A Agent Card or hosted MCP interface.
- Reworded experimental RTP event evidence so address/port tuple filtering is not presented as cryptographic media authentication.
- Clarified Ofcom CLI and abuse-reporting design requirements, the two deployment models, and the distinction between the real local preview and planned paid UK calling.
- Verified local HTTP responses for all public HTML, JSON, CSS, JS, SVG and text resources with content-type and security-header assertions. Actual hosted-browser navigation remains an outstanding deployment test.
- These checks improve first-release trust and usability, **not** live call functionality. None of the R1–R6 production acceptance gates has passed.

## Pre-call readiness, public attribution and website palette (11 October 2026)

- Applied the requested gold `#c29200` and signal blue `#30beff`, supported by `#dedede`, white and black. Darker related ink colours are used where the bright accents would not give accessible small-text contrast on white. Desktop/mobile Chromium checks verify the site and new pages; they are **not** a complete WCAG accessibility audit.
- Researched 20tele and FreePBX UK directly, verified public code repositories, and added attributable origins, community-module references, and an independent-project disclaimer. No endorsement of AI Dial-Tone by Sangoma is claimed. Source references are present in `content/docs/25-origins.md`.
- Restored the distinctive principle from the original MicroSIP-derived Dial-Tone: qualify SIP/account/audio readiness, generate local audible feedback, and provide a useful trace **before** initiating a call. Real carrier/PSTN reachability cannot be guaranteed without an actual INVITE or answered-call evidence.
- Added the **read-only, operator-authenticated** local BYOT `GET /v1/readiness`: observes the configured PJSIP endpoint through Asterisk ARI only; never issues a mandate or originates and always returns `network_call_authorised: false`. It does **not** perform authenticated SIP OPTIONS, verify TLS/SRTP, inspect the dialplan, or certify carrier reachability.
- Added 5 public regression tests around branding, published provenance, agent discoverability, read-only preflight and native-readiness claims; expanded BYOT test coverage to 22. Documentation now has 25 source chapters and the single-source FAQ has 63 answers.
- Public README Project Overview remains verbatim and version remains 0.0.1. No remote GitHub repository, website deployment or real Asterisk/PSTN/payment transaction was created or executed by this update.

## Homepage emphasis review (11 October 2026)

- Reduced the disproportionate homepage emphasis on local dial tone and SIP route preflight; retained those as important technical safeguards in the dedicated readiness page and developer reference.
- Refocused the headline, call-session illustration, metadata, and navigation around autonomous agent calling, human authorisation, optional x402 payment, two-way speech and evidence.
- Verified the approved Project Overview remains byte-for-byte consistent in README and website, and that all preflight documentation is still linked and discoverable.
- Updated source-level brand tests and Chromium desktop/mobile assertions to protect the more balanced emphasis.
- No payment, telecom or voice-runtime implementation changed in this editorial iteration.

## End-to-end product and developer discovery review (11 October 2026)

- The website now presents AI Dial-Tone as a **single end-to-end agent calling product in development**, rather than a BYOT adapter or standalone peer lab. Managed calling and BYOT are explicitly two ways to access the intended common agent capability.
- The agent entry page explains discovery, human mandate, optional managed payment, provider-controlled route admission, conversation, independently controlled termination, and a grounded outcome; it provides clear agent developer, BYOT operator and contributor routes.
- Machine-readable `site/agents.json`, `site/agents.txt`, `site/llms.txt`, and the generated `site/llms-full.txt` distinguish the **target workflow** from **0.0.1 capabilities** and link to developer documentation and the GitHub repository.
- The root README and AGENTS.md distinguish the static product/discovery website from the open-source developer implementation. The approved canonical Project Overview remains verbatim and unchanged.
- Two new public regression tests verify product scope, the intended lifecycle, managed/BYOT options, developer paths and the continuing absence of live calling claims. Browser smoke tests now validate the updated human-facing page titles.
- Full local regression on this revised source: 71 public, 37 peer, 22 BYOT, 20 x402, 12 payment handoff, 33 browser-lab, 3 bot = **198 passed**. Chromium desktop/mobile smoke passed. No production SIP, payment, or hosted service was exercised.

## Final release polish and re-verification (11 October 2026)

- Added a root-level `python tools/verify_first_call.py --out demo-output` command. It runs the existing real local WebSocket/PCM two-peer demonstration and independently checks the received WAVs, documented audio format, roles, termination and explicit limits. It writes `verification.json` and exits unsuccessfully for inconsistent proof. It cannot verify a real network call, language model, payment or booking.
- Added two adversarial Peer Lab regressions confirming that forged real-call evidence and missing received media are rejected. No PSTN, payment or third-party API is touched.
- Added four machine-discovery, OpenAPI, file-existence, FAQ-count and publication-truth regressions. Reconciled the website status language: experimental BYOT ARI origination is implemented but real Asterisk/PSTN integration is **not verified**. Encrypted SIP/SRTP and PBX-independent cutoff remain **not implemented**.
- Regenerated the static HTML reference from its Markdown sources. The approved Project Overview and homepage visual design are unchanged. Re-ran the source audit, 204 local unit/integration tests and Chromium desktop/mobile smoke checks successfully. No production acceptance gates have passed.
- This is a local release-candidate verification, not an independent security audit, a successful remote GitHub Actions run or a deployed-site/browser acceptance test.

## Product boundary and clean publication review (11 October 2026)

- Added `PRODUCT-SCOPE.md` and a source-of-truth `content/product-scope.json`; the site derives `/scope.html` and `/api/product-scope.json` from the same data. Two new contract tests compare the machine publication directly to the release source.
- Browser lab: corrected an asynchronous test that asserted invalid HMAC rejection before the rejection completed; the same strict authentication failure and `4001` close condition remain mandatory.
- Latest measured local result: **80 public, 39 peer, 22 BYOT, 20 x402, 12 operator handoff, 33 browser and 3 bot tests, 209 passing**. The two-peer verifier also executed and confirmed local received audio, session closure and false real-world success fields.
- CI now includes the local audio verifier, but its first hosted run is pending publication. The site and GitHub repo are not independently validated on deployed infrastructure; the approved Project Overview is verified locally against its canonical source.
- Release boundary: public preview only. No real PSTN, real Asterisk media path, trusted x402 settlement, real booking or provider teardown has been verified. See `RELEASE-READINESS.md` for remaining manual release checks.

### Final publication preparation checks (11 October 2026)

- Source/publication suite now has **79** passing tests including privacy, security and quickstart cross-publication contracts. Full locally exercised suites: **79 + 39 + 22 + 20 + 12 + 33 + 3 = 208**.
- Chromium desktop/mobile source-content smoke checks passed after regenerating the privacy and reference pages.
- The hosted repository and cPanel origin are not currently reachable; new live verifier is provided but cannot constitute hosted acceptance before DNS, TLS and publication exist.
- The maintainer contact has a publicly disclosed address; actual hosting access-log retention, legal controller identity at deployment, repository private vulnerability-reporting setting and hosted CI remain outstanding publication actions.
