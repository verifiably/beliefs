"""Cut 24's five frozen declaration units and their source sabotages — one arm
per sabotage site the cut document §5 item 4 names."""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS: tuple[str, ...] = ("W15", "X12", "W8a", "M3", "W4")
CO_CITED: tuple[str, ...] = ()


def unit_of(row: str) -> str:
    matches = [
        unit
        for unit in DECLARATION_UNITS
        if row == unit or (row.startswith(unit) and len(row) == len(unit) + 1 and row[-1].islower())
    ]
    return max(matches, key=len)


CUT24_ARMS = (
    Arm(
        row="W15a",
        asserts="endpoint kinds exclude prose",
        sabotage=Sabotage(
            module="corpus.py",
            before='            if endpoint.partition(":")[0] not in stored.COREFERENCE_ENDPOINT_KINDS:\n',
            after='            if endpoint.partition(":")[0] not in (*stored.COREFERENCE_ENDPOINT_KINDS, *stored.PROSE_KINDS):\n',
        ),
        checks=(
            "acceptance/test_coreference_acceptance.py::test_the_four_endpoint_refusals_durably",
            "test_coreference_attestation.py::TestTheSeam::test_the_endpoint_refusals_over_the_corpus_view",
        ),
    ),
    Arm(
        row="W15b",
        asserts="a self-pair has its own refusal",
        sabotage=Sabotage(
            module="corpus.py",
            before='                endpoints = raw.get("endpoints")\n                if isinstance(endpoints, list) and len(endpoints) == 2 and endpoints[0] == endpoints[1]:\n',
            after='                endpoints = raw.get("endpoints")\n                if False:\n',
        ),
        checks=("test_coreference_attestation.py::TestTheSeam::test_a_raw_self_pair_reaches_its_own_refusal",),
    ),
    Arm(
        row="W15c",
        asserts="resolution must preserve the exact address",
        sabotage=Sabotage(
            module="corpus.py",
            before="            if view.resolve(endpoint) != endpoint:\n",
            after="            if view.resolve(endpoint) is None:\n",
        ),
        checks=("test_coreference_attestation.py::TestTheSeam::test_a_retired_address_does_not_resolve_exactly",),
    ),
    Arm(
        row="W15d",
        asserts="endpoints have the same stored kind",
        sabotage=Sabotage(
            module="corpus.py",
            before="        if kinds[0] != kinds[1]:\n            raise CoreferenceEndpointRefused(\n",
            after="        if False and kinds[0] != kinds[1]:\n            raise CoreferenceEndpointRefused(\n",
        ),
        checks=("test_coreference_attestation.py::TestTheSeam::test_two_kinds_are_a_category_error",),
    ),
    Arm(
        row="W15e",
        asserts="the actor is bound to authority",
        sabotage=Sabotage(
            module="corpus.py",
            before='                if raw.get("actor") != self._authority.actor:\n',
            after='                if False and raw.get("actor") != self._authority.actor:\n',
        ),
        checks=("test_coreference_attestation.py::TestTheSeam::test_the_actor_is_bound",),
    ),
    Arm(
        row="W15f",
        asserts="only attest_coreference mints this kind",
        sabotage=Sabotage(
            module="corpus.py",
            before='        if node.kind == "coreference-attestation" and admitted_kind != "coreference-attestation":\n            raise WriteRefused("a coreference attestation enters through attest_coreference")\n',
            after="        pass\n",
        ),
        checks=("test_coreference_attestation.py::TestTheSeam::test_add_supersede_and_revise_refuse_the_kind",),
    ),
    Arm(
        row="W15g",
        asserts="controlled shape compares id facets and relations",
        sabotage=Sabotage(
            module="corpus.py",
            before='        if record.id != expected.id or record.facets != expected.facets or record.relations != expected.relations:\n            raise MalformedRecord(f"{record.id}: coreference attestation does not match',
            after='        if record.id != expected.id:\n            raise MalformedRecord(f"{record.id}: coreference attestation does not match',
        ),
        checks=(
            "test_coreference_attestation.py::TestTheSeam::test_the_controlled_rebuild_compares_id_facets_and_relations_and_accepts_a_fresh_uid",
        ),
    ),
    Arm(
        row="W15h",
        asserts="capture lifts stored attestations",
        sabotage=Sabotage(
            module="world/epoch.py",
            before="                if node.id not in attestations\n                else derive.CapturedCoreference(\n",
            after="                if True\n                else derive.CapturedCoreference(\n",
        ),
        checks=(
            "acceptance/test_coreference_acceptance.py::test_the_balance_sequence_is_attester_symmetric_and_retains_every_record_durably",
            "test_coreference_attestation.py::TestTheCaptureLift::test_a_stored_attestation_is_captured_and_reduced",
        ),
    ),
    Arm(
        row="W15i",
        asserts="event tokens add records but no weight",
        sabotage=Sabotage(
            module="world/rules_v1/coreference.py",
            before='        units.setdefault(endpoints, set()).add((stance, _nfc(attestation["actor"]), _nfc(attestation["grounds"])))\n    return {\n        "pairs": [\n            {\n                "endpoints": [left, right],\n                "balance": sum(stance for stance, _actor, _grounds in distinct),\n',
            after='        units.setdefault(endpoints, set()).add((stance, _nfc(attestation["actor"]), _nfc(attestation["grounds"]), attestation["event_token"]))\n    return {\n        "pairs": [\n            {\n                "endpoints": [left, right],\n                "balance": sum(stance for stance, _actor, _grounds, _token in distinct),\n',
        ),
        checks=(
            "acceptance/test_coreference_acceptance.py::test_exact_duplicates_add_no_weight_and_different_grounds_do_durably",
        ),
    ),
    Arm(
        row="W15j",
        asserts="the reduction normalizes its key to NFC",
        sabotage=Sabotage(
            module="world/rules_v1/coreference.py",
            before='def _nfc(value):\n    return unicodedata.normalize("NFC", value)\n',
            after="def _nfc(value):\n    return value\n",
        ),
        checks=(
            "test_coreference_attestation.py::TestTheRuleNormalizes::test_two_normalization_forms_of_one_grounds_are_one_unit",
        ),
    ),
    Arm(
        row="W15k",
        asserts="edge reads require every live corpus covered",
        sabotage=Sabotage(
            module="world/read.py",
            before="    missing = tuple(\n        corpus_id for corpus_id in registry._live_corpus_ids(world.registry()) if corpus_id not in covered\n    )\n",
            after="    missing = ()\n",
        ),
        checks=(
            "acceptance/test_coreference_acceptance.py::test_coverage_bounds_the_balance_and_no_epoch_is_unspellable_durably",
        ),
    ),
    Arm(
        row="W15l",
        asserts="attestations carry no relations",
        sabotage=Sabotage(
            module="stored.py",
            before='    return _node("coreference-attestation", slug, title, {COREFERENCE_ATTESTATION_FACET: facet}, ())\n',
            after='    return _node("coreference-attestation", slug, title, {COREFERENCE_ATTESTATION_FACET: facet}, [Relation(source=f"coreference-attestation:{slug}", predicate="cites", target=endpoint) for endpoint in facet["endpoints"]])\n',
        ),
        checks=(
            "acceptance/test_coreference_acceptance.py::test_closure_rewrites_nothing_durably",
            "test_coreference_attestation.py::TestTheBuilder::test_it_sorts_the_pair_digests_the_facet_and_carries_no_relations",
        ),
    ),
    Arm(
        row="W15m",
        asserts="import validates attestation endpoints and shape",
        sabotage=Sabotage(
            module="corpus.py",
            before='            elif record.kind == "coreference-attestation":\n                try:\n                    attestation = self._validated_coreference(record)\n',
            after="            elif False:\n                try:\n                    attestation = self._validated_coreference(record)\n",
        ),
        checks=(
            "test_coreference_attestation.py::TestImport::test_a_bundled_attestation_is_validated_and_resolved_over_the_union",
        ),
    ),
    Arm(
        row="W15n",
        asserts="occurrence records are excluded endpoints",
        sabotage=Sabotage(
            module="stored.py",
            before='    "retraction",\n    "instrument-certification",\n)\n',
            after='    "retraction",\n    "instrument-certification",\n    "act-report",\n)\n',
        ),
        checks=(
            "test_coreference_attestation.py::TestTheKindIsGoverned::test_the_endpoint_kinds_are_the_world_kinds_less_the_three_exclusions",
        ),
    ),
    # 2026-09-10: the projection-only bypass survived the independent identity check.
    Arm(
        row="X12a",
        asserts="the receipt rebuild compares the published reduction",
        sabotage=Sabotage(
            module="world/read.py",
            before='    if epoch._document_bytes(rebuilt) != _claimed_projection(published, kind, receipt):\n        return derive.ReceiptOutcome(\n            kind,\n            "refuted",\n            "rebuilding this subject over the named states with the named implementation "\n            "produced a different projection from the one this epoch published",\n        )\n    if derive.subject_identity(kind, rebuilt) != receipt.subject_identity:\n        return derive.ReceiptOutcome(\n            kind,\n            "refuted",\n            f"the rebuilt subject has identity {derive.subject_identity(kind, rebuilt)}, "\n            f"not the {receipt.subject_identity} this receipt names",\n        )\n',
            after='    if kind != "coreference-reduction" and epoch._document_bytes(rebuilt) != _claimed_projection(published, kind, receipt):\n        return derive.ReceiptOutcome(\n            kind,\n            "refuted",\n            "rebuilding this subject over the named states with the named implementation "\n            "produced a different projection from the one this epoch published",\n        )\n    if kind != "coreference-reduction" and derive.subject_identity(kind, rebuilt) != receipt.subject_identity:\n        return derive.ReceiptOutcome(\n            kind,\n            "refuted",\n            f"the rebuilt subject has identity {derive.subject_identity(kind, rebuilt)}, "\n            f"not the {receipt.subject_identity} this receipt names",\n        )\n',
        ),
        checks=(
            "acceptance/test_coreference_acceptance.py::test_omission_and_a_wrong_balance_refute_and_move_no_digest_durably",
            "test_coreference_attestation.py::TestPopulatedReceipts::test_an_omitted_attestation_and_a_wrong_balance_refute_and_move_no_digest",
        ),
    ),
    Arm(
        row="X12b",
        asserts="coreference is outside the belief input digest",
        sabotage=Sabotage(
            module="world/derive.py",
            before="    return producers[0].subject_identity\n",
            after='    return v1.digest(PRODUCER_SNAPSHOT_DOMAIN, [producers[0].subject_identity, *sorted(r.subject_identity for r in receipts if r.kind == "coreference-reduction")])\n',
        ),
        checks=("acceptance/test_coreference_acceptance.py::test_the_digest_boundary_holds_on_one_coverage_durably",),
    ),
    Arm(
        row="X12c",
        asserts="pair membership alone does not validate balance",
        sabotage=Sabotage(
            module="world/read.py",
            before='    if epoch._document_bytes(rebuilt) != _claimed_projection(published, kind, receipt):\n        return derive.ReceiptOutcome(\n            kind,\n            "refuted",\n            "rebuilding this subject over the named states with the named implementation "\n            "produced a different projection from the one this epoch published",\n        )\n    if derive.subject_identity(kind, rebuilt) != receipt.subject_identity:\n        return derive.ReceiptOutcome(\n            kind,\n            "refuted",\n            f"the rebuilt subject has identity {derive.subject_identity(kind, rebuilt)}, "\n            f"not the {receipt.subject_identity} this receipt names",\n        )\n',
            after='    if kind == "coreference-reduction":\n        rebuilt_members = {\n            tuple(cast(Sequence[str], pair["endpoints"]))\n            for pair in cast(Sequence[Mapping[str, object]], rebuilt["pairs"])\n        }\n        claimed_members = {\n            tuple(cast(Sequence[str], pair["endpoints"]))\n            for pair in cast(\n                Sequence[Mapping[str, object]], published.documents["coreference-map.yaml"]["pairs"]\n            )\n        }\n        mismatched = rebuilt_members != claimed_members\n    else:\n        mismatched = (\n            epoch._document_bytes(rebuilt) != _claimed_projection(published, kind, receipt)\n            or derive.subject_identity(kind, rebuilt) != receipt.subject_identity\n        )\n    if mismatched:\n        return derive.ReceiptOutcome(\n            kind,\n            "refuted",\n            "rebuilding this subject over the named states with the named implementation "\n            "produced a different projection from the one this epoch published",\n        )\n',
        ),
        checks=(
            "acceptance/test_coreference_acceptance.py::test_a_membership_only_rebuild_does_not_validate_a_wrong_balance_durably",
        ),
    ),
    Arm(
        row="W8aa",
        asserts="capture respects declared coverage",
        sabotage=Sabotage(
            module="world/epoch.py",
            before="    for corpus_id in preflight.coverage:\n        carrier = preflight.carriers[corpus_id]\n",
            after="    for corpus_id in registry._live_corpus_ids(world.registry()):\n        carrier = registry._carrier_roots(world.config, corpus_id)[0]\n",
        ),
        checks=(
            "acceptance/test_coreference_acceptance.py::test_the_digest_boundary_holds_on_one_coverage_durably",
            "test_coreference_attestation.py::TestPopulatedReceipts::test_coverage_bounds_the_balance_and_the_narrower_epoch_is_indeterminate_over_the_wider_world",
        ),
    ),
    Arm(
        row="M3a",
        asserts="attestations enter no retraction standing graph",
        sabotage=Sabotage(
            module="corpus.py",
            before='        if stored_node.kind != "retraction":\n            continue\n        retraction = view.get(stored_node.id)\n',
            after='        if stored_node.kind not in ("retraction", "coreference-attestation"):\n            continue\n        retraction = view.get(stored_node.id)\n',
        ),
        checks=(
            "acceptance/test_coreference_acceptance.py::test_coreference_between_retractions_closes_no_route_durably",
        ),
    ),
    Arm(
        row="W4a",
        asserts="the operation inventory contains no merge",
        sabotage=Sabotage(
            module="corpus.py",
            before="    def retract(self, record: Node) -> OperationCommit:\n        return self._run(lambda: self._writer.retract(record))\n",
            after="    def retract(self, record: Node) -> OperationCommit:\n        return self._run(lambda: self._writer.retract(record))\n\n    merge = retract\n",
        ),
        checks=(
            "acceptance/test_coreference_acceptance.py::test_no_operation_retires_an_address_on_coreference_grounds_durably",
        ),
    ),
)
