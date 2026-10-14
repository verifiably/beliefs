---
id: beliefs-bbd142
title: "Decide whether the mm30 target's protein:PHF19 referent should name the gene, and correct it if so"
status: todo
priority: 3
size: s
complexity: mid
process: direct
created: 2026-10-14T15:30:18Z
updated: 2026-10-14T15:30:18Z
depends: []
tags: [reproduction, correction]
source: vdocs-9e9e89
agent: claude-code/claude-opus-5-5
---

Why: the mm30 reproduction's target, `proposition:concept-disease-stage-affects-protein-phf19` (docs/designs/2026-09-05-mm30-reproduction.md §2), relates `concept:disease-stage` to `protein:PHF19`, but the evidence is RNA: the Misund 2022 paired RNA-seq TPM matrix (`GSE179929_gene_tpm.txt.gz`), read on the gene row `ENSG00000119403`. So the claim names a protein while the analysis measures gene expression. The ecosystem overview's worked example (verifiably docs overview.md, "One building block", step 1) now asks "Does disease stage progression increase PHF19 gene expression in multiple myeloma?" but still describes the referent as "the protein PHF19", matching this record. That was left as-is when vdocs-9e9e89 reworded the question.

Known (from the record, 2026-10-14):
- The referent is inherited: the target was selected from the predecessor mm30 corpus's 334 proposition records, which include ten concept→protein `affects` records.
- Under the biology pack the target types as `mm30/affects-concept-molecular-entity`, and slot 1 (`biology/molecular-entity`) resolved `not-consulted` (§5, measured 2026-09-08). The slot may accept a gene as readily as a protein.
- The referent is part of the claim's identity, so changing it means a new proposition (a new claim identity and a re-run of the reproduction), not an edit in place.

Question: should the referent be the gene (for example `gene:PHF19`, or an HGNC/Ensembl-backed term), or is `protein:PHF19` defensible because RNA expression stands in for the protein? Is the same mismatch in the other concept→protein records?

Done: a recorded decision on this task. If the referent should change, open the correction: the new proposition and a re-run, or a follow-up task when that is larger than this one. Name the overview passage to update in verifiably docs. If it should stay, record why. In either case, update the record's prose where it is ambiguous.
Where: docs/designs/2026-09-05-mm30-reproduction.md §2, §5 and the biology pack design §6.4; the mm30 vocabularies under python/tools/reproduction/. If the correction re-mints identities across many records or needs a vocabulary change, switch to `--process planned` before continuing.
