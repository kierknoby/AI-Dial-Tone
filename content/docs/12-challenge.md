# First Call challenge (synthetic)

This repository offers **two deliberately different** exercises. Neither contacts a telephone carrier or makes a booking.

## Challenge A: browser lifecycle fixtures

Open [Playground](/playground.html) to inspect answered, busy, no-answer, deadline and remote-hangup outcomes. Machine-readable vectors are provided under `/api/scenarios/`. Their source is a scripted browser simulator, and all calls are synthetic. The correct agent outcome is to report exactly what the fixture provides and **not** assert that a restaurant was called.

## Challenge B: real local peer transport

From the repository root:

```bash
python -m pip install 'aiohttp==3.13.3'
python tools/verify_first_call.py --out demo-output
```

Two independently authenticated local clients pass actual PCM packets over WebSockets. Inspect `demo-output/proof.json`, both received WAVs, and `demo-output/verification.json`. The verifier fails if the purported local evidence is incomplete or mislabelled. Check that an authorised operator stop or hard deadline ends the session, that the journal hash chain is contiguous and that the agent's transcript assertion is not reported as independent recognition.

## How to evaluate honestly

Passing Challenge B proves local authentication, signalling and media forwarding, not accurate speech understanding, a human interlocutor, SIP registration, PSTN routing, booking confirmation, or compliant payment. The next acceptance gate is two independently implemented **real** speech/model peers solving unseen tasks reliably, followed by isolated Asterisk qualification.
