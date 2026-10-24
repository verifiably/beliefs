---
id: beliefs-79d2ce
title: Is an admitted corpus absent from a session's mounts meant to be silently uncovered by every epoch?
status: idea
priority: 2
reviewed: true
reviewed_at: 2026-10-24T09:57:20Z
created: 2026-10-23T17:10:08Z
updated: 2026-10-24T09:58:25Z
depends: []
parent: beliefs-182296
tags: [publication]
source: sci-13050a
agent: claude-code
---

Found in science commons 1a: after adopt admits a publication, a session opened before the next config load does not mount it, and an epoch published from that session covers only the session's mounts. publication_preview and publish then evaluate selection completeness over that epoch, where selection.absent lists only covered corpora without a carrier (publish.py:345-347, world/view.py:341), so the admitted-but-unmounted corpus is neither covered nor absent and publish succeeds. The science commons spec had assumed publish refuses selection-incomplete naming it until reopen. Science accepted the kernel's behaviour (its publish freezes only the session's own view). Question: is a live admitted corpus outside every epoch the intended state, or should epoch capture or selection completeness consider admissions the session does not mount?

## References

- brief (context, kind=brief): docs/notes/2026-10-24-publication-session-follow-ups-brief.md — scope evidence and disposition

## Notes

- 2026-10-24T09:57:20Z (main): scope: drop; declared epoch coverage is deliberate: world-index packaging design sections 5 and 5.3 at 15b6e08, world/epoch.py:_declared_coverage and test_preflight_pins_a_sorted_carrier_mapping_and_never_substitutes_live_ids checked at 802286e; publication_preview is epoch-bound while live-query coverage reports absent live admissions; a later explicitly covered epoch can include the corpus, so every epoch overstates the limit; brief: docs/notes/2026-10-24-publication-session-follow-ups-brief.md; proposal: drop as answered by the existing declared-coverage contract; retain science's reopen-and-epoch guidance
- 2026-10-24T09:58:25Z (main): Evidence citation correction: the packaging design subsection describing outside-coverage unknown and the staleness bound is 5.4, not 5.3. The scope verdict and proposal are unchanged; the handoff uses the corrected citation.
