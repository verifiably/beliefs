---
id: beliefs-bc3aff
title: "Deliver the domain boundary, biology pack, and second parity fixture"
status: todo
priority: 2
size: xl
created: 2026-08-31T00:38:27Z
updated: 2026-09-05T22:30:27Z
depends: []
tags: [migration, domain, parity]
spec: docs/designs/2026-09-05-facet-contracts-design.md
---

Outcome: Beliefs admits governed domain kinds through a compiled domain boundary, ships the GO/HP/EFO/MONDO biology bindings and mm30 operator vocabulary, and proves a second Python/TypeScript parity fixture.

Acceptance evidence: Design and freeze the domain cut; implement domain-pack compilation and refusal behavior without project-local suppressions; add the biology pack and second `science.identity.v1` parity fixture; discharge D1, D2, D4–D6, D8–D10 and G5; update current status; and pass the Python and TypeScript gates.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `domain-boundary` and `parity-fixture-2`; `docs/designs/2026-08-04-domain-extension-boundary-design.md`; and `docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md` §4.3 and §8 item 3.

Uncertainty: The domain contract is banked, but distribution/governance details and the exact biology bindings require the boundary's design cycle.

## Notes

- 2026-08-31T10:04:46Z (main): Rule 2.6 freezes the base profile until a second separately-evolved corpus exists, so the biology pack will carry fields that are really base-profile candidates. Mark each such field as a base-profile candidate when it lands (agreement/exercise met, reader present, second corpus absent) so later admission is a lookup, not an excavation.
