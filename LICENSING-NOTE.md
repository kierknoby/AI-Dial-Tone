# AI Dial-Tone licensing and attribution

## Licence for the standalone public project

Original AI Dial-Tone program source in this repository is offered under the **GNU General Public License, version 3 or (at your option) any later version** (`GPL-3.0-or-later`). See [LICENSE](LICENSE) for the complete GPLv3 text.

Copyright © 2026 the individual AI Dial-Tone contributors, subject to their respective rights. This statement does not claim copyright over third-party works.

This scope includes original locally authored test clients, WebSocket/PCM peer laboratory, source generators, browser research code, and original public interface code in this repository, except where an individual file or bundled asset carries its own third-party licence or notice. Contributors must preserve those notices. Public API data formats and documentation availability do not imply that a private hosted calling service is licensed under GPL.

## Separate native Dial-Tone and MicroSIP project

The [EgyptianEyes/Dial-Tone](https://github.com/EgyptianEyes/Dial-Tone) native Windows project is a separate codebase derived from MicroSIP. Its inherited source headers permit GPL version 2 or later, and its original notices continue to apply there. **No native Windows/PJSIP source or assets are shipped in this repository.** This repository does not relicense, supersede, or alter any native source. MicroSIP, PJProject, and other third-party names remain with their respective owners.

## Private commercial telephone backend

The carrier, SBC, provisioning, x402 settlement, anti-fraud, and production call orchestration implementations are developed and distributed separately and **are not included** in this public AI subtree. Whether a future change creates derivative-work or distribution obligations depends on the actual code and integration, not the location of a Git branch. Do not copy MicroSIP/PJSIP GPL code into a proprietary component without a specific licence review.

## Agent integrations

GPLv3-or-later is aligned with the other FreePBX-related open-source projects. However, it imposes copyleft conditions on distribution of covered derivative works. Before offering an embeddable SDK that proprietary agent developers are expected to incorporate, evaluate a **separately licensed MIT SDK** with unambiguous source provenance. Do not state that an SDK is MIT until its own LICENSE and scope exist.
