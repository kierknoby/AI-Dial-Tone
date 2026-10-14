# Contributing to AI Dial-Tone

This standalone public repository develops agent-first communications and acknowledges the separate Windows MicroSIP-derived Dial-Tone project. It must remain transparent, accessible and faithful to what is working.

## Requirements for every public pull request

1. **Do not copy native MicroSIP/PJProject code into this repository without a reviewed licensing and engineering need.** Cite the separate project when referencing its readiness design. Preserve third-party notices.
2. **Do not commit** PBX credentials, API keys, DNS private material, ARI credentials, human phone logs, identifiable transcripts, production routes, private backend code or raw test recordings.
3. Update `content/docs/`, `site/agents.json`, schema files, and automated tests whenever you introduce a user- or model-facing capability. Never advertise hosted A2A, MCP, payment, PSTN, or live audio before externally verified endpoint acceptance.
4. Make an explicit distinction between **human authorisation**, **SIP readiness**, **network-confirmed call state**, **agent-reported observations**, and **independently verified business outcomes**.
5. Enforce destination allowlists, limits and hangup in independent PBX/SBC controls, not only API prompts or browser code. Fail closed on SIP TLS/cert validation and media-encryption downgrades.
6. Tests must cover denied, failed, timed-out, duplicated, interrupted and uncertain paths, not just successful conversations.

## Local verification

```bash
python -m pip install 'markdown-it-py==4.2.0'
python tools/build-site.py
python tools/build-reference.py
npm run check
node examples/restaurant-lab.mjs
python tests/browser_smoke.py   # optional: requires Chromium and Playwright
```

`npm run check` runs public/static checks and the fail-closed, **local-only** peer-contract tests. The restaurant demonstration is synthetic. It does not dial any telephone number.

## Changelog and proof

A feature is **implemented** when code and contract tests exist; it is **telecom-proven** only with logged real SIP/ARI/channel evidence. A real conversation additionally requires authorised audio, outcome checks and a service-side deadline. A payment is **settled** only with independently verified chain/facilitator evidence and matching accounting. Track these as separate fields in release evidence.

Use the dated acceptance table in `ROADMAP.md`. Don't change the checkboxes by saying “works on my machine”.

## Licence and AI-assisted contribution disclosure

Original code in this repository is GPL-3.0-or-later unless a file has a separate third-party licence; see [LICENSE](LICENSE) and [LICENSING-NOTE.md](LICENSING-NOTE.md). Do not modify the native MicroSIP GPLv2-or-later headers or treat unrelated media assets as automatically licensed under the AI subtree licence.

Each commit containing AI-assisted code, review, tests, or documentation must disclose the agent and model in its commit message:

```text
Assisted-by: AGENT_NAME:MODEL_VERSION
```

For example: `Assisted-by: ChatGPT:GPT-6`.

The human contributor remains responsible for correctness, provenance, security, and compliance. AI tools must not be listed as Git co-authors.
