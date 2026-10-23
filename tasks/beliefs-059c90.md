---
id: beliefs-059c90
title: admit_publication outside a session lets a corrupt copy escape as an untyped nodes/OS error
status: todo
priority: 2
size: xs
complexity: low
process: direct
created: 2026-10-23T14:00:58Z
updated: 2026-10-23T14:24:27Z
depends: []
tags: [publication]
agent: claude-code
---

publication_arrival.admit_publication reads ReadView.opened_at(root).iter_stored() and load_manifest(root) with no mapping, so a copy with an unparseable record or corpus.yaml raises NodesValidationError, PlacementError, CollisionError or OSError to a caller outside the session (the session doors now map the record read to PublicationReadingRefused("capture-damaged"), beliefs-f24fe9 fbdfc02). Map the same CAPTURE_DAMAGE tuple there, as _held_records already does, and decide whether load_manifest's failure maps to the same refusal; one test each. Seen by the beliefs-f24fe9 final review, declined there as out of scope.

## Notes

- 2026-10-23T14:24:27Z (main): Correction: load_manifest already raises typed ManifestMissing / ManifestMalformed (world/registry.py:500-509); only the record read is an untyped escape here. Leave load_manifest as is unless the API is normalized deliberately.
