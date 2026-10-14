# Repository policy

`kierknoby/AI-Dial-Tone` is a **standalone public research repository**. It has no branch or source-code dependency on `EgyptianEyes/Dial-Tone`.

- `main`: standalone AI Dial-Tone development, documentation, and test baseline. Releases remain technical previews until acceptance gates pass.
- `EgyptianEyes/Dial-Tone`: separate native Windows softphone, neither modified nor included here. Cite its source when discussing inherited design concepts.
- `ai.dial-tone.uk`: intended public address. Deploy **only** the generated static site; do not serve the repository root or expose localhost labs.
- Private carrier, Asterisk/SBC orchestration, payment settlement, anti-fraud, customer credentials, and call billing belong outside this repository. Do not vendor them.

## Contribution and security boundaries

Follow [CONTRIBUTING.md](CONTRIBUTING.md), [LICENSING-NOTE.md](LICENSING-NOTE.md), and [ROADMAP.md](ROADMAP.md). Never claim SIP/PSTN, x402, real-model conversation quality, or live reservations are operational on the strength of simulator tests.

## Licensing

Original source in this standalone repository is GPL-3.0-or-later unless a file or dependency has a separate notice. The Windows MicroSIP-derived repository retains its original GPLv2-or-later notices and is not included.
