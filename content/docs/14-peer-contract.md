# Bot-to-bot interoperability and the human mandate

**Status: contract research and runnable local policy prototype. Not a hosted A2A server, MCP endpoint, call provider, or payable service.** The included pure JavaScript module at `lib/peer-contract.mjs` is an executable design exercise, not a production authorisation service.

## Who is the peer?

There are three different peers, and treating them as one is a design error:

1. **Requesting autonomous agent:** an OpenAI, Anthropic, Google, local or bespoke agent acting for a human. It wants a bounded telephony capability exposed by Dial-Tone via tools.
2. **Dial-Tone calling peer:** a deterministic service that validates a server-held mandate, enforces policy, originates a call through Asterisk and streams media. A model never receives carrier credentials, SIP passwords, a provider signing key, or unrestricted ARI access.
3. **Answering party:** a human receptionist, an IVR or another AI. The PSTN does not advertise which one answers. We detect answer and audio; we do not infer that the voice is human or that an appointment was confirmed from SIP signalling.

Model providers differ. The interoperable contract belongs to Dial-Tone, not to the language-model provider. We will expose a documented REST control API, MCP tools for compatible hosts, and a separate real-time audio session. A future A2A Agent Card will be published **only after a genuine A2A service exists**. `/agents.json` and `/agents.txt` are project-specific documents, not substitutes for A2A conformance.

## The mandatory human-authorised workflow

The authorisation object is a **mandate**, not an instruction hidden in a prompt. An agent cannot authorise its own spend or silently broaden destinations.

The human authorises a specific purpose, destination, time window, call duration, budget and permitted consequential actions. The production platform must authenticate the human, store or sign the mandate on the server, tie it to tenant and agent identity, expire it, allow revocation and enforce the limits **again at the PBX/SBC**. The lab's `human_approved: true` field demonstrates the expected shape; **it cannot establish that a human actually approved anything**.

A restaurant booking task must carry:

- Restaurant identity and one classified UK geographic destination, with number ownership checked before live calling.
- Party size, calendar date, arrival-time range, and the customer's consented name.
- Whether booking itself is authorised or only availability inquiry is authorised.
- Hard call-duration, retry and spend limits, including an explicit prohibition on deposits and card requests in the initial pilot.
- An idempotency key generated outside the model to avoid duplicate outbound calls.

The public `contracts/mandate.schema.json` and `contracts/peer-event.schema.json` are **design schemas**, not published live API guarantees.

## Discovery and capability negotiation

Discovery answer must separate `available_now` and `planned`. At present `available_now.public_live_calling=false`, `hosted_mcp_server=false`, `hosted_a2a_agent=false`, `x402_payment=false`. An agent should use the static scenarios to learn the event shape, but must never treat them as a telephone call. A standard A2A discovery document belongs at `/.well-known/agent-card.json` only when an A2A server actually implements the advertised interface. See the [A2A specification](https://github.com/a2aproject/A2A/blob/main/docs/specification.md).

### Planned peer sequence (not implemented on a public endpoint)

```text
Human -> Requesting agent: "Book a table for two Saturday at 7:30 PM."
Agent -> Human: confirm missing details and maximum cost
Human -> Mandate service: approve exact task and limits
Agent -> Dial-Tone capabilities: check features, destination policy, pricing
Agent -> Dial-Tone: prepare_call(mandate_id, idempotency_key)
Dial-Tone -> PBX: verify isolated route, TLS, SRTP and recent SIP readiness
Dial-Tone -> Agent: priced quote + explicit decision: ready / blocked / uncertain
Agent -> Payment: obtain payer authorisation (only when x402 is live)
Dial-Tone -> Asterisk: originate bounded channel
Asterisk -> Dial-Tone: authoritative ringing / answer / hangup events
Agent <-> Dial-Tone <-> answering human or bot: real-time audio
Agent -> Dial-Tone: booking was apparently agreed (attributed observation)
Asterisk -> Dial-Tone: confirmed channel termination
Dial-Tone -> Agent -> Human: events + cost + reservation evidence status
```

The system should minimise ambient authority: time-limited media tickets, event cursors, tight destination classes, no privilege escalation through SIP REFER/302 redirects, and independent provider timeouts. An MCP tool return is not proof that the telephone network completed an action.

## Proposed session events

Every event has a version, `call_id`, `event_id`, monotonic sequence, UTC timestamp, source (`agent`, `platform`, `sip`, `provider`), and verification status. Possible types include `mandate.accepted`, `readiness.sip_options_passed`, `call.requested`, `call.ringing`, `call.answered`, `media.started`, `agent.interrupted`, `call.hangup_requested`, `call.hangup_confirmed`, `usage.finalised`, `outcome.agent_reported`, and `outcome.independently_verified`.

A model may add attributed transcript and interpretation events. It **may not** create provider-verified `call.answered`, `call.hangup_confirmed`, or settlement events. Persist these separately and reject attempts to cross the trust boundary.

## What must never happen

- An agent receives a dial-string that can reach arbitrary premium-rate, emergency or international destinations.
- A `200 OK` OPTIONS response is presented as proof of PSTN service, working RTP, or a completed reservation.
- A retry after a timeout creates a second PSTN call or a second payment.
- The agent says "booked" and the human UI silently upgrades that to "confirmed" without an independent check.
- A backend failure frees a customer balance while an SBC channel is still active.
- The platform publishes A2A/x402 claims without passing protocol tests and making the endpoint available.

## Runnable local exercise

```bash
cd ai
node examples/restaurant-lab.mjs
node --test tests/peer-contract.test.mjs
```

This exercise prints a **synthetic** approval, preflight decision and post-call evidence classification. It does not make a telephone call or book anything.

A [JSON Schema example mandate](/contracts/examples/reservation-example.json) is published for parser tests. **It is expired, fictional and untrusted.** A peer must not replay it as a valid authorisation or call the illustrative number. It exists to show the intended shape, not proof of human approval.
