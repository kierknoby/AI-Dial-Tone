# Publish AI Dial-Tone as a standalone repository

**Intended repository:** `https://github.com/kierknoby/AI-Dial-Tone`. Its creation and publication require the GitHub account holder's permission. No changes to the separate Windows repository are necessary.

## 1. Review the release

Extract the standalone package into a new directory. From the project root:

```sh
npm run check
npm run test:peer
npm run test:byot
npm run test:x402
npm run test:handoff
python tools/verify_first_call.py --out demo-output
cd labs/web-softphone && npm test && npm run test:bot
```

Run the optional documentation build with `markdown-it-py==4.2.0`, then confirm the generated files are unchanged. Review `PRODUCT-SCOPE.md`, `RELEASE-READINESS.md`, `FIRST-CALL.md`, `SECURITY.md`, the GPL-3.0-or-later `LICENSE`, `LICENSING-NOTE.md`, and site privacy notice. Check that no credentials, customer data, private backend, or audio recordings are present. Confirm `ai@dial-tone.uk` is authorised for general, privacy and initial private security correspondence; separately confirm `dial-tone@egyptianeyes.com` receives abuse reports. This release is developed personally and is being prepared as an Egyptian Eyes project, not presented as an already transferred or operated commercial service.

## 2. Create the GitHub repository

Under the **kierknoby** account, create **AI-Dial-Tone** as a public repository, **without** automatically adding a README, `.gitignore`, or licence (already supplied). This operation has not been performed by the package.

## 3. Initialise and push the exact reviewed files

These commands operate only on your newly extracted standalone AI Dial-Tone directory:

```sh
cd /path/to/AI-Dial-Tone

git init -b main
git add -A
git diff --cached --check
git status --short
git commit -m "Initial public AI Dial-Tone research source" -m "Assisted-by: ChatGPT:GPT-6"
git remote add origin https://github.com/kierknoby/AI-Dial-Tone.git
git push -u origin main
```

If the repository is not empty, **do not force-push or overwrite it**. Inspect its history and merge deliberately. Commit attribution should represent the human owner; the `Assisted-by` trailer discloses AI assistance, not authorship.

## 4. Configure private vulnerability reporting and verify CI

After the repository exists, open **Settings → Code security → Private vulnerability reporting** and turn it on. Until enabled, the established fallback is `ai@dial-tone.uk`, as described in `SECURITY.md`. Do not claim private GitHub reporting is operational without checking. For abuse, use the separate `dial-tone@egyptianeyes.com` address, not the security mailbox.


The workflow at `.github/workflows/verify.yml` targets `main`. Review the GitHub Actions results and generated-document differences before considering a release.

## 5. Publish the website separately

Only after reviewing privacy, legal, public disclosures, and availability claims, use:

```sh
python tools/prepare-release.py --origin https://ai.dial-tone.uk --out ./site-deploy
```

Host **only** the generated static files, not the repository root. Confirm the actual website controller, host/log retention settings, and any data processors before deployment; do not assume those details from the source archive. After deployment run `python tools/verify_publication.py --origin https://ai.dial-tone.uk` to check live HTTPS, redirects, security headers, static discovery, canonical URLs, and the sitemap. DNS and hosting are separate tasks. A public website **does not** imply that live PSTN calling or x402 is enabled.

## Security and licensing

This repository contains only public AI research source, GPLv3-or-later except separately noted third-party material. The native Windows softphone is a separate repository and is not copied or modified. Keep proprietary production credentials, network arrangements, settlement, and fraud-control implementations outside this repository.
