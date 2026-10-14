# Deployment checklist · ai.dial-tone.uk

## Before publishing

1. Configure DNS for `ai.dial-tone.uk` to the static hosting provider. This package **does not** establish that DNS or the hostname is active.
2. Validate TLS certificate issuance and HTTPS with the actual host; don't use an unencrypted API endpoint.
3. Use only the generated **static `site/` files**. Never publish `private-agent-lab/`, `labs/web-softphone/` or `peer-lab/` or `byot/` as an active server, local simulator credentials, SQLite databases, development service ports, or telecom/SBC configuration. The browser research code may exist in GitHub but is **not** a public hosted telephone service.
4. Have the operator verify company identity, contact information, actual hosting access-log retention, privacy notice, source licensing, and any required legal notices.
5. Verify the documented technical-preview limitations against the deployed site. There must be no working paid destination or exposed private fixture endpoint.
6. Keep the Windows Dial-Tone's existing build/release process and GPL notices intact.

## Static files that must load with correct types

- `/`, `/agents.html`, `/playground.html`, `/docs/index.html`, `/docs/api.html` as HTML.
- `/llms.txt`, `/agents.txt`, `/llms-full.txt` as `text/plain; charset=utf-8`.
- `/agents.json`, `/api/openapi.json`, `/api/reference.json`, `/api/challenges.json`, and `/api/scenarios/*.json` as `application/json`.
- `/assets/*.js`, `/assets/*.mjs`, `/assets/*.css`, `/assets/*.svg` with correct content types.
- `/robots.txt` and `/sitemap.xml` should point to `https://ai.dial-tone.uk`.

## Test URLs after deploying

- `https://ai.dial-tone.uk/`
- `https://ai.dial-tone.uk/agents.json`
- `https://ai.dial-tone.uk/llms-full.txt`
- `https://ai.dial-tone.uk/docs/index.html`
- `https://ai.dial-tone.uk/api/openapi.json`
- `https://ai.dial-tone.uk/sitemap.xml`

Test mobile navigation, playground simulations, CSP/headers, content types, browser console errors, and missing pages. Verify security headers on the actual host rather than relying on the lab's local proxy.

## Not part of this release

Real verified SIP and ARI interoperability, public autonomous calling, x402 payments, consent/anti-fraud enforcement, production monitoring, and availability SLAs. Those remain release blockers for commercial calling, regardless of how polished the site is.

## Read-only live-site post-upload verification

After DNS, TLS and the exact static upload are in place, run from the GitHub repository root:

```sh
python tools/verify_publication.py --origin https://ai.dial-tone.uk
```

This deliberately fails closed if the host cannot be reached, the canonical site or expected files are missing, Apache does not apply the security headers, or HTTP fails to redirect to HTTPS. It cannot determine cPanel access-log retention or the legal controller, which the website operator must confirm from the hosting account.
