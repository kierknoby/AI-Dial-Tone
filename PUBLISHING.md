# Publishing and maintaining AI Dial-Tone

**Current status (verified 14 October 2026):** [`kierknoby/AI-Dial-Tone`](https://github.com/kierknoby/AI-Dial-Tone) is a public repository and `https://ai.dial-tone.uk/` is a reachable static website. The initial hosted Actions run succeeded on commit `35348ad0d34bfb5e89b5f1db1a9b7d3eaca19536` (run [38625817798](https://github.com/kierknoby/AI-Dial-Tone/actions/runs/38625817798)); it predates the current uncommitted maintenance changes. This document is therefore a verification and maintenance guide, not an instruction to create or republish the repository.

The project is developed personally, with Egyptian Eyes identified as a planned project affiliation rather than a completed transfer or an already operating commercial service.

## 1. Review a proposed release

From a clean checkout with Python 3.11+ and Node.js 22+:

```sh
python -m pip install 'aiohttp==3.13.3'
npm run check
npm run test:peer
npm run test:byot
npm run test:x402
npm run test:handoff
python tools/verify_first_call.py --out demo-output
cd labs/web-softphone
npm ci
npm run build:sipjs
python -m pip install -r requirements-test.txt
npm test
npm run test:bot
```

Run `node --test tests/wss-integration.test.js` in `labs/web-softphone/` after installing its Python test requirements. Run the optional documentation build with `markdown-it-py==4.2.0`, then confirm generated files are unchanged. Review `PRODUCT-SCOPE.md`, `RELEASE-READINESS.md`, `FIRST-CALL.md`, `SECURITY.md`, the GPL-3.0-or-later `LICENSE`, `LICENSING-NOTE.md`, and site privacy notice. Check that no credentials, customer data, private backend, or audio recordings are present. Confirm `ai@dial-tone.uk` is authorised for general, privacy and initial private security correspondence; separately confirm `dial-tone@egyptianeyes.com` receives abuse reports. Mailbox delivery, legal/privacy review, host access-log retention, and GitHub private reporting settings require owner verification; none is inferred from this guide.

## 2. Verify the repository and CI

The public repository already exists. Review the branch, exact source diff, generated-document changes, licence, and security disclosures before proposing any release changes. The workflow at `.github/workflows/verify.yml` targets `main`; verify the hosted run for the exact candidate commit. Do not treat the historical successful run above as verification of later source changes.

Do not force-push or replace repository history. Use the repository's normal reviewed contribution process for future changes. No publishing, commit, or push is performed by this guide.

## 3. Verify private vulnerability reporting

Open **Settings → Code security → Private vulnerability reporting** and verify its status; it is not claimed enabled here. Until the owner confirms the setting and the security contact, use `ai@dial-tone.uk` as described in `SECURITY.md`. For abuse, use the separate `dial-tone@egyptianeyes.com` address, not the security mailbox. Do not claim either mailbox has been tested for delivery.

## 4. Verify the static website

The existing website is a static product/discovery site, not a calling API. After reviewing any proposed static-site change, build into a separate output directory:

```sh
python tools/prepare-release.py --origin https://ai.dial-tone.uk --out ./site-deploy
```

Host **only** the generated static files, not the repository root. Confirm the actual website controller, host/log retention settings, and any data processors before deployment; do not assume those details from the source archive. Run `python tools/verify_publication.py --origin https://ai.dial-tone.uk` to check live HTTPS, redirects, security headers, static discovery, canonical URLs, sitemap, and `robots.txt` content against repository source. The robots cache may be longer than the short TTL used for frequently changing pages because the verifier checks the exact file bytes. DNS and hosting changes are owner operations. A public website **does not** imply that live PSTN calling or x402 is enabled.

## Security and licensing

This repository contains only public AI research source, GPLv3-or-later except separately noted third-party material. The native Windows softphone is a separate repository and is not copied or modified. Keep proprietary production credentials, network arrangements, settlement, and fraud-control implementations outside this repository.
