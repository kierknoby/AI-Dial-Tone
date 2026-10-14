# Origins, community work and technical provenance

**Developer:** [Kieran Knowles-Byrne (`@kierknoby`)](https://github.com/kierknoby). AI Dial-Tone is an **independent** open-source project, not an official Sangoma, FreePBX, MicroSIP or telecommunications-provider release.

## Project home and current status

AI Dial-Tone is currently being developed in Kieran's personal development space and is being prepared as an [Egyptian Eyes](https://egyptianeyes.com) project. The name also appears on the [separate Egyptian Eyes Windows Dial-Tone codebase](https://github.com/EgyptianEyes/Dial-Tone); the two repositories do not share native application source. The project is not represented as an already transferred business or a live Egyptian Eyes telecom service. General/privacy contact: [ai@dial-tone.uk](mailto:ai@dial-tone.uk); abuse reports: [dial-tone@egyptianeyes.com](mailto:dial-tone@egyptianeyes.com).

## A decade of FreePBX and telephony engineering

[20tele](https://20tele.com/) describes more than a decade working with FreePBX and Asterisk, managed hosting, SIP trunks, numbering, customer support and deployment tooling. [FreePBX UK](https://freepbx.uk/) publicly describes its Official FreePBX partner status for UK hosting and its relationship with 20tele. Kieran is identified there as Head of Product. The differing public historical dates used by those websites are deliberately not repeated here; the defensible statement is **more than a decade of trading and engineering**.

The published projects are concrete examples, not unverifiable claims:

- [Registration Watch](https://github.com/freepbxUK/registrationwatch): signed community module for monitoring PJSIP registration status and alerting.
- [Repeat Caller](https://github.com/kierknoby/repeatcaller): inbound caller detection, incidents and notifications for FreePBX/PBXact.
- [Concurrency Count](https://github.com/kierknoby/concurrencycount): live and historical FreePBX/Asterisk call concurrency reporting.
- [Heqet ISO](https://github.com/20telecom/heqet) and [IN1CLICK](https://github.com/20telecom/IN1CLICK): FreePBX installation and deployment tooling associated with 20tele.

These projects demonstrate experience with operating actual telecom systems, not proof that the experimental AI calling platform is itself production-ready.

## The original Dial-Tone's distinctive contribution

[Dial-Tone](https://github.com/EgyptianEyes/Dial-Tone) is a separate, native Windows MicroSIP-derived softphone. Its central advance for this project is **pre-call readiness**: qualify local PJSIP account and audio prerequisites, receive an authenticated SIP response, play a **locally generated audible dial tone**, and present actionable **Call Trace** observations. The principle is not that a SIP response guarantees a PSTN call; it is that avoidable failure conditions should be discovered **before bothering a person**.

AI Dial-Tone translates that ambition into structured preflight receipts for autonomous agents and a future browser/headless communication interface. No native Windows code is included or asserted to run in the browser. See [Pre-call qualification](24-pre-call-principle.md), [Native security](16-native-security.md), and the public [Project Overview](/overview.html).

## Public and private boundaries

The project's public code includes experimental model/voice tools, a local peer media lab, an optional self-hosted Asterisk connector and an x402 contract experiment. It does **not** contain or explain any operator's internal service provisioning, charging, carrier interconnect or routing technology. The public code should describe standard security and integration contracts only.

**Trademark and partnership distinction:** any FreePBX UK partner designation belongs to FreePBX UK under its own commercial agreement. AI Dial-Tone does not claim Sangoma endorsement, commercial availability, or a production certification.
