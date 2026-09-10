---
id: beliefs-10d667
title: Correct session route refusal contract documentation and regressions
status: done
priority: 2
size: xs
owner: kernel-seams
created: 2026-09-10T01:50:47Z
updated: 2026-09-10T01:56:03Z
depends: []
tags: [session-routes]
source: .superpowers/sdd/2026-09-09-session-routes/final-review.md
---

Address the two final-review minor findings without changing production behavior: document assessment run refusal values and fulfilling-only pre-intent exclusions, and test the actual boundary.

## Notes

- 2026-09-10T01:51:00Z (kernel-seams): seams-final-fix: correcting final-review refusal contracts and boundary regressions; production behavior remains unchanged
- 2026-09-10T01:53:37Z (kernel-seams): science handoff correction: assessment permit failures return RunRefused(permit-exceeded) with no report, intent, or registration; holdings/corpus raise PermitExceeded. Pre-intent frozen-spec, input-heldness, and policy refusals hit forbidden execute on the fulfilling-only route and raise SessionProtocolError; surfaces must prevalidate, and future support requires an explicit intent/ledger amendment.
- 2026-09-10T01:56:02Z (kernel-seams): science handoff: assessment run permit failures return RunRefused(permit-exceeded) with report, intent, and registration all None; holdings and corpus permit failures raise PermitExceeded. The fulfilling-only route rejects pre-intent frozen-spec, input-heldness, and boundary-policy report publication with SessionProtocolError; surfaces must prevalidate, and future support requires an explicit intent/ledger amendment.
- 2026-09-10T01:56:03Z (kernel-seams): Corrected run refusal and fulfilling-only contracts; actual boundary and unheld-input regressions pass with zero durable calls
