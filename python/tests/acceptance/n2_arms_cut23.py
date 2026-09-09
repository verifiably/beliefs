"""Cut 23's eight frozen declaration units and their source sabotages — one arm
per sabotage site the cut document §5 item 4 names."""

from n2_arms import Arm, Sabotage

_VIEW = "world/view.py"
_CORPUS = "corpus.py"
_LINEAGE = "lineage.py"
_RESOLUTION = "resolution.py"
_EVALUATION = "evaluation.py"
_READ = "world/read.py"
_A = "acceptance/test_world_view_acceptance.py"

DECLARATION_UNITS: tuple[str, ...] = ("D3", "S1", "S1a", "S5", "W6", "W10", "R19", "R23")
CO_CITED: tuple[str, ...] = ()


def unit_of(row: str) -> str:
    """The unit a lettered row belongs to. `W8b` and `S1a` are units whose names
    end in a letter, so stripping letters would misfile them; the longest unit
    the row spells, exactly or plus one lowercase letter, is the answer."""
    matches = [
        unit
        for unit in DECLARATION_UNITS
        if row == unit or (row.startswith(unit) and len(row) == len(unit) + 1 and row[-1].islower())
    ]
    return max(matches, key=len)


CUT23_ARMS = (
    Arm(
        row="W10b",
        asserts="map-first resolution: an address the epoch never observed is unknown whatever a carrier holds",
        sabotage=Sabotage(
            module=_VIEW,
            before="        entry = self._recorded.get(ref)\n        if entry is None:\n            return Unknown(self._stamp)\n",
            after=(
                "        entry = self._recorded.get(ref)\n        if entry is None:\n"
                "            for corpus_id, live in self._live.items():\n"
                "                if live.holds(ref):\n"
                "                    return Resolved(Location(corpus_id, live.get(ref).uid), self._stamp)\n"
                "            return Unknown(self._stamp)\n"
            ),
        ),
        checks=(f"{_A}::test_the_capture_is_coherent_and_drift_is_the_next_opens_durably",),
    ),
    Arm(
        row="W6b",
        asserts="an absent covered corpus is not-present, never unknown",
        sabotage=Sabotage(
            module=_VIEW,
            before="        if corpus_id in self._absent:\n            return NotPresent(self._stamp)\n",
            after="        if corpus_id in self._absent:\n            return Unknown(self._stamp)\n",
        ),
        checks=(f"{_A}::test_an_absent_corpus_is_lineage_incomplete_naming_it_durably",),
    ),
    Arm(
        row="W10c",
        asserts="get serves the capture, never the live carrier",
        sabotage=Sabotage(
            module=_VIEW,
            before="        node = self._held[located.location.corpus_id][located.location.uid]\n        return validated_node(node).model_copy(deep=True)\n",
            after="        return self._live[located.location.corpus_id].get(ref)\n",
        ),
        checks=(f"{_A}::test_the_capture_is_coherent_and_drift_is_the_next_opens_durably",),
    ),
    Arm(
        row="W10d",
        asserts="the inbound index files mapped sources only",
        sabotage=Sabotage(
            module=_VIEW,
            before="    for records in held.values():\n        for uid, node in records.items():\n            for relation in node.relations:\n",
            after="    for records in captured.values():\n        for uid, node in records.items():\n            for relation in node.relations:\n",
        ),
        checks=(f"{_A}::test_the_relation_and_lineage_chains_cross_the_edge_durably",),
    ),
    Arm(
        row="W10e",
        asserts="the inbound index resolves targets through the world map, not the local index",
        sabotage=Sabotage(
            module=_VIEW,
            before="    for records in held.values():\n        for uid, node in records.items():\n            for relation in node.relations:\n                if (target := recorded.get(relation.target)) is not None:\n",
            after=(
                "    for corpus_id, records in held.items():\n        for uid, node in records.items():\n            for relation in node.relations:\n                local = next((u for u, n in captured[corpus_id].items() if n.id == relation.target), None)\n                target = (corpus_id, local) if local is not None else recorded.get(relation.target)\n                if target is not None:\n"
            ),
        ),
        checks=(f"{_A}::test_the_relation_and_lineage_chains_cross_the_edge_durably",),
    ),
    Arm(
        row="W10f",
        asserts="an object that leaves the view is detached",
        sabotage=Sabotage(
            module=_VIEW,
            before="        return validated_node(node).model_copy(deep=True)\n",
            after="        return validated_node(node)\n",
        ),
        checks=(f"{_A}::test_a_returned_object_is_detached_durably",),
    ),
    Arm(
        row="W10",
        asserts="cross-corpus edges are ordinary at the world layer and dangling at the corpus layer",
        sabotage=Sabotage(
            module=_VIEW,
            before="            for edge in self._inbound.get(entry, ())\n",
            after="            for edge in self._inbound.get(entry, ())\n            if edge.source_uid in self._held.get(entry[0], {})\n",
        ),
        checks=(f"{_A}::test_the_world_closure_is_complete_and_the_local_one_truncates_durably",),
    ),
    Arm(
        row="S1",
        asserts="the relation chain crossing corpora returns its full closure",
        sabotage=Sabotage(
            module=_CORPUS,
            before="        for edge in self._view.inbound(ref):\n            if edge.relation.predicate != self._predicate or edge.source_uid is None:\n",
            after='        for edge in self._view.inbound(ref):\n            if edge.relation.predicate != self._predicate or edge.source_uid is None or edge.target_uid is None:\n                continue\n            if type(self._view).__name__ == "WorldReadView":\n',
        ),
        checks=(f"{_A}::test_the_relation_and_lineage_chains_cross_the_edge_durably",),
    ),
    Arm(
        row="S1a",
        asserts="the lineage chain crossing corpora, walked as a facet, returns its full closure",
        sabotage=Sabotage(
            module=_CORPUS,
            before='                        resolved=self._view.resolve(ancestor),\n                        entry=LineageEntry(dataset=node.id, route=index, position="ancestor", target=ancestor),\n',
            after='                        resolved=self._view.resolve(ancestor) if type(self._view).__name__ != "WorldReadView" else None,\n                        entry=LineageEntry(dataset=node.id, route=index, position="ancestor", target=ancestor),\n',
        ),
        checks=(f"{_A}::test_the_relation_and_lineage_chains_cross_the_edge_durably",),
    ),
    Arm(
        row="S5b",
        asserts="a route's absent run or ancestor is entered with its corpus",
        sabotage=Sabotage(
            module=_CORPUS,
            before="            for ref in (run, ancestor):\n                corpus_id = _absence_of(view, ref)\n                if corpus_id is not None:\n                    not_present[ref] = corpus_id\n",
            after="            for ref in ():\n                corpus_id = _absence_of(view, ref)\n                if corpus_id is not None:\n                    not_present[ref] = corpus_id\n",
        ),
        checks=(f"{_A}::test_an_absent_corpus_is_lineage_incomplete_naming_it_durably",),
    ),
    Arm(
        row="S5g",
        asserts="an absent root is recorded before any walk",
        sabotage=Sabotage(
            module=_CORPUS,
            before="        corpus_id = _absence_of(view, root)\n        if corpus_id is not None:\n            not_present[root] = corpus_id\n            continue\n",
            after="        corpus_id = _absence_of(view, root)\n        if corpus_id is not None:\n            continue\n",
        ),
        checks=(f"{_A}::test_an_absent_root_is_recorded_before_any_walk_durably",),
    ),
    Arm(
        row="S5c",
        asserts="a published producer survives its absent carrier",
        sabotage=Sabotage(
            module=_CORPUS,
            before="        for run in view.published_producers(dataset):\n",
            after="        for run in ():\n",
        ),
        checks=(f"{_A}::test_a_published_producer_survives_its_absent_carrier_durably",),
    ),
    Arm(
        row="S5d",
        asserts="absence gates divergence: no comparison is made over an absent producer",
        sabotage=Sabotage(
            module=_LINEAGE,
            before='        return "incomplete"\n',
            after="        pass\n",
        ),
        checks=(f"{_A}::test_a_published_producer_survives_its_absent_carrier_durably",),
    ),
    Arm(
        row="S5e",
        asserts="absence is collected from the inspected datasets' references, not the inspected set",
        sabotage=Sabotage(
            module=_LINEAGE,
            before="            for route in basis.routes:\n                for ref in (route.stored_run, route.stored_ancestor):\n                    if ref in snapshot.not_present:\n",
            after="            for route in basis.routes:\n                for ref in (route.stored_run, route.stored_ancestor):\n                    if ref in snapshot.not_present and ref in inspected:\n",
        ),
        checks=(f"{_A}::test_absence_names_what_each_root_can_discover_durably",),
    ),
    Arm(
        row="S5f",
        asserts="a refusal is not absence",
        sabotage=Sabotage(
            module=_CORPUS,
            before="    if not isinstance(view, WorldReadView):\n        return None\n    return view.corpus_of(ref) if type(view.locate(ref)) is NotPresent else None\n",
            after="    if not isinstance(view, WorldReadView):\n        return None\n    try:\n        view.get(ref)\n    except Exception:\n        return view.corpus_of(ref)\n    return None\n",
        ),
        checks=(f"{_A}::test_a_refusal_is_not_absence_durably",),
    ),
    Arm(
        row="R23b",
        asserts="not-present enters the lineage projection, so absence within coverage digests differently",
        sabotage=Sabotage(
            module=_LINEAGE,
            before='        "not_present": [\n            {"ref": ref, "corpus_id": corpus_id} for ref, corpus_id in sorted(snapshot.not_present.items())\n        ],\n',
            after='        "not_present": [],\n',
        ),
        checks=(f"{_A}::test_an_absent_corpus_is_lineage_incomplete_naming_it_durably",),
    ),
    Arm(
        row="D3b",
        asserts="a binding named in two availability states is refused",
        sabotage=Sabotage(
            module=_RESOLUTION,
            before="        if binding in table:\n            raise ResolutionError(\n",
            after='        if binding in table and entry.state != "not-present":\n            raise ResolutionError(\n',
        ),
        checks=(f"{_A}::test_the_five_outcomes_are_produced_and_kept_apart_durably",),
    ),
    Arm(
        row="D3c",
        asserts="not-present is produced, distinct from not-available",
        sabotage=Sabotage(
            module=_RESOLUTION,
            before='        if state.state == "not-present":\n',
            after='        if state.state == "never":\n',
        ),
        checks=(f"{_A}::test_the_five_outcomes_are_produced_and_kept_apart_durably",),
    ),
    Arm(
        row="R19b",
        asserts="attribution happens at the read, never after the fact",
        sabotage=Sabotage(
            module=_EVALUATION,
            before="            corpus_id = view.corpus_of(node.id)\n            assert corpus_id is not None  # A served record has a location in this epoch.\n            attribution.setdefault(value.identity(), set()).add(corpus_id)\n",
            after='            corpus_id = view.corpus_of(value.identity()) or ""\n            attribution.setdefault(value.identity(), set()).add(corpus_id)\n',
        ),
        checks=(f"{_A}::test_evaluation_reports_an_absent_corpus_and_attributes_at_the_read_durably",),
    ),
    Arm(
        row="R19c",
        asserts="a facet read goes through the holding corpus's own ReadView",
        sabotage=Sabotage(
            module=_EVALUATION,
            before="    rows = read_observed_facets(profile, view.corpus_view(target), target)\n",
            after="    rows = read_observed_facets(profile, view, target)\n",
        ),
        checks=(f"{_A}::test_evaluation_reports_an_absent_corpus_and_attributes_at_the_read_durably",),
    ),
    Arm(
        row="R19d",
        asserts="the facet read is held to the capture on its returned row set",
        sabotage=Sabotage(
            module=_EVALUATION,
            before="    if returned != expected:\n",
            after="    if captured.uid != view.get(target).uid:\n",
        ),
        checks=(f"{_A}::test_a_facet_read_is_held_to_the_capture_durably",),
    ),
    Arm(
        row="R19",
        asserts="check_verification recomputes across corpora and reports a well-formed forgery",
        sabotage=Sabotage(
            module="audit.py",
            before="    if derived.verdict != stored_value.verdict:\n",
            after="    if False and derived.verdict != stored_value.verdict:\n",
        ),
        checks=(f"{_A}::test_check_verification_reports_a_cross_corpus_forgery_durably",),
    ),
    Arm(
        row="R19e",
        asserts="an absent corpus is the banked reason, never unheld input",
        sabotage=Sabotage(
            module=_EVALUATION,
            before='        return NoBelief("unavailable-corpus-absent", detail=f"inputs recorded in absent corpora: {corpora}")\n',
            after='        return NoBelief("unavailable-input-unheld", detail=f"inputs recorded in absent corpora: {corpora}")\n',
        ),
        checks=(f"{_A}::test_evaluation_reports_an_absent_corpus_and_attributes_at_the_read_durably",),
    ),
    Arm(
        row="W6",
        asserts="the three states never collapse; removing a corpus does not convert its ids to unknown",
        sabotage=Sabotage(
            module=_READ,
            before="        if not status.present:\n            return NotPresent(stamp)\n",
            after="        if not status.present:\n            return Unknown(stamp)\n",
        ),
        checks=(f"{_A}::test_the_three_states_never_collapse_and_removal_is_not_unknown",),
    ),
    Arm(
        row="W10g",
        asserts="a uid held under two corpora refuses at open as corruption — the view's half of world uid uniqueness",
        sabotage=Sabotage(
            module=_VIEW,
            before="            if uid in owners:\n",
            after="            if False and uid in owners:\n",
        ),
        checks=(f"{_A}::test_one_uid_under_two_corpora_refuses_at_open_durably",),
    ),
)
