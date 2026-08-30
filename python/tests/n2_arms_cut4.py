"""Cut 4's selected arms, paired with the sabotage each must not survive —
plus one clearly-labeled post-freeze strengthening at the end, which belongs
to no cut's accounting.

Same doctrine as `n2_arms.py` (N2: every oracle row can fail), extended over
cut 4's frozen selection. The deferred rows' doctrine stays exactly as the prior
cuts left it: this module neither changes their tables nor claims their arms.

**Most of these checks are durable arms**, and the audit that runs them is the
acceptance command's, not the portable harness's — a cut whose arms could be
audited off the certified tuple would be reporting discharge for a store it
never wrote to. `acceptance/…` node ids are what says so in the table itself.

**One behaviour has no sabotage here, stated rather than quietly omitted.**
Cycle-safety cannot be sabotaged into a *failing* check: removing the visited
guard does not make the walk answer wrongly, it makes it run forever, and a
harness that scores exit codes cannot tell a hang from anything else. What is
sabotaged instead is start-exclusion, whose mutation the cycle fixtures answer
in the same walk — a cycle whose start is re-admitted is exactly what the
mutated guard produces.
"""

from __future__ import annotations

from n2_arms import Arm, Sabotage

__all__ = ["CUT4_ARMS"]


_OVER_EAGER_CHECK = Sabotage(
    module="corpus.py",
    before="    for node in view.iter_stored():\n        if stored.semantic_hash_missing(node):",
    after=(
        "    for node in view.iter_stored():\n"
        "        findings.append(\n"
        "            Finding(\n"
        '                severity="error",\n'
        '                code="eligibility-unmet",\n'
        "                ref=node.id,\n"
        '                detail="",\n'
        '                message="over-eager",\n'
        "            )\n"
        "        )\n"
        "        if stored.semantic_hash_missing(node):"
    ),
)
"""A corpus check that reports every node.

Shared by the two arms whose claim is that a **silent** read stays silent: S8's
negative and R19's (d)/(e). A negative is not sabotaged by breaking the check it
names — it is sabotaged by making the checker over-eager, which is the failure
mode that would quietly turn a stated bound into a false report.
"""


# --- S7 — eligibility at both boundaries --------------------------------------

_S7 = [
    Arm(
        row="S7",
        asserts="the add path refuses to mint an inadmissible `assesses` edge",
        sabotage=Sabotage(
            module="corpus.py",
            before="        reason = eligibility_refusal(self._view, node)\n        if reason is not None:",
            after="        reason = eligibility_refusal(self._view, node)\n        if False:",
        ),
        checks=(
            "acceptance/test_durable_corpus.py::TestS7BothBoundariesDurably" +
            "::test_the_add_path_refuses_an_inadmissible_assesses_edge",
            "test_corpus_write.py::TestS7TheWriteBoundary" +
            "::test_an_assesses_edge_whose_run_has_no_observes_input_refuses",
        ),
    ),
    Arm(
        row="S7",
        asserts="the profile-level corpus check reports a raw-written violation as `eligibility-unmet`",
        sabotage=Sabotage(
            module="corpus.py",
            before="        reason = eligibility_refusal(view, node)\n        if reason is not None:",
            after="        reason = eligibility_refusal(view, node)\n        if False:",
        ),
        checks=(
            "acceptance/test_durable_corpus.py::TestS7BothBoundariesDurably" +
            "::test_the_corpus_check_reports_a_raw_written_violation",
            "test_read_side.py::TestTheCorpusCheck" +
            "::test_an_assesses_edge_whose_run_has_no_observes_input_is_reported_eligibility_unmet",
        ),
    ),
    Arm(
        row="S7",
        asserts="`reads` inputs confer no eligibility, in any quantity, and the facet is what `observes` demands",
        sabotage=Sabotage(
            module="corpus.py",
            before="        if view.holds(dataset_ref) and stored.is_empirical_observation(view.get(dataset_ref)):",
            after="        if view.holds(dataset_ref):",
        ),
        checks=(
            "test_read_side.py::TestTheCorpusCheck" +
            "::test_an_observes_input_without_the_empirical_observation_facet_is_reported",
        ),
    ),
]


