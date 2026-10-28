# Conformance cut 48 — overlapping publications

**Status:** frozen 2026-10-28 before product implementation; not yet discharged.
**Spec:** `../superpowers/specs/2026-10-28-overlapping-publications-design.md`, accepted at `e14315c`.
**Plan:** `../superpowers/plans/2026-10-28-overlapping-publications.md`, revision 4 at `a125fa6`.
Successor to cut 47; all refs and worktrees were rechecked before choosing 48.

## 1. What this cut is

A world may hold one address in several live corpora when the copies have equal
content identity (`science.node-content.v1` over the canonical projection, the
member `corpus_state_identity` already computes): the address map becomes
multi-holder, every world read serves the record once and labels it by its least
present holder while reading the holder set wherever the answer depends on it,
belief acceptance is a union over holders that still reports every holder's
decision, and a republication attributes a multi-holder record by own holder,
then agreeing carriers, then the earliest origin in the held supersession order,
else refuses `attribution-ambiguous`. Differing content still refuses
`duplicate-location` with `consolidate` as the exit; `uid-corruption` is
unchanged and first. Correction standing is folded once, at derivation in a
successor `retraction-enumeration` rule (v2) over a versioned rule input that
carries each retraction's arm, with v1 untouched; snapshot standing and the
filtered fidelity check fold once over the merged holders after record-level
acceptance. This is science commons milestone 1b's precondition
(`beliefs-81367e`, `sci-9104fb`); the brief is
`../notes/2026-10-09-overlapping-publications-brief.md`.

## 2. The boundary

`overlapping-publications` reopens `world-read`: `world/registry.py`
(`content_identity` exposed), `world/derive.py` (`AddressEntry`,
`CapturedRecord.content`, `CapturedRetraction.arm`, `rule_input(version)`),
`world/epoch.py` (`_check_addresses`' two closed shapes, `_captured_records`'
two new fields on untouched lines, `_BuildDraft.run`'s dispatch,
`_derived_members` deriving the address map before the rules), `world/read.py`
(`Location.holders`, `resolve_address`, `_address_map`, `validate_receipt`'s
dispatch and `unresolvable` outcome, `_snapshot_standing`, `reported_receipt`),
`world/view.py`, `world/live.py`, `world/selection.py`, `world/rules.py`
(`RuleBundle.input_version`, two closed `rule.yaml` shapes, the v2 identity
formula, `_HeldRule.input_version`, the raise wrap, the fixture-schema check at
install and resolution only), `world/rules_v1/retraction_v2.py` and its
fixtures, `evaluation.py`, `audit.py`, `publish.py` (`_selected_attributions`),
`corpus.py` (`MountCitations`, `snapshot_standing`, `_absence_of`, the
coreference endpoint refusal), `errors.py` (one new `PublicationRefused` reason
text), and `root.py` only for its shipped-bundle docstring. Shared surfaces under
roadmap rule 3: `corpus.py`, `evaluation.py`, `audit.py`, `errors.py`, the
ledger, the roadmap and the designs index. No format, contract release, world
configuration, permit, write primitive, dependency or TypeScript change; the
holdings reduction bundle and its receipt path do not change.

## 3. Selection

W19, W20, G14 and Y19 are new rows; J17 and J20 are reclosed under their
amendments; W8b, G10, G12, Y5 and Y17 are reclosed by retargets and carry no new
unit. The refusal orders this cut fixes: the derivation refuses `uid-corruption`
over the whole capture, then groups canonical claims per address by content
identity (any difference is `duplicate-location` naming every claim), then folds
deprecated keys (a collision is the typed `ResolutionRefused`); `_derived_members`
derives the address map before any rule runs. At open, every captured holder
must hold the mapped uid, then captured copies of one address must agree with
each other; a damaged holder is skipped only when every captured copy equals
the mapped `content`. Attribution runs own holder, then agreement, then the
unique claim every other claimed marker supersedes (markers of non-selected
undeclared replica holders read only then), then `attribution-ambiguous`
carrying the claims. `address-map.yaml` entries are closed on
`{address, content, holders, uid}`; the legacy `{address, corpus_id, uid}` is
admitted as a second closed shape and never mixed. `rule.yaml` admits `{symbol}`
and `{symbol, input: science.rule-input.v2}` only; the per-version fixture schema
is the retraction member's key set.

Each unit below names `test_<unit lowercased, hyphen to underscore>_<suffix>` in
the module given. Parameter cases stay within one unit; durable tests add
evidence, not units. Every sabotage site is kernel code that stays importable;
none is in rule bytes.

