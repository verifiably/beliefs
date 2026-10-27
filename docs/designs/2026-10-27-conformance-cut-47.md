# Conformance cut 47 — owned replica publication

**Status:** frozen 2026-10-27 before product implementation; not discharged.
**Spec:** `../superpowers/specs/2026-10-27-owned-replica-publication-design.md`.
**Plan:** `../superpowers/plans/2026-10-27-owned-replica-publication.md`.
Successor to cut 46; all refs and worktrees were rechecked before choosing 47.

## 1. What this cut is

An explicit ownership declaration lets an admitted markerless replica contribute
records without inventing a source publication or changing its corpus identity.
This amends cut-46 decision 8 deliberately. Science §4.8 requires origins for
adopted records, while its later §9 Deviation 6 classifies hand-configured,
markerless relocated roots as Own. Downstream carrier's-own acceptance reads
the new publication's marker, which does carry published_from. The declaration
never rewrites registry provenance. Fresh holders already permit copying foreign
records without carried entries; this is no new authorship proof or laundering
capability. The captured-marker guard prevents claiming marker-bearing holders.

## 2. The boundary

`owned-replica-publication` reopens `world-read`: publish.py and session/writer.py.
Add keyword-only `own_corpora: frozenset[str] = frozenset()` to publication_preview,
publish and ScopedWriter.publish. Require exact frozenset/string types and existing
publication._HEX32.fullmatch for every ID, even unselected ones. Wrong types raise
TypeError; malformed IDs raise ValueError at preview entry. Earlier authority,
currency, transport and scoped preflight retain precedence. The no-write boundary
is publication intent and operations-root writes; scoped world recovery can precede it.
No format, contract release, configuration, permit, primitive, dependency or
TypeScript change. Resume takes no declaration and uses only frozen output.

## 3. Selection

Y5 and Y17 are reopened for this amendment. Existing selection, closure and pin
checks retain precedence. Check all selected holder admissions in ascending order
before inspecting declared ownership. Then, in ascending order, scan the complete
captured tuple for each selected declared holder. Any MARKER_KIND node refuses,
regardless of validity, selection, recorded-index membership or Fresh/ForkOf/ReplicaOf
provenance: attribution-own-source-invalid, that corpus ID, sorted selected refs
in that holder, field marker-present. Unknown selected holders still refuse admission;
valid unselected declarations have no effect. Registry provenance stays exact.

Exclude only declared holders that passed that guard from the replica set. V2
refuses attribution-contract-unpinned naming exactly the remaining sorted replicas,
or returns None for own-only selection. V3 validates remaining captured publications
as before and forwards earlier origins unchanged, returning () for own-only selection.
Saved None/tuple attribution values and texts determine all retry markers without
source or registry reads. Source-v3/writer-v2 pin disagreement still wins first.

| **Y17** | Every selected replica-held record except an explicitly declared own markerless holder receives its source publication or forwarded earlier origin, derived before intent and frozen with selection; retries never re-read origin inputs |

Each unit below names `test_<lowercase unit with underscore>_<suffix>` in
`test_owned_replica_publication.py`, except Y17-w in `test_session_publish_door.py`.
Parameter cases stay within one unit; durable tests add evidence, not units.

| Unit | Suffix / decisive behavior | Independent mutation responsibility |
|---|---|---|
| Y5-f | `declaration_validation`: exact frozenset/string/hex shape; unused malformed IDs still fail at preview entry | Bypass the ownership validator call |
| Y17-q | `owned_replica`: declared markerless replica returns None/v2 or ()/v3 with its admission unchanged | Keep declared holders in the replica set |
| Y17-r | `explicit_scope`: empty declaration retains refusal; an unselected declaration cannot exempt a selected holder | Treat a nonempty declaration as applying to every holder |
| Y17-s | `captured_marker_veto`: any marker in full capture vetoes every provenance class | Suppress marker-present rejection |
| Y17-t | `refusal_order`: all admissions first, then sorted declared-holder marker errors, then ordinary replicas | Move marker validation ahead of the complete admission pass |
| Y17-u | `mixed_origins`: omit owned records only, forward remaining source triples unchanged | Suppress carried entries whenever any own holder contributes |
| Y17-v | `preview_matches_freeze`: public preview and publish snapshot agree on texts, pins and None/tuple origins | Drop the declaration at publish-to-preview forwarding |
| Y17-w | `scoped_ownership`: scoped publish forwards the exact frozenset, with existing preflight intact | Drop declaration forwarding in ScopedWriter.publish |
| Y17-x | `frozen_owned_marker`: local/remote reconstruction preserves None/empty own-only formats with source reads trapped | Invent a carried entry for an owned selected record during reconstruction |


## 4. Accounting

**9 arms, 9 declaration units, two exercised rows**: Y5 (1 unit), Y17 (8 units).
No new guarantee IDs or newly closed rows. Freeze is 224/253 closed, 29 open;
successful discharge is 226/253 closed, 27 open. Recent-runner entry is (9, 9, 2):
`guarantee rows exercised: 2 (0 newly closed; Y5 and Y17 amendments reclosed)`.
Five durable functions cover preview/publish, refusal ordering, actual scoped
publication, local retry and remote mark-only retry, with v2/v3 cases as specified.

## 5. N2 and acceptance obligations

Each unique responsible mutation must parse, its baseline must pass and its named
assertion must fail under sabotage. Collection/syntax failures prove no kill.
Canonical declarations are content-pinned when created; this body's §§2–7 freeze
before implementation. No prior check node is reclaimed or co-cited. Preserve all
prior frozen declarations and assertions; live cut-46 Y17-a/g/i anchors are
retargeted in their owning guard and killed. Retarget other arms only if proved stale.

`PREFIX_RUNNERS = ("cut46_acceptance.py",)`.
`PHASE_MODULES = ("test_owned_replica_publication_acceptance.py", "test_n2_cut47.py")`.

A bounded Y17-s baseline/audit pilot plus local/remote durable cases precedes the
complete successor chain through just test-one on the certified kernel/volume.
Capability refusal is not a skip. Y17-x invents an entry from the frozen snapshot
in _expected_marker, killed by local reconstruction or remote reconstruction with
its snapshot. Remote mark-only never calls that function and is additional evidence.

## 6. Second reader

Check a captured marker absent from index/selection; a declared selected holder
missing admission; mixed own and carried content under v2/v3; stale/under-permitted
scoped calls with malformed declarations; and recovery after source inputs disappear.
Reuse the existing durable replicate/export/restore/admit_arrival fixture, retaining
ReplicaOf and its ID, and extend it with a separate Fresh-admitted write root in the
same destination world. Assert preview/snapshot equality, unchanged admission,
exactly one binding/report, and retry marker bytes. Trap source/registry access
only during recovery, restoring patches before independent postconditions.

## 7. Limitations

Ownership is a publisher claim, not authenticated authorship. Existing capture
integrity checks remain; no live source is reopened to classify ownership.
The marker-present before-intent guarantee has construction and uncounted regression
evidence (test_ownership_refusals_before_intent), not a dedicated mutation arm;
Y17-v proves forwarding only. No successor runner has discharged this cut yet.
Science wiring remains sci-9a7ce2; the live milestone rerun sci-775e90 depends on
that task and beliefs-7c612b. No live corpus/configuration change is authorized here.
