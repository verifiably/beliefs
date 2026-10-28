"""Frozen cut-48 declaration: 33 units and 33 independent mutation arms."""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS = (
    "W19-a",
    "W19-b",
    "W19-c",
    "W19-d",
    "W19-e",
    "W19-f",
    "W19-g",
    "W20-a",
    "W20-b",
    "W20-c",
    "W20-d",
    "W20-e",
    "W20-f",
    "W20-g",
    "W20-h",
    "W20-i",
    "G14-a",
    "G14-b",
    "G14-c",
    "G14-d",
    "G14-e",
    "G14-f",
    "G14-g",
    "G14-h",
    "G14-i",
    "Y19-a",
    "Y19-b",
    "Y19-c",
    "Y19-d",
    "Y19-e",
    "Y19-f",
    "J17-c",
    "J20-b",
)
UNIT_CHECKS = {
    "W19-a": "test_world_derive.py::TestW19MultiHolderMap::test_w19_a_equal_content_reads_once",
    "W19-b": "test_world_derive.py::TestW19MultiHolderMap::test_w19_b_differing_content_refuses",
    "W19-c": "test_world_derive.py::TestW19MultiHolderMap::test_w19_c_corruption_outranks",
    "W19-d": "test_world_derive.py::TestW19MultiHolderMap::test_w19_d_deprecated_key_entry",
    "W19-e": "test_world_read.py::TestOverlapResolution::test_w19_e_epoch_shapes",
    "W19-f": "test_world_derive.py::TestW19MultiHolderMap::test_w19_f_discovery_once",
    "W19-g": "test_live_selection.py::TestW19LiveMapHolders::test_w19_g_live_map_holders",
    "W20-a": "test_world_view.py::TestW20ServedSurface::test_w20_a_view_serves_once",
    "W20-b": "test_world_view.py::TestW20ServedSurface::test_w20_b_holders_disagree_refuses",
    "W20-c": "test_world_selection.py::TestW20Holders::test_w20_c_absence_over_holders",
    "W20-d": "test_world_view.py::TestW20ServedSurface::test_w20_d_owners_check_narrowed",
    "W20-e": "test_world_view.py::TestW20ServedSurface::test_w20_e_damaged_holder_rule",
    "W20-f": "test_world_read.py::TestOverlapResolution::test_w20_f_resolve_address_holders",
    "W20-g": "test_world_selection.py::TestW20Holders::test_w20_g_contributing_union",
    "W20-h": "test_world_view.py::TestW20ServedSurface::test_w20_h_mapped_view_and_absence",
    "W20-i": "test_world_audit.py::test_w20_i_audit_files_per_holder",
    "G14-a": "test_acceptance.py::test_g14_a_union_over_holders",
    "G14-b": "test_acceptance.py::test_g14_b_rejected_everywhere_inert",
    "G14-c": "test_acceptance.py::test_g14_c_predicate_per_holder",
    "G14-d": "test_acceptance.py::test_g14_d_filtered_graphs",
    "G14-e": "test_snapshot_retraction.py::TestG14eMergedFold::test_a_counter_accepted_through_one_holder_restores_in_either_order",
    "G14-f": "test_standing_read.py::test_g14_f_merge_self_check",
    "G14-g": "test_acceptance.py::test_g14_g_filtered_fidelity_one_comparison",
    "G14-h": "test_world_rules.py::TestG14V2RuleBinding::test_g14_h_v2_rule_binding",
    "G14-i": "test_world_standing.py::test_g14_i_v2_fold_world",
    "Y19-a": "test_publication_attribution.py::test_y19_a_own_wins",
    "Y19-b": "test_publication_attribution.py::test_y19_b_carriers_agree",
    "Y19-c": "test_publication_attribution.py::test_y19_c_earliest_origin",
    "Y19-d": "test_publication_attribution.py::test_y19_d_ambiguous_refuses",
    "Y19-e": "test_publication_attribution.py::test_y19_e_order_independent",
    "Y19-f": "test_publication_attribution.py::test_y19_f_v2_narrowing",
    "J17-c": "test_mount_citations.py::test_j17_c_a_citation_of_equal_content_resolves_once_with_every_contract_checked",
    "J20-b": "test_acceptance.py::test_j20_b_node_corpus_holder_set",
}
CO_CITED = ()


