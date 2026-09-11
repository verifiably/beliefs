---
id: beliefs-b7994b
title: "World resolution slice 2b: source addresses derived from the normalized identifier"
status: done
priority: 2
size: l
owner: world-resolution-slice-2b
created: 2026-09-10T09:18:24Z
updated: 2026-09-11T13:26:44Z
completed: 2026-09-11T13:26:44Z
depends: [beliefs-113561]
parent: beliefs-d248ba
tags: [world-read]
spec: docs/superpowers/specs/2026-09-10-world-resolution-slice-2b-design.md
plan: docs/superpowers/plans/2026-09-10-world-resolution-slice-2b.md
---

Re-filed from beliefs-113561 on 2026-09-10 by the slice 2 design (docs/superpowers/specs/2026-09-10-world-resolution-slice-2-design.md section 1 and 12). W1, W2 and W5a rest on a source's address being derived from its normalized external identifier, which the world address ruling upholds (section 2 there) and the builder does not do: stored.source_node takes an authored slug, so two papers sharing a citekey collide at the world layer and two records of one DOI do not. Closing them needs a source re-addressing design with a per-scheme normalization rule (doi, pmid, isbn, accession), a choice rule where a source carries several identifiers, and an identifier-correction rename (address ruling section 4.4's mis-transcribed case: uid preserved, address renamed, old address in deprecated_ids). Measured 2026-09-10: 78 source_node call sites across 18 test files and 31 literal source: refs in tests; none in src. Shares no code with the coreference slice.

## Notes

- 2026-09-10T23:34:41Z (world-resolution-slice-2b): Design written 2026-09-10 (docs/superpowers/specs/2026-09-10-world-resolution-slice-2b-design.md): digest address under science.source-address.v1, fixed precedence doi>pmid>isbn>accession, canonicalize-and-refuse, correction attributed in an identifier-correction facet via a session-mediated corpus-write (no new operation kind: cut 19 J1e pins OPERATION_KINDS), consolidate refuses divergent histories, dataset re-addressing filed as a sibling.
- 2026-09-11T12:57:46Z (world-resolution-slice-2b): Slice 2b landed: derived source addresses, correct_identifier, cut 25 frozen at 50726094e7109dc9bad2754a85515580c8614127; W1, W2, W5a closed
- 2026-09-11T13:23:42Z (world-resolution-slice-2b): Reopened for final-review I1 coverage correction under Task 10; existing discharge retained, completion awaits supplemental live audit.
- 2026-09-11T13:26:44Z (world-resolution-slice-2b): Slice 2b complete after final-review I1/M1 correction: W1/W2/W5a closed, 25 live arms audited, original 24-arm freeze preserved.
