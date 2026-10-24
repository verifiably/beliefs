---
id: beliefs-a91959
title: Belief policy distinguishes independent confirmation from a secondary analysis
status: idea
priority: 1
reviewed: true
reviewed_at: 2026-10-24T10:06:05Z
created: 2026-10-18T19:19:49Z
updated: 2026-10-24T10:06:05Z
depends: [beliefs-9bf498, beliefs-5e66ba]
parent: beliefs-8060d0
tags: []
agent: claude-code
---

Filed early from the multiple-myeloma program (its phase-1 protocol section 12 names this gap and planned to file it when phase 3 first needs it; filed 2026-10-18 while listing limitations for a talk). The program labels every confirmatory spec either 'independent confirmation' (runs on a reserved overlap group) or 'secondary analysis' (runs on data already exposed to the claim's selection, under a written justification). The kernel's belief counts every admitted assessment alike, so a belief read over the program's claims cannot tell a confirmation from a secondary analysis; today the label travels only in the spec's applicability and the report. Scope: whether the policy should read such a label (as an applicability field, a run-input role, or a new qualifier), and what a belief answer looks like when only secondary assessments exist.

## References

- brief (input, required, kind=brief): docs/notes/2026-10-24-confirmation-independence-brief.md — current seams, unresolved semantics and reused research

## Notes

- 2026-10-24T10:06:05Z (main): scope: briefed; checked against 18d5a35 and acceptance commits e7b1193/0cbfa7d: current caller-pinned acceptance can select evidence but supplies no built-in confirmation label or secondary-only reason. Preserved original body, priority and source; reused aggregation goal beliefs-8060d0 and research beliefs-9bf498/beliefs-5e66ba with recorded waits and completion wake notes; brief: docs/notes/2026-10-24-confirmation-independence-brief.md. External protocol remains unverified in this fixed checkout.