def unit_of(row: str) -> str:
    if row not in DECLARATION_UNITS:
        raise ValueError(f"{row!r} is not a cut-48 row")
    return row


def _arm(row, module, assertion, before, after):
    return Arm(
        row=row,
        asserts=assertion,
        sabotage=Sabotage(module=module, before=before, after=after),
        checks=(UNIT_CHECKS[unit_of(row)],),
    )


CUT48_ARMS = (
    _arm(
        "W19-a",
        "world/derive.py",
        "Equal-content claims on one address are one record held in several corpora.",
        "        if len({record.content for _, record in claims}) > 1:\n",
        "        if len(claims) > 1:\n",
    ),
    _arm(
        "W19-b",
        "world/derive.py",
        "Claims on one address are grouped by content identity, never by uid.",
        "        if len({record.content for _, record in claims}) > 1:\n            raise AddressMapConflict(\n",
        "        if len({record.uid for _, record in claims}) > 1:\n            raise AddressMapConflict(\n",
    ),
    _arm(
        "W19-c",
        "world/derive.py",
        "Uid corruption is refused over the whole capture before any duplicate location.",
        (
            "    for uid, locations in by_uid.items():\n"
            "        if len({address for _, address in locations}) > 1:\n"
            "            raise AddressMapConflict(\n"
            "                Finding(\n"
            '                    severity="error",\n'
            '                    code="uid-corruption",\n'
            "                    ref=uid,\n"
            '                    detail=f"corpus/address claims={tuple(locations)!r}",\n'
            '                    message="one uid names different canonical addresses; no repair is offered",\n'
            "                )\n"
            "            )\n"
            "    mapping: dict[str, AddressEntry] = {}\n"
        ),
        (
            "    mapping: dict[str, AddressEntry] = {}\n"
            "    for address, claims in by_address.items():\n"
            "        if len({record.content for _, record in claims}) > 1:\n"
            "            raise AddressMapConflict(\n"
            '                Finding(severity="error", code="duplicate-location", ref=address, detail="", message="")\n'
            "            )\n"
            "    for uid, locations in by_uid.items():\n"
            "        if len({address for _, address in locations}) > 1:\n"
            "            raise AddressMapConflict(\n"
            "                Finding(\n"
            '                    severity="error",\n'
            '                    code="uid-corruption",\n'
            "                    ref=uid,\n"
            '                    detail=f"corpus/address claims={tuple(locations)!r}",\n'
            '                    message="one uid names different canonical addresses; no repair is offered",\n'
            "                )\n"
            "            )\n"
        ),
    ),
    _arm(
        "W19-d",
        "world/derive.py",
        "A deprecated key claimed by differing records, or meeting a live address, refuses.",
        "            if held != entry:\n                raise ResolutionRefused(\n",
        "            if False:\n                raise ResolutionRefused(\n",
    ),
    _arm(
        "W19-e",
        "world/read.py",
        "A legacy address-map entry reads as one holder with no content identity.",
        (
            '        if "corpus_id" in entry:\n'
            '            mapping[cast(str, entry["address"])] = derive.AddressEntry(\n'
            '                cast(str, entry["uid"]), None, (cast(str, entry["corpus_id"]),)\n'
            "            )\n"
        ),
        (
            '        if "corpus_id" in entry:\n'
            '            mapping[cast(str, entry["address"])] = derive.AddressEntry(\n'
            '                cast(str, entry["uid"]), "0" * 64, (cast(str, entry["corpus_id"]),)\n'
            "            )\n"
        ),
    ),
    _arm(
        "W19-f",
        "world/derive.py",
        "A retraction held twice is discovered once.",
        "        targets.setdefault(record.retraction.target, set()).add(record.address)\n",
        "        targets.setdefault(record.retraction.target, []).append(record.address)\n",
    ),
    _arm(
        "W19-g",
        "world/live.py",
        "The live capture carries each record's content identity into the address map.",
        "                            content=registry.content_identity(node),\n",
        '                            content="0" * 64,\n',
    ),
    _arm(
        "W20-a",
        "world/view.py",
        "The inbound index files one edge per relation of a record held in several corpora.",
        (
            "    for corpus_id in sorted(held):\n"
            "        for uid in sorted(held[corpus_id]):\n"
            "            if uid in seen:\n"
            "                continue\n"
            "            seen.add(uid)\n"
            "            node = held[corpus_id][uid]\n"
        ),
        (
            "    for corpus_id in sorted(held):\n"
            "        for uid in sorted(held[corpus_id]):\n"
            "            node = held[corpus_id][uid]\n"
        ),
    ),
    _arm(
        "W20-b",
        "world/view.py",
        "Captured copies of one record that disagree refuse at the open, naming every holder.",
        "        if len(present) > 1 and len({contents[holder][entry.uid] for holder in present}) > 1:\n",
        "        if False:\n",
    ),
    _arm(
        "W20-c",
        "world/view.py",
        "A record is not present only when every holder is absent.",
        (
            "        present = self._captured_holders(entry)\n"
            "        if not present:\n"
            "            return NotPresent(self._stamp)\n"
            "        return Resolved(Location(present[0], entry.uid, present), self._stamp)\n"
        ),
        (
            "        present = self._captured_holders(entry)\n"
            "        if len(present) < len(entry.holders):\n"
            "            return NotPresent(self._stamp)\n"
            "        return Resolved(Location(present[0], entry.uid, present), self._stamp)\n"
        ),
    ),
    _arm(
        "W20-d",
        "world/view.py",
        "A shared uid is admitted only where the recorded map established its holders.",
        "        if not established or not set(corpora) <= set(cast(derive.AddressEntry, next(iter(entries))).holders):\n",
        "        if False:\n",
    ),
    _arm(
        "W20-e",
        "world/view.py",
        "A damaged holder is skipped only when every captured copy equals the mapped content.",
        (
            "        if (\n"
            "            present\n"
            "            and entry.content is not None\n"
            "            and all(self._contents[holder][entry.uid] == entry.content for holder in present)\n"
            "        ):\n"
            "            return\n"
        ),
        "        if present:\n            return\n",
    ),
    _arm(
        "W20-f",
        "world/read.py",
        "An address resolves through every present holder, not the first carrier alone.",
        (
            "        for corpus_id, carrier in carriers.items():\n"
            "            try:\n"
            "                view = ReadView.opened_at(carrier)\n"
        ),
        (
            "        for corpus_id, carrier in list(carriers.items())[:1]:\n"
            "            try:\n"
            "                view = ReadView.opened_at(carrier)\n"
        ),
    ),
    _arm(
        "W20-g",
        "world/selection.py",
        "`contributing` names every captured holder of a selected record.",
        "    contributing = sorted({holder for address in selected for holder in held[address][0]})\n",
        "    contributing = sorted({held[address][0][-1] for address in selected})\n",
    ),
    _arm(
        "W20-h",
        "world/view.py",
        "The mapped view sees a record under each of its holders.",
        "            if corpus_id in entry.holders and entry.uid in self._held[corpus_id]\n",
        "            if entry.holders[0] == corpus_id and entry.uid in self._held[corpus_id]\n",
    ),
    _arm(
        "W20-i",
        "audit.py",
        "A recomputation finding is filed under every captured holder of the record.",
        (
            "        if outcome is not None and outcome.contradiction is not None:\n"
            "            found.append(outcome.contradiction)\n"
            "        for holder in targets:\n"
            "            corpora[holder].extend(found)\n"
        ),
        (
            "        if outcome is not None and outcome.contradiction is not None:\n"
            "            found.append(outcome.contradiction)\n"
            "        corpora[corpus_id].extend(found)\n"
        ),
    ),
    _arm(
        "G14-a",
        "evaluation.py",
        "An assessment is accepted iff any holder's decision is true, every holder asked.",
        (
            "        decisions = None if counts is None else [counts(cast(str, holder), node.id) for holder in holders]\n"
            "        accepted = decisions is None or any(decisions)\n"
        ),
        (
            "        decisions = None if counts is None else [counts(cast(str, holders[0]), node.id)]\n"
            "        accepted = decisions is None or any(decisions)\n"
        ),
    ),
    _arm(
        "G14-b",
        "evaluation.py",
        "A verification rejected under every holder is inert.",
        (
            "            decided = [counts(cast(str, holder), node.id) for holder in holders]  # every holder asked (§6)\n"
            "            if not any(decided):\n"
            "                continue\n"
        ),
        (
            "            decided = [counts(cast(str, holder), node.id) for holder in holders]  # every holder asked (§6)\n"
            "            if False:\n"
            "                continue\n"
        ),
    ),
    _arm(
        "G14-c",
        "evaluation.py",
        "The retraction loop asks the predicate for every captured holder.",
        "                holders = _captured_holders(view, ref)\n",
        "                holders = _captured_holders(view, ref)[:1]\n",
    ),
    _arm(
        "G14-d",
        "evaluation.py",
        "The affected set walks transitively to every retraction a rejected one counters.",
        "    pending = list(affected)\n    while pending:\n",
        "    pending = []\n    while pending:\n",
    ),
    _arm(
        "G14-e",
        "corpus.py",
        "A retraction enters the snapshot fold iff some holder accepts it.",
        (
            "            decisions = [counts(corpus_id, node.id) for corpus_id in holders[node.id]]\n"
            "            if not any(decisions):\n"
            "                continue\n"
        ),
        (
            "            decisions = [counts(corpus_id, node.id) for corpus_id in holders[node.id]]\n"
            "            if not all(decisions):\n"
            "                continue\n"
        ),
    ),
    _arm(
        "G14-f",
        "corpus.py",
        "The merge classifies claims on one address before collapsing any record.",
        "        if len({node.uid for _, node, _ in held}) > 1 or len({content for _, _, content in held}) > 1:\n",
        "        if False:\n",
    ),
    _arm(
        "G14-g",
        "evaluation.py",
        "An enumeration recording two resolutions for one ref is refused by rule.",
        (
            "        earlier = receipt.setdefault(canonical, recorded)\n"
            "        if earlier != recorded:\n"
            "            computed = RETRACTION_UPHELD if standing.get(canonical, True) else RETRACTION_OVERTURNED\n"
            "            raise RetractionResolutionDisagreement(\n"
            "                canonical,\n"
            "                earlier,\n"
            "                computed,\n"
            "                detail=(\n"
            '                    f"{canonical}: the enumeration records two resolutions, {earlier!r} and {recorded!r}; "\n'
            '                    "one fold cannot reproduce both (cut 48 §4.5: the epoch folded per corpus over a split)"\n'
            "                ),\n"
            "            )\n"
        ),
        "        receipt[canonical] = recorded\n",
    ),
    _arm(
        "G14-h",
        "world/epoch.py",
        "A build hands each held rule the input version it declares.",
        "        return rules.invoke_held(held, kind, self.capture.rule_input(held.input_version))\n",
        "        return rules.invoke_held(held, kind, self.capture.rule_input(None))\n",
    ),
    _arm(
        "G14-i",
        "world/epoch.py",
        "The address map is derived before any rule runs.",
        (
            "    address_map = derive.address_map(draft.capture)\n"
            '    snapshot = derive.producer_snapshot(draft.run("producer"))\n'
            '    enumeration = derive.retraction_enumeration(draft.run("retraction-enumeration"))\n'
        ),
        (
            '    snapshot = derive.producer_snapshot(draft.run("producer"))\n'
            '    enumeration = derive.retraction_enumeration(draft.run("retraction-enumeration"))\n'
            "    address_map = derive.address_map(draft.capture)\n"
        ),
    ),
    _arm(
        "Y19-a",
        "publish.py",
        "An own holder beside a carried copy makes the record own.",
        "    carried = {ref: holders for ref, holders in holders_of.items() if all(replica(holder) for holder in holders)}\n",
        (
            "    carried = {\n"
            "        ref: tuple(h for h in holders if replica(h))\n"
            "        for ref, holders in holders_of.items()\n"
            "        if any(replica(holder) for holder in holders)\n"
            "    }\n"
        ),
    ),
    _arm(
        "Y19-b",
        "publish.py",
        "Carriers yielding one triple forward it.",
        ("        if len(claims) == 1:\n            result.append(next(iter(claims)))\n            continue\n"),
        (
            "        if len(claims) == 1 and len(carried[ref]) == 1:\n"
            "            result.append(next(iter(claims)))\n"
            "            continue\n"
            "        if len(carried[ref]) > 1:\n"
            '            raise PublicationRefused("attribution-ambiguous", refs=(ref,), corpus_ids=carried[ref])\n'
        ),
    ),
    _arm(
        "Y19-c",
        "publish.py",
        "Disagreeing claims are ordered by the claimed markers, never by the holders' own.",
        "                _supersedes(supersession, (other[1], other[2]), (claim[1], claim[2]))\n",
        (
            "                any(\n"
            "                    _supersedes(supersession, (h, sources[h][0]), (g, sources[g][0]))\n"
            "                    for h in carried[ref]\n"
            "                    for g in carried[ref]\n"
            "                    if h != g and sources[g][1].get(ref, (ref, g, sources[g][0])) == claim\n"
            "                )\n"
        ),
    ),
    _arm(
        "Y19-d",
        "publish.py",
        "Claims with no least element refuse, carrying the claims.",
        (
            "        if len(least) == 1:\n"
            "            result.append(least[0])\n"
            "            continue\n"
            "        raise PublicationRefused(\n"
            '            "attribution-ambiguous",\n'
        ),
        (
            "        if len(least) == 1:\n"
            "            result.append(least[0])\n"
            "            continue\n"
            "        result.append(min(claims))\n"
            "        continue\n"
            "        raise PublicationRefused(\n"
            '            "attribution-ambiguous",\n'
        ),
    ),
    _arm(
        "Y19-e",
        "publish.py",
        "The least element is selected, never the first replica holder in admission order.",
        ("        if len(least) == 1:\n            result.append(least[0])\n            continue\n"),
        (
            "        if len(least) == 1:\n"
            "            first = next(record.corpus_id for record in registry.admissions if record.corpus_id in carried[ref])\n"
            "            result.append(sources[first][1].get(ref, (ref, first, sources[first][0])))\n"
            "            continue\n"
        ),
    ),
    _arm(
        "Y19-f",
        "publish.py",
        "The v2 refusal names only the carriers of a carried record.",
        "    carriers = tuple(sorted({holder for holders in carried.values() for holder in holders}))\n",
        "    carriers = tuple(sorted(holder for holder in grouped if replica(holder)))\n",
    ),
    _arm(
        "J17-c",
        "corpus.py",
        "A citation held by several session corpora compares their content before answering.",
        (
            "        if len(found) > 1 and len({content_identity(view.get(ref)) for _root, view in found}) > 1:\n"
            '            corpora = ", ".join(sorted(self._corpus_id(root) for root, _ in found))\n'
        ),
        ('        if False:\n            corpora = ", ".join(sorted(self._corpus_id(root) for root, _ in found))\n'),
    ),
    _arm(
        "J20-b",
        "evaluation.py",
        "An assessment's attribution names its accepting holders, not the canonical label alone.",
        "            attribution.setdefault(value.identity(), set()).update(cast(tuple[str, ...], accepting))\n",
        "            attribution.setdefault(value.identity(), set()).add(cast(str, view.corpus_of(node.id)))\n",
    ),
)
