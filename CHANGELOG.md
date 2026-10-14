# Changelog

## 0.0.1, initial public development release candidate, 11 October 2026

- Establish the independent `kierknoby/AI-Dial-Tone` open-source research project.
- Publish the canonical, user-approved Project Overview in the README and at `/overview.html`, with a homepage introduction and exact-text regression tests.
- Publish the local authenticated bot-to-bot Peer Lab, PCM/WebSocket transport, and experimental audio-first ASR/model/TTS adapters.
- Publish the static developer website, human-facing preview, machine-readable capability description, SDK laboratory, and executable policy exercises.
- Add operator revocation, hard session cutoff, bounded protocol resources, and negative-path validation.
- Add a provider-neutral x402 v2 upfront/exact payment-admission library: real wire-shaped 402 challenge, operator-bounded destination, changed-term and replay rejection, fixture-tested settlement decisions, one-use permit; no real funds move.
- Add the optional self-hosted Asterisk ARI/RTP BYOT reference connector with real local protocol tests; origination remains disabled by default and unverified with live Asterisk.
- Add an operator-side, loopback-only x402-to-BYOT **development handoff**, binding destination and duration and refusing any backend where live origination is enabled. Validate with real local BYOT HTTP/WebSocket plus negative tests; no real payment or phone call.
- Add **63 FAQs across eight categories**, generated consistently into the website, human/agent documentation and `/api/faqs.json`, with searchable, accessible interaction.
- Expand the reference to 25 chapters and add deployment-safe FAQ navigation and evidence flags.
- Establish GPLv3-or-later licensing, contributor disclosures, reproducible checks, and a truthful 0.0.1 capability statement.
- Add `AGENTS.md` with a reproducible local bot quickstart and explicit non-production capability boundaries.
- Repair GitHub-source documentation links without breaking the website or agent-readable references, and add source-to-publication link tests.
- Expand real HTTP response/MIME/header coverage and clarify that RTP source-tuple pinning is not cryptographic media authentication.
- Document UK calling-line identification and abuse-reporting expectations without claiming they are implemented.

- Publish a maintainer contact for private security reporting and privacy requests; GitHub private vulnerability reporting remains an owner-controlled post-creation setting.
- Add `FIRST-CALL.md` with an exact local proof, evidence scope, troubleshooting and an external HTTPS/headers checker for the eventual cPanel deployment.
- Add automated tests preventing drift between published privacy, security and first-call instructions.

This is a **development preview**, not a production calling service. No publicly hosted PSTN origination, verified restaurant booking, hosted MCP endpoint, or x402 settlement has been implemented. The disabled-by-default BYOT connector has not been verified against a live PBX. Earlier internal development packages were unpublished prototypes and are not separate public releases.
