"""Cut 30 canonical declaration: W5a re-read on the slice 6 reconciliation arms."""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS = ("W5a",)
_U = "test_identifier_correction.py::TestRelocation"
_R = "test_source_address.py::TestReaders"
UNIT_CHECKS = {"W5a": f"{_U}::test_consolidate_absorbs_divergent_histories"}
# The absorb test is also cut 25's re-targeted W5a-m check (test_n2_cut25._LIVE_ARMS, 2026-09-15):
# the successor discharge is cited by both, on purpose.
CO_CITED = (f"{_U}::test_consolidate_absorbs_divergent_histories",)


def unit_of(row: str) -> str:
    """Rows are `<unit>` or `<unit>-<letter>`."""
    unit, hyphen, suffix = row.partition("-")
    if unit not in DECLARATION_UNITS or (hyphen and not (len(suffix) == 1 and suffix.islower())):
        raise ValueError(f"{row!r} is not a cut-30 row")
    return unit


def _arm(row, assertion, module, before, after, *checks):
    return Arm(row=row, asserts=assertion, sabotage=Sabotage(module=module, before=before, after=after), checks=tuple(checks))


CUT30_ARMS = (
    _arm("W5a-p", "Divergent histories are absorbed, not dropped.", "stored.py",
         "    if not remainder:\n        return copy.deepcopy(list(keep))\n",
         "    if True:\n        return copy.deepcopy(list(keep))\n",
         f"{_U}::test_consolidate_absorbs_divergent_histories"),
    _arm("W5a-q", "The absorbed chain is validated.", "stored.py",
         '            absorbed = _read_chain(raw["absorbed"], f"{here} absorbed", seen)\n            if dict(absorbed[-1].to_identifiers) != dict(frm):',
         '            absorbed = _read_chain(raw["absorbed"], f"{here} absorbed", seen)\n            if False:',
         f"{_R}::test_malformed_consolidation_shapes_refuse[absorbed-ends-elsewhere]"),
    _arm("W5a-r", "Held addresses reach into absorbed chains.", "stored.py",
         "        addresses |= held_source_addresses(correction.absorbed)\n",
         "        pass\n",
         f"{_R}::test_held_addresses_reach_into_absorbed_chains_once",
         f"{_R}::test_validate_source_history_holds_the_redirect_set_to_the_absorbed_chain[omits-an-absorbed-address]"),
    _arm("W5a-s", "One token is one event across chains.", "stored.py",
         "        if token in seen and seen[token] != raw:\n",
         "        if False:\n",
         f"{_R}::test_malformed_consolidation_shapes_refuse[conflicting-reuse]"),
    _arm("W5a-t", "A consolidation entry changes nothing.", "stored.py",
         '        elif "absorbed" in raw:\n',
         "        elif False:\n",
         f"{_R}::test_malformed_consolidation_shapes_refuse[six-keys-unequal]"),
    _arm("W5a-u", "The entry carries the operation's token.", "relocation.py",
         "                event_token=intent.event_token,\n",
         "                event_token=secrets.token_hex(16),\n",
         f"{_U}::test_consolidate_absorbs_divergent_histories"),
    _arm("W5a-v", "A prefix fast-forwards without an entry.", "stored.py",
         "    if list(keep) == list(other)[: len(keep)]:\n        return copy.deepcopy(list(other))\n",
         "    if False:\n        return copy.deepcopy(list(other))\n",
         f"{_U}::test_consolidate_fast_forwards_a_prefix",
         "test_source_address.py::TestReconcile::test_a_proper_prefix_fast_forwards_either_way"),
    _arm("W5a-x", "An already-held event is not absorbed again.", "stored.py",
         '    remainder = [entry for entry in other if entry["event_token"] not in held]\n',
         "    remainder = list(other)\n",
         f"{_U}::test_consolidate_retries_after_an_interrupted_replacement",
         "test_source_address.py::TestReconcile::test_an_already_absorbed_chain_is_not_absorbed_again"),
    _arm("W5a-y", "Reconciliation refuses conflicting reuse before any intent.", "stored.py",
         "        if token in held and held[token] != event:\n",
         "        if False:\n",
         f"{_U}::test_consolidate_refuses_conflicting_token_reuse"),
    _arm("W5a-z", "The rationale is validated before reconciliation on every path.", "relocation.py",
         "        if not isinstance(rationale, str) or not rationale:\n",
         "        if False:\n",
         f"{_U}::test_consolidate_refuses_a_malformed_rationale_on_both_paths[identity-path-empty]",
         f"{_U}::test_consolidate_refuses_a_malformed_rationale_on_both_paths[absorb-path-empty]"),
)
