"""Frozen cut-41 declaration: twelve units, twelve sabotage arms, one each."""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS = (
    "Z1-a",
    "Z1-b",
    "Z1-c",
    "Z1-d",
    "Z2-a",
    "Z2-b",
    "Z3-a",
    "Z4-a",
    "Z4-b",
    "Z5-a",
    "Z5-b",
    "Z5-c",
)
_MODULE = "acceptance/test_live_selection_acceptance.py"
UNIT_CHECKS = {
    "Z1-a": f"{_MODULE}::test_z1_a_every_present_admitted_corpus_is_captured_and_stamped_durably",
    "Z1-b": f"{_MODULE}::test_z1_b_a_terminal_corpus_is_never_covered_durably",
    "Z1-c": f"{_MODULE}::test_z1_c_an_absent_corpus_is_listed_and_its_addresses_are_unknown_durably",
    "Z1-d": f"{_MODULE}::test_z1_d_coverage_is_the_registry_not_an_epoch_durably",
    "Z2-a": f"{_MODULE}::test_z2_a_a_state_moving_inside_the_hold_discards_the_evaluation_durably",
    "Z2-b": f"{_MODULE}::test_z2_b_state_reads_and_enumeration_run_inside_the_corpus_hold_durably",
    "Z3-a": f"{_MODULE}::test_z3_a_the_stamp_names_the_states_the_selection_was_denoted_over_durably",
    "Z4-a": f"{_MODULE}::test_z4_a_a_malformed_corpus_refuses_and_is_never_omitted_durably",
    "Z4-b": f"{_MODULE}::test_z4_b_a_disagreeing_base_pin_refuses_durably",
    "Z5-a": f"{_MODULE}::test_z5_a_a_shared_uid_duplicate_location_is_publishs_conflict_durably",
    "Z5-b": f"{_MODULE}::test_z5_b_uid_corruption_outranks_duplicate_location_durably",
    "Z5-c": f"{_MODULE}::test_z5_c_a_uid_shared_with_a_record_outside_the_map_refuses_after_the_map_durably",
}
CO_CITED = ()

_LIVE = "world/live.py"


def unit_of(row: str) -> str:
    """Every arm homes its own unit; no row shares one."""
    if row not in DECLARATION_UNITS:
        raise ValueError(f"{row!r} is not a cut-41 row")
    return row


def _arm(row, assertion, before, after):
    return Arm(
        row=row,
        asserts=assertion,
        sabotage=Sabotage(module=_LIVE, before=before, after=after),
        checks=(UNIT_CHECKS[unit_of(row)],),
    )


CUT41_ARMS = (
    _arm(
        "Z1-a",
        "Every present admitted corpus is captured and stamped, so skipping the last covered corpus loses its records and its coverage pair.",
        "    for corpus_id in sorted(carriers):",
        "    for corpus_id in sorted(carriers)[:-1]:",
    ),
    _arm(
        "Z1-b",
        "Coverage is the registry's live set, so a retired corpus whose carrier is still configured is never captured.",
        "        covered = registry._live_corpus_ids(world._state.registry)",
        "        covered = tuple(sorted({record.corpus_id for record in world._state.registry.admissions}))",
    ),
    _arm(
        "Z1-c",
        "An admitted corpus with no present carrier is listed in `absent`, so the selection is incomplete.",
        "            else:\n                absent.append(corpus_id)",
        "            else:\n                pass",
    ),
    _arm(
        "Z1-d",
        "Coverage never comes from an epoch: a never-published world evaluates, and a corpus admitted after the epoch is covered.",
        "    carriers, absent = _coverage(world)\n",
        "    from beliefs.world.read import current_epoch\n\n"
        "    carriers, absent = _coverage(world)\n"
        "    carriers = {corpus_id: root for corpus_id, root in carriers.items() if corpus_id in dict(current_epoch(world).coverage)}\n",
    ),
    _arm(
        "Z2-a",
        "A state that moves inside a corpus's capture hold raises `CaptureDrift` and returns nothing.",
        "            if before != after:",
        "            if False:",
    ),
    _arm(
        "Z2-b",
        "Both state reads and the enumeration run inside the corpus's own capture hold, which refuses a held writer lock.",
        "        with _operation_lock_for(carrier).capture():",
        '        with __import__("contextlib").nullcontext():',
    ),
    _arm(
        "Z3-a",
        "The stamp carries the states read inside each hold, never a state re-read after the captures.",
        "        stamp=CaptureStamp(world.config.world_id, tuple(sorted(states.items()))),",
        "        stamp=CaptureStamp(world.config.world_id, tuple(sorted((corpus_id, registry.corpus_state_identity(carriers[corpus_id])) for corpus_id in states))),",
    ),
    _arm(
        "Z4-a",
        "A present corpus whose construction fails is collected as damage and refuses the evaluation, never silently omitted.",
        "            except CorpusStateMalformed:\n                damaged.append(corpus_id)\n                continue",
        "            except CorpusStateMalformed:\n                continue",
    ),
    _arm(
        "Z4-b",
        "A present corpus whose base pin disagrees refuses the evaluation as damage.",
        "                view._require_base_pin()\n",
        "                pass\n",
    ),
    _arm(
        "Z5-a",
        "World-record conflicts are publish's: the scoped uid check runs only after the address map, so a shared-uid duplicate location is `duplicate-location`.",
        "    recorded = _address_map(captured, states)\n    _require_unmapped_uids_unique(captured)\n",
        "    _uids = [node.uid for records in captured.values() for node in records]\n"
        "    if len(_uids) != len(set(_uids)):\n"
        '        raise ResolutionRefused("a uid is held twice")\n'
        "    recorded = _address_map(captured, states)\n",
    ),
    _arm(
        "Z5-b",
        "Every captured world record reaches the address map, so uid corruption is refused before any duplicate location.",
        "    located = [\n"
        "        (corpus_id, node) for corpus_id in sorted(captured) for node in captured[corpus_id] if node.kind in stored.WORLD_KINDS\n"
        "    ]",
        "    located = list({\n"
        "        node.uid: (corpus_id, node) for corpus_id in sorted(captured) for node in captured[corpus_id] if node.kind in stored.WORLD_KINDS\n"
        "    }.values())",
    ),
    _arm(
        "Z5-c",
        "A uid a record outside the map shares with another corpus refuses `ResolutionRefused` (W8b, the view's half).",
        "    _require_unmapped_uids_unique(captured)\n",
        "    pass\n",
    ),
)
