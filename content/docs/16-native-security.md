# MicroSIP and Dial-Tone security: source inventory and limitations

**Source review: EgyptianEyes/Dial-Tone, commit `f0d15b3f958b91c20fad05693b74e3902533fc08` (`main` at review), 10 October 2026.** Review scope includes the root README and `extracted/MicroSIP-3.22.3-src/AccountDlg.cpp`, `settings.cpp`, `mainDlg.cpp`, and `global.cpp`. This is a **source-feature inventory**, not a vulnerability audit or live certificate/media verification. The Windows executable was not rebuilt in this documentation pass.

## What the native repository actually contains

Dial-Tone is MicroSIP-derived C++ using PJProject/PJSUA. It retains the SIP account registration and call/media stack. `AccountDlg.cpp` exposes UDP, TCP and TLS transport options and these media policies: Disabled, Optional SRTP (`RTP/AVP`), Mandatory SRTP (`RTP/SAVP`), combined DTLS-SRTP/SRTP, and DTLS-SRTP. `settings.cpp` persists the SRTP setting. `mainDlg.cpp` handles authenticated SIP OPTIONS challenges (`401` and `407`), collects the result, selected transport, source endpoint and elapsed time, and generates pre-call readiness diagnostics.

The native README documents registration, transport, audio device, codec, OPTIONS response and latency tests. `READY` requires suitable local checks, registration, and a successful SIP OPTIONS response. Non-registrar accounts remain `DEGRADED`; RTT above 1,000 ms is degraded. Recent readiness is associated with a subsequent outgoing call for up to 60 seconds. The actual call's answer and RTP still require separate verification.

Read the [source README](https://github.com/EgyptianEyes/Dial-Tone/blob/main/README.md) and [native account security options](https://github.com/EgyptianEyes/Dial-Tone/blob/main/extracted/MicroSIP-3.22.3-src/AccountDlg.cpp).

## What we MUST carry forward, and what cannot be inherited

| Area | Native Dial-Tone | AI/headless/browser requirement |
| --- | --- | --- |
| SIP signalling | UDP, TCP, TLS settings | **TLS only** on the controlled PBX hop, with validated peer identity; no silent downgrade |
| SIP authentication | PJSIP challenge-based SIP credentials | Credentials remain at the PBX side, never in model prompts or browser-exposed backend config |
| Media encryption | Disabled, Optional SRTP, Mandatory SRTP, DTLS-SRTP choices | **Mandatory** encrypted media on SIP/WebRTC public hops; reject optional, disabled and downgrade outcomes |
| Browser media | Windows native audio and PJSUA | Browser uses WebRTC DTLS-SRTP, secure WSS signalling, ICE and permissioned microphone; not a native-source port |
| Remote media gateway | No agent-facing media protocol | TLS-protected, tenant-bound, short-lived media tickets; strict framing, limits and reconciliation |
| Readiness | Registration, OPTIONS, codecs, devices, response time | Reproduce semantic checkpoints in service; distinguish local SIP reachability from actual carrier connectivity |
| Trace | Call states, identifiers, codec and RTP statistics | Structured redacted traces; distinguish provider-confirmed events from model-supplied claims |
| Recording | Native recording capability | Recording disabled by default, explicit retention/legal-basis review and restricted access |
| Redirects/transfer | Supported in native softphone | Deny unattended REFER, 3xx redirection and transfers to unclassified destinations |
| Runtime integrity | CI builds unsigned native executable | Pin dependencies, sign release artefacts, rotate secrets, protect supply chain and keep release provenance |

**Important:** PJSIP's **optional** SRTP setting may negotiate unencrypted RTP and must not be accepted by a production AI security profile. For SDES-SRTP, TLS protects key material conveyed in signalling; for DTLS-SRTP, the media handshake derives keys. PJSIP documentation also notes build and backend requirements for DTLS-SRTP: merely showing a configuration option does not prove support in a particular binary. See [PJSIP SRTP guide](https://docs.pjsip.org/en/latest/specific-guides/security/srtp.html) and [MicroSIP media encryption help](https://www.microsip.org/help).

## Readiness truth table

| Evidence | What it demonstrates | What it does not demonstrate |
| --- | --- | --- |
| PJSUA account exists, SIP REGISTER accepted | This account can register | Dialplan permits the destination |
| OPTIONS final 2xx from registrar/target, current TLS transport | SIP endpoint responded recently | PSTN carrier reachable, INVITE accepted |
| Local sound device and codec present | Endpoint can prepare local media | Remote hearing the agent or bidirectional RTP |
| Asterisk ARI `StasisStart`/call answered | A channel was originated/answered | Any restaurant booking completed |
| Media WebSocket frames flowing both ways | Packets cross our gateway | Transcription accurate, recipient hears intelligible speech |
| Provider's `Hangup` / termination event | Network channel ended | The business confirmed a reservation |

The local contract exercise in `lib/peer-contract.mjs` rejects missing TLS/certificate evidence, disabled/optional SRTP, stale OPTIONS results and unverified route policy. It also marks all observations unauthenticated and `network_call_authorised=false`. It does **not** provide or validate real SIP certificates.

## Asterisk media and trust boundaries

`chan_websocket` is documented for Asterisk 22.6.0+, 21.11.0+, 20.16.0+ and 23.x, with binary audio and text control frames, and `MEDIA_START`, `MEDIA_XOFF`, `MEDIA_XON` signals. Later versions support a JSON control format. Pin the installed version before writing a production adapter, verify codec/frame interpretation, and never connect the ARI/media interface directly to the public Internet. See [Asterisk WebSocket media documentation](https://docs.asterisk.org/Configuration/Channel-Drivers/WebSocket/).

Production hardening is still unverified: test the exact native TLS certificate behaviour and digest algorithms, confirm secure transport in Asterisk, require a valid server certificate and suitable SRTP policy, test ICE/TURN and DTLS-SRTP on browsers, enforce independent call cutoff at the PBX/SBC, prevent redirect bypass, and run external security review.
