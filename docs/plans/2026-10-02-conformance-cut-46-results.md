# Conformance cut 46 — results

**Cut:** `../designs/2026-10-02-conformance-cut-46.md`
**Freeze:** `5981ae6`; SHA-256 `aa87d32a6cd7d1541bf76d7bf9de55b640771c6ac2f13bb4d967a4a577e9953b`
**Declaration:** `python/tests/n2_arms_cut46.py`; SHA-256 `da3e36e19ecf87d3da17da009350bf0c82fcc29315323057f64e9c781cf6dc04`
**Subject:** carried origins frozen before intent, release-pinned attribution and unchanged marker identity
**Design:** `../superpowers/specs/2026-10-02-publication-attribution-design.md`; reviewed SHA-256 `42d39f11fa803f088e0cfec597f223b21f5a5891a34ec56a0bdcbd239e477707`
**Plan:** `../superpowers/plans/2026-10-02-publication-attribution.md`; reviewed SHA-256 `5c0d9e4b30d49250531a18c90722c7ddc62585624cfc80c30726cd42e14c412e`
**Implementation and declaration:** through `454fc55`, branch `feat/publication-attribution`, stacked on acceptance discharge `d466f5f`
**Discharged:** 2026-10-02; final status documentation and task closure in this commit
**Reviewed range:** `d466f5f..eb18c87`; the single Important repair is `454fc55`
**Reviewed document hashes:** those above name reviewed bytes, before final status metadata updates
**Runner:** `python/tools/cut46_acceptance.py`
**Log SHA-256:** `02b823106eb4aa3151b2234c25e300e305224b3881cfae1e135416dc52ee26a9`

## 1. What ran

The bounded pilot finished before the successor: first carry, forwarding,
local retry and remote mark/export-only retry passed **4/4 in 45.95 seconds**.
Y5-c, Y17-c and Y18-i each passed their normal baseline (`resolved`) and
mutation audit (`sound`), **3/3 in 5.61 seconds**. The complete new guard passed
13 tests, with all 36 mutations sound, in 13.48 seconds and 14.52 seconds.
The ten durable functions' 14 cases passed in 149.89 and 146.95 seconds.

All durable runs used the certified tuple: kernel `7.2.2-arch1-1`, volume
`/dev/nvme1n1p2`, ext4 mounted `rw,noatime,data=ordered`. The work root is
main `.work/acceptance/cut46`; it resolves to that certified volume. Commands
ran from the canonical worktree directory, accessed from the main checkout
as `.worktrees/publication-attribution`, avoiding the symlink's pytest ELOOP.
No host launcher, service or shared configuration pointer changed.

The first successor at `eb18c87` was interrupted with exit **130** for the
review's Important v3 mount finding. Seven completed phases passed 145
invocations in 132.85 reported pytest seconds; none failed. This partial run
is retained as main `.work/acceptance/cut46-runner-pre-review.log` and is not
discharge evidence. Its completed portions were analyzed before the repair
and restart; no capability refusal was waived and no environment was changed.

After the mount regression reproduced the finding and passed with the repair,
the full successor restarted from `454fc55` at `2026-10-02T15:36:28.671189+00:00`:

```text
just --set one_cmd 'cd python && uv run --frozen python tools/cut46_acceptance.py' test-one -q
```

The recipe already supplies `host-budget run`. The runner chains the highest
predecessor, cut 45, and adds `test_publication_attribution_acceptance.py` and
`test_n2_cut46.py`. It uses the main-checkout work root through the existing
checkout resolver and needs no shortened-path environment workaround.
The complete retained log is main `.work/acceptance/cut46-runner.log`.

The invocation exited **0** at `2026-10-02T16:39:57.232162+00:00` after **3808.561
seconds**. All **76 pytest phases and 1,172 passing invocations** passed,
without failure, error, skip or capability refusal. The 75 printed summaries
report **3713.49 seconds** of pytest time. Forwarded `-q` suppresses the
final guard's summary; its thirteen passing dots and successful runner return
establish that phase, whose time is excluded from that subtotal.

