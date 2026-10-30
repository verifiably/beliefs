---
id: beliefs-9cbde6
title: Assess the independence assumption in mm30’s documented unpaired comparison of paired inputs
status: todo
priority: 3
size: s
complexity: mid
process: direct
created: 2026-10-30T12:06:02Z
updated: 2026-10-30T12:06:02Z
depends: []
tags: []
source: "sci-b2755f:pilot:sample-independence"
agent: codex
origin: agent
---

Why: the assumption-sweep pilot on sci-b2755f identified a tension between the frozen mm30 spec's "independent samples" assumption and the roster's description of GSE179929 as paired diagnosis/progression data. Reading [ref:reproduction-record] §§2 and 10.1 confirms this is a documented, intentional unpaired two-group rank comparison over a paired source, chosen as a one-file, standard-library kernel measurement rather than the predecessor's paired trajectory statistic. This investigation must preserve that engineering intent and distinguish it from suitability for scientific reuse; it is not a newly established implementation defect or a selected field-wide research priority.

Question: does the stated sample-independence assumption have support for the units actually intended by this estimator, what scientific interpretation does the recorded comparison support, and what minimum clarification or separate analysis would be needed before reusing it as biological evidence?

Read [ref:reproduction-design] and the record's scope first. Inspect python/tools/reproduction/spec.py and python/tools/reproduction/analysis/assoc.py, the exact recorded spec/input identities, and permitted study-design/sample-unit metadata. The pilot's evidence is in sci-b2755f attachments discovery-inventory-v1.md and pilot-v1-report.md §§5–6 (frozen report revision cc203e4); its retained worktree/inputs are named in that task's park and retention records. Do not assume a roster flag establishes which actual samples the frozen input/run included.

Bound: initially metadata and code only, under mm's current exposure/reservation policy. No patient identifiers/rows, expression or outcome values, protected results, new data acquisition, biological analysis, rerun, world write, frozen-spec edit or kernel change. If exact unit inclusion cannot be established through permitted metadata, record it as unknown and identify the needed evidence/read authorization rather than silently broadening the read. Use authoritative statistical sources when assessing the method's assumptions; counts or the observational identification label alone do not establish independence.

Done when the task records: (1) exact spec/input/estimator revision and documented engineering intent; (2) established versus unknown unit/visit facts with sources; (3) an explicit assessment of the independence assumption and its interpretation limits; and (4) the smallest recommended disposition, such as documenting the limitation or proposing a separately governed paired analysis. Any resulting correction/reanalysis is separately scoped; do not carry it out here or retrospectively rewrite the historical measurement.

Related but distinct: beliefs-bbd142 owns gene-versus-protein referent semantics; mm-af6b59 owns reservation-preserving cross-cohort participant matching. Neither currently assesses this within-analysis unit assumption. No existing closed task is declared defective by this filing.

## References

- reproduction-record (input, required, kind=record): docs/designs/2026-09-05-mm30-reproduction.md — engineering scope, paired inputs and intentional unpaired estimator
- reproduction-design (input, required, kind=spec): docs/superpowers/specs/2026-09-05-mm30-reproduction-design.md — original measurement intent and boundaries

## Notes

- 2026-10-30T12:06:02Z (add): created
  provenance: {"harness_session":"codex:01a18c50-32b0-7103-beae-7c810e393c5c","harness_session_source":"CODEX_THREAD_ID","origin":"agent"}
