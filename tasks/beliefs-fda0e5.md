---
id: beliefs-fda0e5
title: "W8b at build: uid uniqueness is unchecked and a duplicate address is a ValueError, not a duplicate-location finding"
status: done
priority: 2
size: m
owner: fix/world-build-duplicates
created: 2026-09-09T12:01:40Z
updated: 2026-09-09T21:43:11Z
depends: []
tags: [world-read, conformance]
---

Measured 2026-09-09 on 197f517: epoch.build_epoch publishes two records at different addresses sharing one uid, and refuses one address held in two corpora with derive.address_map's bare ValueError instead of the duplicate-location finding W8b promises. Cut 23 does not select W8b; the view refuses uid ambiguity at open as its own half.

## Notes

- 2026-09-09T21:16:17Z (fix/world-build-duplicates): Claimed by /root, pid 2130612, for the bounded W8b build fix in fix/world-build-duplicates. Reproduce both violations against the banked contract; preserve frozen cut 23 evidence.
- 2026-09-09T21:24:15Z (fix/world-build-duplicates): Reproduced both defects on 6c32934: seven regression cases failed as expected (unchecked uid publication or bare ValueError). Shared derive.address_map now raises AddressMapConflict with the existing Finding envelope, distinguishing uid-corruption from duplicate-location before publication. 232 focused tests and root just check pass (zero errors/warnings); full root just test and independent review underway. Frozen cut 23 stays unchanged; W8b remains unselected.
- 2026-09-09T21:25:34Z (fix/world-build-duplicates): Independent code and documentation reviews are clean. Current docs record the build repair without selecting W8b; frozen cut 23 and its certified run artifacts are byte-unchanged. Root just test is the remaining validation gate.
- 2026-09-09T21:43:11Z (fix/world-build-duplicates): Final validation: root just check passed with zero errors/warnings; root just test passed 4224 Python tests in 1088.49 s and 142 TypeScript tests across 7 files, no failures or skips. Independent code and documentation reviews clean. Regression evidence includes shared/distinct uid duplicates, uid corruption taking priority, narrower coverage succeeding, and unchanged epochs/current with no publication plan after refusal.
- 2026-09-09T21:43:11Z (fix/world-build-duplicates): Build now refuses uid corruption and duplicate locations with distinct findings before publication; both root gates pass, and W8b remains unselected.