| cut | pytest phases | passing invocations | reported pytest seconds |
|---|---|---|---|
| 17 | 19 | 400 | 1039.66 |
| 18 | 2 | 23 | 106.83 |
| 19 | 2 | 38 | 73.31 |
| 20 | 2 | 22 | 65.97 |
| 21 | 2 | 11 | 34.63 |
| 22 | 2 | 9 | 8.10 |
| 23 | 2 | 37 | 169.75 |
| 24 | 2 | 22 | 115.89 |
| 25 | 2 | 29 | 49.16 |
| 26 | 1 | 10 | 1.60 |
| 27 | 2 | 51 | 296.64 |
| 28 | 2 | 34 | 165.72 |
| 29 | 2 | 19 | 13.87 |
| 30 | 2 | 30 | 43.21 |
| 31 | 2 | 20 | 16.99 |
| 32 | 2 | 20 | 45.87 |
| 33 | 2 | 21 | 86.74 |
| 34 | 2 | 27 | 147.42 |
| 35 | 2 | 37 | 68.84 |
| 36 | 2 | 26 | 106.71 |
| 37 | 2 | 21 | 16.28 |
| 38 | 2 | 31 | 40.78 |
| 39 | 2 | 26 | 61.59 |
| 40 | 2 | 44 | 291.30 |
| 41 | 2 | 29 | 46.01 |
| 42 | 2 | 46 | 321.83 |
| 43 | 2 | 23 | 25.17 |
| 44 | 2 | 20 | 39.78 |
| 45 | 2 | 19 | 73.97 |
| 46 | 2 | 27 | 139.87 + unreported guard |

## 2. Accounting

**36 arms, 36 declaration units, three guarantee rows.** Three Y5 units,
sixteen Y17 units and seventeen Y18 units. Y17/Y18 close; the Y5 amendment
is reclosed. The `publication-attribution` boundary is discharged and the
`world-read` lane closes this commons milestone 1a boundary. The roadmap
computes **226 of 253 rows closed, 27 open**. Other partial/open rows retain
their status.

The recent-runner inventory owns `(cut46, 46, (36, 36, 3))` and asserts:

```text
guarantee rows exercised: 3 (2 newly closed: Y17, Y18; Y5 amendment reclosed)
```

That portable interface check mocks subprocesses; the completed successor
above provides discharge evidence.

