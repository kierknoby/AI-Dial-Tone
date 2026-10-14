# AI Dial-Tone 0.0.1 publication checklist

**Release type:** open-source technical preview. **Not:** hosted telephone calling, production BYOT service, real x402 settlement, or verified booking.

## Evidence-based gates

- [x] Separate static website and runnable public source packages prepared locally.
- [x] Agent and human documentation disclose that live calling and payments are unavailable.
- [x] Source-level safety constraints, operator role separation and fail-closed defaults are covered by automated local tests.
- [x] Local two-peer real audio transport and session closure have a reproducible verifier.
- [x] Product scope clearly distinguishes included, future, excluded and undecided work.
- [ ] **Abuse contact:** confirm `dial-tone@egyptianeyes.com` receives messages, has a named reviewer and an escalation route; `ai@dial-tone.uk` remains the general/privacy/security route.
- [ ] **Project attribution:** confirm "personal development space; being prepared as an Egyptian Eyes project" remains accurate, and do not imply a completed legal transfer or operational service.
- [ ] **Human review:** confirm copyright, GPL notices, public attribution and trademark usage; confirm maintainer privacy/security contact is authorised, the actual hosting operator and provider, access-log retention, and the relevant controller/processor arrangements. A verified contact and draft privacy notice are supplied, but the hosting facts cannot be inferred from the source.
- [ ] **Real hosting:** publish the website over TLS; run `python tools/verify_publication.py --origin https://ai.dial-tone.uk` and inspect real redirects, cache headers, CSP, HSTS, relative URLs and logging configuration.
- [ ] **GitHub:** publish to the intended account, enable private vulnerability reporting in Settings → Code security, and confirm the first hosted CI run passes with the supported dependency versions.
- [ ] **External validation:** an independent developer must follow the clean-install instructions without private maintainer knowledge.

## Later live calling gates, not blockers to publishing research source

- [ ] Real isolated Asterisk call and both media directions confirmed, with no PSTN egress.
- [ ] Telecoms-controlled cutoff independently observed after agent failure and timeout.
- [ ] Caller ID, recording/consent, abuse controls and territory policy approved for the actual use case.
- [ ] Real settlement, reconciliation, accounting and refunds verified before managed paid calls.

**Release labelling rule:** passing local source tests does not mean production acceptance. Preserve the "technical preview" warnings and never label real PSTN, settlement, model quality or real-world task outcomes as verified without independent evidence.

**First operator action after publication:** verify hosted CI and private vulnerability reporting, then run the live-site verification script. The independent maintainer contact is available by email before repository creation. This checklist intentionally does not claim either has already been completed.
