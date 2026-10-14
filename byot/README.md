# AI Dial-Tone 0.0.1 — Bring Your Own Telecoms (experimental)

**Asterisk ARI outbound calling reference connector. LOCAL LAB ONLY. DISABLED BY DEFAULT.**

This module turns the existing public AI Dial-Tone audio contract into an optional **self-hosted Asterisk** call path. It supports human-bound destination mandates, a separate agent bearer credential, a single-use WebSocket media ticket, fixed-trunk PJSIP origination, ARI `StasisStart` answer observation, ARI `externalMedia` RTP/L16 at 16 kHz, a mixing bridge, DTMF, a hard process-local timer, and best-effort hangup with an explicit channel-absence check.

It uses the documented Asterisk ARI endpoints, rather than shipping or porting native MicroSIP code. The MicroSIP/Dial-Tone Windows repository is not used or modified.

**Status:** local, simulated-Asterisk HTTP/WebSocket + UDP integration tests pass. **No real Asterisk, SIP trunk, PSTN call, encrypted SIP transport, or native OPTIONS check has been tested with this release.** This module is not a production-ready calling service. It cannot establish that a booking was accepted, a carrier released a call, or SIP media was encrypted. Credentials and state are held in one process; a process crash could orphan an Asterisk channel.

## Routing authority and teardown

A human mandate permits an agent to request a bounded call; it **does not authorise PSTN egress on its own**. The telecoms operator retains independent control of permitted destinations, dialplan routes, trunk access, spending limits, caller ID and final termination. The agent cannot select a route or alter PBX configuration. This adapter only attempts origination through one **preconfigured** PJSIP endpoint: it never creates or removes outbound routes for a call.

In this experimental release, an operator may stop a call and the adapter attempts ARI hangup. That is **not** a guarantee that the carrier has released the call. Provider-owned PBX timeouts, supervision and orphan cleanup must survive a connector or host failure; **these are not implemented as an independent production watchdog in 0.0.1**. A human approval, agent credential, or x402 payment cannot override the telecoms operator's routing decision.

## Requirements

- Python 3.11+ and `aiohttp==3.13.3`.
- Asterisk with ARI enabled and `externalMedia` RTP/UDP support (introduced in Asterisk 16.6). **Asterisk 22 LTS** is the preferred isolated test target.
- A dedicated, **non-production** PJSIP endpoint or trunk under your control, with a known reachable destination and SIP `qualify` where supported.
- The connector on the **same host** as Asterisk for the default `127.0.0.1` RTP configuration. Remote ARI must use properly verified HTTPS/WSS; cross-host RTP requires a dedicated firewalled private network and an explicit configuration switch, since this reference RTP path has **no SRTP**.
- Strictly outbound calling. This is not an inbound carrier gateway or a public SIP registration client. The agent cannot create SIP accounts, choose the trunk, change the destination, or alter dialplan configuration.

### Asterisk configuration (isolated example, not production copy/paste)

Review `/etc/asterisk/http.conf` and `/etc/asterisk/ari.conf` for your installation. The following examples deliberately bind ARI to **loopback only** and require a separately managed secret:

```ini
; /etc/asterisk/http.conf (illustrative local test setup)
[general]
enabled=yes
bindaddr=127.0.0.1
bindport=8088
```

```ini
; /etc/asterisk/ari.conf (illustrative; supply a unique secret)
[general]
enabled=yes
pretty=no

[aidt]
type=user
read_only=no
password=<SET_A_STRONG_UNIQUE_PASSWORD>
```

Do **not** reuse an administrative ARI credential, publish port 8088, or copy illustrative PJSIP endpoint settings into a live FreePBX-managed file. Configure the dedicated endpoint/trunk using your own PBX's supported configuration interface. Verify its allowed route and SIP TLS/SRTP policy on the PBX itself. `GET /ari/endpoints/PJSIP/<trunk>` reporting `online` is a **reachability observation**, not successful SIP OPTIONS/INVITE, media negotiation, or carrier readiness.

