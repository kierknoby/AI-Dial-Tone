# AI Dial-Tone 0.0.1 — Initial Public Development Release

**11 October 2026 · Local technical preview with experimental BYOT and x402 admission contracts**

## Publication and maintenance note (14 October 2026)

The 11 October release preparation was followed by publication of the public repository and static website. The initial hosted Actions run succeeded on commit `35348ad0d34bfb5e89b5f1db1a9b7d3eaca19536` (run [38625817798](https://github.com/kierknoby/AI-Dial-Tone/actions/runs/38625817798)); it does not include the changes in the current hardening worktree. The repository and website status in the original notes below is historical and must not be read as the present publication status.

This maintenance update makes the WSS browser-lab integration a required test, bundles the pinned SIP.js dependency locally instead of loading it from a third-party runtime CDN, raises the declared Node.js minimum to 22, and corrects the publication verifier's robots.txt cache expectation. These changes do not enable or claim live SIP/PSTN calls, production payment settlement, or a hosted calling API. See [QA-REPORT.md](QA-REPORT.md) and [RELEASE-EVIDENCE.json](RELEASE-EVIDENCE.json) for validation scope and point-in-time evidence.

The first public version of AI Dial-Tone is an independent repository under `kierknoby`, unrelated to the Windows softphone's Git history. It includes executable, authenticated bot-to-bot WebSocket PCM experiments, an audio-first ASR/model/TTS pipeline with fixture-tested interruption and operator stop, a static website, and human/agent documentation.

### What is demonstrable

- A local, bounded, independently authenticated bot-to-bot PCM session with revocation and a test event journal.
- A locally testable speech pipeline using a model-protocol fixture (not a real hosted LLM).
- An explicitly synthetic browser playground and a separate experimental browser softphone.
- An x402 v2 `exact`/`upfront` payment-admission library with local challenge/response tests and a fake facilitator. This makes no payment or phone call.
- A new local, operator-only x402-to-BYOT handoff that refuses enabled origination and does not dial.
- A searchable 63-question website FAQ, generated into machine-readable JSON and the developer reference.
- The complete approved Project Overview, preserved verbatim in the README and on a dedicated website page, with a prominent homepage entry point.
- A new optional Asterisk ARI/RTP reference adapter under `byot/`, with real loopback HTTP/WebSocket and UDP network integration against a fake Asterisk implementation. Real telephone origination is OFF by default.

### What does not work yet

There is no publicly hosted calling API, **real PBX/PSTN integration proof**, proven human booking, successful high-accuracy recognition, payment settlement, or provider-confirmed hangup. The self-hosted experimental ARI connector must not be treated as production-ready. The site is not a live service. See `QA-REPORT.md` and `ROADMAP.md` for acceptance criteria.

### Readiness, operator provenance and public presentation (pre-publication work)

- Applies the project palette: gold `#c29200`, blue `#30beff`, neutral `#dedede`, white and black.
- Adds verifiable Kieran Knowles-Byrne, 20tele and FreePBX UK background with public project links, without implying an AI Dial-Tone endorsement.
- Restores the original Dial-Tone pre-call readiness, audible feedback and Call Trace principle as an explicit design goal; makes the SIP/PSTN qualification boundary clear.
- Adds operator-authenticated read-only `/v1/readiness` to the **local** BYOT reference connector. It never authorises an outbound call.
- Expands technical docs and FAQs while preserving the approved Project Overview unchanged.

### Agent-calling homepage priority (pre-publication, 11 October 2026)

- Leads with the purpose: give autonomous AI agents the ability to make telephone calls on behalf of their humans.
- Makes human approval, optional managed x402 access, conversations, and evidence the primary journey.
- Removes oversized pre-call qualification blocks and the Pre-call top navigation item; retains the dedicated readiness page, footer link, and engineering documents.
- Points the navigation CTA to the runnable developer quickstart instead of making the scripted playground look like the whole product.
- Preserves the approved canonical Project Overview, the exact 0.0.1 version, and all operator/private boundaries.

### Final pre-release developer verification (11 October 2026)

- Adds a root-level one-command local first-call verifier. It executes the existing independent two-peer PCM demonstration and validates received WAV media, bounded permissions, local session shutdown and unverified outcome boundaries, emitting a machine-readable `verification.json`.
- Enriches static agent discovery with exact locally runnable interface availability, documentation routes and proof scope; adds cross-surface regression checks.
- Clarifies that experimental self-hosted BYOT origination exists but has **not been verified on real Asterisk**, while encrypted SIP/SRTP and PBX-independent supervision are **not implemented**. No hosted service or real settlement is introduced.

### End-to-end product clarity and developer capability (pre-publication, 11 October 2026)

- The website is the public entry point for **one end-to-end AI calling service in development**, with managed access or Bring Your Own Telecoms as two paths to the same intended agent-facing experience.
- The GitHub repository is the source, developer tooling, reference implementations, tests and contributor home, not a separate BYOT-only product.
- Human approval and telecoms operator call admission, routing and independent termination remain separate responsibilities.
- The agent page and machine-readable discovery now describe the entire intended journey and link to developer integration, BYOT, and contribution documentation.
- Version 0.0.1 remains an honest static-site technical preview with local experiments. No new live telephony, x402 payment, or hosted service capability is implied.

### Product boundary and publication verification (11 October 2026)

- Adds an explicit human and machine-readable register of shipped, target, excluded, and undecided capabilities, displayed by the static website without claiming that planned features are live.
- Adds negative cross-document publication checks and runs the two-peer local audio proof in hosted CI.
- Removes an asynchronous timing assumption in the browser lab authentication rejection regression without weakening the security condition.
- Retains the approved homepage styling and Project Overview, with no new public telephone or payment API.

### Personal development and Egyptian Eyes preparation (11 October 2026)

- Describes the current personal development workspace and the intended Egyptian Eyes project affiliation without suggesting a completed transfer or production telecoms operation.
- Keeps `ai@dial-tone.uk` for general/privacy enquiries and initial private vulnerability reporting; designates `dial-tone@egyptianeyes.com` for abuse reports.
- Adds distinct contact routes in the published trust and privacy pages, source security policy, developer documentation and FAQ. Neither mailbox is represented as verified or monitored until confirmed by the owner.

### Final public-contact, developer onboarding and live verification preparation (11 October 2026)

- Publish a known public maintainer contact for privacy requests and initial private security disclosure, with an explicit warning not to email credentials or exploit material unencrypted.
- Provide a clear `FIRST-CALL.md` demonstration, exact `verification.json` success fields, clean-run expectations and troubleshooting.
- Supply the read-only `tools/verify_publication.py` for post-upload HTTPS, static discovery, HSTS/CSP and HTTP-to-HTTPS checks.
- Refresh stale changelog figures and lock the public contact/onboarding boundaries under automated tests.
- At the time of the 11 October release-preparation snapshot, no actual website upload, repository creation, hosted CI run or GitHub private-vulnerability-reporting setting was claimed. See the 14 October publication note above for subsequently verified facts and remaining owner actions.

### Refined six-colour palette consistency (final 0.0.1 visual revision, 11 October 2026)

- Enforces only `#000000`, `#ffffff`, `#dedede`, `#808080`, `#c29200`, and `#30beff` across the static site, shared logo/social artwork and local browser softphone laboratory.
- Uses black, white and grey for shared navigation, typography and site structure. Public pages use gold as their sole accent; agent, developer and local playground pages use blue as their sole accent. Gold and blue are not mixed in one page.
- Removes previous extra greys, colour tints, mixed gold/blue embellishments and glow effects. Status meaning remains expressed through text as well as colour.
- Preserves the approved wording and content, including the canonical Project Overview, developer contracts, Egyptian Eyes preparation and the two published contact addresses. No additional phone or payment functionality is introduced.
- Public automated suite retains **80 passing tests**, now enforcing the five-token colour restriction and page-specific accents. All other existing local test suites have been re-run. Live deployment remains unverified.

### Neutral hierarchy and full-size preview restoration (11 October 2026)

- Adds the approved `#808080` mid-grey for neutral dividers and large decorative numbering. Retains black for small text on white backgrounds, where `#808080` does not reach WCAG AA normal-text contrast.
- Rebuilds the complete presentation pack with full-page desktop and mobile images. The preceding pack omitted roughly 2.26 MB of previews, not application source files.
