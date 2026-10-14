# x402 payment admission lab (0.0.1)

**Research code. Not a live payment service, merchant gateway, wallet, or telephone service.**

This folder implements a narrow, useful part of the original AI Dial-Tone goal: an autonomous agent can receive a genuine **x402 v2 HTTP 402 challenge**, supply a payment authorisation, and receive a *single-use call admission* only after an independently configured, trusted facilitator reports **durable settlement**. That admission is **not** permission to dial: a separate, independently enforced telephony gate must still check the human mandate, number, SIP/PJSIP readiness, call limits, and provider control.

The public code contains no merchant wallet, settlement credentials, provider implementation, carrier configuration, or private provisioning system. The facilitator is an injected dependency, with a **fake test facilitator only**. There is no actual USDC transfer in the demonstration.

## Why x402 `exact` + `upfront`?

A telephone call cannot be undone if a payment later fails. This lab uses the x402 v2 `exact` scheme with `extra.paymentFlow = "upfront"`. The HTTP resource being purchased is *one fixed-price admission*, not minutes or a confirmed outcome. The facilitator is asked to settle before an admission permit can be exposed.

This trade-off is deliberate and not yet suitable for consumers: an **upfront payment can settle even when a subsequent call cannot connect**. The specification provides no automatic refund, so refund/dispute handling, reconciliation after crashes, and clear customer terms must exist before a chargeable launch. Do not market this as usage-based billing. For future metered services, evaluate the x402 `upto`/escrow mechanisms supported by the chosen facilitator.

The configurable payment network is Base mainnet (`eip155:8453`) or Base Sepolia (`eip155:84532`) with the respective **native USDC** asset address, and **six-decimal integer atomic units**. GBP display and FX quotations are NOT implemented; they must never be guessed from a USDC amount.

## Run the local demonstration

From the repository root, with Python 3.11 or later:

```bash
python -m unittest discover -s payments/tests -p 'test_*.py' -v
python -m payments.examples.first_paid_admission
```

The demonstration constructs an imaginary human-approved call, prints the canonical `PAYMENT-REQUIRED` header and a lab-only protocol payload, and runs through a fake facilitator before producing a one-use permit. **No wallet is used and no call is made.** It uses a test-only payee address; never fund any address printed by a demo.

## Boundaries of the API

1. A private, operator-authenticated `operator_approve(...)` authorises one UK geographic destination, maximum duration, and fixed USDC atomic-unit price. The lab operator secret is not a real human identity, consent, or account system.
2. `challenge(mandate_id)` produces HTTP `402` and the x402 v2 base64-encoded `PAYMENT-REQUIRED` header, with `resource`, `accepts`, and `extra.paymentFlow="upfront"`.
3. An agent submits the base64-encoded x402 v2 `PaymentPayload` as `PAYMENT-SIGNATURE`. The lab rejects altered network, asset, recipient, amount, timeout, flow, resource, or unsupported versions *before* invoking the facilitator.
4. `settle_and_admit(...)` calls the **trusted** injected facilitator's `/settle` equivalent once. It does not call `/verify` as a substitute for durable settlement. A false, ambiguous, timed-out, or invalid settlement produces **no permit**.
5. After a positive settlement, `redeem(...)` consumes a random one-use permit. It returns the operator-bound destination and time limit, together with `network_call_authorised:false`. The dialling service must then independently check SIP readiness, consent and remaining budget, and provider-specific routing restrictions.
6. Revocation prevents further permit redemption. Revocation while settlement is in flight cannot guarantee a refund or undo a completed transfer, and requires reconciliation.

## Known limitations and release blockers

- **In-memory only.** Mandate state, transaction replay detection, and permit consumption are not durable or multi-worker-safe. Do not expose this component to the public Internet or real funds without a transactional database and crash reconciliation.
- No real facilitator, wallet signature verification, on-chain settlement proof, FX rate, metered billing, refunds, tax handling, webhooks, human account authentication, KYC/AML review, or trusted payment reconciliation.
- No HTTP gateway exposing these calls: this is a Python library plus tests and a synthetic demonstration. It supports x402 v2 data structures but is **not a deployed interoperable x402 endpoint**.
- Fixed-price prepayment does not prove that a telephone call connected or that its outcome succeeded. Paid-but-not-admitted and paid-but-failed-call conditions require explicit policies before launch.
- No connection to actual ARI origination. BYOT can remain free and self-hosted; the hosted service will enforce payment separately before granting provider access.
- Actual financial and call authorization must be anchored in durable, independent human/operator evidence. Model-generated text cannot create or extend a mandate.

## Canonical references

- [x402 v2 core specification](https://github.com/x402-foundation/x402/blob/main/specs/x402-specification-v2.md)
- [x402 v2 HTTP transport](https://github.com/x402-foundation/x402/blob/main/specs/transports-v2/http.md)
- [x402 `exact` scheme](https://github.com/x402-foundation/x402/blob/main/specs/schemes/exact/scheme_exact.md)
- [Circle native USDC on Base](https://www.circle.com/blog/usdc-now-available-natively-on-base)

**Do not import private fulfilment, telephone-route, merchant, or account details into this public folder.**
