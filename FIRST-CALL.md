# First call: independently verifiable local audio

**Release:** 0.0.1 technical preview. **Scope:** two fictional local peers exchanging PCM over loopback WebSockets. **Not:** PSTN, a live Asterisk call, a model-quality test, a reservation, or a payment.

## Prerequisites

- Python **3.11+**, with pip. Use an isolated development environment, preferably a virtual environment.
- Network access to install the pinned package **aiohttp==3.13.3**, unless it is already installed.
- Run all commands at the extracted **repository root**, not in the `site/` directory.
- Optional `espeak` synthesises audible test phrases. Without it the demonstration can use the built-in tone fallback, which proves media transport but not speech quality.

## Run

```bash
python -m pip install 'aiohttp==3.13.3'
python tools/verify_first_call.py --out demo-output
```

The tool starts an isolated loopback service, acquires lab-only admission for two separate fictional agents, exchanges audio in **both** directions, closes the session and independently verifies its evidence. It exits non-zero if the proof fails. It does not need a carrier account, SIP credentials, a wallet or an AI API key.

## Expected success

```text
PASS: two received-audio WAV files and local session receipt verified.
Evidence: .../demo-output/verification.json
NO PSTN CALL, PAYMENT, MODEL QUALITY OR BOOKING HAS BEEN VERIFIED.
```

Examine `demo-output/verification.json`. These exact fields must be present:

```json
{
  "status": "PASS",
  "scope": "LOCAL_WEB_SOCKET_PCM_AND_SESSION_ONLY",
  "bidirectional_received_audio_verified": true,
  "local_session_ended": true,
  "real_pstn_call_verified": false,
  "real_payment_settlement_verified": false,
  "real_world_booking_verified": false,
  "carrier_release_verified": false
}
```

The verifier also writes `caller_heard.wav`, `peer_heard.wav` and `proof.json` to the specified output directory. The WAV files must contain received, non-silent, 16 kHz mono PCM16 audio. An event-chain hash shows consistency of *local* events only, not network or carrier attestation.

## Troubleshooting and reruns

- If Python reports `No module named aiohttp`, repeat the pinned pip installation in the Python environment used to run the tool.
- If the local socket cannot bind, close any previous lab process using the loopback test port; do not change it to a public listening address.
- Run `python tools/verify_first_call.py --out demo-output` again for a fresh demonstration. Do not treat a stale proof as a new run.
- To validate existing output without starting a new demo, run `python tools/verify_first_call.py --out demo-output --verify-only`.
- Keep generated WAVs, proof files and credentials out of commits and support tickets. They are ignored by the repository's `.gitignore` when saved in `demo-output/`.
- For the extended tests run `npm run check` (Node 20+) and `npm run test:peer`.

## What comes next

Read [the Peer Lab README](peer-lab/README.md) to connect your own local peers; see [BYOT](byot/README.md) for an **off-by-default, unverified** Asterisk adapter. **Do not enable PSTN routing for this demonstration.** See [the product-scope register](PRODUCT-SCOPE.md) for implemented, planned and excluded functionality.