| Unit | Module | Suffix / decisive behavior | Independent mutation site and responsibility |
|---|---|---|---|
| W19-a | `test_world_derive.py` | `equal_content_reads_once`: two and three corpora map one entry with sorted holders, either capture order | `address_map` per-address grouping: refuse every multi-claim address |
| W19-b | `test_world_derive.py` | `differing_content_refuses`: shared uid with differing content, and distinct uids, refuse `duplicate-location` naming every claim | `address_map` content comparison: group claims by uid instead of content |
| W19-c | `test_world_derive.py` | `corruption_outranks`: one uid at two addresses refuses `uid-corruption` before any duplicate, both orders | `address_map` loop order: check addresses before uids |
| W19-d | `test_world_derive.py` | `deprecated_key_entry`: one entry through two holders; a key colliding with a live or differing record refuses typed `ResolutionRefused`, both orders, same and cross corpus | `address_map` deprecated fold: keep the first claimant of a key |
| W19-e | `test_world_read.py` | `epoch_shapes`: the new shape is written; the legacy shape reads as singleton holders with `content=None`; a mixed document refuses `EpochMalformed` | `read._address_map`: read a legacy entry as the new shape |
| W19-f | `test_world_derive.py` | `discovery_once`: a retraction held twice is discovered once | `retraction_discovery_map`: collect refs as a list |
| W19-g | `test_live_selection.py` | `live_map_holders`: over two corpora holding one record with equal content, `evaluate_live_query` selects it once with `contributing` naming both holders, and with differing content refuses `AddressMapConflict("duplicate-location")`; Z5-a/b/c behaviour unchanged | `live._address_map`: drop content from the live capture |
| W20-a | `test_world_view.py` | `view_serves_once`: `get`, `resolve`, `inbound` (one edge per relation) and `Location.holders` over equal-content holders | `open_world_view` inbound construction: build edges per holder |
| W20-b | `test_world_view.py` | `holders_disagree_refuses`: a captured copy that differs after the epoch refuses `ResolutionRefused` naming every holder, never `NotPresent` | `open_world_view` agreement check: serve the least holder without comparing |
| W20-c | `test_world_selection.py` | `absence_over_holders`: `NotPresent` only when every holder is absent; `Resolved` with one present; `_require_located` lists every absent holder; `Unresolved.corpus_id` is the least | `WorldReadView.locate`: not-present when any holder is absent |
| W20-d | `test_world_view.py` | `owners_check_narrowed`: a map-established shared uid opens; a raw-written unmapped shared uid still refuses with the existing text | `open_world_view` owners check: admit every shared uid |
| W20-e | `test_world_view.py` | `damaged_holder_rule`: served when every captured copy equals the mapped `content`; refuses `CorpusDamaged` naming the damaged corpus for a legacy entry or a differing copy | `_refuse_damaged`: skip the damaged holder without the content comparison |
| W20-f | `test_world_read.py` | `resolve_address_holders`: per-holder uid rule, unreadable-holder skip against `content`, disagreement refuses, `holders=readable` | `resolve_address`: resolve through the first carrier only |
| W20-g | `test_world_selection.py` | `contributing_union`: `contributing` names every captured holder of a selected record; disagreeing pins refuse `pins-disagree` | `_denoted`: keep the last holder per record |
| W20-h | `test_world_view.py` | `mapped_view_and_absence`: `_mapped_view` sees the record under each holder; `_absence_of` and the coreference endpoint name the least holder only when all are absent | `_mapped_view`: filter by `holder == corpus_id` |
| W20-i | `test_world_audit.py` | `audit_files_per_holder`: a finding is filed under every captured holder; `_CapturedCitations._holder` reads the first readable holder and is unreadable only when none is | `audit_world` recomputation loop: file under the canonical holder only |
| G14-a | `test_acceptance.py` | `union_over_holders`: an assessment rejected under one holder, accepted under another: read once, counts, attributed to the accepting holder, rejected pair in `excluded` | gather's assessment loop: stop at the first holder's decision |
| G14-b | `test_acceptance.py` | `rejected_everywhere_inert`: a verification rejected under every holder is inert and every pair reported | gather's verification loop: accept regardless of the decisions |
| G14-c | `test_acceptance.py` | `predicate_per_holder`: a retraction held in two corpora, rejected under the least holder and accepted under the other, takes effect in gather's retraction loop; the per-holder call count and per-pair caching are supporting evidence | gather's retraction loop: ask only the canonical holder |
| G14-d | `test_acceptance.py` | `filtered_graphs`: R and C in *A*, R in *B*, policy rejects C: R upheld, fidelity passes with C's rejection reported; C accepted: R overturned; both hold R and C, C accepted through *B* only: R overturned | `_check_filtered_world_standing` affected-set walk: skip the transitive parents |
| G14-e | `test_snapshot_retraction.py` | `snapshot_merged_fold`: both hold snapshot-arm R and counter C, C accepted through *B* only: not retracted; one history chain `((C, upheld), (R, overturned))`; both holder orders; with R in *A* only and C in *B* only, C's target resolves and validates across holders and R is overturned | `snapshot_standing` acceptance: decide `counts` per holder inside the fold |
| G14-f | `test_standing_read.py` | `merge_self_check`: through `validate_receipt` and `reported_receipt` directly, two copies of one uid with differing content, with differing addresses, and one id under two uids, both orders: `unresolvable` with the conflict's finding, never `retracted` | `snapshot_standing` merge: collapse by uid without the classification |
| G14-g | `test_acceptance.py` | `filtered_fidelity_one_comparison`: one comparison against gather's fold; two recorded resolutions for one ref refuse explicitly | `_check_filtered_world_standing` receipt lookup: keep the last recorded resolution per ref |
| G14-h | `test_world_rules.py` | `v2_rule_binding`: `rule.yaml` shapes, identities, `input_version` dispatch at build, validation and fixture run; a v2 bundle with a fixture lacking `arm` refuses at install; the same pair raw-written, correctly named, refuses at resolution and is then removable (the report's `binding` and `severed_receipts`, every member gone) | `_BuildDraft.run`: hand a v2 rule the v1 input |
| G14-i | `test_world_standing.py` | `v2_fold_world`: v2-bound build over R,C/R publishes one `(R, overturned)` either order with one receipt identity, `validate_receipt` validates, `gather` agrees; v1-bound publishes both pairs; R,C,D/R,C says `upheld`; the moved counter is overturned; the colliding route adds no edge in `gather`; a raw-written counter cycle across holders refuses `RuleNonconformant` through the wrap; a capture with one address under two distinct uids refuses `AddressMapConflict`, not the rule | `_derived_members`: run the rules before the address map (killed by the distinct-uids precedence case) |
| Y19-a | `test_publication_attribution.py` | `own_wins`: an own holder beside a carried copy yields no entry | `_selected_attributions` rule 3.1: prefer the carried claim over own |
| Y19-b | `test_publication_attribution.py` | `carriers_agree`: two carriers with one triple forward it | rule 3.2: refuse any two carriers |
| Y19-c | `test_publication_attribution.py` | `earliest_origin`: P1/P3; re-adopted own P2 beside them; a third party holding P2 and P3; sibling tips over P1; P7 → P3 → P1 read through P3's marker only when rule 3.3 is reached; an idle replica's invalid marker refuses `attribution-source-invalid` naming it with empty `refs` only then | rule 3.3: order holders' markers instead of claimed markers |
| Y19-d | `test_publication_attribution.py` | `ambiguous_refuses`: unrelated origins, and a chain with its intermediate unheld, refuse `attribution-ambiguous` carrying the claims, nothing written | rule 3.4: pick the lowest claim on disagreement |
| Y19-e | `test_publication_attribution.py` | `order_independent`: over captures and admissions supplied in both orders, arranged so the two orders put different replica holders first, `_selected_attributions` yields equal tuples | rule 3.3's selection: take the first replica holder's claim in `registry.admissions` order instead of the least element |
| Y19-f | `test_publication_attribution.py` | `v2_narrowing`: v2 names only holders of carried records; an own-made record needs no source | the v2 refusal's holder set: name every replica holder |
| J17-c | `test_mount_citations.py` | `citation_equal_content`: two session corpora holding equal content resolve once with every mount's contract checked; differing content refuses naming every holder | `MountCitations._one`: return the first holder's view without comparing |
| J20-b | `test_acceptance.py` | `node_corpus_holder_set`: an assessment, a run and an observed dataset held in two corpora are attributed to both holders without a policy and to the accepting holders with one | gather's attribution sets: add only `corpus_of`'s label instead of the holders |

Each arm must fail at its named assertion, not a collection, syntax or unrelated
guard error; a check that drives a build or a publish wraps it so the failure
lands in the named assertion. `CO_CITED = ()`.

Live-table arm beside the declaration, not counted: beliefs-cb2a39's ride-along,
a sabotage dropping the `continue` on an unheld observed target in gather's
observes loop, with the check
`test_world_view.py::TestEvaluationOverTheWorld::test_an_absent_input_corpus_is_the_banked_reason`.

Evidence the spec requires beside the units, uncounted: one producer edge, one
certification ref and one coreference unit from a record held twice
(`test_receipts_fold_a_record_held_twice_once`; the three folds are rule bytes,
so they have portable test evidence and fixture equivalence, not independently
counted mutation arms, as the spec's dated §4.2 note records); v2's refusals over
the shipped bytes; the v2-to-`retraction_standing` equivalence over every fixture
in both input orders; the closure-digest invariance for a world with no split
under v1 and v2; the rewritten `TestTheSplit` with its v1-bound twin; and the 1b
fixture end to end (`test_overlapping_publications_acceptance.py`).

## 4. Accounting

**33 arms, 33 declaration units, six exercised rows**: W19 (7 units), W20 (9),
G14 (9), Y19 (6), J17 (1), J20 (1). Four newly closed rows (W19, W20, G14, Y19);
J17 and J20 reclosed under their amendments; W8b, G10, G12, Y5 and Y17 reopened
at freeze and reclosed by retargets. Four rows join the corpus: 257 rows. Freeze
is 219/257 closed, 38 open (seven reopened); successful discharge is 230/257
closed, 27 open. Recent-runner entry is (33, 33, 6):
`guarantee rows exercised: 6 (4 newly closed: W19, W20, G14, Y19; J17 and J20 amendments reclosed)`.

## 5. N2 and acceptance obligations

Each unique responsible mutation must parse, its baseline must pass and its named
assertion must fail under sabotage. Collection/syntax failures prove no kill.
Canonical declarations are content-pinned when created; this body's §§2–7 freeze
before implementation. No prior check node is reclaimed or co-cited. Preserve all
prior frozen declarations and assertions; live arms the change falsifies (cut 23
W10g; cut 28 W8 and W8b-a..d; cut 41 Z5-a/b/c; cut 44 J17-a/J17-b; cut 45 G10-d/f
and G12-a/b/c/d/e/g/h/i/l; cut 46's Y17 arms over `_selected_attributions`; cut 34
BI-4/BI-8; cut 7's `Location` checks) are retargeted in their owning guards'
`_LIVE_SABOTAGES`, in the task whose change falsifies them, and the kills are
proved collectively at discharge. Obligation changes (`TestTheSplit`,
`test_g12_h_split_with_exclusion`, `test_g12_l_accept_all_refusal_parity[split]`)
are rewritten with a ledger disposition.

`PREFIX_RUNNERS = ("cut47_acceptance.py",)`.
`PHASE_MODULES = ("test_overlapping_publications_acceptance.py", "test_n2_cut48.py")`.

R23's retained rules-store clauses (install a newer rule beside the old; the old
receipt still validates; unhold the old and it is `unresolvable`) describe the
state shipping v2 beside v1 produces; this cut neither discharges nor alters them.

A bounded W20-b baseline/audit pilot plus one durable case precedes the complete
successor chain, run under cut 47's isolation (`TASK_TEST_HOME`, `GIT_CONFIG_GLOBAL=/dev/null`,
`GIT_CONFIG_NOSYSTEM=1`) on the certified kernel/volume. Capability refusal is
not a skip.

## 6. Second reader

Check: a legacy epoch opened beside a rebuilt one, and a document mixing the two
shapes; three holders where two agree and one differs after the epoch; a route
identity equal to a retraction's address, retracted by route, in one corpus; a
recipient holding P1 and P7 with P3 retired, and with P3 kept; a policy that
rejects a counter under one holder and accepts it under another over a v1-bound
epoch; a write root revising a carried record in place; a damaged carrier beside
a captured copy under a legacy entry; two copies of one uid with differing content
through the receipt path with no world view opened; the removal of a correctly
named raw-written v2 pair whose fixture lacks `arm`. Reuse the existing two-world
publish → adopt fixtures; retain `ReplicaOf` and corpus ids; assert exact refusal
reasons and no operations-root writes on refusal.

## 7. Limitations

A carried record's content is frozen in the publisher's own world while a carrier
is mounted (spec §10 item 1); a renamed record beside its predecessor stays
`uid-corruption` (item 2, follow-up beliefs-49afc2); the supersession order is
readable only through held markers, so science keeps chain members mounted while
a predecessor is dependency-kept (item 3); equality is exact (item 4); a damaged
holder is skipped only against a published content identity (item 5); legacy
epochs stay singular and v1-bound until rebuilt (item 6); authenticity is
unchanged (item 7); no cost measurement (item 8). Science's side (spec §8: the
`Carrier` content check, the adopt checklist, session-holder resolution, `explain`
wording, pins, the in-place change refusal, chain retention, `show`'s marker
naming, the `SYMBOL_FIELDS` replacement) is a science task filed at discharge; no
live corpus, mount, registry or configuration changes here. No successor runner
has discharged this cut yet.
