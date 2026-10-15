# AI Dial-Tone 0.0.1 publication checklist

**Release type:** open-source technical preview. **Not:** hosted telephone calling, production BYOT service, real x402 settlement, or verified booking.

## Publication status verified 14 October 2026

- [x] The public GitHub repository exists and is public on `main`.
- [x] The initial GitHub Actions run completed successfully for commit `35348ad0d34bfb5e89b5f1db1a9b7d3eaca19536` (run [38625817798](https://github.com/kierknoby/AI-Dial-Tone/actions/runs/38625817798)). This run predates the WSS hardening changes in the current worktree.
- [x] The static website is reachable over HTTPS. The published `robots.txt` matched the repository copy; its observed four-hour cache lifetime is appropriate for this low-churn file.
- [x] The updated read-only publication verifier accepts that robots policy while still checking that its bytes match the repository source, along with the required pages, redirect and response security headers.

These are point-in-time checks, not a claim that the public service is operational or that the current uncommitted source has passed hosted CI.

## Evidence-based gates

- [x] Separate static website and runnable public source packages prepared locally.
- [x] Agent and human documentation disclose that live calling and payments are unavailable.
- [x] Source-level safety constraints, operator role separation and fail-closed defaults are covered by automated local tests.
- [x] Local two-peer real audio transport and session closure have a reproducible verifier.
- [x] Product scope clearly distinguishes included, future, excluded and undecided work.
- [ ] **Abuse contact:** confirm `dial-tone@egyptianeyes.com` receives messages, has a named reviewer and an escalation route; `ai@dial-tone.uk` remains the general/privacy/security route.
- [ ] **Project attribution:** confirm "personal development space; being prepared as an Egyptian Eyes project" remains accurate, and do not imply a completed legal transfer or operational service.
- [ ] **Human review:** confirm copyright, GPL notices, public attribution and trademark usage; confirm maintainer privacy/security contact is authorised, the actual hosting operator and provider, access-log retention, and the relevant controller/processor arrangements. A verified contact and draft privacy notice are supplied, but the hosting facts cannot be inferred from the source.
- [ ] **Operational review:** confirm actual hosting access-log retention, privacy/controller arrangements, mailbox ownership and delivery, and the required legal review. These facts cannot be inferred from HTTP checks or repository code.
- [ ] **GitHub security reporting:** verify whether private vulnerability reporting is enabled in Settings → Code security. It is not claimed enabled here.
- [ ] **External validation:** an independent developer must follow the clean-install instructions without private maintainer knowledge.

## Later live calling gates, not blockers to publishing research source

- [ ] Real isolated Asterisk call and both media directions confirmed, with no PSTN egress.
- [ ] Telecoms-controlled cutoff independently observed after agent failure and timeout.
- [ ] Caller ID, recording/consent, abuse controls and territory policy approved for the actual use case.
- [ ] Real settlement, reconciliation, accounting and refunds verified before managed paid calls.

**Release labelling rule:** passing local source tests does not mean production acceptance. Preserve the "technical preview" warnings and never label real PSTN, settlement, model quality or real-world task outcomes as verified without independent evidence.

**Remaining owner actions:** verify private vulnerability reporting and mailbox delivery; inspect cPanel access-log and privacy settings; and review the updated workflow in a new hosted run before treating the current worktree as CI-verified. No mailbox delivery test or live-hosting configuration change is claimed.