| unit | named check | sabotage module | normal | mutation |
|---|---|---|---|---|
| Y5-c | `test_publication_attribution.py::test_y5_c_v3_destination_pins` | `publish_request.py` | resolved | sound |
| Y5-d | `test_publication_attribution.py::test_y5_d_v3_disagreement` | `publish_request.py` | resolved | sound |
| Y5-e | `test_publication_attribution.py::test_y5_e_v2_pin_precedence` | `publish_request.py` | resolved | sound |
| Y17-a | `test_publication_attribution.py::test_y17_a_local_holdings` | `publish.py` | resolved | sound |
| Y17-b | `test_publication_attribution.py::test_y17_b_first_carry` | `publish.py` | resolved | sound |
| Y17-c | `test_publication_attribution.py::test_y17_c_forwarded_origin` | `publish.py` | resolved | sound |
| Y17-d | `test_publication_attribution.py::test_y17_d_selection_scope` | `publish.py` | resolved | sound |
| Y17-e | `test_publication_attribution.py::test_y17_e_distinct_holders` | `publish.py` | resolved | sound |
| Y17-f | `test_publication_attribution.py::test_y17_f_v2_refusal` | `publish.py` | resolved | sound |
| Y17-g | `test_publication_attribution.py::test_y17_g_before_intent` | `publish.py` | resolved | sound |
| Y17-h | `test_publication_attribution.py::test_y17_h_markerless_replica` | `publish.py` | resolved | sound |
| Y17-i | `test_publication_attribution.py::test_y17_i_missing_holder` | `publish.py` | resolved | sound |
| Y17-j | `test_publication_attribution.py::test_y17_j_invalid_source_order` | `publish.py` | resolved | sound |
| Y17-k | `test_publication_attribution.py::test_y17_k_admission_before_layout` | `publish.py` | resolved | sound |
| Y17-l | `test_publication_attribution.py::test_y17_l_held_capture` | `publish.py` | resolved | sound |
| Y17-m | `test_publication_attribution.py::test_y17_m_local_frozen_marker` | `publish.py` | resolved | sound |
| Y17-n | `test_publication_attribution.py::test_y17_n_remote_frozen_marker` | `publish.py` | resolved | sound |
| Y17-o | `test_publication_attribution.py::test_y17_o_registry_boundary` | `publish.py` | resolved | sound |
| Y17-p | `test_publication_attribution.py::test_y17_p_legacy_source` | `publish.py` | resolved | sound |
| Y18-a | `test_publication_attribution.py::test_y18_a_closed_shapes` | `publication.py` | resolved | sound |
| Y18-b | `test_publication_attribution.py::test_y18_b_member_types` | `publication.py` | resolved | sound |
| Y18-c | `test_publication_attribution.py::test_y18_c_strict_order` | `publication.py` | resolved | sound |
| Y18-d | `test_publication_attribution.py::test_y18_d_selected_addresses` | `publication.py` | resolved | sound |
| Y18-e | `test_publication_attribution.py::test_y18_e_identity_split` | `publication.py` | resolved | sound |
| Y18-f | `test_publication_attribution.py::test_y18_f_snapshot_formats` | `publish_request.py` | resolved | sound |
| Y18-g | `test_publication_attribution.py::test_y18_g_snapshot_commitment` | `publish_request.py` | resolved | sound |
| Y18-h | `test_publication_attribution.py::test_y18_h_snapshot_tamper` | `publish.py` | resolved | sound |
| Y18-i | `test_publication_attribution.py::test_y18_i_snapshot_pin` | `publish.py` | resolved | sound |
| Y18-j | `test_publication_attribution.py::test_y18_j_staged_release` | `corpus.py` | resolved | sound |
| Y18-k | `test_publication_attribution.py::test_y18_k_audit_release` | `corpus.py` | resolved | sound |
| Y18-l | `test_publication_attribution.py::test_y18_l_arrival_release` | `publication_arrival.py` | resolved | sound |
| Y18-m | `test_publication_attribution.py::test_y18_m_tip_release` | `publication_arrival.py` | resolved | sound |
| Y18-n | `test_publication_attribution.py::test_y18_n_source_release` | `publish.py` | resolved | sound |
| Y18-o | `test_publication_attribution.py::test_y18_o_remote_release` | `publish.py` | resolved | sound |
| Y18-p | `test_publication_attribution.py::test_y18_p_v3_succession` | `profile.py` | resolved | sound |
| Y18-q | `test_publication_attribution.py::test_y18_q_explicit_activation` | `profile.py` | resolved | sound |

## 3. Durable behavior and mutation dispositions

| durable function | passing cases | decisive result |
|---|---|---|
| first carry | 1 | Real v2 A copy/restore/admission, then v3 B names every selected A-held record |
| forwarding without origin | 1 | C holds B alone, copies A's entry unchanged and names B for B's own record |
| two carriers and selection | 1 | Canonical alias selection, distinct A/D origins, no unselected entries; v2 refuses sorted carriers before intent |
| markerless replica | 2 | Real restore and admit_arrival into a fresh world; v2 unpinned and v3 marker-absent refusals leave no intent |
| retirement after capture | 3 | Preparation scan actually observes retired and preserves origin; real state drift refuses; unmapped markers remain selectable |
| local retry frozen | 1 | Partial population resumes with a fresh writer and removed source; exact marker bytes, one binding/report |
| remote retry export-only | 1 | Mark/export survive request/selection/source removal; exact origins, one binding/report |
| new roots and arrival releases | 1 | Existing manifest refuses replacement; a new v3 publication restores and admits under its own pin |
| snapshot and staged marker tamper | 2 | Origin-only edits refuse snapshot-mismatch or staging-corrupt/marker before binding |
| remote export origin tamper | 1 | Changed content fails export evaluation before push or binding |

Honest publication markers are minted by actual acts. Copy, replication,
restore, epoch construction, admission and retirement use the public root
lifecycle on registered corpora. Damaged fixtures are explicitly labelled;
all roots and external metadata are cleaned by the existing source fixture.

The initial new mutation audit found 35 sound arms. Y18-p was uncollected:
the test module eagerly imported publish/request, which loads v3 during
collection, so changing v3's predecessor prevented the named succession test
from running. Act/request imports now occur inside their owning test functions
and helpers. The named test reaches the wrong predecessor and fails; all
36 normal checks resolve and all 36 mutations are sound. Assertions and
frozen obligations were not weakened. The accounting guard now matches the
frozen document's exact sentence.

