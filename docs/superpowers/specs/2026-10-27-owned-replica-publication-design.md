# Publishing an explicitly owned, markerless replica

**Status:** draft for review; implementation is not authorized by this document.
**Task:** beliefs-7c612b.
**Baseline:** beliefs `1024ee6`; science `32f1274e9c70f2da7be205d2558b8779e2d920ac`.
**Scope:** Python publication preparation and the scoped publish door, with a
required science consumer follow-up. No live-world changes in this task.

## 1. Intent and evidence

Science's second-project milestone could read the relocated mm30 corpus but
could not preview publishing a findings view over it. The recorded result was
`attribution-contract-unpinned`, naming corpus `8b5d0c802677ee445e2b9d91ebf5d6a7`.
The writer pins coordination v2. Switching to v3 alone would instead refuse
`attribution-source-invalid`, `field="marker-absent"`.

The source is sci-0d00d2, its committed
`docs/records/2026-10-26-second-project-milestone.md` §§4 R4 and 5 F12, and
beliefs-c08725. The latter used `reproduction.relocate`: replicate, restore
against an exported head artifact, then verified `admit_arrival` into a new
world. It retained the corpus identity and admitted `ReplicaOf`; it did not
produce a publication. The original measurement fixture remains separate.

Intent provenance: the user accepted the milestone measurement in Claude
session `74a061f4-8320-41fa-a2a3-a3ce105dd286`; the relayed review required
filing the attribution discrepancy. The implementing agent filed this task in
session `8b479072-91d3-4b9c-b77c-d178525b6574`. No recorded human turn chooses
an ownership mechanism. All choices below are this design author's proposals,
subject to the user's review.

This is an amendment, not a correction to an accidentally omitted branch.
The [cut-46 attribution spec](2026-10-02-publication-attribution-design.md)
decision 8 explicitly refuses even a restored copy of one's own unpublished
corpus. `_selected_attributions` implements that rule. Admission provenance
is immutable and records how a corpus arrived, not who owns its contents.

Science already distinguishes these matters for belief acceptance. Its
`docs/specs/2026-09-30-science-commons-design.md` §9, 2026-10-22 amendment
Deviation 6, and `python/src/science/acceptance.py::acceptance_inputs` treat
hand-configured markerless roots as Own, excluding sharing-registry roots.
Publishing currently cannot receive that distinction.

The intended outcome is that an explicitly declared own replica can contribute
records to publication without inventing a source publication. Imported
publications retain their existing per-record origins. The declaration is a
publisher's ownership claim, not authenticated authorship or evidence that
two actor strings identify the same person.

## 2. Approaches and decision

1. **Recommended: explicit own corpus IDs, guarded by captured content.** Add
   one immutable argument to the existing preparation and publication doors.
   Science derives it from its existing Own classification. Beliefs permits
   the exemption only for a selected, admitted holder with no publication
   marker. This preserves corpus identity, registry history and publication
   formats. Its cost is an explicit caller responsibility: beliefs cannot
   authenticate an ownership claim about unpublished records.
2. **Fork the relocated corpus and mount the fork.** Existing `fork_corpus`
   and `ForkOf` admissions avoid replica attribution, but mint a new corpus
   identity. Co-mounting the old and new holders would introduce duplicate
   records, so this also requires deliberate mount/epoch changes. Reject as
   the default: publication should not require changing the research corpus's
   identity or making a writable fork of a read-only source.
3. **Persist new ownership provenance in the world registry.** This would
   need an append-only amendment for already admitted replicas, a new durable
   act, audit semantics and migration policy. It still cannot prove authorship
   merely from an actor's assertion. Reject for this bounded task: the
   installation already supplies the distinction, and publication already
   freezes the resulting provenance claim.

Also reject automatic exemption for every markerless replica, actor-name
matching, path-based ownership inference inside beliefs, registry rewriting,
fake source markers, and repinning existing v2 write roots.

## 3. Interface

Add the keyword-only argument below to `publication_preview`, `publish`, and
`ScopedWriter.publish`:

```python
own_corpora: frozenset[str] = frozenset()
```