### Configuration

Run from the repository root. Use shell-protected environment variables or a local secret manager; never commit credentials:

```sh
python -m pip install 'aiohttp==3.13.3'
export AIDT_ARI_URL=http://127.0.0.1:8088
export AIDT_ARI_USER=aidt
export AIDT_ARI_PASSWORD='<YOUR_STRONG_ARI_PASSWORD>'
export AIDT_PJSIP_TRUNK=your_isolated_endpoint
export AIDT_OPERATOR_TOKEN="$(python -c 'import secrets;print(secrets.token_urlsafe(48))')"
export AIDT_AGENT_TOKEN="$(python -c 'import secrets;print(secrets.token_urlsafe(48))')"
python -m byot.server --check-config
```

**Origination is disabled** unless you add `export AIDT_ENABLE_LIVE_ORIGINATION=YES`. Do not enable that in a shared or production PBX. `AIDT_PJSIP_TRUNK` is a *single fixed PJSIP endpoint name*; no agent API accepts a trunk or arbitrary channel URI. ARI requests must authenticate successfully before the connector serves local callers. The server runs on `127.0.0.1:8877` by default and has no browser CORS configuration.

On a **separate lab machine**, cross-host RTP can be explicitly configured with `AIDT_MEDIA_BIND`, `AIDT_MEDIA_ADVERTISE`, and `AIDT_ASTERISK_MEDIA_IP`, plus `AIDT_ALLOW_PRIVATE_RTP=YES`. All must be private IPv4 addresses. **RTP is still unencrypted**. Arrange real network isolation and firewall controls before use. Do not advertise a public or NAT-mapped RTP endpoint.

If a trunk does not report ARI PJSIP state `online`, origination is refused. The owner may explicitly choose `AIDT_ALLOW_UNQUALIFIED_ENDPOINT=YES` for an isolated non-qualifying test endpoint, but that is *not* proof of readiness or permission to dial production routes.

### Check Asterisk before any call

On your isolated Asterisk host, independently inspect:

```sh
asterisk -rx 'module show like res_ari'
asterisk -rx 'module show like chan_rtp'
asterisk -rx 'pjsip show endpoint your_isolated_endpoint'
asterisk -rx 'http show status'
```

Confirm the dedicated endpoint has **no unrestricted PSTN route**, SIP security is appropriate, and carrier egress is administratively blocked. Native Windows Dial-Tone's TLS/SRTP and OPTIONS checks are **not inherited** by this Python connector.

### Read-only pre-call observation (no telephone call)

Before an authorised trial, an operator can inspect the **fixed PJSIP endpoint** through the local ARI connection:

```sh
curl --fail-with-body --silent --show-error \
  --header "Authorization: Bearer $AIDT_OPERATOR_TOKEN" \
  http://127.0.0.1:8877/v1/readiness
```

This endpoint never dials, issues a mandate, performs a charge, changes PBX configuration, or accepts an agent-supplied route. It requires the operator bearer; an agent bearer receives HTTP 401. It reports a timestamped `online`/`offline` endpoint observation when Asterisk ARI responds, or fails closed with HTTP 503 if ARI cannot provide evidence.

**`ENDPOINT_ONLINE_ROUTE_UNVERIFIED` is NOT a dialling clearance.** This first stage neither captures the authentic SIP OPTIONS response nor proves dialplan reachability, SRTP, carrier access or remote media. `network_call_authorised` is always `false`; normal human-mandate and agent-admission steps remain separate. The original Windows Dial-Tone's fuller checks, audible local tone and diagnostic trace are a design reference, **not yet ported**. See [Pre-call qualification](../content/docs/24-pre-call-principle.md).

### Start the local connector

```sh
python -m byot.server --port 8877
```

