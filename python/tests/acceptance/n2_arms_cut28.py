"""Cut 28 canonical declaration: W7, W8 and W8b over the slice 4 seams."""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS = ("W7", "W8", "W8b")
_A = "acceptance/test_world_selection_acceptance.py"
UNIT_CHECKS = {
    "W7": f"{_A}::test_w7_addresses_selects_the_other_corpus_record_and_contributes_its_corpus_durably",
    "W8": f"{_A}::test_w8_duplicate_location_refuses_the_build_in_either_order_and_consolidate_repairs_durably",
    "W8b": f"{_A}::test_w8b_uid_corruption_offers_no_repair_and_consolidate_is_unavailable_durably",
}
CO_CITED = ()


def unit_of(row: str) -> str:
    """Rows are `<unit>` or `<unit>-<letter>`."""
    unit, hyphen, suffix = row.partition("-")
    if unit not in DECLARATION_UNITS or (hyphen and not (len(suffix) == 1 and suffix.islower())):
        raise ValueError(f"{row!r} is not a cut-28 row")
    return unit


def _arm(row, assertion, module, before, after, check):
    checks = (f"{_A}::{check}",)
    if row == "W7-a":
        checks += (UNIT_CHECKS["W7"],)
    return Arm(row=row, asserts=assertion, sabotage=Sabotage(module=module, before=before, after=after), checks=checks)


_DAMAGED = "test_w7_a_damaged_view_refuses_durably"
_DRIFT = "test_w7_a_drifted_view_refuses_and_the_earlier_capture_evaluates_durably"
_UNKNOWN = "test_w7_an_unknown_address_refuses_naming_every_unknown_one_durably"
_ABSENT = "test_w7_the_absent_corpus_refuses_reports_or_names_itself_by_form_durably"
_TWO = "test_w7_two_clauses_select_and_contribute_both_durably"
_CLOSURE = "test_w7_closure_out_selects_the_other_corpus_dataset_and_not_the_run_durably"
_CYCLE = "test_w7_a_retired_anchor_over_a_cycle_selects_what_the_live_anchor_selects_durably"
_DANGLING = "test_w7_dangling_and_absent_inbound_steps_are_reported_not_dropped_durably"
_PROJECTION = "test_w7_projection_members_are_asserted_directly_durably"
_STALE_SELECTED = "test_w7_a_stale_selected_record_refuses_durably"
_STALE_TERM = "test_w7_a_stale_edit_that_removed_the_term_refuses_durably"
_TERMS = "test_w7_terms_in_arguments_and_restrictions_select_and_a_malformed_facet_refuses_durably"
_TYPE = "test_w7_empty_clauses_and_a_read_view_durably"
_DUP = "test_w8_duplicate_location_refuses_the_build_in_either_order_and_consolidate_repairs_durably"
_CONFLICT = "test_w8_address_conflict_refuses_the_build_and_consolidate_and_the_write_boundary_durably"
_CORRUPT = "test_w8b_uid_corruption_offers_no_repair_and_consolidate_is_unavailable_durably"
_SAME = "test_w8b_duplicate_location_is_the_same_finding_with_shared_or_distinct_uids_durably"
_PRECEDENCE = "test_w8b_corruption_outranks_duplication_and_a_corpus_alone_reports_neither_durably"

