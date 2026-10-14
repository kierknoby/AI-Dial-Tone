# For humans: ask an agent to make a call

**Human-facing walkthrough, not a working booking service.** This guide is distinct from the [agent integration contract](14-peer-contract.md): it explains what a person should see, approve and receive. The public website does not currently make calls.

## Imagine you say: "Call that restaurant and book me a table."

The requesting agent needs to know which restaurant to call, the party size, preferred date and arrival time, whose name to use, and any restrictions. It should use structured data or ask concise questions, not invent missing details.

**Example mandate:** two people, 17 October 2026, 19:00–20:30, Example Restaurant, a fictional UK test number, maximum two minutes, no deposit, no recording, no second attempt without renewed approval. The example number is illustrative and MUST NOT be dialled.

### 1. Human decides

The UI displays the selected restaurant and telephone number, the exact task, any personal details the agent will share, a maximum permitted cost, and a short list of actions the agent may take. **Book the table** can be authorised; a payment, deposit, cancellation fee, upsell, new date or different venue requires a separate permission. A button press or authorised account action must create a server-verifiable mandate. An LLM-generated JSON flag alone is not permission.

### 2. Agent prepares

The agent discovers Dial-Tone's current capabilities and asks for a priced preflight. The system checks its account permissions, destination class, call concurrency, route, recent SIP OPTIONS, TLS signalling and mandatory encrypted media policy. It returns either ready for a restricted attempt, blocked, or insufficient evidence. **SIP readiness is not a promise that the restaurant will answer.**

### 3. Dial-Tone places the call

Once a real provider connection exists and the human's mandate and payment are verified, Dial-Tone asks Asterisk to originate the bounded channel. The network, not the agent's script, reports ringing, answer and termination. Audio becomes available to the agent through a controlled media gateway. The caller can hear and speak without having SIP credentials.

### 4. Agent speaks normally

A suitable opening would be: "Hello, I'm an automated assistant calling on behalf of a customer. Could I book a table for two for Saturday 17 October, ideally at 7:30 PM?" The model listens, allows the other person to interrupt, repeats a name or number only as authorised, checks the time, asks whether there is a booking reference, and does not provide card details or agree to a deposit. If the business refuses automated calls, the agent ends politely.

The answering party may be a person, an IVR or another voice agent. Calling voice bots should be treated as capable peers but cannot be assumed to support MCP or A2A simply because they answer the phone. DTMF, IVR navigation, hold music, voice activity, and disconnections are first-class telephony outcomes.

### 5. Human sees what actually happened

The result is presented in separate fields: `Call connected` (network event), `Call ended` (provider-confirmed release), `Agent reports a reservation` (agent's interpretation), `Booking reference` (if provided by the restaurant), `Independent confirmation` (if obtained from a trusted booking system or customer verification), and `Total charge` (after verified metering and settlement). **Do not present an agent-reported reservation as independently verified.**

If the restaurant is busy or unreachable, the agent returns that outcome and requests a fresh mandate for another attempt rather than redialling indefinitely. If call termination is uncertain, the service surfaces `needs_reconciliation` until the network confirms release. Recording/transcription policies must be explicit and appropriate to UK privacy law before deployment.

## Human and agent experiences are intentionally different

| Human-facing information | Agent-facing machine contract |
| --- | --- |
| Who is being called and why | `mandate_id`, scoped principal and capability |
| Approval and maximum cost | Server-enforced bounds and idempotency key |
| Connecting / answered / finished | Sequenced provider events with source and trust |
| What the restaurant said | Timestamped, attributed observations |
| Was a table actually booked? | Claim versus independent booking confirmation |
| Receipt and ability to stop | Usage, settlement reference and kill switch |

## Controls the human must retain

Before live launch: revoke authorisations, cancel a queued call, request hangup, review per-call spend, choose whether any audio/transcript is retained, see error and dispute paths, manage agent credentials and inspect the exact call evidence. The platform must honour abuse reports and a recipient's request not to be called.

**No live call, booking, wallet transaction or invitation to the public beta exists in this preview.** Read the [readiness roadmap](17-roadmap.md) for acceptance criteria.
