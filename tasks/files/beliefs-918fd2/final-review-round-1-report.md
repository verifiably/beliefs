# Final whole-branch review — cut 48 (round 1)

Reviewer: claude-code/claude-fable-5-1 (fresh subagent, read-only), 2026-10-28. Range 11f6bb2..60a43ff.

## Review of conformance cut 48 (`design/918fd2-overlapping-publications`, 11f6bb2..60a43ff)

Read in passes: (1) the spec in full (§§1–12) and the plan's headings, Review Focus and task interfaces; (2) the product diff for `world/derive.py`, `epoch.py`, `registry.py`, `read.py`, `live.py`, `selection.py`, `view.py`, `rules.py`, `root.py`, `rules_v1/retraction_v2.py` and its eight fixtures, `evaluation.py`, `audit.py`, `publish.py`, `errors.py`, `corpus.py`; (3) the pinning tests for each Review Focus item, the four extended checks, G14-c/d/f/h, Y19-c/d/e, J17-c, `TestTheSplit`, the N2 declaration and guard, the 1b fixture's header and case list; (4) the results record, ledger, roadmap, designs index, cut document header, backlog-brief amendment, the task records the spec's §12 names, and the science checkout for consumers of changed APIs. I ran the five focus tests plus `TestW19MultiHolderMap` and `test_world_rules.py` (98 passed) and one micro-benchmark of `content_identity` from the scratchpad; nothing in the checkout was written. The checkout's HEAD (7e6b1bb) is one task-note commit past the review head; the source tree is identical.

### Strengths

- **Derivation order is exactly §4.2 and order-independent by construction.** `derive.address_map` checks uid-corruption over the whole capture first, groups canonical claims by address and refuses on any content disagreement (never by uid, never by first claim), and the deprecated-key rule compares `held != entry` against the already-complete live map, so a live/deprecated collision is caught in both input orders and a key reached through two holders of one record is one entry. `_derived_members` derives the map before any rule runs, so the typed refusals keep precedence over `RuleNonconformant`.
- **The v2 rule is pure, versioned and honest about its domain.** `retraction_v2.py` imports nothing, resolves node-arm targets over live and deprecated ids across corpora, treats route/snapshot arms as vertices, folds in acyclic postorder with cycle detection, and ignores the per-corpus resolution. The input version is a property of the held rule (`RuleBundle.input_version`, two closed `rule.yaml` shapes, a three-member identity only for a declared version, so no v1 identity moves), read at build (`_BuildDraft.run`) and validation (`_rebuilt_receipt`) alike; the fixture-schema check lives on the running half and `remove_rule_binding` stays untouched. `test_every_shipped_fixture_carries_a_captured_view` pins the key set per version.
- **The served surface is one coherent model.** `open_world_view`'s three checks (carrier holds the mapped uid and maps back naming the holder; captured copies agree with each other; a shared uid is admitted only where the map established it) and `resolve_address`'s per-holder read with the damaged/faulted rule both implement §5.1/§5.3 literally, and `_refuse_damaged` is the one place the epoch's `content` is read, as §4.3 says. `corpus_of` is a label, `holders_of`/`captured()`/`_mapped_holders()` are the holder-set readers, and every §5.4 caller was moved (I checked each row).
- **Correction standing folds once in all three places.** `_check_filtered_world_standing` is one comparison against gather's own map-only fold with the explicit two-resolutions refusal; `snapshot_standing` merges with a self-check that mirrors the map's classification between holders and returns `unresolvable` plus the conflict's finding through `_snapshot_standing`/`reported_receipt`; the per-corpus capture boundary is untouched.
- **Attribution is order-independent by construction.** Claims are a set per ref, the least element is computed over sorted claims with `_supersedes` on `(origin corpus, marker uid)` pairs, idle replicas' markers are read only when rule 3.3 is reached, and Y19-e proves both orders on the frozen tuple.
- **Testing discipline is strong.** RED→GREEN recorded per task, pre-passing pins declared rather than hidden, every retarget proved by kill in its owning guard, the four check extensions assert the row's own behaviour more directly (W19-c's differing third claim, W20-a's shared run with a relation, W20-g's addresses-only query, W20-i's cross-kind finding) and are honest. G14-f covers all four merge refusals in both holder orders through `validate_receipt` and `reported_receipt`. The 1b fixture exists on the certified tuple with eight cases including the chain-gap/retention pair and the receipt-path merge refusals.
- **Science's side is filed, not made.** sci-73c80e exists in the science checkout (3d1c624) with §8 verbatim; the science tree uses none of the changed kernel APIs except `SYMBOL_FIELDS`, which the task names. Ledger, roadmap, designs index, README, guide pages and the backlog-brief amendment are consistent (230 of 257, cut 48 current, lane closed).