# --- S8 — the capability boundary and its negative -----------------------------

_S8 = [
    Arm(
        row="S8",
        asserts="no module outside the write API constructs or receives a mutable `Corpus`",
        sabotage=Sabotage(
            module="root.py",
            before="from beliefs.corpus import CorpusWriter",
            after="from nodes.core.corpus import Corpus\nfrom beliefs.corpus import CorpusWriter",
        ),
        checks=(
            "test_capability_boundary.py::TestS8TheMutableCorpusHandleHasOneHolder" +
            "::test_no_module_outside_the_write_api_names_the_mutable_corpus[root.py]",
        ),
    ),
    Arm(
        row="S8",
        asserts="a raw write producing a valid node is read without refusal and reported by nothing — the bound",
        sabotage=_OVER_EAGER_CHECK,
        checks=(
            "acceptance/test_durable_corpus.py::TestS8TheNegative" +
            "::test_a_self_consistent_raw_write_passes_both_reads",
        ),
    ),
    Arm(
        row="S8",
        asserts="a raw write that moved the fields and not the stamp is refused on read (`semantic-hash-stale`)",
        sabotage=Sabotage(
            module="corpus.py",
            before="        if stored.semantic_hash_disagrees(node):\n            raise SemanticHashStale(",
            after="        if False:\n            raise SemanticHashStale(",
        ),
        checks=(
            "acceptance/test_durable_corpus.py::TestS8TheNegative" +
            "::test_a_raw_write_that_moved_the_fields_alone_is_refused_on_read",
            "test_read_side.py::TestTheFacadesNodeReadPath::test_a_stale_semantic_hash_is_refused_on_get",
        ),
    ),
]


# --- W3 — the basis refusal at the write boundary ------------------------------

_W3 = [
    Arm(
        row="W3",
        asserts="a `source` with no accepted external identifier is refused, never coerced to a note",
        sabotage=Sabotage(
            module="corpus.py",
            before='        if node.kind == "source" and not stored.external_identifiers(node):',
            after="        if False:",
        ),
        checks=(
            "acceptance/test_durable_corpus.py::TestW3Durably" +
            "::test_a_source_with_no_accepted_external_identifier_is_refused_before_it_lands",
            "test_corpus_write.py::TestW3TheBasisRefusal" +
            "::test_a_source_with_no_accepted_external_identifier_refuses",
        ),
    ),
    Arm(
        row="W3",
        asserts="a `dataset` with no content identity is refused",
        sabotage=Sabotage(
            module="corpus.py",
            before='        if node.kind == "dataset" and dataset_address(stored.dataset_declaration(node)) is None:',
            after="        if False:",
        ),
        checks=(
            "acceptance/test_durable_corpus.py::TestW3Durably" +
            "::test_a_dataset_with_no_content_identity_is_refused_before_it_lands",
            "test_corpus_write.py::TestW3TheBasisRefusal::test_a_dataset_with_one_unpinned_resource_refuses",
        ),
    ),
    Arm(
        row="W3",
        asserts="the accepted-identifier set is closed — no derived-identity escape exists to reach",
        sabotage=Sabotage(
            module="stored.py",
            before='ACCEPTED_EXTERNAL_IDENTIFIERS = ("accession", "doi", "isbn", "pmid")',
            after='ACCEPTED_EXTERNAL_IDENTIFIERS = ("accession", "doi", "isbn", "pmid", "url")',
        ),
        checks=("test_corpus_write.py::TestW3TheBasisRefusal::test_an_unaccepted_identifier_is_not_a_basis",),
    ),
]


# --- G9 — minted as a world entity, with no bytes held anywhere ----------------

_G9 = [
    Arm(
        row="G9",
        asserts="a dataset carrying a content identity and no bytes is minted, addressable and referenceable",
        sabotage=Sabotage(
            module="corpus.py",
            before='        if node.kind == "dataset" and dataset_address(stored.dataset_declaration(node)) is None:\n'
            "            raise BasisMissing(",
            after='        if node.kind == "dataset":\n            raise BasisMissing(',
        ),
        checks=(
            "acceptance/test_durable_corpus.py::TestG9DurablyMintedWithNoBytesHeld" +
            "::test_a_declared_dataset_is_minted_and_is_referenceable",
            "test_corpus_write.py::TestW3TheBasisRefusal::test_a_dataset_whose_bytes_are_held_nowhere_is_minted",
        ),
    ),
]


