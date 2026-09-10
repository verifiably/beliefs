---
id: beliefs-efc32d
title: The mm30 driver cannot rebuild target.yaml and reproduce unaided
status: done
priority: 2
size: m
owner: main
created: 2026-09-07T09:30:22Z
updated: 2026-09-10T21:47:43Z
depends: []
tags: [reproduction-finding]
---

The reproduction driver's end-to-end re-run during the verification-publication slice completed only after four analysis parameters were supplied by hand — value_row, value_row_symbol, group_separator, positive_level — taken verbatim from the already-frozen 2026-09-05 record. No driver step writes them; spec.py:47-49,101-102 consumes them and raises KeyError when they are absent.

So step 10b is proven to read the stored comparison report correctly ONCE TARGET SELECTION IS COMPLETE. It is NOT proven that the driver can rebuild target.yaml and reproduce end to end without foreknowledge of the answer. The 10b JSON from that run should not be cited as a clean end-to-end reproduction.

The gap belongs to the earlier target-selection/holding steps: select_target.py, type_target.py, hold.py. Note hold.py:54's 'driver correction' message covers a different failure (a non-regular held file) and is not a precedent for this one.

## Notes

- 2026-09-09T09:17:06Z (hygiene/n2-arms): pyright over tools/ (2026-09-09, not part of the gate) reports one live error here: select_target.py:56 keys lines by f.get('target'), which may be None, so an evidence line without a target is silently filed under None rather than refused - a fail-early gap in the same target-selection step this task owns.
- 2026-09-10T21:43:12Z (mm30-target-selection): 2026-09-10: the five keys (held_file, value_row, value_row_symbol, group_separator, positive_level) are now written by a new step 2a, tools/reproduction/analysis_inputs.py: symbol from the protein term, row via the crosswalk the dataset record's identity_context names, levels from the held file's header, separator and level order from a checked-in declaration (analysis-inputs.yaml) the header must agree with; the predecessor states these only in prose, so the declaration replaces the plan's by-hand append. select_target now refuses an eligible evidence line without a target (the pyright finding). Rebuilt target.yaml unaided into .work/reproduction/mm30-rebuild: identical to the frozen 2026-09-05 file.
- 2026-09-10T21:47:43Z (mm30-target-selection): step 2a analysis_inputs.py derives held_file, value_row, value_row_symbol, group_separator and positive_level from the selection, the dataset record's identity_context, the held file's header and the checked-in analysis-inputs.yaml; select_target refuses an eligible evidence line without a target. Rebuilt target.yaml unaided (identical to the frozen file, same spec identity 86aaa1a8) and ran the full path to clean-environment/passed/Admitted with equal 10a/10b; ledger in docs/plans/2026-09-10-mm30-reproduction-rebuild-run/