Each member is an exact string containing a corpus ID: 32 lowercase hexadecimal
characters. Require an exact `frozenset` and validate the full value at the
public preparation boundary; malformed input raises `TypeError` for type
errors or `ValueError` for malformed identifiers, before any intent or write.
The ordinary publish and session doors retain their existing authority,
currency, transport and other earlier precondition ordering. They pass the
argument unchanged to the shared preparation path; validation is not copied
into each forwarding wrapper.

The empty default retains existing behavior, including the cut-46 markerless
replica refusals. A declaration does not admit, select, mount, accept for
belief, or grant write permission to a corpus. Valid IDs not contributing to
the selection have no effect. All selected holders still need a registry
admission, regardless of declaration.

`ScopedWriter.publish` takes the value per call, alongside its other publication
inputs. No new session constructor option, world configuration field, registry
record, service protocol or permit is needed. The calling application owns
the declaration; an unattended caller's authorization to make that claim is
outside this kernel change. It cannot supply arbitrary attribution triples.

`resume_publish` gains no argument. Preparation determines the record texts
and attribution tuple once, before intent. Recovery uses those frozen results
and never recomputes ownership from current configuration.

## 4. Preparation semantics and precedence

Keep selection completeness, non-empty selection, closure, pin derivation and
all existing capture-integrity checks. In `_selected_attributions`:

1. Group selected addresses by their actual captured holder. Check every
   holder's admission in sorted holder order, as today. Never infer a holder
   from the address, an alias, a path or `published_from.world_id`.
2. For each selected holder named in `own_corpora`, in sorted holder order,
   inspect its entire captured record tuple, including unmapped coordination
   records. If **any** node has `kind == MARKER_KIND`, refuse
   `PublicationRefused("attribution-own-source-invalid", corpus_ids=(holder,),
   refs=selected_addresses_in_holder, field="marker-present")`. This applies
   regardless of admission provenance, marker validity, release or selection.
   Do not validate a marker and then treat a failure as its absence.
3. Exclude declared holders that passed step 2 from the set of replicas needing
   a source publication. `Fresh` and `ForkOf` holders otherwise retain their
   current behavior; undeclared `ReplicaOf` holders retain all current checks.
4. Under v2, any remaining replica causes the existing
   `attribution-contract-unpinned`, naming exactly those remaining holders.
   An own-only selection returns `None`, preserving the v2 marker shape.
5. Under v3, derive entries for the remaining replicas exactly as today from
   captured, layout-validated, release-authorized markers. Forward earlier
   origins unchanged; own holders contribute no entries. Return the canonical
   tuple, including `()` when all selected records are own.

Admission errors precede ownership-content errors, which precede the
carried-selection v2 refusal and v3 source validation. Earlier pin errors keep
their precedence: for example, a v2 writer still refuses a contributing v3
coordination pin before attribution processing. The declaration does not
weaken source world-domain agreement or staging-profile checks.

Use the same captured records as selection. Do not reopen a live corpus to
decide ownership. Removing a publication marker out of band is not a supported
way to become own: existing captured-state and integrity checks remain in
force. These checks do not claim to prevent an authorized caller from falsely
declaring independently authored markerless records as its own.

## 5. Persistence and release scope

No marker, intent, snapshot or request encoding changes. In both releases,
absence of a carried entry means the publisher claims the selected record as
own. This amendment supplies an explicit way to make that claim for a
markerless replica; it invents neither an origin marker nor a new marker
release. v2 still cannot publish a selection containing undeclared replicas;
v3 still requires an origin for every such selected record.

The snapshot freezes the resulting attribution tuple and canonical texts,
as it already does for Fresh/ForkOf provenance. The input declaration itself
is not persisted or authenticated. Thus a saved publication proves what the
publisher claimed, not which installation configuration justified that claim.
Changing or removing the declaration after intent cannot change a retry.
Old saved v2/v3 attempts keep their original behavior and bytes.

Explicitly amend Y17's universal replica wording to distinguish declared own
markerless holdings from carried holdings, and extend Y5's pre-intent refusal
coverage. Y18's release/content/identity rules remain unchanged. Preserve the
frozen cut-46 bodies and historical evidence; add a successor cut and a dated
current-facing amendment rather than rewriting history. The implementation
plan determines the next unused cut number and declaration counts.

## 6. Required consumer integration