### Issues

#### Critical (Must Fix)

None.

#### Important (Should Fix)

1. **`snapshot_standing` now pays a canonical-JSON digest for every record on every call, which `gather` makes once per evaluation under a policy.** `corpus.py:1240` (`_merged_capture`) computes `content_identity(node)` for every record of every holder before grouping; `view.py:231` returns an uncached fold whenever `counts` is given, and `evaluation.py:406` calls it on every `gather`. Measured on this checkout: 274 µs per node, so ~2.7 s per 10,000 records *per proposition evaluated with a policy*; the 1b decisive case (`accept = [B]`) is exactly the policy path, so science's `belief`/`explain` over a mid-sized world slows by seconds per call. It also contradicts §4.5's "a one-holder caller is unchanged": a single-corpus `snapshot_standing` caller now digests every record for a check that can never fire. Fix: group claims first and compute `content_identity` only inside the per-address loop when `len(held) > 1` (the content set is only consulted there); that removes the cost for every singly-held record and for every one-holder caller, and keeps the self-check exact. Optionally thread the view's already-computed `_contents` through for the world path.

#### Minor (Nice to Have)

2. **Dead variable shaped by a mutation.** `audit.py:810` `corpus_id = targets[0]` is never read after the rewrite (only `unreachable.corpus_id` follows). It survives so W20-i's frozen `after` text (`corpora[corpus_id].extend(found)`) still parses. Removing it would leave the arm sound (the mutation then kills by `NameError`, which is weaker evidence), so the choice is between a dead name in product code and a weaker arm in a frozen declaration; I'd remove it at the next cut that retargets W20-i and note it in the ledger now.
3. **`content` is checked as text at open but as 64 lower hex at read.** `epoch.py:778` admits any non-empty string; `read._address_map` then constructs `AddressEntry`, whose `__post_init__` raises a bare `ValueError` outside the `EpochMalformed` wrapper. Likewise `derive.py:521` will serialise `content: None` for a re-projected legacy entry, producing a member the next open refuses. Both are unreachable through the kernel's own writes (packaging identity guards the member), so Minor: add `_require_lower_hex` to `_check_addresses` and refuse `None` in `address_map_projection`.
4. **The W20 row's "including for a legacy entry" is pinned only structurally.** W19-e asserts `AddressEntry(uid, None, (holder,))`; the behavioural consequence (a legacy entry's damaged single holder refuses) rests on the single-holder path, which Task 2's ruling 3 correctly says is the only reachable one. A one-line test driving `_refuse_damaged` with `content=None` and one damaged, one captured holder would make the fail-closed branch a tested branch rather than an unreachable one.
5. **Disagreement message may name an alias.** `view.py:455` reports the first key in `sorted(recorded.items())` for the uid, which can be a deprecated id rather than the live address. Use `node.id` of a present copy.
6. **v2 does not refuse uid-corruption itself.** `retraction_v2.py:36` lets the last record win for `live_of[uid]`; at build the address map runs first, but `_rebuilt_receipt` reruns the rule over a recapture without it, so a uid-corrupted drift validates as `refuted` rather than naming corruption. Same as v1 today and within the spec's two named refusals; a third `ValueError` would make the rule's docstring ("two inputs are not worlds") complete.
7. **One constant, two spellings.** `derive.py:410` hard-codes `"science.rule-input.v2"` while `rules.RULE_INPUT_V2` is the exported name (presumably to avoid a `derive`→`rules` import); a shared constant module or a comment naming the reason would stop the two drifting.
8. **Spec §12's record actions are not reflected.** beliefs-354eae is still `todo` with no cut-48 note although §4.2 says this cut absorbs it, and beliefs-0e1acb carries no dependency or note sequencing it after this cut. These are task-record edits, not code; the plan did not assign them and the rulings do not mention them.
9. `_CapturedCitations._holder` (`audit.py:647`) now labels a holder with neither a recorded cause nor a readable view `unreadable`; previously that path returned `None` silently. An improvement, but the label is invented rather than observed; `no-capture` would say what happened.