Cut 40's canonical declaration and all prior cut bodies remain unchanged.
Its owning live guard adds a Y6-a override to the actual audited tuple using
`replace`: the probe includes attributions and the mutation still reselects
after intent. All other live arms pass staleness checks. The cut 46 declaration
is pinned only after its complete sound audit.

## 4. Verification and fresh review

Implementation gates passed 108 release checks, 75 codec/pin checks,
89 source-preparation checks and 184 wiring/recovery regressions. The final
portable attribution module passes 83 parameter cases. Durable checks pass
14 cases. Root/permit/staleness/recent-runner inventories pass 606 tests;
the mount repair's mount/routes/staleness gate passes 47 tests.
The stable post-review fast suite passes **6,080 tests with one existing
skip**, in 107.06 seconds; static checks report zero errors and zero warnings.
The complete successor contains no skip. Final document/guide/recent-runner
checks pass **44 tests in 1.19 seconds**. After those status changes, the fast
gate passes **6,080 tests with one existing skip in 79.94 seconds**; the affected
TypeScript selector finds no changed test files. Static checks and `tasks check`
pass with zero errors and warnings. Pyright reports an available newer release;
the locked tool version remains unchanged.

A single fresh read-only review by `codex/gpt-6-astra` examined
`d466f5f..eb18c87`. It returned **revise, Important/P2 1**, no Critical or
Minor findings. Manifest-driven `compile_mount_profile` still searched only
coordination v1/v2, so a shipped v3 root raised `MountPinUnresolved` before
standard session mounting. The repair extends its existing candidate tuple
and the existing shipped-profile regression to v1/v2/v3. The v3 case was
observed RED with that exact refusal, then GREEN; focused checks and the
fast suite pass, and the successor above reruns from the repaired commit.
The replacement AGENTS instructions required a scoped re-review of
`eb18c87..454fc55`. It accepted the correction with no Critical/Important
findings; its independent mount run passed 14 tests. Its one P3 finding was
a stale current writer-session description listing v1/v2. Task 7 current-facing
document cleanup updates that sentence, as repository instructions require.
No deferred minor remains. The re-review set aside outstanding discharge,
covered by the same withhold-discharge ruling below.

All five Review Focus cases were examined. The reviewer explicitly set aside
migration, authenticated authorship/overlapping holdings, and unfinished
Task 7 discharge. The author's rulings retain the approved new-root route,
retain attribution as a claim and singleton-holder scope, and withhold
discharge until repaired-source successor evidence and final checks pass.

The execution's complete rulings are:

- Extend report.py's closed request-corrupt reason vocabulary with
  `snapshot-pin-disagrees`, reusing its codec. The spec requires it and the
  plan omitted that owning file. Cost if wrong: consumers with an independent
  closed reason vocabulary need the new reason.
- Exercise local/remote forwarding separately with destination-conditioned
  mutations around the shared marker factory and distinct context anchors.
  Production branches are not duplicated for audits. Cost if wrong: the two
  mutations share a source site, while independently affecting their destination.
- Retain new-root-only v3 activation. Existing manifests are immutable.
  Cost if wrong: existing roots need a separate migration feature.
- Retain attribution as a publisher claim and singleton-holder selection.
  Authorship and overlap are separate boundaries. Cost if wrong: claims are
  not independently authenticated and overlapping holders remain unsupported.
- Withhold discharge until the repaired successor and final checks pass.
  The reviewer did not certify outstanding evidence. Cost if wrong: extra
  completion time, without an unsupported discharge claim.
- Integrate the reviewed acceptance/publication stack locally after discharge,
  rather than leaving it parked, under the replacement personal-profile rule.
  External writes and live global surfaces stay outside that authorization.
  Cost if wrong: main receives the completed stack earlier than intended.

## 5. Remaining boundary

None for `publication-attribution`: the Y5 amendment and Y17/Y18 are discharged.
New-root activation, publisher claims and singleton holdings retain their stated
limits. L1 remains partial under `persistence-cut`, and T7 remains partial under
`cross-root-publication`. The full `contract-cut`, authority labels, weighted
belief and extraction boundaries remain open as the ledger and roadmap state.
This cut neither reads those rows in full nor re-ranks them.