# --- the add-only guard and the single-planner lock ----------------------------

_ADD_ONLY = [
    Arm(
        row="S7",
        asserts="the add-only guard refuses an existing `(uid, id)` pair before plan construction",
        sabotage=Sabotage(
            module="corpus.py",
            before="        existing = self._corpus.index.by_uid.get(node.uid)\n        if existing is not None and existing.id == node.id:",
            after="        existing = self._corpus.index.by_uid.get(node.uid)\n        if False:",
        ),
        checks=(
            "test_corpus_write.py::TestTheAddPathIsAddOnly" +
            "::test_an_existing_uid_and_id_pair_refuses_before_plan_construction",
            "test_corpus_write.py::TestTheAddPathIsAddOnly" +
            "::test_no_plan_this_surface_emits_carries_a_replace_or_a_delete",
        ),
    ),
    Arm(
        row="S8",
        asserts="the operation lock serializes each add end to end — read, refuse, plan, execute",
        sabotage=Sabotage(
            module="corpus.py",
            before="        with self._operation:\n            self._refuse(node)\n            return self._corpus.add(node)",
            after="        self._refuse(node)\n        return self._corpus.add(node)",
        ),
        checks=(
            "test_corpus_write.py::TestTheOperationLock::test_two_same_uid_adds_are_serialized_end_to_end",
        ),
    ),
]


# --- S1 — the relation fixture, walked out of the store ------------------------

_S1 = [
    Arm(
        row="S1",
        asserts="an unrelated predicate is not followed",
        sabotage=Sabotage(
            module="corpus.py",
            before="            if relation.predicate != self._predicate or relation.source != node.id:",
            after="            if relation.source != node.id:",
        ),
        checks=(
            "acceptance/test_durable_traversal.py::TestS1TheRelationFixtureWalkedOutOfTheStore" +
            "::test_an_unrelated_predicate_is_not_followed",
            "test_read_side.py::TestTheRelationAdapter::test_an_unrelated_predicate_is_not_followed",
        ),
    ),
    Arm(
        row="S1",
        asserts="a deprecated ref resolves to the live node",
        sabotage=Sabotage(
            module="corpus.py",
            before="        uid = self._corpus.index.resolve_uid(ref)",
            after="        uid = self._corpus.index.id_to_uid.get(ref)",
        ),
        checks=(
            "acceptance/test_durable_traversal.py::TestS1TheRelationFixtureWalkedOutOfTheStore" +
            "::test_a_deprecated_ref_resolves_to_the_live_node",
            "test_read_side.py::TestTheRelationAdapter::test_a_deprecated_ref_resolves_to_the_live_node",
        ),
    ),
    Arm(
        row="S1",
        asserts="an undirected relation is reached from its stored source and not from its stored target",
        sabotage=Sabotage(
            module="corpus.py",
            before="        node = self._view.get(ref)\n        steps: list[Step] = []\n"
            "        for position, relation in enumerate(node.relations):",
            after="        node = self._view.get(ref)\n"
            "        steps: list[Step] = [\n"
            "            Step(\n"
            "                stored=edge.relation.source,\n"
            "                resolved=self._view.resolve(edge.relation.source),\n"
            "                entry=RelationEntry(\n"
            "                    source=edge.relation.source,\n"
            "                    position=0,\n"
            "                    predicate=edge.relation.predicate,\n"
            "                    target=ref,\n"
            "                ),\n"
            "            )\n"
            "            for edge in self._view.inbound(ref)\n"
            "            if edge.relation.predicate == self._predicate and not edge.relation.directed\n"
            "        ]\n"
            "        for position, relation in enumerate(node.relations):",
        ),
        checks=(
            "acceptance/test_durable_traversal.py::TestS1TheRelationFixtureWalkedOutOfTheStore" +
            "::test_an_undirected_relation_is_not_reached_from_its_stored_target",
            "test_read_side.py::TestTheRelationAdapter" +
            "::test_an_undirected_relation_is_not_reached_from_its_stored_target",
        ),
    ),
    Arm(
        row="S1",
        asserts="an unresolvable step is reported with the source node's id and the relation's stored position",
        sabotage=Sabotage(
            module="corpus.py",
            before="                        source=node.id,\n                        position=position,",
            after="                        source=node.id,\n                        position=0,",
        ),
        checks=(
            "acceptance/test_durable_traversal.py::TestS1TheRelationFixtureWalkedOutOfTheStore" +
            "::test_a_dangling_target_is_reported_with_its_source_and_position",
            "test_read_side.py::TestTheOneAlgorithmsSharedBehaviour" +
            "::test_two_dangling_edges_from_different_sources_are_two_entries",
        ),
    ),
]