### Review Focus, checked against the code

1. **Legacy beside rebuilt:** `_check_addresses` picks the shape from the first entry and `_entries` enforces that exact key set on every entry, so a mixed document is `EpochMalformed` under `_locked_open_epoch`'s wrapper; `read._address_map` reads both shapes; `resolve_address` serves a legacy entry with no faults and refuses on any fault since `entry.content is None`. W19-e exercises all three. Correct.
2. **Three holders, two agree:** `open_world_view` builds `present` over all captured holders of the uid and refuses when the content set has two members, naming `tuple(present)` (all three) and raising before any view object exists; `resolve_address` does the same over `readable`. W20-b asserts all three ids. Correct.
3. **Colliding route identity:** `retraction_v2` sets `target = None` for any non-node arm, and `corpus.retraction_standing` skips non-node arms before resolving, so neither adds an edge whatever the string resolves to; the fixture `colliding-route` and G14-i's gather clause both pin it. Correct.
4. **P1 and P7 with P3 retired:** claims `(r,P1,m1)` and `(r,P7,m7)`; `_held_supersession` has no key for the retired P3, so `_supersedes((P7,m7),(P1,m1))` stops at `(P3,m3)` and returns False; `least` is empty → `attribution-ambiguous` with both claims in `field`. With P3 held the walk reaches `(P1,m1)` and `least == [(r,P1,m1)]`. Y19-d and Y19-c pin both. Correct, and the 1b fixture's `test_chain_gap_refuses_and_retention_resolves` covers it durably.
5. **v1-bound epoch, counter split by policy:** `_check_filtered_world_standing` refuses on `receipt.setdefault` disagreement before any affected-set reasoning, independent of sort order and of whether the ref is affected; G14-g asserts the "two resolutions" detail and the no-policy refusal. Correct.

### Ledger rulings

All 24 `Ruling:` lines read. None I would overturn. Three I checked specifically: Task 2's untested legacy damaged branch (correct that it is unreachable from a legacy document; see Minor 4); Task 4's "self-check between different holders only" (spec §4.5's exact words, and the corpus index covers the rest); Task 5's `_held_supersession` requiring an admission (the spec's "captured undeclared `ReplicaOf` holder" cannot be classified without one). Task 7's ride-along re-homing is sound and recorded in the results; the pre-passing pins are declared and each is killed by its arm.

### Declined to judge

- The owners-check text "corruption, not a record with two homes" (`view.py:473`) now also fires in the ordinary 1b state between `adopt` and the next rebuild; spec §5.1 mandates the existing text, so I set it aside (recommendation below).
- `remove_rule_binding` leaving an empty rule directory: pre-existing, ruled in Task 3.
- Per-holder duplicate filing of audit findings: spec §5.4's explicit ruling.
- Legacy epochs staying singular and v1-bound until rebuilt: spec §10.6.
- A rejected copy listed in `excluded` beside an accepted twin: spec §6's intended report; the wording is science's (sci-73c80e).
- `_HeldRule.input_version` defaulting to `None` positionally: spec §4.5's compatibility requirement for the holdings bundle.
- The checkout's HEAD being one note commit past the review head: records only, no source change.

### Recommendations

- Apply the lazy content computation in `_merged_capture` (Important 1) and re-run G14-e/f and `test_standing_read.py`; no frozen arm text touches those lines.
- When a future cut retargets W20-d, give the owners-check refusal a second clause for the established-but-stale case ("rebuild to publish the new holder") since that is the state 1b produces by design.
- Close beliefs-354eae with a note citing cut 48 §4.2 rule 3 and add the sequencing note/dependency on beliefs-0e1acb (Minor 8).
- Add `_require_lower_hex` to `_check_addresses` and a `None` refusal in `address_map_projection` (Minor 3).

### Assessment

**Ready to merge?** With fixes

**Reasoning:** The implementation matches the spec's decisions and the plan's interfaces in every case I traced, the proofs are honest and complete, and the documentation is consistent; the one Important finding is a measurable per-evaluation cost regression in `snapshot_standing` that a one-condition change removes without touching any frozen arm.

claude-code/claude-fable-5-1
