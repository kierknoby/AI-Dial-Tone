# AI Dial-Tone Browser SIP Lab 0.0.1

**Development-only browser softphone and AI-agent media playground. Not suitable for production, public deployment, or billable PSTN calling.**

This is a separate browser experiment based on the user experience and diagnostic priorities of [EgyptianEyes/Dial-Tone](https://github.com/EgyptianEyes/Dial-Tone). Dial-Tone itself is a Windows C++/PJSIP application derived from MicroSIP. **No native/GPL MicroSIP code was copied or linked into this web lab.** The private commercial AI Dial-Tone backend remains separate and closed source.

## What the 0.0.1 browser lab implements

- Localhost browser dialler using SIP.js 0.21.2 and WebRTC for test-only Asterisk WSS extensions. Human account registration and calling functions are coded, **but not tested against a live PBX**.
- `dialtone.agent.v2`, a documented bot control contract with correlated command results, structured events, session-local command deduplication and restricted call initiation.
- WSS mutual authentication using one 32+ character random pairing secret, HMAC-SHA256, a fresh client nonce and fresh server nonce. The pairing token is **never transmitted** to the controller. The example Python server accepts **one successful pairing per secret**, requiring restart with a new secret to pair again.
- Explicit operator call arming, allowlisted 2-6 digit test extensions, separate permission for audio, and separate action to turn on outgoing bot audio during an **answered** test call.
- Bidirectional 16-kHz signed 16-bit little-endian mono PCM audio, sent in 20-ms binary frames over the authenticated controller WebSocket. Frames travel from remote telephone audio to the bot, and from the bot through the WebRTC sender to the telephone. **The AudioWorklet code has unit tests and the binary transport has a cross-language integration test, but the complete media path has not been validated in a browser or with a real telephone call.**
- Call-scoped 60-second local deadline, controller-disconnect cleanup, and bot-owned call termination on controller loss. Independent server-side hangup **must** be implemented before any billable destinations can be allowed.
- RTC jitter, packet loss, packet and byte counts, and RTT diagnostics returned as sanitised numeric data. Raw peer connection stats, candidate IPs, device IDs, and SIP credentials are not sent to bots.
- Real example bot controller in Python using `websockets`. It accepts typed commands, plays a 16-kHz mono PCM WAV towards the telephone, saves received telephone audio as WAV, supports optional audio echo for lab tests, and has a lightweight energy-based voice-activity detector with optional playback interruption. **This is not an ASR, TTS, LLM, or production AI voice engine.**

### Architecture

```text
                   OPERATOR PERMISSION & ARMING
                               |
Browser SIP.js/WebRTC ---------|------> isolated Asterisk WSS extension
          |                            (PBX dialplan must block PSTN)
          | Remote audio track
          v
    WebAudio AudioWorklet -> PCM16/16k -> mutual-HMAC WSS -> Python bot
    WebRTC outgoing sender <- PCM16/16k <- mutual-HMAC WSS <- WAV/echo/agent
          |
          +--> privacy-filtered RTCPeerConnection.getStats()

Future private telephone infrastructure (x402, PSTN, SBC, ARI): NOT CONNECTED
```

### Run locally

Requires Node.js 22+, Python 3.11+, Python package `websockets>=14`, OpenSSL, and a current browser with WebRTC and AudioWorklet. `npm test` needs Python and OpenSSL to run its cross-language integration test, and skips that one test if prerequisites are missing. `npm run test:bot` tests the Python VAD.

```sh
npm test
npm run test:bot
npm start
# Open http://127.0.0.1:8787 in the same machine's browser
```

The browser page can be viewed offline, but SIP registration currently imports the **pinned** SIP.js 0.21.2 release from `esm.sh`. This remains an important security and deployment limitation. **Do not enter real SIP credentials in a web page whose dependency is fetched from a third-party CDN.** Before even a restricted field pilot, pin and bundle SIP.js locally, verify the bundled code, remove `esm.sh` from the Content Security Policy, and use HTTPS with an explicit hostname and access control.

### Start the Python bot lab

Use a fresh secret and a TLS certificate trusted by your own lab browser. Do not copy an SSL key to or from a production system. Here is an **ephemeral self-signed development certificate** for local testing; import its cert into an appropriate dedicated test trust store rather than globally disabling browser security.

```sh
# Use a separate terminal. Do not check certs, keys or tokens into Git.
mkdir -p /tmp/dialtone-lab
openssl req -x509 -newkey rsa:2048 -sha256 -nodes -days 1 \
  -keyout /tmp/dialtone-lab/key.pem -out /tmp/dialtone-lab/cert.pem \
  -subj '/CN=localhost' -addext 'subjectAltName=DNS:localhost,IP:127.0.0.1'
python -c 'import secrets; print(secrets.token_urlsafe(40))'
# Copy that secret into --token and the browser Pairing Token field.
python bot/controller.py --cert /tmp/dialtone-lab/cert.pem \
  --key /tmp/dialtone-lab/key.pem --token 'YOUR_UNIQUE_RANDOM_SECRET' \
  --out /tmp/dialtone-lab/received.wav --echo
```

The controller listens on `wss://127.0.0.1:8766/`. The browser must trust the development certificate. For audio playback, add `--play path/to/16k_mono_pcm.wav` instead of `--echo`. For interruption tests, add `--barge-in` to flush bot playback upon detected caller energy. `--demo-target 1002 --noninteractive` is available for automation, and is exercised in the cross-language test. Production systems must not use a static command-line token or a local development certificate.

### Browser test sequence

1. On a PBX dedicated to testing, create a **WebRTC test SIP account**, configure secure SIP WSS and media encryption, configure TLS, ICE, and suitable codecs. The extension dialplan must be unable to reach carriers, PSTN, emergency, premium, international, or feature-code redirects that can reach those destinations. All paths must have a server-side timeout.
2. In Dial-Tone Web, connect a test account and confirm registration. Local readiness is not a substitute for a real call.
3. Set **1002** as the explicit allowlist, tick *Arm bot and manual test calls*, and apply. Tick and apply the separate *Permit bot audio* consent when ready.
4. Enter the Python controller WSS address and the identical fresh secret, and pair. The UI should show `PAIRED`. Pairing consumes the secret at the server.
5. Place a local extension-to-extension call or ask the bot to `call 1002`. Confirm both the SIP answer and remote audio before enabling media injection.
6. In the web UI click **Activate bot audio**. In the Python bot terminal enter `audio on`; it will send `audio.enable`. A 16-kHz mono WAV from `--play` can then be injected; `--out` saves received audio. The local microphone is replaced as the WebRTC sender source until bot audio stops.
7. Inspect `diagnostics`, `media.stats`, call lifecycle events, audio output and recording. Terminate or disconnect and verify WebRTC outgoing microphone restoration, agent audio shutdown, and hangup.

**Do not test chargeable calls with this browser lab.** The 2-6 digit input limit is not a security boundary: a PBX can route short numbers to a paid external call.

## Bot protocol

Transport: one operator-initiated **WSS** connection, JSON for control and binary for audio. Version `dialtone.agent.v2`. All JSON messages must be at most 4096 bytes. Single active connection per server instance in the example controller. No SIP account secrets are sent.

```json
{"version":"dialtone.agent.v2","kind":"hello","nonce":"0123456789abcdef0123456789abcdef","capabilities":["status","readiness","call:test-extension","hangup","audio:pcm16-16000-mono"]}
```

Controller returns `challenge` with fresh `nonce` and `proof = hex(HMAC_SHA256(secret, "dialtone.agent.v2|server|CLIENT_NONCE|SERVER_NONCE"))`. Browser verifies it, returns `proof = hex(HMAC_SHA256(secret, "dialtone.agent.v2|client|CLIENT_NONCE|SERVER_NONCE"))`, and controller verifies then sends `paired` with `accepted:true`. New nonces are mandatory; pairing times out in ten seconds. A new secret must be issued for another successfully paired session.

Commands are `status`, `readiness`, `diagnostics`, `call` (must include operator-allowlisted `target`), `hangup`, `audio.enable`, `audio.disable`, and `audio.flush`. Example:

```json
{"version":"dialtone.agent.v2","kind":"command","id":"bot-12","command":"call","target":"1002"}
```

Each command gets a `result` with the same `id` and `ok`; errors return a narrow `error.code`. Successful response IDs are cached for one session; retrying an identical command returns the cached result, whereas retrying an ID with changed arguments is rejected. There is only one executing command at a time; overlapping commands get `BUSY`. Call-state and `media.stats` messages are pushed independently as `event` messages. An optional application `ping` gets a `pong`.

Binary audio uses exactly **641 bytes**, `1` direction byte plus 640 audio bytes: `0x01` remote telephone audio towards bot, `0x02` bot speech towards WebRTC. Each packet contains 320 PCM16LE mono samples (20 ms at 16 kHz). Both directions are gated by audio consent and `audio.enable`, and the browser drops frames on excessive WSS backpressure rather than buffering indefinitely. These frames have no timestamps or sequence numbers yet, so packet timing and concealment will need serious real-network testing.

## Test results and limitations

Local automated tests exercise JS unit logic, the AudioWorklet in a mocked render environment, the local static server, and a **real TLS WebSocket** to the Python bot server using a short-lived, privately trusted development certificate. The integration test has the bot request a test-extension call, enable audio, and echo binary frames; this validates cross-language framing and authentication without placing a telephone call. Additional Python unit tests cover the energy VAD.

`tests/browser_integration.py` attempts to exercise the real browser UI and AudioWorklet with synthetic media. In the development environment where this package was built, Chromium navigation was blocked with `ERR_BLOCKED_BY_ADMINISTRATOR`. **The browser integration test is supplied but has not passed.** Run it only in a browser test environment allowed to access a local server, and do not weaken real browser security for deployment.

Still unverified / unfinished:

- SIP.js behaviour under a real registered and answered Asterisk WebRTC call.
- End-to-end audio capture and playback through a real WebRTC sender, including mic restoration after hangup, race conditions, interruption latency, NAT and ICE behaviour.
- Testing on Chrome, Firefox, Safari, iOS, and real devices.
- Independent, enforced server-side call duration and destination allowlisting.
- ASR/TTS/LLM integration, bot identity policy, concurrency guarantees across processes, WebSocket reconnection, durable idempotency, and production security assessment.
- The managed AI Dial-Tone calling service, actual x402 receipt settlement, private customer entitlement systems, managed network routing, or live PSTN calling.

## Repository boundaries and licences

Dial-Tone's native source is GPL-derived and must retain applicable MicroSIP notices. This web lab contains new standalone JavaScript and Python code and no copied MicroSIP C++ code. Do not merge proprietary AI Dial-Tone orchestration into Dial-Tone or reuse GPL source inside the closed AI Dial-Tone service without reviewing licence obligations. This directory has not been pushed to GitHub and should remain a private experiment until a deliberate publication decision.
