# Bring Your Own Telecoms — Asterisk (experimental)

**New in the pre-publication 0.0.1 source:** the standalone repository now includes an optional, self-hosted Asterisk ARI connector under `byot/`. It is **off by default**, has been tested against a simulated ARI HTTP/WebSocket server and real UDP RTP sockets, and has **not** completed interoperability testing with a live Asterisk/SIP system.

## Who is this for?

A developer who already operates an **isolated Asterisk PBX**, owns a permitted outbound endpoint, and wants to experiment with a model-neutral agent talking through that PBX. It is **not** a public hosted dialling service and not a ready-made SIP trunk account.

An operator provides the destination through a short-lived one-use mandate. A separate agent credential consumes that mandate. The agent connects its WebSocket *before* dialling starts. The connector checks the ARI event connection and configured PJSIP endpoint state, originates on a fixed configured PJSIP trunk, waits for a Stasis answer, creates a mixing bridge and `externalMedia` channel, and forwards audio between RTP L16 and AI Dial-Tone's 16-kHz `DT01` PCM frames.

## Who controls call routing and teardown?

**The telecoms operator retains final authority.** A person's bounded mandate authorises the agent to *request* a call; it does not grant the agent permission to choose a trunk, open a PSTN route or keep the call alive. The PBX/telco independently decides whether origination is permitted, which configured route may carry the call, and whether to refuse or stop it. Destination permissions, CLI, cost controls and route restrictions belong on the operator's infrastructure, not in a model prompt.

The experimental connector uses one preconfigured PJSIP endpoint. It **does not create, edit or remove PBX outbound routes** when a call begins or ends. An operator stop or deadline requests ARI channel hangup, but **ARI channel absence is not proof of carrier release**. The telecoms operator must own an independent, PBX-side hard timeout, active-call reconciliation and orphan-channel cleanup so calls are terminated even if the agent or Python connector fails. **That independent provider-owned teardown is a requirement for production, not a completed 0.0.1 feature.**

## Practical first steps

From the public GitHub checkout, install `aiohttp==3.13.3`, read [`byot/README.md`](https://github.com/kierknoby/AI-Dial-Tone/blob/main/byot/README.md), and run:

```sh
python -m unittest discover -s byot/tests -p 'test_*.py' -v
python -m byot.server --check-config
```

The configuration check requires operator, agent and ARI credentials but **does not contact Asterisk or place a call**. When the isolated PBX is ready, `python -m byot.server` starts the loopback-only server. Origination requires an additional explicit operator setting, `AIDT_ENABLE_LIVE_ORIGINATION=YES`; without it, no outgoing call is permitted.

## Exact capabilities and limits

- **Works in the local synthetic ARI integration suite:** user-scoped mandate, no dial before authenticated agent admission, one-time media ticket, ARI REST plus event WebSocket, outbound PJSIP endpoint, one mixing bridge, external RTP media, bidirectional network PCM, DTMF control, operator stop, best-effort channel deletion, and local terminal status.
- **Not yet verified on actual Asterisk:** exact live ARI event timing, authentication configuration, endpoint state, `slin16` payload mapping, codec negotiation, SIP OPTIONS, TLS/SRTP, caller ID, NAT, DTMF interop, actual answered audio, RTP jitter, and carrier release.
- **Not implemented:** inbound routes, independently persisted mandates, human accounts, concurrent PSTN calls, SIP registration as a standalone endpoint, provider billing, x402, or verified real-world booking outcomes.
- **Important failure:** if the Python runtime or host crashes while a call is active, the process-local deadline will not necessarily hang up that channel. The Asterisk owner must install a PBX-side timeout, network route restrictions and an orphan cleanup mechanism before production use.

The driver deliberately keeps `carrier_release_verified:false` even when ARI reports the channel absent. `media.ready` is emitted after one validated RTP frame, not after proven two-way speech. There is no magical PSTN preflight guarantee.

## Open source and hosted calling

The BYOT connector is GPLv3-or-later alongside the public agent runtime. It uses Asterisk's REST and RTP interfaces; it does **not** redistribute MicroSIP or private hosted-service infrastructure. A future managed calling service could expose the same agent-facing concepts while supplying hosted SBCs, PSTN, payments and human account security separately.

## Operator-only read-only endpoint preflight

The local BYOT service offers `GET /v1/readiness` requiring the operator bearer. It reads the configured fixed PJSIP endpoint state from Asterisk ARI, does not dial or charge, and always reports `network_call_authorised: false`. `ENDPOINT_ONLINE_ROUTE_UNVERIFIED` means exactly that, not a successful SIP OPTIONS or proven PSTN route. See [Pre-call qualification](24-pre-call-principle.md).
