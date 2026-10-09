---
id: beliefs-256f17
title: Design cross-root publication residue
status: shelved
priority: 4
size: l
created: 2026-08-31T00:38:28Z
updated: 2026-10-09T11:25:35Z
depends: []
tags: [migration, design, publication]
---

Outcome: Beliefs gains an approved rule for the cross-root provenance/report residue in T7 without creating an unguarded write path.

Acceptance evidence: Decide how a dataset provenance reference and acquiring report cross roots, where their durable identities live, how refusal and retry work, and how the result composes with existing act reports and publication; map the ruling to T7 and plan implementation only after approval.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `cross-root-publication`; `docs/designs/2026-08-11-act-report-design.md`; and `docs/guide/open-questions.md` The act-report's residue.

Uncertainty: Cross-root publication is currently refused and no acceptable authority or transport rule has been selected.

## Notes

- 2026-10-09T11:25:34Z (main): shelved: Wake when an operation must place a dataset's provenance reference or acquiring report in a root other than the one it writes: a science design that routes kernel acquire across roots, or a commons milestone that stops composing fetch from look plus a store write (science-commons §5 step 4)
- 2026-10-09T11:25:34Z (main): scope: shelved; T7's cross-root case stays refused and nothing needs it: science-commons §5 step 4 composes fetch from the holdings look and a store write and never from acquire, and its §11 kernel requirements name no cross-root act; wake condition recorded by shelve
