---
id: beliefs-faf658
title: Cut 17 and cut 18 freeze-ancestry pins name commits no longer in history
status: done
priority: 1
size: s
owner: main
created: 2026-09-06T03:38:28Z
updated: 2026-09-06T10:59:39Z
depends: []
tags: [conformance]
---

tests/acceptance/test_n2_cut17.py pins IMPLEMENTATION_AMENDMENT_COMMIT a0f2302 and RENUMBERING_AMENDMENT_COMMIT 398491d; tests/acceptance/test_n2_cut18.py pins 2071be0/e9e592a. None is an ancestor of main (779fa7a) after a history rewrite (surviving twins b25fcc7, e6b8c0b), so test_the_frozen_cut_and_the_amendment_are_ancestors_and_the_frozen_sections_are_byte_exact and test_the_freeze_commit_and_sections_two_through_seven_are_pinned fail on main; addopts --ignore=tests/acceptance hid it. Every N2 arm audit of cuts 17 and 18 passes. Consequence: tools/cut18_acceptance.py (and cut 19's runner, whose prefix it is) cannot complete phase 1 end to end. Found by the writer-session lane (cut 19, Task 11) 2026-09-05; the fix is a re-pin to the surviving twins recorded as a dated amendment in each cut record, not a lane-local edit.

## Notes

- 2026-09-06T10:59:39Z (main): Re-pinned test_n2_cut17.py to b25fcc7/e6b8c0b and test_n2_cut18.py to c7d78f5/e0bc65c (the rewritten twins, matched by tree and author date); re-cited every rewrite-orphaned id in the cut 17 and 18 records, results and plans in place; dated citation amendments in write-permits design §17 and cut 18 §9
