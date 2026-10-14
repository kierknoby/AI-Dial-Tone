# AI Dial-Tone 0.0.1 security policy

## Supported scope

`0.0.1` is a **development-only research source preview**, not a supported production telephone service. The static public website does not expose a calling, identity or payment API. The local Peer Lab must bind only to loopback (`127.0.0.1` or `::1`). Do not expose research servers to the Internet or connect the browser SIP laboratory to public PSTN, emergency services or commercial dialplans.

## Private security reporting

**Email the project maintainer at [ai@dial-tone.uk](mailto:ai@dial-tone.uk?subject=AI%20Dial-Tone%20security%20report)** with the subject **AI Dial-Tone security report**. This is a publicly disclosed maintainer contact, not a claim that ordinary email provides end-to-end encryption. Start with a short description and request a secure disclosure channel **before sending exploits, credentials, recordings or sensitive logs**. Never publish a live exploit or a secret in GitHub Issues.

After the repository has been created and GitHub **Private vulnerability reporting** has been enabled under **Settings → Code security**, you can alternatively use the repository's private vulnerability reporting interface. That option is **not yet confirmed to be enabled**. The maintainer does not currently promise a response-time SLA, a bug bounty or 24-hour incident coverage.

## Abuse reports

Report suspected misuse, unwanted calls or other abuse associated with the AI Dial-Tone project to **[dial-tone@egyptianeyes.com](mailto:dial-tone@egyptianeyes.com?subject=AI%20Dial-Tone%20abuse%20report)**. This is the designated abuse contact, not the private vulnerability-disclosure address. The 0.0.1 public preview does **not** make telephone calls or operate a live telecoms service, and this mailbox is not an emergency response service. Do not include passwords, credentials, payment details or private call recordings in an initial report.

This project is presently maintained in the developer's personal workspace and is being prepared as an [Egyptian Eyes](https://egyptianeyes.com) project. That planned association is not a claim of a completed organisational transfer or a production Egyptian Eyes telecommunications service.

## Boundaries

Reports concerning the code in this standalone repository are welcome. The separate MicroSIP-derived Windows Dial-Tone project is independently maintained. Telecom infrastructure, wallets, real user accounts, PSTN routing and private payment systems are not supplied as part of this release.

Any deployment beyond local experimentation needs independent threat modelling, authentication, TLS/media security, durable audit state, abuse controls and incident response. See [FORENSIC-AUDIT.md](FORENSIC-AUDIT.md). Local automated tests do **not** establish production security.
