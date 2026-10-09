---
id: beliefs-cb2a39
title: Add a live arm for gather's observes-loop held filter
status: shelved
priority: 2
created: 2026-10-01T18:25:11Z
updated: 2026-10-09T11:14:11Z
depends: []
parent: beliefs-7e341d
tags: [n2]
agent: claude-code/claude-opus-5-5
---

From cut 44's final whole-branch review (mount-citations). In python/src/beliefs/evaluation.py, gather's observed-facet loop skips an observes target the view does not hold ('for target in stored.inputs_of(run_node, stored.OBSERVES): if not view.holds(target): continue'). Before cut 44, cut 22's B4b arm guarded the absent-dataset behaviour; cut 44 re-targeted B4b in test_n2_cut22.py's _LIVE_SABOTAGES to J21-a's mutation (removing the InputOutsideCorpus refusal), so no live arm now mutates this filter. It is still load-bearing on world views: an observed dataset held by an absent corpus is recorded in 'absent' by the input loop above, and this filter keeps the facet read from calling view.get on it. Add a live sabotage (e.g. drop the continue) to the highest live guard's _LIVE_SABOTAGES, with a check that evaluates over a world view whose observed dataset's corpus is absent and asserts NoBelief('unavailable-corpus-absent') rather than a raise. Done when test_arm_staleness and the new arm run sound.

## Notes

- 2026-10-09T11:14:09Z (main): shelved: The next cut that touches evaluation.py's gather (likely beliefs-918fd2, overlapping publications) plans its arms: add this as a ride-along arm whose check is test_world_view.py::test_an_absent_input_corpus_is_the_banked_reason
- 2026-10-09T11:14:09Z (main): scope: shelved; the portable suite already asserts the filter (test_an_absent_input_corpus_is_the_banked_reason evaluates the J20 split with the observed dataset's corpus absent), so only N2 arm evidence is missing; rides with the next gather cut; parented under beliefs-7e341d; brief: docs/notes/2026-10-09-mount-citations-follow-ups-brief.md