## 6. Release behavior and remaining limits

Coordination v3 is explicit and resolves through both direct profile activation
and manifest-driven mounts. The shipped default remains v2. New v3 write roots
are required for Science milestone 1a; existing manifests cannot be re-pinned.

V2's new `attribution-contract-unpinned` refusal for replica-held selections
is a named shipped-contract amendment. V2 carrying a v3 source still refuses
earlier as `pins-disagree` on coordination. Own-only publishing and existing
v2 attempts preserve their bytes and recovery format. Every new publication
performs the preparation registry scan; retirement retains admissions, and a
missing admission or failed second scan fails closed before intent.

Markerless replicas remain readable, but cannot be newly published. Forwarding
copies explicit earlier entries only. A legacy unattributed v2 B can name B's
marker but cannot reconstruct A's lost provenance. Attribution is a publisher's
claim, not authenticated authorship, timestamp or trust. No graph lookup,
overlapping-publication support, re-pin act, verification driver,
push, PR or Science deployment is included. Local integration of the finished reviewed stack follows discharge under the
replacement personal-profile instructions. The authorized bounded N2 preflight
pilot follows this task's closure.

## 7. Source hashes

These are the repaired implementation, declaration and evidence inputs before
successor execution. Current-facing status documentation changes only after
the completed run; frozen declaration and cut-body bytes remain pinned.

| input | SHA-256 |
|---|---|
| `python/tests/n2_arms_cut46.py` | `da3e36e19ecf87d3da17da009350bf0c82fcc29315323057f64e9c781cf6dc04` |
| `python/src/beliefs/contracts/coordination/v3/CONTRACT.yaml` | `633343b2666e04a56b159b2248b38d582965701ee6846f1d06b60a7a25728b0c` |
| `python/src/beliefs/profile.py` | `f03ac7e114b1026d622f75acf67d90e50ef47a43e46ced2c3daf456c15e12a5d` |
| `python/src/beliefs/publication.py` | `139c6665ee42aebd1ee1585a3761445e862539c8830017b5e73cc61e9a4db866` |
| `python/src/beliefs/corpus.py` | `cd23cde561e97ac20fd4ce62c81578bd6a585cc878615ea61b4c3879a3e8dd8a` |
| `python/src/beliefs/publication_arrival.py` | `0b59cdafb0d11573df9025497170426a39bb72cfea2fe3fe0ac3781eacf6f8ee` |
| `python/src/beliefs/publish_request.py` | `fcc3c620dd2333de7321c482d45967cae1b5ac87a50cfcca41b2ee0a1e6b5d3b` |
| `python/src/beliefs/publish.py` | `fd62da343eee7141522be67bfd47991282eae0fb279558bad6adaa87e68ca111` |
| `python/src/beliefs/report.py` | `050b58daf61a05d2f370e68532bab870d19fc4e08213a4748a7b85f605da42bf` |
| `python/tests/test_publication_attribution.py` | `a18d90f24eaa94c3f7baf7948e4070a9a3eefd697e70163adeb562ce00674eb2` |
| `python/tests/acceptance/test_publication_attribution_acceptance.py` | `9cb98d3b131374ca6d2f16379e8632060c3f5234b206b293ec45838172d606a8` |
| `python/tests/acceptance/test_n2_cut46.py` | `f80168301efc15f5c1715ed18989ad1fab5929949ef0236042ea81b1ca3b99ae` |
| `python/tests/acceptance/test_n2_cut40.py` | `c444857e4afa74965068bd0088e15d2999f158c4e6d38f40c07ea71157c22742` |
| `python/tools/cut46_acceptance.py` | `0c43114b92b67b5af0f6683fa6e1c005b6d434a5609d9fdf4b788229395ebf56` |
| `python/src/beliefs/mount.py` | `68f135c419d1557c77730bb657cc002f6a198b0a8795155ee4d8303492a7da2e` |
| `python/tests/test_mount.py` | `93bfe2c056b193a1391aab51248e58ef2c4837e0deb84203c7ddaf1797f7673e` |
