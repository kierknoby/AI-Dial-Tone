# Quickstart: first local AI peer session

This is a **reproducible public-source** example. It runs entirely on the developer's computer, uses fictional actors and does **not** dial a telephone number. You do not need a private laboratory package.

## Prerequisites

- Python 3.11 or newer, with `aiohttp==3.13.3` installed.
- Optional `espeak` for audible locally synthesised phrases. Without it, a tone fallback demonstrates media transport only.
- An isolated, non-production development machine.

From the checkout root:

```bash
python -m pip install 'aiohttp==3.13.3'
python tools/verify_first_call.py --out demo-output
python -m unittest discover -s peer-lab/tests -p 'test_*.py' -v
```

For a repository-level walkthrough, expected JSON fields and troubleshooting see the root `FIRST-CALL.md` included in the GitHub source archive. The example starts an isolated loopback server, obtains an operator-issued lab mandate and single-use admission tickets, connects a caller and fictional restaurant bot separately, relays actual 16 kHz PCM, and shuts the session down. It writes `demo-output/proof.json`, two *received-audio* WAVs and `demo-output/verification.json`. The verifier exits non-zero if media, identity, session release or synthetic-evidence boundaries are inconsistent. It does not establish a real telephone call, model understanding or booking. The same entry point works from the repository root. Output is local; don't commit test recordings.

## Run the lab server yourself

```bash
cd peer-lab
python peer_lab.py --host 127.0.0.1 --port 8765
```

The server prints high-entropy, ephemeral **operator**, **caller**, and **peer** credentials into the terminal. Do not publish those credentials or expose the server beyond loopback. Its capabilities endpoint is `http://127.0.0.1:8765/v1/capabilities`; it deliberately advertises `real_pstn: false`.

The REST request sequence is documented in [HTTP API](05-api.md). The binary audio format is in [Media](08-media.md). The machine-readable source-backed specification is [`/api/openapi.json`](/api/openapi.json), a **static copy describing this local-only server**, not an online API.

## Optional experiments

Run `python examples/audio_first_call.py` from `peer-lab/` for actual audio-derived recognition experiments, subject to its local speech dependencies. A high-quality ASR and real hosted LLM have **not** been accepted. Run `npm run check` at the repository root to validate static contracts and docs. Browser lab commands are in `labs/web-softphone/README.md`.

## Optional self-hosted telecom connector

The standalone `byot/` directory contains an **off-by-default**, experimental ARI/RTP bridge for an operator who already owns an isolated Asterisk endpoint. Start with [BYOT Asterisk](20-byot-asterisk.md) and its local fake-ARI tests. This is not a hosted API, and no real Asterisk/PSTN call has been verified.
