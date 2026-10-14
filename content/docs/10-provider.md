# Provider and Asterisk integration boundary

**The 0.0.1 repository now contains a disabled-by-default Asterisk ARI connector in `byot/`, tested against a synthetic ARI server and network UDP.** This is a local reference implementation, not a verified or deployed SIP/PSTN integration; real Asterisk interoperability, SIP.js registration, PSTN reachability, and settlement remain untested.

## Gateway acceptance requirements

Before enabling live testing or any future private Asterisk/SBC adapter, independently verify the following against an **isolated** PBX with carrier egress disabled:

1. Asterisk and TLS/WSS listeners authenticated with valid certificate and endpoint policy.
2. SIP registration or configured-peer readiness and successful authenticated OPTIONS, without claiming this proves INVITE route or remote media.
3. Mandatory SRTP/DTLS-SRTP where the endpoint and network permit it; reject downgrades. Confirm the negotiated media protection, not merely a checkbox.
4. Actual INVITE, answer, bidirectional audio, RTP metrics, DTMF and release events.
5. Independently enforce maximum session time **at the provider/PBX**, even if the AI process crashes.
6. Reconcile unknown or partial states after process restart and network failure.
7. Permit only explicitly approved test destinations before any UK geographic pilot.

## Do not conflate products

The Windows [Dial-Tone MicroSIP fork](https://github.com/EgyptianEyes/Dial-Tone) is a separate native application. Its security and readiness patterns have been reviewed, **not ported** into this Python service. The private telephony backend must remain separately reviewed and outside this public development release.

For the public self-hosted reference, see [BYOT: Asterisk](20-byot-asterisk.md). The agent never supplies a trunk or arbitrary SIP endpoint.
