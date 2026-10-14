# Agent integration, SDKs, and MCP status

AI Dial-Tone is designed for **model-neutral** agents. In 0.0.1 there is a Python client in `peer-lab/client.py`, protocol experiments in `labs/web-softphone/`, and a generic chat-compatible model adapter in `peer-lab/model_adapter.py`.

## What agents can do today

An agent process can authenticate as a named **local** caller or peer, request its own WebSocket ticket, exchange PCM and text/DTMF signals, react to interruptions, end a test session, and read its attributed events. See [Quickstart](02-quickstart.md) and the [`PeerClient` implementation](https://github.com/kierknoby/AI-Dial-Tone/blob/main/peer-lab/client.py) once the repository is published.

A model adapter uses a restricted chat-completions response. It rejects model-requested tool calls and does not expose dialling, payment or booking powers. The audio-first path uses speech recognition before model reasoning, rather than silently accepting another bot's asserted transcript. Its offline recognition results do **not** meet real-booking accuracy.

## Not offered at 0.0.1

There is no hosted Model Context Protocol (MCP) endpoint, no A2A Agent Card service, no turnkey hosted SDK, no real AI agent registration, and no tool capable of originating a telephone call. `agents.json` is a **project-specific capability directory**, not a standard A2A Agent Card. A model should parse explicit feature booleans and must not assume future capabilities are live.

Developers integrating a future paid service must separately obtain actual human consent, check policies and network readiness, verify real-world outcomes and respect session stop authority.