The unauthenticated `GET /health` reveals only the 0.0.1 experimental status and whether the ARI event stream is connected, not secrets. This loopback server is not suitable for exposure via a public reverse proxy or arbitrary tunnels.

## One deliberately authorised test call

Only in an isolated lab, to a **telephone endpoint you own or have express permission to test**, and only after explicitly enabling origination:

1. Operator issues a mandate bound to **one destination and one duration**, through `python -m byot.examples.operator --destination '<YOUR_UK_GEOGRAPHIC_TEST_NUMBER>' --max-seconds 35`. It requires typing `AUTHORISE` and prints a one-use `mandate_id`.
2. Pass only that `mandate_id`, not the operator token, to the agent process.
3. Set `AIDT_MANDATE_ID` and `AIDT_AGENT_TOKEN` in the agent process, then run `python -m byot.examples.tone_call`. The agent creates a session, obtains a one-use 20-second WebSocket ticket, **connects before the call begins**, and only then sends `start`.
4. The connector verifies ARI availability and PJSIP endpoint state before originating `PJSIP/<approved-number>@<fixed-trunk>`. Once answered, it creates an external-media channel and a mixing bridge. It waits for first incoming RTP before advertising `media.ready`; the test agent then sends 425 Hz diagnostic PCM for one second.
5. The operator may invoke `python -m byot.examples.operator --stop '<CALL_ID>'` at any moment; the connector attempts ARI channel hangup, confirms absence when ARI returns 404, and records whether that check succeeded. It **never claims carrier release was verified**.

