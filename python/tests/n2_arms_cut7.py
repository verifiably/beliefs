"""Cut 7's 48 frozen epoch-carrier arms and their exact sabotages.

**38 selected + 10 labeled = 48**, one declaration unit per `Selected` and
`Labeled` bullet of `docs/designs/2026-08-20-conformance-cut-7.md` §3, counted
once at its home. `test_n2_cut7.py` reconciles this table against those bullets
and against §4's row accounting; nothing here restates a cross-referenced
clause at a second home.

**The sabotage paths are slice 2's, not cut 6's.** Cut 6 declared its arms
against `science/world.py`; slice 2 promoted that module to the
`science/world/` package, and the cut records that cut 6's committed paths
"remain historical evidence" rather than being recreated. Every arm below names
a path that exists in the present tree — `world/epoch.py`, `world/read.py`,
`world/rules.py`, `world/derive.py`, `corpus.py`, `closure.py`, `belief.py`,
`root.py` — and `test_n2_cut7.py` asserts none of them is `world.py`.

**Every check is one test function, fully qualified.** The frozen cut's
inventory names each check as ``<file>::<function>``; most of those functions
live inside a class, so the *resolvable* node id carries the class between the
two. The file and the function name are the frozen ones, verbatim; the class
segment is what makes `pytest` collect them at all — a bare
``file.py::function`` for a method exits 4, which the harness scores
`uncollected` rather than `sound`.
"""

from __future__ import annotations

from n2_arms import Arm, Sabotage

__all__ = ["CUT7_ARMS", "INTERPOSED_WRITE", "RELOCATED_HEAD_CHECK", "RELOCATED_HEAD_WITNESS"]


# --- shared mutations ---------------------------------------------------------

_NO_REFUTATION = Sabotage(
    module="world/read.py",
    before=(
        "    if epoch._document_bytes(rebuilt) != _claimed_projection(published, kind, receipt):\n"
        "        return derive.ReceiptOutcome(\n"
        "            kind,\n"
        '            "refuted",\n'
        '            "rebuilding this subject over the named states with the named implementation "\n'
        '            "produced a different projection from the one this epoch published",\n'
        "        )\n"
        "    if derive.subject_identity(kind, rebuilt) != receipt.subject_identity:"
    ),
    after=(
        "    if False:\n"
        "        return derive.ReceiptOutcome(\n"
        "            kind,\n"
        '            "refuted",\n'
        '            "rebuilding this subject over the named states with the named implementation "\n'
        '            "produced a different projection from the one this epoch published",\n'
        "        )\n"
        "    if False:"
    ),
)
"""Both roads to ``refuted`` closed at once.

Closing only the byte comparison is vacuous: the subject-identity comparison
immediately below reaches the same verdict by a second route, so an arm that
mutated one alone would score `sound` on a defect the code still catches.
"""

_REGISTERED_PATHS = "            registered_paths=tuple(dict.fromkeys(operation.path for operation in plan)),"
"""`science/root.py`'s one registration site — cut 6's durable seam, reused here
for the two world-transaction arms with their own filters."""


# --- X9's relocated head, and the vacuousness the cut pins at declaration time -

INTERPOSED_WRITE = (
    '        __import__("nodes.core.corpus", fromlist=["Corpus"]).Corpus(carrier).add(\n'
    '            stored.dataset_node(__import__("uuid").uuid4().hex, title="interposed")\n'
    "        )\n"
)
"""The corpus write the relocated-head sabotage interposes between the state
capture and the relocated head capture.

Cut 7 §3.1's X9 head/state bullet requires it and finding 6 of §6.1 is why:
without an interleaved write the relocated head reads the same chain the hold
would have read, so the *published* epoch is byte-identical and a check over it
passes vacuously. `RELOCATED_HEAD_WITNESS` is the check that demonstrates
exactly that, and `test_n2_cut7.py` runs the demonstration.
"""

RELOCATED_HEAD_CHECK = (
    "test_world_build.py::test_chain_head_and_state_are_captured_in_one_hold"
)
"""The frozen check node this arm declares — instrumented, so it sees the
relocation itself."""

RELOCATED_HEAD_WITNESS = (
    "acceptance/test_n2_cut7.py::test_anchored_head_describes_the_captured_corpus_view"
)
"""The uninstrumented witness: it compares the anchored head with the captured
corpus state and therefore sees the *consequence* rather than the relocation.
It passes under relocation alone and fails once the write is interposed."""

_RELOCATED_HEAD_BEFORE = (
    "        with state.lock.capture():\n"
    "            genesis_digest, head_digest = world._chain_head(carrier)\n"
    "            before = registry.corpus_state_identity(carrier)\n"
    "            records = _captured_records(carrier)\n"
    "            after = registry.corpus_state_identity(carrier)\n"
    "            if before != after:"
)

_RELOCATED_HEAD_AFTER = (
    "        with state.lock.capture():\n"
    "            before = registry.corpus_state_identity(carrier)\n"
    "            records = _captured_records(carrier)\n"
    "            after = registry.corpus_state_identity(carrier)\n"
    + INTERPOSED_WRITE
    + "        genesis_digest, head_digest = world._chain_head(carrier)\n"
    "        with state.lock.capture():\n"
    "            if before != after:"
)

