"""Cut 29 canonical declaration: W2, W3 and W8 dataset arms over the slice 5 seams."""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS = ("W2", "W3", "W8")
_A = "acceptance/test_dataset_address_acceptance.py"
UNIT_CHECKS = {
    "W2": f"{_A}::test_w2_two_corpora_mint_one_address_from_one_declaration_durably",
    "W3": f"{_A}::test_w3_the_builder_refuses_without_a_basis_and_mints_a_declared_unheld_dataset_durably",
    "W8": f"{_A}::test_w8_a_handle_addressed_dataset_refuses_on_add_import_and_move_durably",
}
CO_CITED = ()


def unit_of(row: str) -> str:
    """Rows are `<unit>` or `<unit>-<letter>`."""
    unit, hyphen, suffix = row.partition("-")
    if unit not in DECLARATION_UNITS or (hyphen and not (len(suffix) == 1 and suffix.islower())):
        raise ValueError(f"{row!r} is not a cut-29 row")
    return unit


def _arm(row, assertion, module, before, after, *checks):
    return Arm(row=row, asserts=assertion, sabotage=Sabotage(module=module, before=before, after=after), checks=tuple(checks))


CUT29_ARMS = (
    _arm("W2-a", "The builder derives the id from the declaration, never the title.", "stored.py",
         '    return _node("dataset", address.partition(":")[2], title, facets, ())',
         '    return _node("dataset", title, title, facets, ())',
         f"{_A}::test_w2_two_corpora_mint_one_address_from_one_declaration_durably",
         "test_stored.py::TestTheDatasetBuilder::test_one_byte_set_is_one_id_whatever_the_title_order_repetition_or_names"),
    _arm("W2-b", "dataset_address_of reads the stored declaration.", "stored.py",
         "    return dataset_address(dataset_declaration(node))",
         "    return node.id",
         "test_stored.py::test_dataset_address_of_reads_the_stored_declaration_not_the_id",
         "test_corpus_write.py::TestDatasetAddress::test_a_handle_addressed_dataset_refuses_on_add"),
    _arm("W3-a", "The builder refuses a declaration with no address before minting.", "stored.py",
         "    address = dataset_address(_declaration_of(facets[DATASET_FACET]))\n    if address is None:",
         "    address = dataset_address(_declaration_of(facets[DATASET_FACET]))\n    if False:",
         f"{_A}::test_w3_the_builder_refuses_without_a_basis_and_mints_a_declared_unheld_dataset_durably",
         "test_stored.py::TestTheDatasetBuilder::test_an_unpinned_or_empty_declaration_refuses_at_the_builder"),
    _arm("W8-a", "A dataset's stored id must equal its derived address on every write path.", "corpus.py",
         "            if node.id != address:\n                raise DatasetAddressDisagreement(",
         "            if False:\n                raise DatasetAddressDisagreement(",
         f"{_A}::test_w8_a_handle_addressed_dataset_refuses_on_add_import_and_move_durably",
         "test_corpus_write.py::TestDatasetAddress::test_a_handle_addressed_dataset_refuses_on_add",
         "test_relocation.py::test_move_refuses_a_handle_addressed_dataset_into_a_governed_destination"),
    _arm("W8-b", "consolidate validates both dataset inputs before reconciling.", "relocation.py",
         '            for position, node, writer in (\n                ("keep", keep_node, keep_writer),\n                ("other", other_node, other_writer),\n            ):',
         '            for position, node, writer in (\n                ("keep", keep_node, keep_writer),\n            ):',
         f"{_A}::test_w8_consolidate_judges_both_declarations_before_it_discards_one_durably[other]",
         "test_relocation.py::test_consolidate_validates_both_dataset_inputs_before_reconciling[other]"),
    _arm("W8-c", "Import validates datasets like every other member.", "corpus.py",
         "                self._refuse(record, document_validated=True, view=union, provenance=True)",
         '                if record.kind != "dataset":\n                    self._refuse(record, document_validated=True, view=union, provenance=True)',
         "test_corpus_write.py::TestDatasetAddress::test_a_bundle_with_a_handle_addressed_dataset_refuses_naming_the_member"),
)
