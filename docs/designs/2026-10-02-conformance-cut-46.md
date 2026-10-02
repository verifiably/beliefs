# Conformance cut 46 — publication attribution

**Status:** frozen 2026-10-02 before product implementation; discharged 2026-10-02 (`../plans/2026-10-02-conformance-cut-46-results.md`).
**Spec:** `../superpowers/specs/2026-10-02-publication-attribution-design.md`.
**Plan:** `../superpowers/plans/2026-10-02-publication-attribution.md`.
Successor to cut 45; all refs and worktrees were rechecked before choosing 46.

## 1. What this cut is

Selected replica-held records receive their source publication or an explicit
forwarded origin. Origins are frozen in the existing Snapshot before intent.
A → B → C retains A's entry. Attribution is a publisher's claim, not authorship
proof. Marker uid, address and consistency remain unchanged.

## 2. The boundary

`publication-attribution` reopens `world-read`: publication.py, publish.py,
publish_request.py, profile.py, corpus.py and publication_arrival.py. Coordination
v3 is explicit, its predecessor is v2 and its outer kind fields are unchanged.
Default coordination remains v2. Existing manifests cannot be re-pinned: Science
1a requires new v3 write roots. No write primitive or dependency is added.

## 3. Selection

Y5 is reopened for the named **v2 carried-selection refusal** amendment and v3
writer-derived coordination. Historical v2 selection/closure/base/domain/staging
checks retain precedence; writer v2 with source v3 refuses pins-disagree on
coordination before preparation. Every new attempt then scans the registry once,
checks ALL selected holder admissions in ascending order before any layout,
refuses v2 with all selected replica ids sorted, or validates each v3 source
in ascending holder order under its own captured manifest pin. Missing admission
is attribution-holder-unregistered; first invalid source is attribution-source-invalid
with the exact layout reason. Markerless replicas refuse, including restored
personal corpora. Retirement/departure retains admission; registry errors fail
before intent. Only mapped selected canonical ids receive entries.

| **Y17** | Every selected replica-held record receives its source publication or forwarded earlier origin, derived before intent and frozen with selection; retries never re-read origin inputs |
| **Y18** | Canonical attribution content is authorized by the marker release, changes the selection commitment and artifact content, and preserves marker identity; source world-domain pins remain required |

Each unit below names one portable check in `test_publication_attribution.py`:
`test_<lowercase unit with underscore>_<suffix>`. Parameter cases stay in their
unit; durable tests are additional evidence.

| Unit | Suffix and decisive assertion | Mutation responsibility |
|---|---|---|
| Y5-c | `v3_destination_pins`: v2/v3 source coordination pins are replaced by writer v3; other domains are unioned | Keep source coordination in v3 union |
| Y5-d | `v3_disagreement`: base and non-coordination mismatch refuse with exact field/corpus ids | Suppress a v3 world-domain disagreement |
| Y5-e | `v2_pin_precedence`: source v3 plus writer v2 refuses coordination disagreement before preparation scan/intent | Apply v3 derivation relaxation to v2 |
| Y17-a | `local_holdings`: Fresh/ForkOf yield None under v2 and empty tuple under v3 | Emit an origin for a non-replica |
| Y17-b | `first_carry`: each selected world kind gets holder and own marker uid | Omit replica own-origin fallback |
| Y17-c | `forwarded_origin`: earlier tuple is copied exactly | Replace earlier origin with current holder |
| Y17-d | `selection_scope`: no unselected source attribution escapes | Return entire source attribution map |
| Y17-e | `distinct_holders`: canonical selected keys and per-holder origins, ascending | Reuse one source marker for another holder |
| Y17-f | `v2_refusal`: exact unpinned reason and all selected replica ids ascending | Permit v2 replica selection |
| Y17-g | `before_intent`: v2 refusal runs before `_open_publication` and leaves ops/written state unchanged | Bypass preparation for a v2 destination |
| Y17-h | `markerless_replica`: marker-absent refuses, not an own-only classification | Treat markerless ReplicaOf as Fresh |
| Y17-i | `missing_holder`: v2/v3 missing admission reports first holder and ascending refs | Default unknown admission to Fresh |
| Y17-j | `invalid_source_order`: reverse input order still reports ascending first invalid holder | Iterate source captures in registry/input order |
| Y17-k | `admission_before_layout`: missing admission wins before an earlier holder's invalid marker is inspected | Validate layouts during admission discovery |
| Y17-l | `held_capture`: preparation uses held records/manifests once per replica, never reopens a root | Reopen source through ReadView |
| Y17-m | `local_frozen_marker`: reconstruction forwards frozen local origins, with source access trapped | Drop frozen origins for local reconstruction |
| Y17-n | `remote_frozen_marker`: reconstruction forwards frozen remote origins; mark-only recovery uses export | Drop frozen origins for remote reconstruction |
| Y17-o | `registry_boundary`: once-per-new-publish scan, retained retired admission, scan error before intent | Reject an admission with terminal status |
| Y17-p | `legacy_source`: unattributed v2 B falls back to B; explicit v3 B forwards A | Guess absent upstream provenance |
| Y18-a | `closed_shapes`: exactly old/new nested maps; old marker bytes remain exact | Accept unknown nested keys |
| Y18-b | `member_types`: malformed containers/triples/mixed members return malformed or factory/codec refusal | Coerce malformed attribution members |
| Y18-c | `strict_order`: duplicate and descending keys refuse, including valid-empty distinction | Remove strict ascending check |
| Y18-d | `selected_addresses`: invalid world ids and unselected keys refuse | Omit selected-key membership check |
| Y18-e | `identity_split`: same intent/different origins keep uid/address/id, change content and remain consistent | Include origins in marker uid |
| Y18-f | `snapshot_formats`: old bytes and new bytes round-trip exactly; missing/empty remain distinct | Decode absent entries as empty tuple |
| Y18-g | `snapshot_commitment`: origin-only change moves snapshot identity | Omit origins from snapshot projection |
| Y18-h | `snapshot_tamper`: origin edit reports mismatch, malformed entry reports undecodable | Bypass snapshot identity check |
| Y18-i | `snapshot_pin`: coherent request/snapshot with wrong pairing reports snapshot-pin-disagrees before stage | Omit request pin/format guard |
| Y18-j | `staged_release`: shape-valid but unauthorized marker refuses the staged write | Skip stage release predicate |
| Y18-k | `audit_release`: matching profile/manifest plus wrong marker shape yields coordination-facet-malformed | Skip profile-aware audit predicate |
| Y18-l | `arrival_release`: unauthorized marker refuses marker-malformed before admission | Skip arrival release predicate |
| Y18-m | `tip_release`: unauthorized held marker refuses with its corpus id | Skip tip release predicate |
| Y18-n | `source_release`: unauthorized captured marker reports attribution-source-invalid/marker-malformed | Skip source release predicate |
| Y18-o | `remote_release`: validated-export marker must agree with export manifest pin | Skip remote marker release predicate |
| Y18-p | `v3_succession`: v3 names v2 predecessor and retains every outer kind field | Parse v3 against v1 instead of v2 |
| Y18-q | `explicit_activation`: shipped default remains v2; fresh v3 root works, existing manifest cannot be re-adopted | Change shipped default to v3 |