# --- the shared walk -----------------------------------------------------------

_WALK = [
    Arm(
        row="S1a",
        asserts="the walk is start-excluding, so a cycle back to the start does not re-admit it",
        sabotage=Sabotage(
            module="traversal.py",
            before="    seen = {start}",
            after="    seen = set()",
        ),
        checks=(
            "test_read_side.py::TestTheOneAlgorithmsSharedBehaviour::test_the_start_is_never_in_the_reached_set",
            "acceptance/test_durable_traversal.py::TestS1aTheLineageFixtureWalkedAsAFacet" +
            "::test_one_algorithm_serves_both_adapters_over_this_store",
        ),
    ),
    Arm(
        row="S1a",
        asserts="an unresolvable step is skipped and **reported**, never dropped",
        sabotage=Sabotage(
            module="traversal.py",
            before="                unresolved.append(step.entry)",
            after="                pass",
        ),
        checks=(
            "acceptance/test_durable_traversal.py::TestS1TheRelationFixtureWalkedOutOfTheStore" +
            "::test_a_dangling_target_is_reported_with_its_source_and_position",
            "acceptance/test_durable_traversal.py::TestS1aTheLineageFixtureWalkedAsAFacet" +
            "::test_an_unresolvable_ancestor_is_reported_as_an_ancestor",
        ),
    ),
    Arm(
        row="S1a",
        asserts="the reached set is sorted, so two readers of one store agree on the order",
        sabotage=Sabotage(
            module="traversal.py",
            before="        reached=tuple(sorted(reached)),",
            after="        reached=tuple(sorted(reached, reverse=True)),",
        ),
        checks=(
            "acceptance/test_durable_traversal.py::TestS1aTheLineageFixtureWalkedAsAFacet" +
            "::test_a_basis_chain_walks_transitively",
            "test_read_side.py::TestTheOneAlgorithmsSharedBehaviour::test_a_chain_is_walked_transitively",
        ),
    ),
]


# --- S1a — the lineage adapter -------------------------------------------------

_S1a = [
    Arm(
        row="S1a",
        asserts="an unresolvable producing run is told apart from an unresolvable ancestor",
        sabotage=Sabotage(
            module="corpus.py",
            before='entry=LineageEntry(dataset=node.id, route=index, position="run", target=run),',
            after='entry=LineageEntry(dataset=node.id, route=index, position="ancestor", target=run),',
        ),
        checks=(
            "acceptance/test_durable_traversal.py::TestS1aTheLineageFixtureWalkedAsAFacet" +
            "::test_an_unresolvable_producing_run_is_told_apart_from_it",
        ),
    ),
    Arm(
        row="S1a",
        asserts="a producing run is checked and not walked into — it is not an ancestor",
        sabotage=Sabotage(
            module="corpus.py",
            before="                        follow=False,",
            after="                        follow=True,",
        ),
        checks=(
            "acceptance/test_durable_traversal.py::TestS1aTheLineageFixtureWalkedAsAFacet" +
            "::test_a_basis_chain_walks_transitively",
            "test_read_side.py::TestTheLineageAdapter" +
            "::test_a_resolvable_producing_run_is_checked_and_not_walked_into",
        ),
    ),
    Arm(
        row="S1a",
        asserts="a `conflict` basis yields **every** route",
        sabotage=Sabotage(
            module="corpus.py",
            before="        for index, route in enumerate(stored.basis_routes(node)):",
            after="        for index, route in enumerate(stored.basis_routes(node)[:1]):",
        ),
        checks=(
            "acceptance/test_durable_traversal.py::TestS1aTheLineageFixtureWalkedAsAFacet" +
            "::test_a_conflict_basis_yields_every_route",
            "test_read_side.py::TestTheLineageAdapter::test_a_conflict_basis_yields_every_route",
        ),
    ),
]


