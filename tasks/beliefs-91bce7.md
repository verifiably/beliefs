---
id: beliefs-91bce7
title: "Annotations are not observations: a dataset of labels made by people or models must not bear on empirical belief"
status: idea
priority: 2
created: 2026-10-12T11:22:20Z
updated: 2026-10-14T01:35:07Z
depends: []
parent: beliefs-9396cf
tags: []
source: sun-08c8ea
agent: claude-code/claude-opus-5-5
---

G1 (docs/guide/foundations.md, 'The epistemic invariant') keeps literature out of belief: a source-assertion records what someone wrote, not the world, and has no belief-bearing edge. Annotations are the same kind of thing in data form and nothing yet says so. An annotation is a label or derived datum that a person or a model produced about observations: the detected coordinates and time bounds of an inferred solar event (HEK, DONKI, the LASCO CME catalog, GOES flare lists), the boundaries of a coding region in a genome annotation, a cell-type label from a classifier. Its bytes can be held, so today a run over a held annotation dataset yields an assessment that passes G1 as if it had been reproduced from primary observations.

The user's position (2026-10-12): annotations are predictions, like literature are things people believe, and must not touch the epistemic layer as evidence about the world.

Questions for a design:
- Where the distinction lives: a dataset kind or role (observation vs annotation), a lineage property (any annotation input in the closure), or both; and how a dataset that mixes measured values with labels (a flare list carrying a peak flux read from XRS) is classed.
- What an annotation carries: its annotator (person, team, or named detection module and version) as a required field, the way a source-assertion carries its source.
- What an assessment over annotations may bear on: plausibly propositions about the annotation process itself (a detector's agreement with another, a catalog's completeness) but not propositions about the observed system; or nothing at all.
- How this reads beside existing kinds: whether an annotation record is a sibling of source-assertion, and whether the nine dagger labels' 'leave the classifications as annotations' (docs/guide/open-questions.md) uses the word in the same sense.

The sun program has written the rule into its own framing (§4.3, 'Annotations are not primary data') and will meet the first worked case in its phase 2b characterization of event catalogs.