## 4. Accounting

**36 arms, 36 declaration units, three exercised rows**: Y5 (3 units), Y17
(16 units), Y18 (17 units). Two newly banked rows Y17/Y18, Y5 amended and
reopened. Freeze is 223/253 closed, 30 open; successful discharge is 226/253
closed, 27 open. Recent-runner entry is `(36, 36, 3)` and reports:
`guarantee rows exercised: 3 (2 newly closed: Y17, Y18; Y5 amendment reclosed)`.
Ten durable functions prove first carry, forwarding, multiple carriers, markerless
restore, retirement, local retry, remote mark-only retry, explicit v3 roots,
snapshot/staged tamper and export tamper.

## 5. N2 and acceptance obligations

Every named mutation replaces one unique responsible branch and parses. Its
normal check passes and its own sabotaged check fails; collection errors are
not evidence. Canonical declarations and this body's §§1–7 stay immutable.
Cut40 Y6-a receives a live sabotage override in its owning guard, preserving its
check/assertion; other stale arms require explicit disposition.

`PREFIX_RUNNERS = ("cut45_acceptance.py",)`.
`PHASE_MODULES = ("test_publication_attribution_acceptance.py", "test_n2_cut46.py")`.

Pinned release boundaries are stage, corpus audit, arrival, tip, source preparation
and remote export marker agreement. Old-shape v2 and attributed-shape v3 pair
exactly. Factory, global shape, layout, consistency and coordination.tips_at are
shape-only deliberately. Snapshot None preserves exact v2 bytes; tuples including
empty authorize v3, enter commitment, and are reused without origin reads on retries.
Saved pin/format mismatch is snapshot-pin-disagrees after existing identity checks.
Run a bounded end-to-end pilot before the full successor, under the test front door
on the certified kernel/volume tuple. Missing capability refuses, never skips.

## 6. Second reader

Audit two-pass holder/layout precedence, exact forwarded tuples, selected-key
membership, ordering and closed wire shapes. V2 byte fixtures were captured before
implementation and must never be regenerated. Pin tests use coherent snapshots
and request identities so earlier checks cannot hide a missing release guard.
Release tests use matching v2/v3 capable profiles. Recovery tests use real crashes
and fresh writers; remote mark/export retry removes saved request/selection and
traps origin lookup. Markerless replicas enter a fresh recipient world. Retirement
cases assert the preparation scan actually saw retired status. Honest carriers
are published, exported, restored and admitted on registered real roots.

## 7. Limitations

Legacy v2 B that carried A without entries forwards B's own marker origin; A
cannot be reconstructed. New v3 roots are required, not an automatic upgrade.
Overlapping holders, contract freeze and bounded N2 preflight remain separate.
No successor runner has discharged this cut; portable checks alone cannot do so.
