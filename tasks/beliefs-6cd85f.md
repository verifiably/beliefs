---
id: beliefs-6cd85f
title: Participant-overlap evidence between datasets as input to independence certification
status: idea
priority: 2
created: 2026-10-18T19:19:51Z
updated: 2026-10-24T10:06:11Z
depends: [beliefs-9bf498]
parent: beliefs-8060d0
tags: []
agent: claude-code
---

Filed 2026-10-18 from the multiple-myeloma program. The kernel certifies independence pairwise from each dataset's lineage. The program has accumulated overlap evidence that lineage does not express: GEO series sharing GSM records (17 entries in 13 pairs), byte-identical CEL files across five UAMS series (3,108 sample records, 1,064 distinct arrays; GSE4204 and GSE4581 are complete subsets of GSE2658), nested cohorts (Immune Atlas inside CoMMpass), shared patient identifiers across series, and publication statements of overlap or disjointness. All of it lives in the program's roster.yaml as 19 overlap records plus assumed relations, read only by its reservation tool. Scope: a record kind or lineage link through which participant-level overlap between two held datasets (shared, nested, disjoint, with evidence) reaches the kernel's independence rule, so that two assessments on GSE24080 and GSE2658 are certified shared-source rather than not-certified. Related: beliefs-8ecbb5 (lineage-inherited standing, shelved).

## References

- brief (input, required, kind=brief): docs/notes/2026-10-24-confirmation-independence-brief.md — current seams, unresolved semantics and reused research
