# Audio-first autonomous conversations

**Status: implemented and tested on loopback only. Not a telephone service.**

AI Dial-Tone now includes `peer-lab/voice_peer.py`: an actual audio-derived bot conversation pipeline rather than a chat agent responding to a peer's claimed transcript.

## The pipeline

```text
Human operator issues a short-lived local test mandate
  → independent bot identities connect over WebSocket
  → PCM16 16 kHz 20 ms frames arrive from the other bot
  → bounded energy-based segmentation, or explicit audio.end
  → audio upload to a configured ASR provider, or optional offline PocketSphinx
  → independently validated transcription (still fallible)
  → text chat-completion-compatible model endpoint
  → TTS via configured /audio/speech-compatible endpoint or local eSpeak
  → paced PCM16 16 kHz 20 ms frames returned through the same WebSocket
  → deadline, operator stop, event chain, and media-frame evidence
```

The receiver **does not treat remote `say` messages as transcripts**. They are separate, unverified bot assertions. The runtime transcribes only received audio. When speech begins during an outgoing response, it cancels the response and asks the peer to flush pending playback. Interrupted, partial media is not a completed utterance.

## Reproduce the test without external APIs

From the **standalone repository root**, using Python 3.11+:

```sh
python -m pip install 'aiohttp==3.13.3'
cd peer-lab
python -m unittest discover -s tests -p 'test_*.py' -v
```

On Debian/Ubuntu, an additional optional offline demonstration requires `espeak`, `ffmpeg`, the PocketSphinx C library and its English acoustic/language models. Once installed:

```sh
python examples/audio_first_call.py --out audio-proof
```

The output contains `caller_spoke.wav`, `caller_heard.wav`, and `proof.json`. The generated waveforms really cross a WebSocket, the receiving agent actually attempts speech recognition with PocketSphinx, and a **deterministic local HTTP chat fixture**, not a real LLM, supplies the reply. PocketSphinx's errors are deliberately preserved in the evidence. It is not a reliable production ASR engine.

## Connect a capable speech and reasoning provider

The example `peer-lab/examples/voice_model_peer.py` can use:

- `AIDT_ASR_URL`, `AIDT_ASR_MODEL`, optionally `AIDT_ASR_KEY`: an HTTP service compatible with `POST /audio/transcriptions`, accepting 16 kHz mono WAV and returning `{"text":"..."}`.
- `AIDT_MODEL_URL`, `AIDT_MODEL_NAME`, optionally `AIDT_MODEL_KEY`: `POST /chat/completions`, accepting standard messages and returning `choices[0].message.content`. Tool calls are not authorised.
- Optional `AIDT_TTS_URL`, `AIDT_TTS_MODEL`, `AIDT_TTS_VOICE`, `AIDT_TTS_KEY`: `POST /audio/speech` returning WAV. If omitted, local eSpeak is used.
- `AIDT_PEER_SESSION`, `AIDT_PEER_TOKEN`, and `AIDT_PEER_URL` for an operator-issued, loopback-only test session.

Set `AIDT_EXTERNAL_AUDIO_PROCESSING_APPROVED=YES` **only after explicitly agreeing to upload audio and text to the selected external providers**. All remote endpoints must use HTTPS; redirects are rejected. Do not paste credentials into a model prompt or commit secrets to GitHub. Audio is personal data when it contains identifiable speech, and sharing it with another provider requires appropriate notice and safeguards.

The TTS converter enforces mono, 16 kHz, PCM16 audio; a WAV returned at another rate is *resampled*, never merely relabelled. All utterances, responses, turn counts, provider bodies, and TTS output are bounded, and no model can trigger SIP, PSTN, payments, or reservations through these adapters.

## What this proves and what it does not

| Capability | Evidence | Current status |
|---|---|---|
| Actual PCM delivered between independent bot sockets | Local network test | Passed |
| Incoming media, not peer text, drives ASR | Audio-first integration regression | Passed |
| ASR, HTTP reasoning fixture, and TTS complete a round trip | Network fixture and offline proof | Passed locally |
| Barge-in cancels old audio | Concurrent peer audio regression | Passed locally |
| Human stop interrupts ongoing model speech | Operator revocation regression | Passed locally |
| Offline speech recognition reliability | eSpeak → PocketSphinx → transcript | **Poor accuracy** |
| Speech quality across different real hosted LLMs | No credentials / live providers contacted | **Unverified** |
| Natural conversation with a real business | No live SIP/PSTN | **Unavailable** |
| Independently confirmed booking and payment | No trusted booking/payment providers | **Unavailable** |

The local event chain is a useful tamper-evidence check *against a retained digest*, not carrier or reservation evidence. **An ASR transcript, regardless of quality, must never be treated as proof of a real-world action.**

## Production requirements not yet met

Real telephony requires PJSIP/Asterisk registration, TLS certificate validation, secure media, OPTIONS readiness, actual INVITE and call-state checks, uninterrupted duplex PCM with echo cancellation, independently enforced hangup, carrier billing, UK telephone/fraud restrictions, and payment settlement. The Windows Dial-Tone application supports its own separate SIP features; this audio lab **does not inherit them merely by sharing the brand**.