_RELOCATED_HEAD = Sabotage(
    module="world/epoch.py", before=_RELOCATED_HEAD_BEFORE, after=_RELOCATED_HEAD_AFTER
)


CUT7_ARMS: tuple[Arm, ...] = (
    # --- X1 — the epoch is immutable and members are never deleted singly ------
    Arm(
        row="X1",
        asserts=(
            "no public API edits or deletes an individual epoch member — whole-epoch GC is the sole "
            "deletion operation, and a member-targeted mutation is unspellable through the surface"
        ),
        sabotage=Sabotage(
            module="world/epoch.py",
            before=(
                "    def __post_init__(self) -> None:\n"
                '        object.__setattr__(self, "members", MappingProxyType(dict(self.members)))'
            ),
            after=(
                "    def delete_member(self, member: str) -> None:\n"
                '        """A member-targeted mutation, spelled on the public carrier type."""\n'
                "        object.__setattr__(\n"
                '            self, "members", MappingProxyType({name: content for name, content in self.members.items() if name != member})\n'
                "        )\n"
                "\n"
                "    def __post_init__(self) -> None:\n"
                '        object.__setattr__(self, "members", MappingProxyType(dict(self.members)))'
            ),
        ),
        checks=(
            "test_world_epoch.py::TestOpening::test_public_surface_has_no_individual_epoch_member_mutation",
        ),
    ),
    Arm(
        row="X1",
        asserts=(
            "a raw-edited published member is detected by `open_epoch`'s packaging-identity "
            "recomputation and refuses `EpochMalformed`"
        ),
        sabotage=Sabotage(
            module="world/epoch.py",
            before="    recomputed = packaging_identity_of(members)",
            after="    recomputed = packaging_identity  # the name is taken as its own evidence",
        ),
        checks=("test_world_epoch.py::TestOpening::test_open_epoch_refuses_raw_member_edit",),
    ),
    # --- X2 — publication is crash-atomic and `current` is durable -------------
    Arm(
        row="X2",
        asserts=(
            "killing the writer at every Science-observable stage boundary of the one-transaction "
            "write leaves `current` naming either the prior epoch or the new, complete epoch on the "
            "next entry through the recovery barrier — never nothing, never incomplete content; "
            "intra-transaction stages belong to the engine's certified recovery and are not "
            "Science-observable, so the frozen \"every stage\" resolves to those boundaries"
        ),
        sabotage=Sabotage(
            module="world/epoch.py",
            before=(
                "        plan = _locked_publication_plan(world_root, packaging_identity, members)\n"
                "        if plan:\n"
                "            world._executor_factory(world_root).execute(plan)"
            ),
            after=(
                "        plan = _locked_publication_plan(world_root, packaging_identity, members)\n"
                "        executor = world._executor_factory(world_root)\n"
                "        for operation in reversed(plan):\n"
                "            executor.execute([operation])"
            ),
        ),
        checks=("acceptance/test_n2_cut7.py::test_recovery_barrier_never_selects_partial_epoch",),
    ),
    Arm(
        row="X2",
        asserts=(
            "on the certified tuple the publication transaction commits a registration entry naming "
            "every epoch member and `current`, decoded from the engine-owned chain"
        ),
        sabotage=Sabotage(
            module="root.py",
            before=_REGISTERED_PATHS,
            after=(
                "            registered_paths=tuple(\n"
                "                path\n"
                "                for path in dict.fromkeys(operation.path for operation in plan)\n"
                '                if not path.startswith("epochs/")\n'
                "            ),"
            ),
        ),
        checks=("acceptance/test_n2_cut7.py::test_publication_registration_names_epoch_and_current",),
    ),
    # --- X3 — belief never reads `current` -------------------------------------
    Arm(
        row="X3",
        asserts=(
            "a belief computation selecting \"current\" is unspellable — the closure's "
            "producer-snapshot input is a required explicit identity argument with no default and no "
            "current-accepting parameter, and no API composes `current_epoch` into a belief input"
        ),
        sabotage=Sabotage(
            module="belief.py",
            before=("def evaluate(\n    *,\n    proposition: str,\n    records: Records,"),
            after=(
                "def evaluate(\n"
                "    *,\n"
                "    proposition: str,\n"
                "    current_epoch: object = None,\n"
                "    records: Records,"
            ),
        ),
        checks=("test_world_read.py::TestTheBoundStamp::test_belief_has_no_current_epoch_input",),
    ),
    Arm(
        row="X3",
        asserts="every retained epoch — current and non-current — remains readable by its packaging identity while it exists",
        sabotage=Sabotage(
            module="world/read.py",
            before=(
                "    with registry._locked_barrier(world) as world_root:\n"
                "        return epoch._locked_open_epoch(world_root, packaging_identity)"
            ),
            after=(
                "    with registry._locked_barrier(world) as world_root:\n"
                "        named = epoch._locked_current_identity(world_root)\n"
                "        return epoch._locked_open_epoch(world_root, packaging_identity if named is None else named)"
            ),
        ),
        checks=("test_world_epoch.py::TestOpening::test_retained_epochs_open_by_packaging_identity",),
    ),
    # --- X5 — duplicate `corpus_id` detected at build --------------------------
    Arm(
        row="X5",
        asserts=(
            "two configured corpora carrying one `corpus_id` refuse a build whose coverage names it, "
            "`CoverageUnresolvable` at preflight — the frozen cell's \"reported\""
        ),
        sabotage=Sabotage(
            module="world/epoch.py",
            before="            if len(roots) != 1:",
            after="            if not roots:  # two carriers become a choice rather than a refusal",
        ),
        checks=("test_world_build.py::test_build_refuses_duplicate_carrier_coverage",),
    ),
    # --- X7 — admission is the cross-root commit point -------------------------
    Arm(
        row="X7",
        asserts="a build whose coverage names a manifest-bearing but unadmitted corpus refuses `CoverageUnknown`",
        sabotage=Sabotage(
            module="world/epoch.py",
            before="            if not any(record.corpus_id == corpus_id for record in view.admissions):",
            after="            if False:  # a readable manifest read as an admission",
        ),
        checks=("test_world_build.py::test_build_refuses_unadmitted_manifest_carrier",),
    ),
    Arm(
        row="X7",
        asserts="admitting that corpus lets the same build input proceed through preflight",
        sabotage=Sabotage(
            module="world/epoch.py",
            before="            if any(record.corpus_id == corpus_id for record in view.statuses):",
            after="            if not any(record.corpus_id == corpus_id for record in view.statuses):",
        ),
        checks=("test_world_build.py::test_admission_allows_same_build_preflight",),
    ),
    # --- X8 — every epoch answer is bound-stamped ------------------------------
    Arm(
        row="X8",
        asserts=(
            "every answer from every read API — address resolution in all three result states, the "
            "edge query, and epoch opening — carries the epoch packaging identity and the complete "
            "coverage declaration"
        ),
        sabotage=Sabotage(
            module="world/read.py",
            before="    return BoundStamp(published.packaging_identity, published.coverage)",
            after=(
                "    return BoundStamp(\n"
                '        published.packaging_identity, tuple((corpus_id, "") for corpus_id, _state in published.coverage)\n'
                "    )"
            ),
        ),
        checks=("test_world_read.py::TestTheBoundStamp::test_every_epoch_answer_carries_complete_bound_stamp",),
    ),
    Arm(
        row="X8",
        asserts="a stampless answer is unconstructible — the closed result types have no stampless constructor",
        sabotage=Sabotage(
            module="world/read.py",
            before="    stamp: BoundStamp\n\n\ndef resolve_address(",
            after="    stamp: BoundStamp | None = None\n\n\ndef resolve_address(",
        ),
        checks=("test_world_read.py::TestTheBoundStamp::test_bound_answer_types_have_no_stampless_constructor",),
    ),
    # --- X9 — one coherent state view per corpus, held by the corpus lock ------
    Arm(
        row="X9",
        asserts="an API write to a covered corpus while the build holds its capture refuses `BuildHold` — never queued, never interleaved",
        sabotage=Sabotage(
            module="corpus.py",
            before='            self._holder = "capture"\n            self._capture_generation += 1',
            after="            self._capture_generation += 1  # the capture takes no hold at all",
        ),
        checks=("test_world_build.py::test_api_write_refuses_during_capture",),
    ),
    Arm(
        row="X9",
        asserts="a capture started on a corpus whose lock an active writer holds refuses `BuildContended` — the build never waits",
        sabotage=Sabotage(
            module="corpus.py",
            before="            if self._holder is not None:\n                raise BuildContended(",
            after="            if False:\n                raise BuildContended(",
        ),
        checks=("test_world_build.py::test_capture_refuses_active_writer_without_waiting",),
    ),
    Arm(
        row="X9",
        asserts="a raw mutation during a corpus's capture makes the post-enumeration recompute discard it with `CaptureDrift`, and nothing publishes",
        sabotage=Sabotage(
            module="world/epoch.py",
            before="            if before != after:\n                raise CaptureDrift(",
            after="            if False:\n                raise CaptureDrift(",
        ),
        checks=("test_world_build.py::test_capture_drift_discards_without_publication",),
    ),
    Arm(
        row="X9",
        asserts=(
            "no published epoch's receipts name two states of one corpus: the producer, retraction, "
            "certification-enumeration and coreference-reduction receipts name identical per-corpus "
            "states within one epoch"
        ),
        sabotage=Sabotage(
            module="world/derive.py",
            before="            corpus_states=states,",
            after='            corpus_states=states if kind == "producer" else states[:1],',
        ),
        checks=("test_world_build.py::test_four_receipts_share_identical_corpus_states",),
    ),
    Arm(
        row="X9",
        asserts=(
            "head/state coherence: the only head-capture site is inside the hold that captured the "
            "state, so a chain head captured outside it is unconstructible through the build — "
            "declared with a corpus write interposed between the state capture and the relocated "
            "head capture, without which the relocation is vacuous (cut 7 §6.1 finding 6)"
        ),
        sabotage=_RELOCATED_HEAD,
        checks=(RELOCATED_HEAD_CHECK,),
    ),
    Arm(
        row="X9",
        asserts=(
            "the ABA negative, as an undetectability assertion: a raw `A -> B -> A` move within one "
            "capture leaves the pre/post identities matching, the build publishes, and nothing "
            "detects the mixed scan — packaging limitation 7, pinned as built and claiming no detection"
        ),
        sabotage=Sabotage(
            module="world/epoch.py",
            before="            after = registry.corpus_state_identity(carrier)",
            after=(
                "            after = registry.corpus_state_identity(carrier)\n"
                "            if {record.address for record in records} != {\n"
                "                node.id for node in ReadView.opened_at(carrier).iter_stored()\n"
                "            }:\n"
                "                raise CaptureDrift(\n"
                '                    f"{corpus_id}: the enumeration saw a corpus the state does not describe"\n'
                "                )"
            ),
        ),
        checks=("test_world_build.py::test_raw_aba_during_capture_is_undetectable",),
    ),
    # --- X10 — receipts resolve rule bindings against the held store only ------
    Arm(
        row="X10",
        asserts=(
            "removing the binding a validated receipt names returns `unresolvable`, never `refuted` — "
            "nothing in any corpus changed (parameterized over all four receipt kinds)"
        ),
        sabotage=Sabotage(
            module="world/read.py",
            before=(
                "            return derive.ReceiptOutcome(\n"
                "                kind,\n"
                '                "unresolvable",\n'
                '                f"the exact pair this receipt names is not held here: {caught}",\n'
                "            )"
            ),
            after=(
                "            return derive.ReceiptOutcome(\n"
                "                kind,\n"
                '                "refuted",\n'
                '                f"the exact pair this receipt names is not held here: {caught}",\n'
                "            )"
            ),
        ),
        checks=("test_world_receipts.py::TestReceiptOutcomes::test_removed_binding_makes_every_receipt_kind_unresolvable",),
    ),
    Arm(
        row="X10",
        asserts=(
            "with a second conforming implementation installed beside the named one, the receipt "
            "still validates against the exact pair it names and is never revalidated against the newcomer"
        ),
        sabotage=Sabotage(
            module="world/rules.py",
            before=(
                '        source = _read_member(directory / "implementations" / binding.implementation_identity)\n'
                "        if implementation_identity(source) != binding.implementation_identity:\n"
                '            raise _RuleRefusal("the stored implementation does not recompute its content identity")'
            ),
            after=(
                '        siblings = sorted(path.name for path in (directory / "implementations").iterdir())\n'
                "        chosen = next(\n"
                "            (name for name in siblings if name != binding.implementation_identity),\n"
                "            binding.implementation_identity,\n"
                "        )\n"
                '        source = _read_member(directory / "implementations" / chosen)'
            ),
        ),
        checks=("test_world_receipts.py::TestReceiptOutcomes::test_receipt_uses_named_binding_beside_successor",),
    ),
    Arm(
        row="X10",
        asserts=(
            "a receipt naming a bare version string is `malformed`, decided with no corpus present "
            "and no rule held"
        ),
        sabotage=Sabotage(
            module="world/read.py",
            before=(
                "    declared = epoch.RECEIPT_KEYS[member]\n"
                "    keys = {str(key) for key in receipt.document}"
            ),
            after=(
                "    if receipt.implementation_identity is None:\n"
                "        return None  # a bare rule version, read as a reference to be resolved leniently\n"
                "    declared = epoch.RECEIPT_KEYS[member]\n"
                "    keys = {str(key) for key in receipt.document}"
            ),
        ),
        checks=("test_world_receipts.py::TestReceiptOutcomes::test_bare_version_receipt_is_malformed_without_availability",),
    ),
    Arm(
        row="X10",
        asserts=(
            "for this row's two coreference outcomes — `unresolvable` (binding removed) and "
            "`malformed` — every covered edge reads `indeterminate` and a query expansion over one "
            "refuses `EdgeIndeterminate`, never `inactive`"
        ),
        sabotage=Sabotage(
            module="world/read.py",
            before=(
                "    if missing or not outcome.validated:\n"
                "        return EdgeAnswer(\n"
                '            "indeterminate", stamp, missing, None if outcome.validated else outcome.outcome\n'
                "        )"
            ),
            after=(
                "    if missing:\n"
                "        return EdgeAnswer(\n"
                '            "indeterminate", stamp, missing, None if outcome.validated else outcome.outcome\n'
                "        )"
            ),
        ),
        checks=("test_world_read.py::TestCoreferenceEdges::test_coreference_nonvalidated_outcomes_are_indeterminate",),
    ),
    # --- X11 — GC's two hard rules ---------------------------------------------
    Arm(
        row="X11",
        asserts="the GC act naming `current`'s epoch refuses `EpochCurrent` with nothing deleted",
        sabotage=Sabotage(
            module="world/epoch.py",
            before="        if current == packaging_identity:\n            raise EpochCurrent(",
            after="        if False:\n            raise EpochCurrent(",
        ),
        checks=("test_world_gc.py::TestRefusalOrder::test_delete_current_epoch_refuses",),
    ),
    Arm(
        row="X11",
        asserts=(
            "deleting a non-current epoch reports the producer-snapshot identity and the four receipt "
            "identities the epoch carried, each with its severed flag"
        ),
        sabotage=Sabotage(
            module="world/epoch.py",
            before="            receipts.append(SeveredIdentity(RECEIPT_KINDS[member], identity, identity in elsewhere))",
            after="            receipts.append(SeveredIdentity(RECEIPT_KINDS[member], identity, False))",
        ),
        checks=("test_world_gc.py::TestWholeEpochDeletion::test_delete_noncurrent_epoch_reports_severed_identities",),
    ),
    # --- X12 — completeness over the epoch's coverage --------------------------
    Arm(
        row="X12",
        asserts=(
            "a standing retraction in-coverage at build is in the retraction-discovery map, an "
            "out-of-coverage retraction is absent, and the coverage declaration states the bound"
        ),
        sabotage=Sabotage(
            module="world/derive.py",
            before=(
                "        if record.retraction is None:\n"
                "            continue\n"
                "        targets.setdefault(record.retraction.target, set()).add(record.address)"
            ),
            after=(
                '        if record.retraction is None or record.retraction.resolution == "overturned":\n'
                "            continue\n"
                "        targets.setdefault(record.retraction.target, set()).add(record.address)"
            ),
        ),
        checks=("test_world_derive.py::TestRetractionDiscoveryMap::test_retraction_map_is_bounded_by_coverage",),
    ),
    Arm(
        row="X12",
        asserts=(
            "omitting an in-coverage retraction and repackaging into an internally consistent epoch "
            "is refuted by receipt validation, rebuilding with the named binding against corpora at "
            "the named states (this unit also discharges W8a's identical arm, counted once here)"
        ),
        sabotage=Sabotage(
            module="world/read.py",
            before="    produced = held.invoke(derive.Capture(tuple(captured)).rule_input())",
            after=(
                "    produced = (\n"
                "        _thawed(receipt.document[_SUBJECT_KEYS[kind]])\n"
                "        if kind in _SUBJECT_KEYS\n"
                "        else held.invoke(derive.Capture(tuple(captured)).rule_input())\n"
                "    )"
            ),
        ),
        checks=("test_world_receipts.py::TestReceiptOutcomes::test_retraction_omission_refutes_repackaged_epoch",),
    ),
    Arm(
        row="X12",
        asserts=(
            "a covered corpus moved off a named state returns `unresolvable`, never a pass (this unit "
            "also discharges W8a's resolvability clause, counted once here)"
        ),
        sabotage=Sabotage(
            module="world/read.py",
            before="        if before != corpus_state:\n            return None",
            after="        if False:\n            return None",
        ),
        checks=("test_world_receipts.py::TestReceiptOutcomes::test_moved_corpus_state_makes_receipt_unresolvable",),
    ),
    Arm(
        row="X12",
        asserts=(
            "the empty-enumeration instance, recorded as such: a nonzero coreference balance published "
            "over attestation-free coverage is refuted by the rebuild — the reduction is checked, not "
            "merely the membership"
        ),
        sabotage=_NO_REFUTATION,
        checks=("test_world_receipts.py::TestReceiptOutcomes::test_nonzero_coreference_balance_refutes_empty_coverage",),
    ),
    Arm(
        row="X12",
        asserts=(
            "a refuted coreference receipt moves no `belief_input_digest` and its covered edges read "
            "`indeterminate`, with expansion refusing"
        ),
        sabotage=Sabotage(
            module="world/derive.py",
            before='BELIEF_INPUT_KIND = "producer"',
            after='BELIEF_INPUT_KIND = "coreference-reduction"',
        ),
        checks=("test_world_read.py::TestCoreferenceEdges::test_refuted_coreference_is_nonbelief_indeterminate",),
    ),
    # --- W8a — the derived-maps row --------------------------------------------
    Arm(
        row="W8a",
        asserts=(
            "deleting the world index and rebuilding from the corpora alone reconstructs the address, "
            "producers, retraction and coreference maps identically — the rebuild fixture carries "
            "populated address, producers and retraction maps, with only the coreference map "
            "kind-empty (the empty-enumeration instance)"
        ),
        sabotage=Sabotage(
            module="world/derive.py",
            before=(
                "def address_map_projection(mapping: Mapping[str, tuple[str, str]]) -> dict[str, object]:\n"
                '    """The `address-map.yaml` member\'s projection, sorted by address."""\n'
                "    return {\n"
                '        "addresses": [\n'
                '            {"address": address, "corpus_id": corpus_id, "uid": uid}\n'
                "            for address, (corpus_id, uid) in sorted(mapping.items())\n"
                "        ]\n"
                "    }"
            ),
            after=(
                "_DERIVATIONS: list[int] = []\n"
                "\n"
                "\n"
                "def address_map_projection(mapping: Mapping[str, tuple[str, str]]) -> dict[str, object]:\n"
                '    """The `address-map.yaml` member\'s projection, sorted by address."""\n'
                "    _DERIVATIONS.append(1)\n"
                '    marker = "" if len(_DERIVATIONS) == 1 else f"#{len(_DERIVATIONS)}"\n'
                "    return {\n"
                '        "addresses": [\n'
                '            {"address": f"{address}{marker}", "corpus_id": corpus_id, "uid": uid}\n'
                "            for address, (corpus_id, uid) in sorted(mapping.items())\n"
                "        ]\n"
                "    }"
            ),
        ),
        checks=("test_world_build.py::test_delete_and_rebuild_reconstructs_all_four_maps",),
    ),
    Arm(
        row="W8a",
        asserts="editing each map in a published epoch only, and asserting the rebuild discards every edit",
        sabotage=Sabotage(
            module="world/epoch.py",
            before=(
                "        retained = _locked_open_epoch(world_root, packaging_identity)\n"
                "        if dict(retained.members) != dict(members):\n"
                '            raise EpochMalformed(f"{directory}: a retained epoch of this name holds different bytes")'
            ),
            after=(
                "        operations.extend(\n"
                '            ReplaceOp(f"epochs/{packaging_identity}/{member}", members[member],\n'
                '                      rules.member_content_digest((directory / member).read_bytes()))\n'
                "            for member in EPOCH_MEMBERS\n"
                "        )"
            ),
        ),
        checks=("test_world_build.py::test_rebuild_discards_all_map_only_edits",),
    ),
    Arm(
        row="W8a",
        asserts=(
            "building over a narrower corpus set with every included corpus byte-identical leaves the "
            "producers map smaller, the coverage declaration different, and `belief_input_digest` "
            "different — an enumeration is bounded by what it consulted"
        ),
        sabotage=Sabotage(
            module="world/derive.py",
            before=(
                "        return {\n"
                '            "producers": [\n'
                '                {"dataset": dataset, "runs": sorted(runs)} for dataset, runs in sorted(self.producers.items())\n'
                "            ],\n"
                '            "coverage": sorted(self.coverage),\n'
                "        }"
            ),
            after=(
                "        return {\n"
                '            "producers": [\n'
                '                {"dataset": dataset, "runs": sorted(runs)} for dataset, runs in sorted(self.producers.items())\n'
                "            ],\n"
                "        }"
            ),
        ),
        checks=("test_world_derive.py::TestSnapshotIsSemanticNotPositional::test_narrower_producer_coverage_moves_snapshot_and_belief",),
    ),
    Arm(
        row="W8a",
        asserts=(
            "moving an entity between two covered corpora so both corpus-state identities change while "
            "the producers map and covered-corpus set do not leaves the semantic snapshot identity and "
            "`belief_input_digest` unchanged, and re-deriving mints a new receipt at a different "
            "receipt identity naming the same snapshot identity"
        ),
        sabotage=Sabotage(
            module="world/epoch.py",
            before="            [[corpus_id, corpus_state] for corpus_id, corpus_state in sorted(corpus_states)],",
            after="            [[corpus_id] for corpus_id, _corpus_state in sorted(corpus_states)],",
        ),
        checks=("test_world_receipts.py::TestReceiptOutcomes::test_receipt_changes_when_location_states_move_but_snapshot_does_not",),
    ),
    Arm(
        row="W8a",
        asserts=(
            "re-deriving under a newly installed rule mints a new receipt at a new receipt identity, "
            "leaves the old receipt untouched, and mints a new snapshot only if the map or coverage "
            "differ (X10 owns the install-beside and un-hold transitions, cross-referenced)"
        ),
        sabotage=Sabotage(
            module="world/epoch.py",
            before="            rule_identity,\n            implementation_identity,\n        ],\n    )",
            after="            rule_identity,\n        ],\n    )",
        ),
        checks=("test_world_receipts.py::TestReceiptOutcomes::test_rule_successor_mints_receipt_and_snapshot_only_on_subject_change",),
    ),
    Arm(
        row="W8a",
        asserts=(
            "malformed against unresolvable at the evaluator: a fixture-authored receipt whose keys, "
            "discriminant, identity members or corpus states violate §7.5 is `malformed`, decided with "
            "no corpus present and no rule held — never reached by consulting availability first"
        ),
        sabotage=Sabotage(
            module="world/read.py",
            before=(
                "    member = _member_for(kind)\n"
                "    receipt = published.receipts[member]\n"
                "    fault = _contract_fault(kind, member, receipt)"
            ),
            after=(
                "    member = _member_for(kind)\n"
                "    receipt = published.receipts[member]\n"
                "    with registry._locked_barrier(world) as _early_root:\n"
                "        rules._locked_resolve_rule_binding(\n"
                "            _early_root,\n"
                "            rules.RuleBinding(\n"
                "                cast(str, receipt.rule_identity), cast(str, receipt.implementation_identity)\n"
                "            ),\n"
                "        )\n"
                "    fault = _contract_fault(kind, member, receipt)"
            ),
        ),
        checks=("test_world_receipts.py::TestReceiptOutcomes::test_receipt_well_formedness_precedes_availability",),
    ),
    Arm(
        row="W8a",
        asserts=(
            "two installations — two world roots over the same corpora, each resolving the binding and "
            "the states from its own store — reach the same outcome for one receipt, and the one "
            "lacking the rule returns `unresolvable`: agreement within an availability context and "
            "across nothing else"
        ),
        sabotage=Sabotage(
            module="world/read.py",
            before=(
                "        try:\n"
                "            held = rules._locked_resolve_rule_binding(world_root, binding)\n"
                "        except RuleNotHeld as caught:"
            ),
            after=(
                "        try:\n"
                '            first = getattr(validate_receipt, "_first_store", None) or world_root\n'
                "            validate_receipt._first_store = first  # type: ignore[attr-defined]\n"
                "            held = rules._locked_resolve_rule_binding(first, binding)\n"
                "        except RuleNotHeld as caught:"
            ),
        ),
        checks=("test_world_receipts.py::TestReceiptOutcomes::test_rule_conformance_and_two_worlds_agree_within_availability",),
    ),
    Arm(
        row="W8a",
        asserts=(
            "the quantifier is per corpus and per conjunct: a receipt built over two corpora with one "
            "moved off its named state is `unresolvable`, the still-standing corpus does not satisfy "
            "the moved one's entry, and the same holds for the rule conjunct"
        ),
        sabotage=Sabotage(
            module="world/read.py",
            before="    for corpus_id, corpus_state in named_states:",
            after="    for corpus_id, corpus_state in named_states[:1]:",
        ),
        checks=("test_world_receipts.py::TestReceiptOutcomes::test_receipt_resolution_quantifies_each_corpus_and_rule",),
    ),
    Arm(
        row="W8a",
        asserts=(
            "belief invariance, narrow: changing corpus availability leaves the digest and admission "
            "unchanged — mounting is not an argument — and the producer-snapshot identity is a "
            "required argument with no default (X3 owns the no-implicit-latest half, cross-referenced)"
        ),
        sabotage=Sabotage(
            module="closure.py",
            before="    producer_snapshot_identity: str,",
            after='    producer_snapshot_identity: str = "",',
        ),
        checks=("test_world_read.py::TestTheBoundStamp::test_belief_is_invariant_to_availability_and_requires_snapshot",),
    ),
    Arm(
        row="W8a",
        asserts=(
            "absent is not empty, narrow: a corpus held out from inside coverage makes its producing "
            "run resolve `NotPresent`, never `Unknown` and never `Resolved` — with the frozen contrast "
            "that a producer outside coverage resolves `Unknown`, sub-problem 4 §11.15's stated limit"
        ),
        sabotage=Sabotage(
            module="world/read.py",
            before="        if not status.present:\n            return NotPresent(stamp)",
            after="        if not status.present:\n            return Unknown(stamp)",
        ),
        checks=("test_world_read.py::TestBoundResolution::test_inside_coverage_absence_is_not_outside_coverage_unknown",),
    ),
    # --- the ten labeled declarations (§3.3) -----------------------------------
    Arm(
        row="labeled:lock-capture-generation",
        asserts=(
            "a writer that entered the wait queue and wakes after a capture began and ended refuses "
            "`BuildHold` by the capture generation, never proceeding as if no capture intervened "
            "(specification §5.1)"
        ),
        sabotage=Sabotage(
            module="corpus.py",
            before='                if self._holder == "capture" or self._capture_generation != snapshot:',
            after='                if self._holder == "capture":',
        ),
        checks=("test_operation_lock.py::test_writer_waiting_across_capture_generation_refuses",),
    ),
    Arm(
        row="labeled:rule-install",
        asserts=(
            "byte-identical reinstallation of a held binding is idempotent success; an existing "
            "content-addressed path with different bytes refuses `RuleCollision`; an implementation "
            "failing the normative fixtures refuses `RuleNonconformant` before any transaction "
            "(specification §4.2)"
        ),
        sabotage=Sabotage(
            module="world/rules.py",
            before=(
                "            if target.read_bytes() != content:\n"
                '                raise RuleCollision(f"{target}: a content-addressed rule path holds different bytes")\n'
                "            continue"
            ),
            after=(
                "            if target.read_bytes() != content:\n"
                "                pass  # a content-addressed path is taken as good enough\n"
                "            continue"
            ),
        ),
        checks=("test_world_rules.py::TestInstallation::test_rule_install_is_idempotent_and_refuses_collision_or_nonconformance",),
    ),
    Arm(
        row="labeled:rule-removal",
        asserts=(
            "`remove_rule_binding` on an unknown pair refuses `RuleBindingUnknown`; a completed "
            "removal returns every receipt in this world that names the removed pair; nothing is "
            "removed by installing a successor (specification §4.3)"
        ),
        sabotage=Sabotage(
            module="world/rules.py",
            before="        if identity is not None and receipt.binding == pair:",
            after="        if identity is not None and receipt.binding is not None and receipt.binding[0] == pair[0]:",
        ),
        checks=("test_world_rules.py::TestExplicitRemoval::test_rule_removal_is_exact_and_reports_severed_receipts",),
    ),
    Arm(
        row="labeled:rule-self-verification",
        asserts=(
            "the held check recomputes the stored symbol, the stored fixture set and the named "
            "implementation's content identity from the stored bytes, so a raw swap of `rule.yaml` or "
            "of a fixture member leaves the binding not held (specification §4.1)"
        ),
        sabotage=Sabotage(
            module="world/rules.py",
            before="    return _HeldRule(binding, stored.symbol, stored.source, invoke)",
            after="    return _HeldRule(binding, stored.symbol, stored.document, invoke)",
        ),
        checks=("test_world_rules.py::TestHeldResolution::test_held_rule_recomputes_stored_symbol_and_fixtures",),
    ),
    Arm(
        row="labeled:publication-recheck",
        asserts=(
            "a named binding removed between capture and publication refuses `RuleNotHeld` at the "
            "pre-publication recheck under the world lock, and nothing is published (specification §5.4)"
        ),
        sabotage=Sabotage(
            module="world/epoch.py",
            before=(
                "        _locked_recheck_rule_bindings(world_root, draft)\n"
                "        plan = _locked_publication_plan(world_root, packaging_identity, members)"
            ),
            after="        plan = _locked_publication_plan(world_root, packaging_identity, members)",
        ),
        checks=("test_world_build.py::test_removed_rule_before_publication_refuses",),
    ),
    Arm(
        row="labeled:exact-rebuild",
        asserts=(
            "rebuilding an identical epoch swaps only the pointer; with the pointer already naming it "
            "the act succeeds submitting nothing; a same-name collision with different or malformed "
            "content refuses `EpochMalformed` with no member overwritten (specification §6.3)"
        ),
        sabotage=Sabotage(
            module="world/epoch.py",
            before=(
                "    else:\n"
                "        operations.extend(\n"
                '            CreateOp(f"epochs/{packaging_identity}/{member}", members[member]) for member in EPOCH_MEMBERS\n'
                "        )"
            ),
            after=(
                "    if True:\n"
                "        operations.extend(\n"
                '            CreateOp(f"epochs/{packaging_identity}/{member}", members[member]) for member in EPOCH_MEMBERS\n'
                "        )"
            ),
        ),
        checks=("test_world_epoch.py::TestExactRebuild::test_exact_epoch_rebuild_swaps_only_current",),
    ),
    Arm(
        row="labeled:resolution-refusals",
        asserts=(
            "a duplicate carrier, a malformed present manifest, and a present carrier that fails to "
            "produce the mapped `uid` each refuse `ResolutionRefused` — never `NotPresent`, never "
            "`Unknown` (specification §8.3)"
        ),
        sabotage=Sabotage(
            module="world/read.py",
            before='        if any(finding.code == "duplicate-carrier" for finding in status.findings):',
            after="        if False:  # ambiguity borrows the absence answer",
        ),
        checks=("test_world_read.py::TestBoundResolution::test_resolution_refuses_every_carrier_ambiguity",),
    ),
    Arm(
        row="labeled:edge-span",
        asserts=(
            "an epoch whose coverage lacks a live `corpus_id` yields `indeterminate` before any "
            "balance is considered, and `EdgeIndeterminate` names every unestablished input — the "
            "sorted missing live ids and/or the exact non-`validated` receipt outcome; a generic "
            "message fails the declared check (specification §8.4)"
        ),
        sabotage=Sabotage(
            module="world/read.py",
            before='        unestablished.append(f"the live corpora {list(missing)} are outside this epoch\'s coverage")',
            after='        unestablished.append("some live corpora are outside this epoch\'s coverage")',
        ),
        checks=("test_world_read.py::TestCoreferenceEdges::test_edge_indeterminate_names_missing_span_and_receipt_outcome",),
    ),
    Arm(
        row="labeled:ungoverned-kind",
        asserts=(
            "a record whose kind is an enumerated map kind but is present only as ungoverned prose "
            "refuses the build with `EnumeratedKindUngoverned` during capture — nothing derives from "
            "unvalidated content and nothing is silently dropped (specification §5.3, §10, §13)"
        ),
        sabotage=Sabotage(
            module="world/epoch.py",
            before="        if node.kind in ENUMERATED_SOURCE_KINDS and node.kind not in stored.SEMANTIC_DOMAINS:",
            after="        if False:  # an ungoverned enumerated record is derived from anyway",
        ),
        checks=("test_world_build.py::test_build_refuses_ungoverned_enumerated_record",),
    ),
    Arm(
        row="labeled:durable-world-transactions",
        asserts=(
            "on the certified tuple the rule-install, rule-removal and GC-deletion transactions each "
            "commit a registration entry naming their world-root paths; publication's entry is X2's "
            "selected unit (specification §4.2, §4.3, §9)"
        ),
        sabotage=Sabotage(
            module="root.py",
            before=_REGISTERED_PATHS,
            # All three halves at once, and that is the point rather than a
            # convenience: this arm asserts rule install *and* rule removal
            # *and* GC deletion, so a filter reaching only `rules/` would leave
            # the deletion half unfalsified — a partly vacuous arm, which is
            # exactly what this harness exists to refuse. `world.yaml`,
            # `corpus.yaml` and `registry/` stay registered so the fixture's own
            # construction is untouched and the arm fails on what it names.
            after=(
                "            registered_paths=tuple(\n"
                "                path\n"
                "                for path in dict.fromkeys(operation.path for operation in plan)\n"
                '                if not path.startswith(("rules/", "epochs/"))\n'
                "            ),"
            ),
        ),
        checks=("acceptance/test_n2_cut7.py::test_world_transactions_register_every_path",),
    ),
)