# --- S5 — the walk that produces the snapshot ----------------------------------

_S5 = [
    Arm(
        row="S5",
        asserts="the inspected set is `{observed root} ∪ closure`, the root included because the walk excludes it",
        sabotage=Sabotage(
            module="corpus.py",
            before="        for dataset in (root, *closure(root, adjacency).reached):",
            after="        for dataset in closure(root, adjacency).reached:",
        ),
        checks=(
            "acceptance/test_durable_traversal.py::TestS5TheWalkThatProducesTheSnapshot" +
            "::test_the_inspected_set_is_the_observed_root_plus_its_closure",
            "acceptance/test_durable_traversal.py::TestS5TheWalkThatProducesTheSnapshot" +
            "::test_a_conflict_tag_short_circuits_on_the_tag_alone",
        ),
    ),
    Arm(
        row="S5",
        asserts="the stored tag is what the snapshot carries, so a `conflict` short-circuits on the tag alone",
        sabotage=Sabotage(
            module="corpus.py",
            before='            bases[dataset] = Basis(tag=str(facet.get("tag", "single")), routes=routes)',
            after='            bases[dataset] = Basis(tag="single", routes=routes[:1])',
        ),
        checks=(
            "acceptance/test_durable_traversal.py::TestS5TheWalkThatProducesTheSnapshot" +
            "::test_a_conflict_tag_short_circuits_on_the_tag_alone",
        ),
    ),
    Arm(
        row="S5",
        asserts="a basis entry that does not resolve yields `lineage-incomplete` and no certificate",
        sabotage=Sabotage(
            module="corpus.py",
            before='                resolved_ancestor=view.resolve(str(route.get("ancestor", ""))),',
            after='                resolved_ancestor=str(route.get("ancestor", "")),',
        ),
        checks=(
            "acceptance/test_durable_traversal.py::TestS5TheWalkThatProducesTheSnapshot" +
            "::test_an_unresolvable_basis_entry_yields_incomplete_and_no_certificate",
        ),
    ),
    Arm(
        row="S5",
        asserts="the producer set comes from the store's own `produces` edges",
        sabotage=Sabotage(
            module="corpus.py",
            before="        if edge.relation.predicate != stored.PRODUCES:",
            after="        if False:",
        ),
        checks=(
            "acceptance/test_durable_traversal.py::TestS5TheWalkThatProducesTheSnapshot" +
            "::test_the_producer_set_comes_from_the_stores_produces_edges",
        ),
    ),
]


# --- R23 — `derived_from` as a view --------------------------------------------

_R23 = [
    Arm(
        row="R23",
        asserts="`derived_from` resolves as a view over `produces ∘ transforms`, walked out of the store",
        sabotage=Sabotage(
            module="corpus.py",
            before="            steps.extend(RelationAdjacency(self._view, stored.TRANSFORMS, \"outbound\").steps(producer.resolved))",
            after="            pass",
        ),
        checks=(
            "acceptance/test_durable_traversal.py::TestR23DerivedFromIsAView" +
            "::test_derived_from_resolves_over_produces_then_transforms",
            "test_read_side.py::TestTheDerivedFromView" +
            "::test_derived_from_resolves_as_a_view_over_produces_then_transforms",
        ),
    ),
    Arm(
        row="R23",
        asserts="independence follows the stamped basis, not the composition the view reports",
        sabotage=Sabotage(
            module="corpus.py",
            before='                resolved_ancestor=view.resolve(str(route.get("ancestor", ""))),',
            after='                resolved_ancestor=view.resolve(str(route.get("run", ""))),',
        ),
        checks=(
            "acceptance/test_durable_traversal.py::TestR23DerivedFromIsAView" +
            "::test_independence_follows_the_stamped_basis_not_the_composition",
        ),
    ),
]


