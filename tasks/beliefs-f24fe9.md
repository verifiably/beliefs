---
id: beliefs-f24fe9
title: Session doors and ledger evidence for the publish and sharing acts (science commons 1a)
status: todo
priority: 1
size: m
complexity: high
process: planned
created: 2026-10-22T22:44:06Z
updated: 2026-10-22T23:10:59Z
depends: []
tags: [publication]
source: sci-13050a
agent: claude-code/claude-fable-5-1
---

Science commons milestone 1a (science docs/specs/2026-09-30-science-commons-design.md §5, §7.4, §11; command framework §3.3 and §4.4 amendments of 2026-10-01) needs four things the kernel's session surface lacks today. (1) A constructible requirement for the sharing write class: RequiredCapabilities.sharing() whose permit names the families {lifecycle, registry} and no kinds, admitted like publishes() as a kernel requirement; today every permit naming lifecycle or registry outside _PUBLICATION_PERMIT is refused. (2) Doors on ScopedWriter for the sharing acts, under the scoped authority: restore a fetched copy (restore_root) and admit a publication (admit_publication over a World opened under that authority), each ledgered as a new 'sharing' line kind carrying the framework §4.4 amendment's evidence: corpus_id, marker uid, head artifact identity, the marker's world id, pin source, location fetched from, chain verification verdict, and the transition made; LedgerReader exposes the lines per invocation. The §7.1 comparison for this class is ledger-versus-registry. (3) A door for the publish act: ScopedWriter.publish(...) and resume_publish(...) run beliefs.publish with the scoped CorpusWriter, the session's coordination resolver and a World under the scoped authority, so the marker and binding commits reach the ledger as act lines; today publish takes a raw CorpusWriter and writes under writer._operation, which no session door reaches. (4) A public publication preview: the pre-intent computation publish runs (resolved view, selection, closure_missing, derived pins, attribution entries) as one function publish itself calls, so science's publish dry run shows exactly what the act would freeze and cannot disagree with it. Science's milestone plan consumes these four names; its tasks for publish, provider-bind and adopt wait on this.

## Notes

- 2026-10-22T23:10:59Z (main): From science's 1a plan review (2026-10-22): the sharing transitions are {bound, fetched, admitted, mounted, retired} (no 'inspected': inspection uses evaluate_copy and no door); a sharing line carries corpus, marker, artifact, world, view, source, location, verdict, transition, at; the publish door ledgers only the write-root records (binding, act report), since the marker lives in the publication corpus and science's ledger-rebuilt report reads configured roots. Question: resume_publish refuses an actor other than the intent's (session:<id>), so a stranded remote attempt cannot be resumed from a later service session; is a same-world resume across sessions intended, or does the pair stay blocked?