CUT28_ARMS = (
    _arm("W7-a", "Damage refuses selection.", "world/selection.py", "if view.damaged():", "if False:", _DAMAGED),
    _arm("W7-b", "Drift refuses selection.", "world/selection.py", "if moved:", "if False:", _DRIFT),
    _arm("W7-c", "Unknown addresses refuse.", "world/selection.py", "    if unknown:\n        raise SelectionRefused(\"address-unknown\", refs=unknown)", "    if False:\n        raise SelectionRefused(\"address-unknown\", refs=unknown)", _UNKNOWN),
    _arm("W7-d", "Absent addresses remain distinct from unknown ones.", "world/selection.py", '        raise SelectionRefused(\n            "address-not-present",\n            refs=[address for address, _ in not_present],\n            corpus_ids=[corpus_id for _, corpus_id in not_present],\n        )', '        raise SelectionRefused("address-unknown", refs=[address for address, _ in not_present])', _ABSENT),
    _arm("W7-e", "Clauses union while predicates intersect.", "world/selection.py", "            members = denoted if members is None else members & denoted\n        selected |= members or set()", "            members = denoted\n        selected = members if not selected else selected & members", _TWO),
    _arm("W7-f", "Closure excludes its anchor.", "world/selection.py", "        return set(reach.reached)", "        return set(reach.reached) | {live}", _CLOSURE),
    _arm("W7-g", "Closure begins at the live address.", "world/selection.py", "        reach = closure(live, _QueryAdjacency(view, predicate.predicates, predicate.direction))", "        reach = closure(predicate.anchor, _QueryAdjacency(view, predicate.predicates, predicate.direction))", _CYCLE),
    _arm("W7-h", "Inbound unresolved edges are retained.", "world/selection.py", '            if edge.source_uid is None:\n                steps.append(\n                    Step(\n                        stored=edge.relation.source,\n                        resolved=None,\n                        entry=RelationEntry(source=ref, position=position, predicate=self._predicate, target=edge.relation.source),\n                    )\n                )\n                continue', "            if edge.source_uid is None:\n                continue", _DANGLING),
    _arm("W7-i", "Unresolved steps are projection members.", "world/selection.py", '            "unresolved": [step.projection() for step in self.unresolved],', '            "unresolved": [],', _PROJECTION),
    _arm("W7-j", "Absent corpora are projection members.", "world/selection.py", '            "absent": list(self.absent),', '            "absent": [],', _PROJECTION),
    _arm("W7-k", "Selected records are validated.", "world/selection.py", "    for address in selected:\n        validated_node(held[address][1])", "    pass", _STALE_SELECTED),
    _arm("W7-l", "Claim records are validated before facet reads.", "world/selection.py", "def _binds_term(node: Node, term: str) -> bool:\n    validated_node(node)", "def _binds_term(node: Node, term: str) -> bool:", _STALE_TERM),
    _arm("W7-m", "Restrictions participate in term matching.", "world/selection.py", "    return term in args or term in restrictions", "    return term in args", _TERMS),
    _arm("W7-n", "Malformed claims refuse.", "world/selection.py", '        raise SelectionRefused("record-malformed", refs=[node.id]) from None', "        return False", _TERMS),
    _arm("W7-p", "Stored term comparison preserves case.", "decode.py", '    return tuple(args), tuple(body["restriction"] for body in qualifier_bodies.values())', '    return tuple(term.lower() for term in args), tuple(body["restriction"] for body in qualifier_bodies.values())', _TERMS),
    _arm("W7-o", "Corpus-local views are rejected.", "world/selection.py", "    if type(view) is not WorldReadView:", "    if False:", _TYPE),
    _arm("W8-a", "Duplicate locations refuse publication.", "world/derive.py", "        if len(locations) > 1:\n            raise AddressMapConflict(Finding(\n                severity=\"error\",\n                code=\"duplicate-location\",", "        if False:\n            raise AddressMapConflict(Finding(\n                severity=\"error\",\n                code=\"duplicate-location\",", _DUP),
    _arm("W8-b", "Conflicting source maps cannot consolidate.", "relocation.py", "            if keep_map != other_map:", "            if False:", _CONFLICT),
    _arm("W8-c", "Move refuses an occupied destination before writing.", "relocation.py", '        if destination.read_view.resolve(node.id) == node.id:\n            raise DuplicateLocation(\n                f"{node.id}: destination already holds this canonical address"\n            )', "        if False:\n            pass", _DUP),
    _arm("W8b-a", "One uid cannot name multiple addresses.", "world/derive.py", "        if len({address for _, address in locations}) > 1:", "        if False:", _CORRUPT),
    _arm("W8b-b", "Uid corruption outranks duplicate location.", "world/derive.py", '    for uid, locations in by_uid.items():\n        if len({address for _, address in locations}) > 1:\n            raise AddressMapConflict(Finding(\n                severity="error",\n                code="uid-corruption",\n                ref=uid,\n                detail=f"corpus/address claims={tuple(locations)!r}",\n                message="one uid names different canonical addresses; no repair is offered",\n            ))\n    for address, locations in by_address.items():\n        if len(locations) > 1:\n            raise AddressMapConflict(Finding(\n                severity="error",\n                code="duplicate-location",\n                ref=address,\n                detail=f"corpus/uid claims={tuple(locations)!r}",\n                message="one canonical address is held in multiple corpora; resolve with consolidate",\n            ))', '    for address, locations in by_address.items():\n        if len(locations) > 1:\n            raise AddressMapConflict(Finding(\n                severity="error", code="duplicate-location", ref=address, detail=f"corpus/uid claims={tuple(locations)!r}", message="duplicate"\n            ))\n    for uid, locations in by_uid.items():\n        if len({address for _, address in locations}) > 1:\n            raise AddressMapConflict(Finding(\n                severity="error", code="uid-corruption", ref=uid, detail=f"corpus/address claims={tuple(locations)!r}", message="corrupt"\n            ))', _PRECEDENCE),
    _arm("W8b-c", "Duplicate location ignores uid equality.", "world/derive.py", "        by_address.setdefault(record.address, []).append((corpus_id, record.uid))", "        by_address.setdefault((record.address, record.uid), []).append((corpus_id, record.uid))", _SAME),
    _arm("W8b-d", "Consolidation requires one canonical address.", "relocation.py", "        if keep_node.id != other_node.id:", "        if False:", _CORRUPT),
)