# --- R19 — the genuine availability transition and the read-side negatives -----

_R19 = [
    Arm(
        row="R19",
        asserts="a minted verification reloads without refusal, and reading the record validates nothing",
        sabotage=Sabotage(
            module="corpus.py",
            before="    @staticmethod\n    def _validated(node: Node) -> Node:\n        if stored.semantic_hash_missing(node):",
            after="    @staticmethod\n    def _validated(node: Node) -> Node:\n        if True:",
        ),
        checks=(
            "acceptance/test_durable_records.py::TestR19aTheGenuineAvailabilityTransition" +
            "::test_the_record_reloads_and_is_not_refused",
            "acceptance/test_durable_records.py::TestR19aTheGenuineAvailabilityTransition" +
            "::test_reading_the_record_validates_nothing",
        ),
    ),
    Arm(
        row="R19",
        asserts="a self-consistent forged verification and a raw-written run are not detected on read",
        sabotage=_OVER_EAGER_CHECK,
        checks=(
            "acceptance/test_durable_records.py::TestR19deTheReadSideNegatives" +
            "::test_reload_does_not_validate_it",
            "acceptance/test_durable_records.py::TestR19deTheReadSideNegatives" +
            "::test_a_self_consistent_raw_written_run_is_not_detected",
            "acceptance/test_durable_records.py::TestR19deTheReadSideNegatives" +
            "::test_an_unaudited_verification_is_indistinguishable_from_a_genuine_one",
        ),
    ),
]


# --- R22 — the forgery at the address a genuine record would occupy ------------

_R22 = [
    Arm(
        row="R22",
        asserts="the belief digest moves when a forgery at the correct address changes the derived facet",
        sabotage=Sabotage(
            module="closure.py",
            before="    assessment_facets = sorted((a.identity(), a.facet_digest()) for a in ours)",
            after='    assessment_facets = sorted((a.identity(), "") for a in ours)',
        ),
        checks=(
            "acceptance/test_durable_records.py::TestR22TheForgeryAtTheCorrectAddress" +
            "::test_the_belief_digest_differs_from_the_correct_states",
        ),
    ),
    Arm(
        row="R22",
        asserts="the forged file is self-consistent, so neither read reports it — change detection, not truth detection",
        sabotage=Sabotage(
            module="stored.py",
            before='    return stored is not None and stored != recompute_semantic_hash(node)',
            after="    return stored is not None",
        ),
        checks=(
            "acceptance/test_durable_records.py::TestR22TheForgeryAtTheCorrectAddress" +
            "::test_the_forgery_is_self_consistent_so_the_stale_hash_check_has_nothing_to_say",
            "acceptance/test_durable_corpus.py::TestS8TheNegative" +
            "::test_a_self_consistent_raw_write_passes_both_reads",
        ),
    ),
]


# --- post-freeze strengthening — outside the frozen selection -----------------

_POST_FREEZE = [
    Arm(
        row="S3 (post-freeze strengthening)",
        asserts=(
            "an unstamped record of a governed kind is refused on get and reported "
            "`semantic-hash-missing` by the corpus check; declared here so the check is "
            "sabotage-audited, and counted in no cut's accounting — the 2026-08-18 "
            "adapter-design review added it after cut 4 froze, and the frozen selection "
            "is untouched"
        ),
        sabotage=Sabotage(
            module="stored.py",
            before="    return node.kind in SEMANTIC_DOMAINS and stored_semantic_hash(node) is None",
            after="    return False",
        ),
        checks=(
            "test_read_side.py::TestTheFacadesNodeReadPath" +
            "::test_an_unstamped_governed_record_is_refused_on_get",
            "test_read_side.py::TestTheCorpusCheck" +
            "::test_an_unstamped_governed_record_is_reported_semantic_hash_missing",
        ),
    ),
]


CUT4_ARMS = (
    *_S7, *_S8, *_W3, *_G9, *_ADD_ONLY, *_S1, *_WALK, *_S1a, *_S5, *_R23, *_R19, *_R22, *_POST_FREEZE
)