A production UK caller-ID policy must use a valid, dialable number that uniquely identifies the caller, consistent with Ofcom General Condition C6, and should support an appropriate return route for enquiries or abuse reports. This project does **not** configure or verify CLI presentation or an abuse-report service; those remain operator obligations. See [Ofcom CLI guidance](https://www.ofcom.org.uk/phones-and-broadband/phone-numbers/calling-line-identification).

The first-release sample's UK geographic number constraint is intentionally conservative (`+44` followed by an area code beginning with `1` or `2`, and ten national digits). Premium, mobile, emergency, arbitrary international destinations, and SIP URI/dialplan injection are rejected. It is **not** a general worldwide calling policy or an authoritative numbering-plan validator. Configure your carrier and PBX to enforce independent egress restrictions.

### Integrate a real agent rather than the test tone

The adapter `byot/client.py` uses **the same 656-byte DT01 PCM framing** as the public Peer Lab. `byot/examples/model_call.py` connects the existing `peer-lab/voice_peer.py` audio-first pipeline, so a developer can supply their own compatible ASR, chat model, and TTS endpoints. For example, supply `AIDT_ASR_URL`, `AIDT_ASR_MODEL`, `AIDT_MODEL_URL`, `AIDT_MODEL_NAME`, and optionally TTS settings, then run:

```sh
python -m byot.examples.model_call
```

Do not use this with real people until speech quality, interruption, consent, external-audio-processing approval, data retention, and fallback actions are independently evaluated. If any speech or model provider is outside loopback, **a separate** `AIDT_EXTERNAL_AUDIO_PROCESSING_APPROVED=YES` flag is required. The model never receives ARI credentials, carrier keys, numbers to choose freely, spend authority, or a direct tool to create a booking.

## Agent protocol

All control-plane REST requests are loopback-only and authenticated with distinct bearer tokens. All call IDs and mandates are random 24-character hex strings; tickets are high-entropy single-use values in the first WebSocket message, **never in the URL**.

| Method | Path | Authority | Meaning |
| --- | --- | --- | --- |
| GET | `/health` | None | Local status; no telecom guarantee |
| GET | `/v1/readiness` | operator | Non-dialling ARI endpoint observation, explicitly **not** a route guarantee |
| POST | `/v1/mandates` | operator | One immutable UK geographic number + 10–120 seconds (server cap applies) |
| POST | `/v1/mandates/{mandate_id}/revoke` | operator | Prevent future use / end current call |
| POST | `/v1/calls` | agent | Consume a mandate and create a non-dialling session |
| POST | `/v1/calls/{call_id}/tickets` | agent | Obtain a 20-second one-use WebSocket ticket |
| GET WebSocket | `/v1/calls/{call_id}/media` | ticket first message | Admission, explicit `start`, PCM and DTMF |
| GET | `/v1/calls/{call_id}` | agent or operator | Non-transcript state and media counters |
| POST | `/v1/calls/{call_id}/stop` | operator | Independent emergency stop |

Incoming/outgoing WS PCM uses `DT01` + `seq` + `timestamp_ms` + 640 little-endian signed PCM bytes, just like Peer Lab. Asterisk's external-media RTP uses **network-endian L16**; byte conversion is explicit and tested both ways. Incoming RTP packets are restricted to the exact ARI-reported Asterisk IP:port, with stream and sequence continuity validation. Agent-originated PCM is bounded and paced at 20 ms, with a finite outgoing queue. Asterisk packet payload type is *learned from real incoming RTP* and is never guessed; no audio is transmitted before the first validated packet. The connector requires that first RTP packet within eight seconds of bridge creation or it tears the call down.

`call.answered` reflects ARI Stasis admission; `media.bridged` reflects bridge creation; `media.ready` reflects one valid inbound RTP packet; **none** proves two-way speech, SIP TLS, SRTP, actual carrier reachability, DTMF success at the far end, or a completed task.

The running connector handles no more than **one active call** and retains at most 100 local mandates and 100 local call records before a restart. A call must obtain its WebSocket agent before any origination. A call without an agent is cancelled after 20 seconds. A process-local hard call deadline, operator stop, remote release, and agent disconnect all trigger cleanup; real PBX safety still requires an independent Asterisk-side maximum call duration and orphan reconciliation if this process crashes.

## Security and publication boundaries

- **Not yet audited or tested on a real PBX**; do not expose to the public Internet or place unauthorised calls.
- No inbound public API, SIP user registration, carrier credentials, third-party payment access, or x402 settlement.
- Plain RTP/L16 is not SRTP. The code does not validate PJSIP TLS, SRTP configuration, secure SIP registration, remote call audio quality, or full dialplan restriction. Those remain **release blockers**.
- The 0.0.1 operator role is a local bearer token, **not** proof of a verified human account/consent signature.
- Asterisk channel absence after DELETE is observed via ARI GET 404; the connector still sets `carrier_release_verified:false`.
- Outbound calls may incur costs; PBX/carrier owner must provide a cost ceiling and independently authorised routes. The first release has **no spend-metering or credit cutoff**.
- Source GPLv3-or-later; underlying Asterisk and other dependencies retain their own licences. There is no MicroSIP code in this component.

## Validation

```sh
python -m unittest discover -s byot/tests -p 'test_*.py' -v
npm run check
```

One test launches **a real fake ARI HTTP/WebSocket server and UDP RTP socket** and checks actual request parameters, admission, audio framing, event subscription, hangup, and ARI absence observation. Other tests cover unauthorised agents, replayed tickets, forbidden dial targets, unqualified PJSIP endpoints, nonresponsive sessions, shutdown, and falsified confirmation claims. These tests are *not* a substitute for an isolated Asterisk 22 test with actual SIP/SDP negotiation and human-observed speech.

**Reference documentation:** [Asterisk External Media and ARI](https://docs.asterisk.org/Development/Reference-Information/Asterisk-Framework-and-API-Examples/External-Media-and-ARI/), [ARI Bridge Operations](https://docs.asterisk.org/Configuration/Interfaces/Asterisk-REST-Interface-ARI/Introduction-to-ARI-and-Bridges/ARI-and-Bridges-Bridge-Operations/), [PJSIP Endpoint API](https://docs.asterisk.org/Asterisk_23_Documentation/API_Documentation/Asterisk_REST_Interface/Endpoints_REST_API/).
