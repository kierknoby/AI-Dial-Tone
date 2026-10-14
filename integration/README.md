# Local payment-to-telecom handoff (0.0.1)

**Development-only, disabled-origination proof. Not a publicly callable API.**

The two previously independent reference components are connected by `LocalHandoff`:

1. The operator issues a scoped x402 lab mandate and a fixed-price challenge.
2. A locally injected facilitator can return fixture settlement. **No actual transaction has been demonstrated.**
3. The gate produces and consumes a one-use permit, preserving the destination and maximum duration.
4. The handoff checks the local BYOT `/health` endpoint, and **refuses to proceed if live origination is enabled**.
5. The operator-side handoff issues a separate BYOT mandate with the exact same destination and duration.
6. The BYOT agent still needs its own credential and normal call-admission path. **No call is placed by the handoff.**

The agent is never handed the operator bearer, receiving wallet, SIP password, routing information, or x402 merchant credential. The handoff is deliberately not exposed over HTTP. It accepts only numeric loopback origins (`127.0.0.1` or `::1`); a remote BYOT connector is rejected.

If a permit is redeemed but the downstream response is unknown, the attempt becomes **unresolved**. It must be reconciled by an operator; there is no automatic retry or implied refund. All state is in memory and therefore **not safe for real money or real telephony**.

## Test the actual contract

```bash
python -m unittest discover -s integration/tests -p 'test_*.py' -v
```

The tests start both a contract-level local HTTP fixture **and the actual BYOT HTTP/WebSocket service** (with a fake ARI), use the actual `X402Gate` against a fake facilitator, and assert identical destination/duration, one-use admission, no calls, fail-closed origination policy, and rejection of mismatches. This is protocol integration, **not proof of live Base settlement, FreePBX interoperability, real human consent or PSTN termination**.

For the longer-term hosted design, see [Call architecture](../ARCHITECTURE.md), [x402 payment admission](../content/docs/21-x402-payment-admission.md), and [BYOT Asterisk](../byot/README.md). A production coordinator requires a durable mandate/permit registry, authenticated human accounts, a real x402 settlement and reconciliation provider, restricted FreePBX routes, and PBX-owned cutoff independent of this process.
