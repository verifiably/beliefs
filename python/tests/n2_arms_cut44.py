"""Frozen cut-44 declaration: 24 units, 24 sabotage arms, one each."""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS = (
    "J16-a",
    "J16-b",
    "J16-c",
    "J16-d",
    "J16-e",
    "J16-f",
    "J16-g",
    "J16-h",
    "J16-i",
    "J16-j",
    "J16-k",
    "J16-l",
    "J16-m",
    "J17-a",
    "J17-b",
    "J18-a",
    "J18-b",
    "J19-a",
    "J19-b",
    "J19-c",
    "J19-d",
    "J19-e",
    "J20-a",
    "J21-a",
)
_MC = "test_mount_citations.py"
_SW = "test_session_writer.py"
_RS = "test_read_side.py"
_WA = "test_world_audit.py"
_ASSESSMENT_WRITTEN = f"{_MC}::test_an_assessment_over_a_mount_dataset_and_proposition_is_written"
UNIT_CHECKS = {
    "J16-a": _ASSESSMENT_WRITTEN,
    "J16-b": _ASSESSMENT_WRITTEN,
    "J16-c": f"{_MC}::test_a_verification_of_a_mount_assessment_is_written",
    "J16-d": f"{_MC}::test_a_citation_across_differing_identities_refuses",
    "J16-e": f"{_SW}::test_the_session_writer_cites_its_read_mounts",
    "J16-f": f"{_MC}::test_an_assessment_over_a_dataset_a_third_mount_produces_refuses",
    "J16-g": f"{_SW}::test_a_symlinked_write_root_mount_key_is_filtered_after_normalization",
    "J16-h": f"{_MC}::test_revise_adding_the_facet_to_a_dataset_a_mount_run_produces_refuses",
    "J16-i": f"{_MC}::test_an_acquired_dataset_a_mount_run_produces_refuses",
    "J16-j": f"{_MC}::test_an_imported_run_producing_a_mount_observation_refuses",
    "J16-k": f"{_MC}::test_a_dataset_whose_retrieval_report_is_in_a_mount_refuses",
    "J16-l": f"{_MC}::test_an_assessment_over_a_raw_split_dataset_refuses",
    "J16-m": f"{_MC}::test_an_imported_assessment_over_a_dataset_a_mount_produces_refuses",
    "J17-a": f"{_MC}::test_a_ref_held_twice_refuses_duplicate_location_naming_both",
    "J17-b": f"{_MC}::test_a_held_read_mount_lock_refuses_build_contended",
    "J18-a": f"{_RS}::test_a_dataset_the_corpus_does_not_hold_is_eligibility_unresolved",
    "J18-b": f"{_RS}::test_one_held_invalid_and_one_unheld_dataset_is_unresolved",
    "J19-a": f"{_WA}::test_j19_a_supported_cross_corpus_citation_has_no_finding",
    "J19-b": f"{_WA}::test_j19_b_an_absent_holder_is_unresolved",
    "J19-c": f"{_WA}::test_j19_c_the_judgment_reads_the_capture_not_the_live_carrier",
    "J19-d": f"{_WA}::test_j19_d_a_damaged_holder_is_unresolved_and_the_audit_continues",
    "J19-e": f"{_WA}::test_j19_e_an_absent_producer_keeps_the_dataset_produced",
    "J20-a": "test_world_view.py::test_j20_the_two_installation_split_evaluates_as_one_corpus",
    "J21-a": "test_domain_facet_read.py::test_an_absent_observed_dataset_is_absent_from_gather",
}
# J16-a and J16-b name one check; J21-a re-cites the check cut 22's B4b names.
CO_CITED = (_ASSESSMENT_WRITTEN, UNIT_CHECKS["J21-a"])


def unit_of(row: str) -> str:
    """Every arm homes its own unit; no row shares one."""
    if row not in DECLARATION_UNITS:
        raise ValueError(f"{row!r} is not a cut-44 row")
    return row


def _arm(row, module, assertion, before, after):
    return Arm(
        row=row,
        asserts=assertion,
        sabotage=Sabotage(module=module, before=before, after=after),
        checks=(UNIT_CHECKS[unit_of(row)],),
    )