The beliefs API alone does not change science's existing calls. After design
approval, file a science task sourced to beliefs-7c612b for both call sites:

- `commands/publish_preview.py`: pass `acceptance_inputs(ctx).own_roots` to
  `publication_preview`.
- `commands/publish.py`: pass that same classification to a **new**
  `writer.publish` attempt. The resume branch never computes or passes it.

Reuse the existing classification and its duplicate-carrier refusals. Do not
derive ownership from all `WorldConfig.corpus_roots`: science augments that
set with adopted publications. A sharing-registry root remains excluded even
if hand-listed, and a marker-bearing root cannot gain the exemption.
No new user-facing configuration key or command flag is needed.

The science task also updates its preview comment, reference documentation
and tests, and makes sci-775e90 depend on consumer integration as well as the
kernel change. sci-775e90 retains the live rerun and dated milestone addendum,
including explicitly selecting the assessment anchor. The stored-edge versus
projection-derived closure discrepancy remains beliefs-37d7ca.

This design authorizes no mutation of the live world, its mounts, registry,
profiles or corpus contents. The kernel task's completion reports the consumer
task and live-rerun dependency; it must not claim the milestone is fixed merely
because the API exists.

## 7. Verification and affected surfaces

Implementation tests must establish:

- The empty default preserves v2 and v3 refusals for a markerless replica.
- Explicit ownership succeeds for that replica under both releases, keeping
  the same corpus ID and producing no carried entry.
- Mixed own and publication holders retain only the real publication entries
  under v3; under v2 the refusal names only the remaining replicas.
- A selected declared holder with any marker refuses, including malformed
  markers and markers excluded from the selected world records. Cover Fresh,
  ForkOf and ReplicaOf declarations for this guard.
- Missing admission, malformed declarations, unselected declaration members,
  pin disagreements, closure refusals and damaged captures retain the specified
  behavior and precedence. Refusals leave no intent or operations files.
- A real restored markerless corpus admitted through `admit_arrival`, then
  captured in an epoch, exercises public preview and publish with the same
  declaration. Their selected records and attribution results agree.
- Local and remote retry after changing/removing the declaration or making
  source inputs unavailable uses frozen values. At least one actual scoped
  session publish proves argument forwarding and preserves permit/currency
  rejection before effects.
- Science's later tests cover configured markerless roots, sharing-registry
  exclusion, marker-bearing roots, duplicate-holder refusal, preview/publish
  parity, and resume without recomputing ownership.

Primary code: `python/src/beliefs/publish.py` and `session/writer.py`.
Primary existing tests: `test_publication_attribution.py`,
`test_session_publish_door.py`, publication acceptance tests and the cut runner.
Inspect every `publication_preview`/`publish` caller and test double when
planning, including tools and public exports; do not add wrappers or exports
where the existing functions suffice. No TypeScript counterpart exists for
these Python kernel acts; verify that boundary before implementation.

The plan owns the dated Y5/Y17 amendment, adoption-ledger and roadmap status,
new cut/runner/accounting, `test_recent_cut_acceptance.py` row, and any live
sabotage-anchor retarget needed by the change. Preserve frozen function pins
and historical guarantees according to the existing frozen-guard doctrine.
No new write primitive is proposed; if implementation adds one, it must enter
both permit inventories. `root.py` remains the sole atoms importer.

Run the hydrated worktree's full `just test` baseline at execution Setup,
before code changes, recording its actual test count. Develop through
`just test-one`, then `just test-fast` before implementation commits, and
`just check`/the installed hooks. The successor conformance route and its N2
coverage must prove the amended behavior without invalidating earlier cuts.
Design preparation has not run the suite or a live reproduction; the failure
evidence is the milestone record plus the inspected implementation and tests.

## 8. Builder latitude and limits

The builder chooses private helper placement, minimal fixture reuse, the next
cut number, and exact test names. The explicit declaration, captured-marker
guard, refusal precedence, frozen-retry behavior and consumer integration
are decisions to preserve, not unresolved implementation options.

No general ownership service, authenticity system, registry migration, corpus
fork, acceptance-policy change, overlapping-publication support or closure
redesign belongs in this slice. If durable proof of ownership rather than an
explicit publisher claim is required, this design is insufficient and must be
replaced before implementation.
