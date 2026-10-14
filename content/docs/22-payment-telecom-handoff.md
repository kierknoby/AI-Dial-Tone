# Connecting payment admission to a telephone mandate

**Version 0.0.1 · Local experimental integration · NOT LIVE TELEPHONY OR SETTLEMENT.**

The original AI Dial-Tone idea is one controlled sequence: a human directs an agent, the human authorises a bounded call, the managed service accepts an x402 payment when required, the telephony gateway qualifies and starts the call, and the agent receives a truthful outcome. The public components now include a **local proof of a safe handoff**, not that entire live service.

## The real trust boundaries

| Stage | Responsible actor | Evidence / 0.0.1 status |
| --- | --- | --- |
| Task and destination | Human / operator | Operator bearer in the lab; not identity or consent verification |
| Fixed upfront price | x402 gate | HTTP 402 challenge with bound network, asset, amount, recipient and resource |
| Settlement | Trusted facilitator | Fake facilitator only; **no real USDC transfer** |
| Single-use permit | Payment gate | Cryptographically random, consumed once; not a telephone call |
| PBX mandate | Operator-side handoff | Local-only HTTP POST to the BYOT operator API; same destination and maximum seconds |
| Call admission | Asterisk adapter | Different agent bearer, preconfigured PJSIP endpoint and disabled-by-default origination |
| Real media / hangup | FreePBX/Asterisk and gateway | Simulated ARI/WebSocket/RTP integration; no certified PBX or carrier release |
| Task confirmation | Agent / destination | No real reservation verification available |

The model must never hold the operator bearer, PBX password, receiving wallet signing key, or routing configuration. It cannot choose a new destination during the handoff. Payment alone is insufficient to originate.

## What has actually been implemented

`integration/handoff.py` provides `LocalHandoff`. It checks that the Asterisk adapter is the expected experimental `0.0.1` component and that **live origination is explicitly disabled**. It consumes a paid lab permit from `X402Gate`, then issues a separate BYOT mandate with exactly the original destination and maximum duration.

It rejects non-loopback endpoints, credential problems, mismatched mandate replies, expired/replayed permits, and live-origination backends. An ambiguous HTTP outcome after permit consumption becomes **unresolved**: never silently retry or claim a refund. It never creates a call or passes the agent's credentials into the operator side.

This makes the two reference components consistent and testable. It intentionally **does not turn a mock settlement into the right to place a real paid call**. A production gateway will need independently authenticated humans, persistent payment records, verified USDC settlement, reconciliation, a real FreePBX policy engine and a provider-owned hangup watchdog.

## Reproduce the contract integration

Run from the standalone repository root:

```bash
python -m pip install 'aiohttp==3.13.3'
python -m unittest discover -s integration/tests -p 'test_*.py' -v
```

The tests use the real x402 gate, a local BYOT-compatible HTTP fixture, and the actual BYOT HTTP/WebSocket service with a fake ARI. They verify number and duration binding, one-use consumption, concurrent replay prevention, disabled-origination enforcement, rejection of swapped destinations, and safe failure. They are not an on-chain or SIP interoperability test.

## The agent-facing product still needs building

The agent should ultimately receive **one stable discoverable interface**, independent of whether the route is managed or BYOT. Required, separately verifiable stages include human consent, payment, SIP/WSS readiness, audio admission, network-controlled call states, forced termination, and a receipt that differentiates remote confirmation from model inference.

The public proof deliberately leaves these stages separate so no agent can bypass an unfinished gate. See the [BYOT reference](/docs/byot-asterisk.html), [x402 reference](/docs/x402-payment-admission.html), [security review](/docs/native-security.html), and [frequently asked questions](/faqs.html).