CUT44_ARMS = (
    _arm(
        "J16-a",
        "corpus.py",
        "Eligibility is judged over the reading view, so a mount dataset and proposition are accepted.",
        "        self._refuse_ineligible(node, view=view)\n",
        "        self._refuse_ineligible(node, view=self._view)\n",
    ),
    _arm(
        "J16-b",
        "corpus.py",
        "The assesses-target-kind refusal reads through the mount-aware view.",
        "        self._refuse_assesses_target_kind(node, view=reading)\n",
        "        self._refuse_assesses_target_kind(node, view=self._view)\n",
    ),
    _arm(
        "J16-c",
        "corpus.py",
        "A verification of a mount assessment is judged over the mount-aware view.",
        "            self._refuse_verification(node, view=self._view if view is None else view)\n",
        "            self._refuse_verification(node, view=self._view)\n",
    ),
    _arm(
        "J16-d",
        "corpus.py",
        "A citation across differing contract identities refuses.",
        "        if root is not None:\n            self._refuse_contract_mismatch(root)\n",
        "        if False:\n            self._refuse_contract_mismatch(root)\n",
    ),
    _arm(
        "J16-e",
        "session/__init__.py",
        "The session writer is handed its read mounts.",
        "            read_mounts=read_mounts,\n",
        "            read_mounts=(),\n",
    ),
    _arm(
        "J16-f",
        "corpus.py",
        "Producers of a dataset are the union over the write root and every read mount.",
        "        found = set(self._own.producers(dataset, aliases=aliases))\n"
        "        for _root, view in self._read_views():\n"
        "            found.update(view.producers(dataset, aliases=aliases))\n"
        "        return tuple(sorted(found))\n",
        "        holder = self.holder(dataset)\n        return () if holder is None else holder.producers(dataset, aliases=aliases)\n",
    ),
    _arm(
        "J16-g",
        "session/__init__.py",
        "The write root's own key is filtered from the read mounts after normalization.",
        "    read_mounts = tuple(sorted(path for path in mounted if path != root)) if mounted is not None else ()\n",
        "    read_mounts = tuple(sorted(Path(key) for key in mounts if Path(key) != root)) if mounts is not None else ()\n",
    ),
    _arm(
        "J16-h",
        "corpus.py",
        "A revise adding a facet is judged over the mount-aware view.",
        "        self._refuse_facets(restamped, provenance=True)\n",
        "        self._refuse_facets(restamped, view=self._view, provenance=True)\n",
    ),
    _arm(
        "J16-i",
        "corpus.py",
        "The overlay's producers include those of every read mount.",
        "        for _root, view in self._citations._read_views():\n"
        "            found.update(view.producers(dataset, aliases=aliases))\n",
        "        pass\n",
    ),
    _arm(
        "J16-j",
        "corpus.py",
        "The overlay resolves a ref through the mount that holds it.",
        "        view = self._citations._one(ref, self._base)\n        return None if view is None else view.resolve(ref)\n",
        "        view = self._base if self._base.holds(ref) else None\n        return None if view is None else view.resolve(ref)\n",
    ),
    _arm(
        "J16-k",
        "corpus.py",
        "A retrieval report held in a mount refuses its dataset.",
        "            local = reading if isinstance(reading, _ImportView) else self._view\n",
        "            local = reading\n",
    ),
    _arm(
        "J16-l",
        "corpus.py",
        "A raw split dataset is judged against its holders' reports.",
        "                judge, reports = reading, citations.holder\n",
        "                judge, reports = reading, None\n",
    ),
    _arm(
        "J16-m",
        "corpus.py",
        "An imported assessment is judged over the mount overlay.",
        "                judge, reports = citations.overlay(reading), (lambda _ref: reading)\n",
        "                judge, reports = None, (lambda _ref: reading)\n",
    ),
    _arm(
        "J17-a",
        "corpus.py",
        "A ref held in two locations refuses as a duplicate location.",
        "        if len(found) > 1:\n",
        "        if False:\n",
    ),
    _arm(
        "J17-b",
        "corpus.py",
        "A read mount's operation lock is held for the session's capture.",
        "            self._holds.enter_context(_operation_lock_for(root).capture())\n",
        "            pass\n",
    ),
    _arm(
        "J18-a",
        "corpus.py",
        "A dataset the corpus does not hold is eligibility-unresolved.",
        "        if outcome is not None and outcome.unresolved:\n",
        "        if False:\n",
    ),
    _arm(
        "J18-b",
        "corpus.py",
        "Every unresolved dataset is reported, not only when all are unresolved.",
        "        tuple(unresolved),\n    )\n",
        "        tuple(unresolved) if len(unresolved) == len(observed) else (),\n    )\n",
    ),
    _arm(
        "J19-a",
        "audit.py",
        "The disagreeing-scope findings read the cross-corpus citations.",
        "        second = _record_findings(captured, profile, scope, disagreeing, citations=reader)\n",
        "        second = _record_findings(captured, profile, scope, disagreeing)\n",
    ),
    _arm(
        "J19-b",
        "audit.py",
        "An absent holder is recorded as unresolved.",
        '    causes = {corpus_id: "absent" for corpus_id in view.absent()}\n',
        "    causes = {}\n",
    ),
    _arm(
        "J19-c",
        "audit.py",
        "The judgment reads the capture, not the live carrier.",
        "        return self._readable.get(corpus_id)\n",
        "        return self._view.corpus_view(ref)\n",
    ),
    _arm(
        "J19-d",
        "audit.py",
        "A damaged holder is unresolved and the audit continues.",
        '        if cause is not None:\n            self.unreadable[ref] = f"{corpus_id} {cause}"\n            return None\n',
        '        if cause is not None:\n            raise CorpusDamaged(f"eligibility:{ref}", corpus_id, self._view.stamp)\n',
    ),
    _arm(
        "J19-e",
        "audit.py",
        "An absent producer keeps the dataset produced.",
        "        found.update(self._view.published_producers(dataset))\n",
        "        pass\n",
    ),
    _arm(
        "J20-a",
        "evaluation.py",
        "A split two-installation world evaluates as one corpus.",
        "_facets_held_to_capture(profile, view, target) if world else read_observed_facets(profile, view, target)",
        'read_observed_facets(profile, view.corpus_view(stored.typed_ref("run", a.run)) if world else view, target)',
    ),
    _arm(
        "J21-a",
        "evaluation.py",
        "An observed dataset absent from the corpus is refused as outside it.",
        "        if outside:\n            raise InputOutsideCorpus(a.identity(), ref, tuple(sorted(set(outside))))\n",
        "",
    ),
)
