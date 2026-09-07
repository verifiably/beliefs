---
id: beliefs-d245a9
title: Decide the empirical-observation facet's payload contract
status: done
priority: 2
size: m
created: 2026-09-05T20:00:55Z
updated: 2026-09-07T15:18:58Z
depends: [beliefs-5f855c]
parent: beliefs-bc3aff
tags: [domain, reproduction-finding]
---

Finding from the mm30 reproduction record (docs/designs/2026-09-05-mm30-reproduction.md, §6, step 3; prediction P2 confirmed): is_empirical_observation reads presence only, so the driver's authored facet payload {boundary, source, asserted_by} was accepted unread, and nothing refuses a dataset that is not an observation. Owner: the domain lane (D1/D2 own facet compilation; kernel §11's open question). Deliverable: the payload contract as a dated amendment to the domain-extension boundary design, and the refusal the writer or the eligibility predicate makes on a payload outside it.

## Notes

- 2026-09-05T22:30:27Z (feat/domain-boundary): decided by docs/designs/2026-09-05-facet-contracts-design.md §2 item 2 and §6 (locator, attested_by, reserved retrieval; bearer invariant); lands with slice 1 of the domain lane, cut 20
- 2026-09-07T15:18:58Z (feat/domain-boundary): decided and enforced: locator + attested_by + reserved retrieval, validated at every seam (facet-contracts design §6, F1)
