# Overview

**AI Dial-Tone 0.0.1 is an open-source agent communications development project.** It is not a hosted telephone platform or a booking service. No public API exists at `ai.dial-tone.uk` for originating calls, and the domain currently represents a planned static site.

## What the repository actually contains

- **Peer Lab (`peer-lab/`)**: a runnable Python 3.11+ localhost HTTP/WebSocket service connecting two separately authenticated bot processes, with bounded PCM media and a local operator who can end sessions.
- **Voice runtime**: an optional experimental path from *received* PCM to speech recognition, a model-compatible text endpoint, speech synthesis and returned PCM. Tests use fixtures. No live LLM quality claim is made.
- **BYOT Asterisk (`byot/`)**: an experimental self-hosted ARI/RTP connector. A human operator issues a one-use UK geographic mandate, the agent is admitted before dialling, and the fixed PJSIP endpoint is checked before any optional outbound originate. Real origination is off by default; tests use a simulated Asterisk and real local UDP, never a real carrier. See [BYOT Asterisk](20-byot-asterisk.md).
- **Browser lab (`labs/web-softphone/`)**: an independent experimental browser SIP and agent-control interface, not a hosted service and not verified against Asterisk.
- **Static site and fixtures (`site/`)**: documentation, synthetic examples and machine-readable declarations, with no live endpoints.
- **Contracts (`contracts/`)**: versioned experimental JSON shapes for future human mandates and peer events. They are not proof of verified human authorisation.

## What the project does not contain

No independently verified real SIP origination or PSTN call, Asterisk interoperability report, carrier integration, independently verified booking, x402 settlement, hosted MCP/A2A endpoint, recording policy, customer accounts or provider-confirmed carrier hangup. No MicroSIP-derived Windows code is shipped here.

## Choose a path

**Developers and agents:** start with the [local quickstart](02-quickstart.md) and [Peer Lab](18-peer-lab.md). **Human users:** read the [human journey](15-human-journey.md), a proposed experience, not an available booking feature. For security and criteria for a real launch, read [readiness](13-readiness.md) and the [roadmap](17-roadmap.md).
