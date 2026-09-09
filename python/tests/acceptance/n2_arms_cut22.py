"""Cut 22's nine frozen declaration units and their source sabotages
(docs/designs/2026-09-08-conformance-cut-22.md §3, §5 item 4), one arm per
frozen sabotage."""

from __future__ import annotations

from n2_arms import Arm, Sabotage

_DOMAIN, _PROFILE, _CONSULTED, _READ, _EVAL, _BELIEF, _CLOSURE = (
    "contract/domain.py", "profile.py", "consulted.py", "facet_read.py", "evaluation.py", "belief.py", "closure.py",
)
_TDC, _TP, _TC, _TFR, _TDF, _TSB = (
    "test_domain_contract.py", "test_profile.py", "test_consulted.py", "test_facet_read.py",
    "test_domain_facet_read.py", "test_shipped_biology.py",
)

DECLARATION_UNITS = ("B1", "B2", "B3", "B4", "B5", "B6", "B7", "D6", "M8")
CO_CITED: tuple[str, ...] = ()


def unit_of(row: str) -> str:
    return row.rstrip("abcdefghijklmnopqrstuvwxyz")


CUT22_ARMS = (
    Arm("B1a", "drop the own-namespace refusal",
        Sabotage(_DOMAIN, "    if foreign == namespace:\n", "    if False and foreign == namespace:\n"),
        (f"{_TDC}::TestSortReferences::test_own_namespace_is_refused",)),
    Arm("B1b", "namespace a namespaced name again",
        Sabotage(_PROFILE, '    term = name if "/" in name else contract.term(name)\n', "    term = contract.term(name)\n"),
        (f"{_TP}::TestCrossContractSlots::test_a_foreign_sort_resolves_when_its_contract_is_compiled",)),
    Arm("B1c", "drop the unresolved-reference refusal",
        Sabotage(_PROFILE, "    if term not in sorts:\n        namespace = term.partition(\"/\")[0]\n", "    if False:\n        namespace = term.partition(\"/\")[0]\n"),
        (f"{_TP}::TestCrossContractSlots::test_an_unresolved_reference_refuses_naming_the_namespace",)),
    Arm("B2a", "add the operator's contract alone",
        Sabotage(_CONSULTED, "        for sort in operator.arg_sorts:\n            read.add(profile.sorts[sort].contract)\n", "        for sort in ():\n            read.add(profile.sorts[sort].contract)\n"),
        (f"{_TC}::TestSlotSorts::test_a_claim_reaches_its_slot_sorts_contracts",)),
    Arm("B2b", "stop collecting facet namespaces",
        Sabotage(_CONSULTED, "            if separator:\n                read.add(namespace)\n", "            if separator:\n                pass\n"),
        (f"{_TDF}::test_isolated_case_biology_enters_through_the_ledger_alone",)),
    Arm("B3a", "a field-wise constructor",
        Sabotage(_READ, "        raise MalformedRecord(\n            \"FacetRead is minted by the reader", "        return None  # sabotage: a field-wise constructor\n        raise MalformedRecord(\n            \"FacetRead is minted by the reader"),
        (f"{_TFR}::test_facet_read_has_no_field_wise_constructor",)),
    Arm("B3b", "mint over anything shaped like a view",
        Sabotage(_READ, "    if type(view) is not ReadView:\n", "    if False:\n"),
        (f"{_TFR}::test_the_reader_refuses_anything_but_a_corpus_view",)),
    Arm("B3c", "a view over a fabricated corpus",
        Sabotage("corpus.py", "        if type(corpus) is not Corpus:\n", "        if False:\n"),
        (f"{_TFR}::test_a_view_over_a_fabricated_corpus_is_refused",)),
    Arm("B4a", "skip re-validation",
        Sabotage(_READ, "        validate_payload(facet, payload, where=node.id)\n", "        pass\n"),
        (f"{_TFR}::test_a_malformed_payload_refuses_the_derivation",)),
    Arm("B4b", "fetch an unheld observed dataset",
        Sabotage(_EVAL, "            if not view.holds(target):\n                continue\n", ""),
        (f"{_TDF}::test_an_absent_observed_dataset_is_absent_from_gather",)),
    Arm("B5a", "empty the observed_facets member",
        Sabotage(_CLOSURE, '        "observed_facets": [row.projection() for row in observed_facets],\n', '        "observed_facets": [],\n'),
        (f"{_TDF}::test_a_payload_byte_change_moves_the_digest",)),
    Arm("B5b", "take the ledger from nowhere",
        Sabotage(_BELIEF, "    for row in records.observed_facets:\n        ledger.setdefault(row.address, []).append(row.key)\n", "    for row in ():\n        ledger.setdefault(row.address, []).append(row.key)\n"),
        (f"{_TDF}::test_isolated_case_a_biology_bump_moves_the_digest", f"{_TDF}::test_gather_and_evaluate_agree_on_the_consulted_set")),
    Arm("B6a", "read the shipped pack from the base's path",
        Sabotage(_PROFILE, '    resource = resources.files("beliefs").joinpath(f"domains/{namespace}/DOMAIN.yaml")\n', '    resource = resources.files("beliefs").joinpath("contracts/science/CONTRACT.yaml")\n'),
        (f"{_TSB}::test_the_shipped_pack_declares_the_floor",)),
    Arm("B7a", "drop the science agreement",
        Sabotage(_CONSULTED, '    if base_identity != "science:" + profile.base_contract_identity:\n', "    if False:\n"),
        (f"{_TC}::TestPinAgreement::test_the_base_pin_must_agree_with_the_profile",)),
    Arm("B7b", "drop the domain agreement",
        Sabotage(_CONSULTED, '        if identity != f"{namespace}:{expected}":\n', "        if False:\n"),
        (f"{_TC}::TestPinAgreement::test_a_consulted_namespace_pinned_to_another_identity_refuses",)),
    Arm("D6a", "drop observed addresses from the closure nodes",
        Sabotage(_BELIEF, "    closure_nodes = tuple(a.identity() for a in matched) + observed\n", "    closure_nodes = tuple(a.identity() for a in matched)\n"),
        (f"{_TDF}::test_isolated_case_a_biology_bump_moves_the_digest",)),
    Arm("M8a", "drop the sort-contract collection under a belief",
        Sabotage(_CONSULTED, "        for sort in operator.arg_sorts:\n            read.add(profile.sorts[sort].contract)\n", "        for sort in ():\n            read.add(profile.sorts[sort].contract)\n"),
        (f"{_TDF}::test_m8_an_editorial_bump_of_a_foreign_sorts_contract_leaves_claim_identity_and_moves_the_digest",)),
)
