"""Cut 16's 11 frozen declaration units and their source sabotages."""

from n2_arms import Arm, Sabotage

_ACCEPTANCE = "acceptance/test_relocation_acceptance.py"

CUT16_ARMS = (
    Arm(
        row="W5",
        asserts="a move preserves the carried record's identity and producer semantics",
        sabotage=Sabotage(
            module="relocation.py",
            before="        moved = destination._add_locked(node)\n",
            after=('        moved = destination._add_locked(node.model_copy(update={"uid": "0" * 32}))\n'),
        ),
        checks=(f"{_ACCEPTANCE}::test_w5_move_changes_only_location_and_preserves_producer_semantics",),
    ),
    Arm(
        row="W16a",
        asserts="consolidation unions the two records' outgoing relations",
        sabotage=Sabotage(
            module="relocation.py",
            before="    for relation in (*survivor.relations, *loser.relations):\n",
            after="    for relation in survivor.relations:\n",
        ),
        checks=(f"{_ACCEPTANCE}::test_w16_consolidates_one_address_without_asserting_identity",),
    ),
    Arm(
        row="W16b",
        asserts="consolidation unions divergent lineage bases",
        sabotage=Sabotage(
            module="relocation.py",
            before='            "facets": stored.union_lineage_bases(survivor, loser),\n',
            after='            "facets": dict(survivor.facets),\n',
        ),
        checks=(f"{_ACCEPTANCE}::test_w16_consolidates_one_address_without_asserting_identity",),
    ),
    Arm(
        row="W16c",
        asserts="the selected survivor uid is preserved rather than minted or taken from the loser",
        sabotage=Sabotage(
            module="relocation.py",
            before="    unstamped = survivor.model_copy(\n",
            after="    unstamped = loser.model_copy(\n",
        ),
        checks=(f"{_ACCEPTANCE}::test_w16_consolidates_one_address_without_asserting_identity",),
    ),
    Arm(
        row="W16d",
        asserts="different canonical addresses refuse before consolidation can answer coreference",
        sabotage=Sabotage(
            module="relocation.py",
            before="        if keep_node.id != other_node.id:\n",
            after="        if False:\n",
        ),
        checks=(f"{_ACCEPTANCE}::test_w16_consolidates_one_address_without_asserting_identity",),
    ),
    Arm(
        row="W16e",
        asserts="a conflict with fewer than two distinct sorted routes is unconstructible",
        sabotage=Sabotage(
            module="stored.py",
            before=(
                '    if tag == "conflict" and (\n'
                "        len(routes) < 2 or len(set(keys)) != len(keys) or keys != sorted(keys)\n"
                "    ):\n"
            ),
            after=(
                '    if tag == "conflict" and (\n        len(set(keys)) != len(keys) or keys != sorted(keys)\n    ):\n'
            ),
        ),
        checks=(f"{_ACCEPTANCE}::test_w16_consolidates_one_address_without_asserting_identity",),
    ),
    Arm(
        row="G3",
        asserts="the carrying corpus is not a belief closure member",
        sabotage=Sabotage(
            module="belief.py",
            before="        producer_snapshot_identity=context.producer_snapshot_identity,\n",
            after=(
                "        producer_snapshot_identity=context.producer_snapshot_identity\n"
                "        + repr(sorted(context.node_corpus.items())),\n"
            ),
        ),
        checks=(f"{_ACCEPTANCE}::test_g3_location_is_not_a_belief_closure_member",),
    ),
    Arm(
        row="D7a",
        asserts="public move refuses domain, base-contract, and missing-pin disagreement",
        sabotage=Sabotage(
            module="relocation.py",
            before=(
                "        _refuse_excluded_kind(node)\n"
                "        _refuse_contract_disagreement(node, source, destination)\n"
                "        if destination.read_view.resolve(node.id) == node.id:\n"
            ),
            after=(
                "        _refuse_excluded_kind(node)\n        if destination.read_view.resolve(node.id) == node.id:\n"
            ),
        ),
        checks=(f"{_ACCEPTANCE}::test_d7_each_public_relocation_refuses_contract_disagreement",),
    ),
    Arm(
        row="D7b",
        asserts="public consolidate refuses domain, base-contract, and missing-pin disagreement",
        sabotage=Sabotage(
            module="relocation.py",
            before=(
                "        _refuse_contract_disagreement(other_node, other_writer, keep_writer)\n"
                "        merged = _reconcile(keep_node, other_node)\n"
            ),
            after="        merged = _reconcile(keep_node, other_node)\n",
        ),
        checks=(f"{_ACCEPTANCE}::test_d7_each_public_relocation_refuses_contract_disagreement",),
    ),
    Arm(
        row="C3",
        asserts="a move changes exact receipt states while leaving the belief digest unchanged",
        sabotage=Sabotage(
            module="world/epoch.py",
            before=(
                '        "corpus_states": [\n'
                '            {"corpus_id": corpus_id, "corpus_state": corpus_state}\n'
                "            for corpus_id, corpus_state in receipt.corpus_states\n"
                "        ],\n"
            ),
            after=(
                '        "corpus_states": [\n'
                '            {"corpus_id": corpus_id, "corpus_state": "0" * 64}\n'
                "            for corpus_id, _corpus_state in receipt.corpus_states\n"
                "        ],\n"
            ),
        ),
        checks=(f"{_ACCEPTANCE}::test_c3_move_changes_exact_receipt_states_but_not_the_belief",),
    ),
    Arm(
        row="R23a",
        asserts="the producer receipt identity is not substituted for its semantic subject in belief",
        sabotage=Sabotage(
            module="world/derive.py",
            before="    return producers[0].subject_identity\n",
            after="    return producers[0].identity()\n",
        ),
        checks=(f"{_ACCEPTANCE}::test_r23_location_and_receipt_identity_are_not_belief_inputs",),
    ),
    Arm(
        row="R23b",
        asserts="differing routes make the consolidated basis a conflict rather than a single",
        sabotage=Sabotage(
            module="stored.py",
            before='            "tag": "single" if len(ordered) == 1 else "conflict",\n',
            after='            "tag": "single",\n',
        ),
        checks=(f"{_ACCEPTANCE}::test_w16_consolidates_one_address_without_asserting_identity",),
    ),
    Arm(
        row="R23c",
        asserts="lineage traversal decides divergence from the conflict tag before comparison",
        sabotage=Sabotage(
            module="lineage.py",
            before='        if basis.tag == "conflict":\n',
            after="        if False:\n",
        ),
        checks=(f"{_ACCEPTANCE}::test_w16_consolidates_one_address_without_asserting_identity",),
    ),
    Arm(
        row="M3",
        asserts="consolidation carries an equal-basis retraction replica without rewriting its counter",
        sabotage=Sabotage(
            module="corpus.py",
            before=(
                "        self._refuse_family_kinds(node, admitted_kind=node.kind)\n"
                "        self._refuse_missing_basis(node)\n"
            ),
            after=("        self._refuse_family_kinds(node)\n        self._refuse_missing_basis(node)\n"),
        ),
        checks=(f"{_ACCEPTANCE}::test_m3_consolidates_retraction_replicas_without_touching_the_counter",),
    ),
    Arm(
        row="T2",
        asserts="each touched root records one intent and one qualifying report in order",
        sabotage=Sabotage(
            module="corpus.py",
            before="        operation_port.execute_fulfilling([operation], intent_digest)\n",
            after="        operation_port.execute([operation])\n",
        ),
        checks=(f"{_ACCEPTANCE}::test_t2_each_root_records_one_intent_before_one_qualifying_report",),
    ),
    Arm(
        row="T8",
        asserts="both public relocation operations refuse an act-report input",
        sabotage=Sabotage(
            module="relocation.py",
            before="    if node.kind in EXCLUDED_KINDS:\n",
            after="    if False:\n",
        ),
        checks=(f"{_ACCEPTANCE}::test_t8_move_and_consolidate_refuse_act_reports",),
    ),
    Arm(
        row="boundary-reresolution-a",
        asserts="retract re-resolves its target immediately before plan construction",
        sabotage=Sabotage(
            module="corpus.py",
            before=(
                "            try:\n"
                "                self._view.get(target_ref)\n"
                "            except RefError as caught:\n"
                "                raise RelocationTargetMissing(\n"
                '                    f"{target_ref}: the target no longer resolves in this corpus; a concurrent move "\n'
                '                    "or deletion removed it (world-changing families §3.6)"\n'
                "                ) from caught\n"
                "            return self._corpus.add(record)\n"
            ),
            after="            return self._corpus.add(record)\n",
        ),
        checks=(f"{_ACCEPTANCE}::test_boundary_reresolution_refuses_both_create_only_calls_after_real_move",),
    ),
    Arm(
        row="boundary-reresolution-b",
        asserts="supersede re-resolves its predecessor immediately before plan construction",
        sabotage=Sabotage(
            module="corpus.py",
            before=(
                "            try:\n"
                "                self._view.get(predecessor_id)\n"
                "            except RefError as caught:\n"
                "                raise RelocationTargetMissing(\n"
                '                    f"{of}: the target no longer resolves in this corpus; a concurrent move "\n'
                '                    "or deletion removed it (world-changing families §3.6)"\n'
                "                ) from caught\n"
                "            return self._corpus.add(candidate)\n"
            ),
            after="            return self._corpus.add(candidate)\n",
        ),
        checks=(f"{_ACCEPTANCE}::test_boundary_reresolution_refuses_both_create_only_calls_after_real_move",),
    ),
    Arm(
        row="boundary-lock-dedup",
        asserts="resolved same-root spellings acquire their one distinct lock exactly once",
        sabotage=Sabotage(
            module="relocation.py",
            before=("    roots = {str(Path(writer.root).resolve()): writer for writer in (first, second)}\n"),
            after=(
                "    roots = {\n"
                '        f"{index}:{Path(writer.root).resolve()}": writer\n'
                "        for index, writer in enumerate((first, second))\n"
                "    }\n"
            ),
        ),
        checks=(f"{_ACCEPTANCE}::test_boundary_lock_deduplicates_resolved_same_root_before_refusal",),
    ),
)

_UNIT_OF = {
    **{f"W16{letter}": "W16" for letter in "abcde"},
    "D7a": "D7",
    "D7b": "D7",
    "R23a": "R23",
    "R23b": "R23",
    "R23c": "R23",
    "boundary-reresolution-a": "boundary-reresolution",
    "boundary-reresolution-b": "boundary-reresolution",
}


def unit_of(row: str) -> str:
    return _UNIT_OF.get(row, row)


DECLARATION_UNITS = (
    "W5",
    "W16",
    "G3",
    "D7",
    "C3",
    "R23",
    "M3",
    "T2",
    "T8",
    "boundary-reresolution",
    "boundary-lock-dedup",
)

CO_CITED: dict[str, tuple[str, ...]] = {}
