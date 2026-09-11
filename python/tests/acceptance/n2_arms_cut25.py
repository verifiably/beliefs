"""Cut 25's three declaration units and 24 source sabotages (design §10.4)."""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS: tuple[str, ...] = ("W1", "W2", "W5a")
CO_CITED: tuple[str, ...] = ()


def unit_of(row: str) -> str:
    """Rows are `<unit>` or `<unit>-<letter>`; the hyphen lets `W5a` carry rows."""
    unit, hyphen, suffix = row.partition("-")
    if unit not in DECLARATION_UNITS or (hyphen and not (len(suffix) == 1 and suffix.islower())):
        raise ValueError(f"{row!r} is not a cut-25 row")
    return unit


CUT25_ARMS = (
    Arm(
        row="W2-a",
        asserts="DOI suffixes fold to lowercase",
        sabotage=Sabotage(
            module="source.py",
            before='    remainder = _remainder("doi", value, _DOI_PREFIX).lower()\n',
            after='    remainder = _remainder("doi", value, _DOI_PREFIX)\n',
        ),
        checks=("test_source_address.py::TestNormalizeDoi::test_every_spelling_folds_to_one_canonical_form",),
    ),
    Arm(
        row="W2-b",
        asserts="DOI prefixes are stripped",
        sabotage=Sabotage(
            module="source.py",
            before='_DOI_PREFIX = re.compile(r"^(?:doi:|https?://(?:dx\\.)?doi\\.org/)", re.IGNORECASE)\n',
            after='_DOI_PREFIX = re.compile(r"^$")\n',
        ),
        checks=("test_source_address.py::TestNormalizeDoi::test_every_spelling_folds_to_one_canonical_form",),
    ),
    Arm(
        row="W2-c",
        asserts="one tuple fixes basis precedence",
        sabotage=Sabotage(
            module="source.py",
            before='SCHEMES = ("doi", "pmid", "isbn", "accession")\n',
            after='SCHEMES = ("accession", "isbn", "pmid", "doi")\n',
        ),
        checks=(
            "test_source_address.py::TestBasisAndAddress::test_precedence_over_every_non_empty_subset",
            "test_source_address.py::TestRefusalOrder::test_one_tuple_in_precedence_order",
        ),
    ),
    Arm(
        row="W2-d",
        asserts="every identifier is validated before selection",
        sabotage=Sabotage(
            module="source.py",
            before="    return {scheme: normalize(scheme, identifiers[scheme]) for scheme in sorted(schemes)}\n",
            after="    return {scheme: normalize(scheme, identifiers[scheme]) for scheme in sorted(schemes)[:1]}\n",
        ),
        checks=("test_source_address.py::TestRefusalOrder::test_every_entry_is_validated_before_selection",),
    ),
    Arm(
        row="W2-e",
        asserts="ISBN-13 check digits are verified",
        sabotage=Sabotage(
            module="source.py",
            before="        if _isbn13_check(remainder[:12]) != remainder[12]:\n",
            after="        if False:\n",
        ),
        checks=("test_source_address.py::TestNormalizeIsbn::test_malformed[978-0-306-40615-8]",),
    ),
    Arm(
        row="W2-f",
        asserts="an unknown scheme precedes value validation",
        sabotage=Sabotage(
            module="source.py",
            before="    if scheme not in _RULES:\n",
            after="    if False:\n",
        ),
        checks=("test_source_address.py::TestRefusalOrder::test_unknown_scheme_wins_over_its_own_value",),
    ),
    Arm(
        row="W2-g",
        asserts="an empty stripped value has its own refusal",
        sabotage=Sabotage(
            module="source.py",
            before='    if not remainder:\n        raise _refuse(scheme, value, "empty", "nothing remains after trimming and prefix stripping")\n',
            after='    if False:\n        raise _refuse(scheme, value, "empty", "nothing remains after trimming and prefix stripping")\n',
        ),
        checks=("test_source_address.py::TestRefusalOrder::test_empty_after_trim_and_prefix_strip",),
    ),
    Arm(
        row="W1-a",
        asserts="a source id agrees with its derived address",
        sabotage=Sabotage(
            module="corpus.py",
            before="        if node.id != address:\n",
            after="        if False:\n",
        ),
        checks=("test_identifier_correction.py::TestTheBoundary::test_a_handle_address_refuses",),
    ),
    Arm(
        row="W1-b",
        asserts="replacement validates the source boundary",
        sabotage=Sabotage(
            module="corpus.py",
            before="        self._refuse_source(node, provenance=True)\n",
            after="",
        ),
        checks=(
            "test_identifier_correction.py::TestRelocation::test_consolidate_refuses_a_handle_addressed_replica_at_replace",
        ),
    ),
    Arm(
        row="W1-c",
        asserts="stored identifier values are canonical",
        sabotage=Sabotage(
            module="corpus.py",
            before="        canonical = source_basis_projection.normalized_identifiers(identifiers)\n        for scheme, value in canonical.items():\n            if identifiers[scheme] != value:\n",
            after="        canonical = source_basis_projection.normalized_identifiers(identifiers)\n        for scheme, value in canonical.items():\n            if False:\n",
        ),
        checks=("test_identifier_correction.py::TestTheBoundary::test_a_non_canonical_stored_value_refuses",),
    ),
    Arm(
        row="W5a-a",
        asserts="dataset admission still requires content identity",
        sabotage=Sabotage(
            module="corpus.py",
            before="        self._refuse_source(node, provenance=provenance)\n        self._refuse_dataset_basis(node)\n",
            after="        self._refuse_source(node, provenance=provenance)\n",
        ),
        checks=("test_corpus_write.py::TestW3TheBasisRefusal::test_a_dataset_with_no_content_identity_refuses",),
    ),
    Arm(
        row="W5a-b",
        asserts="correction rebuilds the held-address redirects",
        sabotage=Sabotage(
            module="corpus.py",
            before="            successor.deprecated_ids = sorted(held - {new_address})\n",
            after="            successor.deprecated_ids = []\n",
        ),
        checks=("test_identifier_correction.py::TestTheSeamEffects::test_moved_creates_and_deletes_preserving_uid",),
    ),
    Arm(
        row="W5a-c",
        asserts="correction leaves referrers byte-unchanged",
        sabotage=Sabotage(
            module="corpus.py",
            before="            plan: list[CreateOp | DeleteOp | ReplaceOp]\n            if new_path != old_path:\n                plan = [CreateOp(path=new_path, content=content), DeleteOp(path=old_path, expected_digest=expected)]\n            else:\n                plan = [ReplaceOp(path=new_path, content=content, expected_digest=expected)]\n            self._corpus.executor.execute(plan)\n",
            after="            self._corpus.rename(subject.id, new_address)\n",
        ),
        checks=("test_identifier_correction.py::TestTheSeamEffects::test_referrers_are_byte_unchanged",),
    ),
    Arm(
        row="W5a-d",
        asserts="correction attribution is bound to authority",
        sabotage=Sabotage(
            module="corpus.py",
            before='                    "actor": self._authority.actor,\n',
            after='                    "actor": "nobody",\n',
        ),
        checks=("test_identifier_correction.py::TestTheSeamEffects::test_moved_creates_and_deletes_preserving_uid",),
    ),
    Arm(
        row="W5a-e",
        asserts="an unchanged correction has its own refusal",
        sabotage=Sabotage(
            module="corpus.py",
            before="            if canonical == current:\n",
            after="            if False:\n",
        ),
        checks=("test_identifier_correction.py::TestTheSeamRefusals::test_unchanged",),
    ),
    Arm(
        row="W5a-f",
        asserts="the current source is validated before append",
        sabotage=Sabotage(
            module="corpus.py",
            before="            self._refuse_source(subject, provenance=True)\n",
            after="",
        ),
        checks=("test_identifier_correction.py::TestTheSeamRefusals::test_a_raw_edited_subject_refuses_before_append",),
    ),
    Arm(
        row="W5a-g",
        asserts="ordinary add cannot mint correction history",
        sabotage=Sabotage(
            module="corpus.py",
            before="        if stored.IDENTIFIER_CORRECTION_FACET in node.facets and not provenance:\n",
            after="        if stored.IDENTIFIER_CORRECTION_FACET in node.facets and False:\n",
        ),
        checks=("test_identifier_correction.py::TestTheBoundary::test_add_refuses_a_history",),
    ),
    Arm(
        row="W5a-h",
        asserts="import validates source history as provenance",
        sabotage=Sabotage(
            module="corpus.py",
            before="                self._refuse(record, document_validated=True, view=union, provenance=True)\n",
            after='                if record.kind != "source":\n                    self._refuse(record, document_validated=True, view=union, provenance=True)\n',
        ),
        checks=(
            "test_identifier_correction.py::TestTheBoundary::test_import_admits_a_well_formed_history_and_refuses_a_malformed_one",
        ),
    ),
    Arm(
        row="W5a-i",
        asserts="validated reads check correction history and redirects",
        sabotage=Sabotage(
            module="corpus.py",
            before='    if node.kind == "source":\n        try:\n            stored.validate_source_history(node)\n        except MalformedRecord as caught:\n',
            after="    if False:\n        try:\n            stored.validate_source_history(node)\n        except MalformedRecord as caught:\n",
        ),
        checks=(
            "test_identifier_correction.py::TestTheReadSide::test_a_raw_edited_history_refuses_on_read",
            "test_identifier_correction.py::TestTheReadSide::test_a_duplicated_deprecated_id_refuses_on_read",
        ),
    ),
    Arm(
        row="W5a-j",
        asserts="the check view reports malformed source history",
        sabotage=Sabotage(
            module="corpus.py",
            before='        if node.kind == "source":\n            try:\n                stored.validate_source_history(node)\n            except MalformedRecord as refused:\n',
            after="        if False:\n            try:\n                stored.validate_source_history(node)\n            except MalformedRecord as refused:\n",
        ),
        checks=("test_identifier_correction.py::TestTheReadSide::test_the_check_view_reports_facet_payload_malformed",),
    ),
    Arm(
        row="W5a-k",
        asserts="redirect agreement rejects duplicates and unsorted ids",
        sabotage=Sabotage(
            module="stored.py",
            before="    if list(node.deprecated_ids) != expected:\n",
            after="    if set(node.deprecated_ids) != set(expected):\n",
        ),
        checks=(
            "test_source_address.py::TestReaders::test_validate_source_history_refuses_a_disagreeing_redirect[duplicate]",
            "test_source_address.py::TestReaders::test_an_unsorted_redirect_refuses",
        ),
    ),
    Arm(
        row="W5a-l",
        asserts="each correction changes its identifier map",
        sabotage=Sabotage(
            module="stored.py",
            before="        if frm == to:\n",
            after="        if False:\n",
        ),
        checks=("test_source_address.py::TestReaders::test_from_equal_to_refuses_and_nothing_else_does",),
    ),
    Arm(
        row="W5a-m",
        asserts="consolidation refuses divergent correction histories",
        sabotage=Sabotage(
            module="relocation.py",
            before="            if keep_node.facets.get(\n                stored.IDENTIFIER_CORRECTION_FACET\n            ) != other_node.facets.get(stored.IDENTIFIER_CORRECTION_FACET):\n",
            after="            if False and keep_node.facets.get(\n                stored.IDENTIFIER_CORRECTION_FACET\n            ) != other_node.facets.get(stored.IDENTIFIER_CORRECTION_FACET):\n",
        ),
        checks=("test_identifier_correction.py::TestRelocation::test_consolidate_refuses_divergent_histories",),
    ),
    Arm(
        row="W5a-n",
        asserts="dataset revision preserves the resource",
        sabotage=Sabotage(
            module="corpus.py",
            before="        if candidate_fields != current_fields:\n            moved = sorted(\n",
            after="        if False:\n            moved = sorted(\n",
        ),
        checks=("acceptance/test_source_address_acceptance.py::test_w5a_dataset_arm_a_rehold_is_a_new_entity",),
    ),
)
