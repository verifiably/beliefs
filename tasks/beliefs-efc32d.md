---
id: beliefs-efc32d
title: The mm30 driver cannot rebuild target.yaml and reproduce unaided
status: todo
priority: 2
size: m
created: 2026-09-07T09:30:22Z
updated: 2026-09-07T09:30:22Z
depends: []
tags: [reproduction-finding]
---

The reproduction driver's end-to-end re-run during the verification-publication slice completed only after four analysis parameters were supplied by hand — value_row, value_row_symbol, group_separator, positive_level — taken verbatim from the already-frozen 2026-09-05 record. No driver step writes them; spec.py:47-49,101-102 consumes them and raises KeyError when they are absent.

So step 10b is proven to read the stored comparison report correctly ONCE TARGET SELECTION IS COMPLETE. It is NOT proven that the driver can rebuild target.yaml and reproduce end to end without foreknowledge of the answer. The 10b JSON from that run should not be cited as a clean end-to-end reproduction.

The gap belongs to the earlier target-selection/holding steps: select_target.py, type_target.py, hold.py. Note hold.py:54's 'driver correction' message covers a different failure (a non-regular held file) and is not a precedent for this one.
