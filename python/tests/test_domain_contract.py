"""Domain contracts and succession.

M6's arms selected into cut 1 are here. Its deferred arm — *"consulted belief
digests move"* on an additive successor — needs belief, which the slice does not
compute, and is not asserted anywhere below.
"""

import copy

import pytest
import yaml

from beliefs.contract import domain
from beliefs.errors import MalformedContract, SubclassRefused, SuccessionViolation
from beliefs.identity import v1


@pytest.fixture()
def parse(base_contract):
    def _parse(
        document: object,
        source: str = "<test>",
        predecessor: domain.DomainContract | None = None,
    ) -> domain.DomainContract:
        return domain.parse_domain_contract(document, source=source, base=base_contract, predecessor=predecessor)

    return _parse


class TestTheTestingContract:
    def test_it_loads(self, parse, testing_document):
        contract = parse(testing_document)
        assert contract.namespace == "testing"
        assert contract.predecessor is None  # genesis
        assert set(contract.operators) == {"affects", "subtype-of", "correlates-with", "measured-by"}

    def test_term_identifiers_are_namespaced(self, parse, testing_document):
        # §7.3: authored, stable, namespaced — and it is what enters π_claim.
        assert parse(testing_document).term("affects") == "testing/affects"

    def test_both_polarity_regimes_are_reachable(self, parse, testing_document):
        operators = parse(testing_document).operators
        assert operators["affects"].sign_apt is True
        assert operators["subtype-of"].sign_apt is False

    def test_restriction_sorts_resolve_through_dimensions_not_operators(self, parse, testing_document):
        # §7.1: so two operators sharing `population` cannot disagree about what
        # a population restriction is bound to.
        contract = parse(testing_document)
        assert contract.dimensions["population"].restriction_sort == "cohort"
        assert not hasattr(contract.operators["affects"], "restriction_sorts")


class TestVocabularyBindings:
    def test_a_namespace_with_a_release_binds(self, parse, testing_document):
        binding = parse(testing_document).sorts["entity"].vocabulary
        assert (binding.namespace, binding.release) == ("EX", "2026-01-01")

    def test_a_held_dataset_binds_by_content_identity(self, parse, testing_document):
        binding = parse(testing_document).sorts["cohort"].vocabulary
        assert binding.dataset_identity == "0" * 64

    def test_a_bare_namespace_is_refused(self, parse, testing_document):
        # D §5, and the case §7.1's own biology example would fail on.
        broken = copy.deepcopy(testing_document)
        broken["sorts"]["entity"]["vocabulary"] = {"namespace": "EX", "release": None}
        with pytest.raises(MalformedContract, match="bare namespace"):
            parse(broken)

    def test_an_empty_dataset_binding_is_refused(self, parse, testing_document):
        broken = copy.deepcopy(testing_document)
        broken["sorts"]["entity"]["vocabulary"] = "dataset:"
        with pytest.raises(MalformedContract):
            parse(broken)


class TestTheBindingIsASumAndNotAProduct:
    """D §5 says *dataset* **or** *namespace with a release*, and three optional
    fields say neither. The record admits values off both arms, and ``projection``
    drops ``namespace``/``release`` on the dataset arm — correctly, since there
    they carry nothing — so an off-arm value projects as though the namespace were
    absent. That makes ``projection`` non-injective, and two readers take
    identities through it: a contract's own content identity, and a
    `ResolutionSnapshot`'s ordering.
    """

    def test_a_binding_carrying_both_arms_is_refused(self):
        with pytest.raises(MalformedContract, match="one arm or the other"):
            domain.VocabularyBinding(namespace="EX", release="2026-01-01", dataset_identity="0" * 64)

    def test_that_refusal_is_what_makes_the_projection_injective(self):
        # The pair the constructor now refuses is exactly the collision: two
        # bindings that differ, are therefore distinct dictionary keys resolved
        # against different vocabularies, and encode alike.
        colliding = [
            {"namespace": "EX", "release": "2026-01-01", "dataset_identity": "0" * 64},
            {"namespace": "OTHER", "release": "1999-01-01", "dataset_identity": "0" * 64},
        ]
        for fields in colliding:
            with pytest.raises(MalformedContract):
                domain.VocabularyBinding(**fields)

    def test_distinct_bindings_on_the_arms_that_remain_project_distinctly(self):
        bindings = [
            domain.VocabularyBinding(namespace="EX", release="2026-01-01", dataset_identity=None),
            domain.VocabularyBinding(namespace="EX", release="2027-01-01", dataset_identity=None),
            domain.VocabularyBinding(namespace="OTHER", release="2026-01-01", dataset_identity=None),
            domain.VocabularyBinding(namespace=None, release=None, dataset_identity="0" * 64),
            domain.VocabularyBinding(namespace=None, release=None, dataset_identity="1" * 64),
        ]
        encoded = [v1.encode(binding.projection()) for binding in bindings]
        assert len(set(encoded)) == len(bindings)

    @pytest.mark.parametrize(
        "fields",
        [
            {"namespace": "EX", "release": None, "dataset_identity": None},
            {"namespace": None, "release": "2026-01-01", "dataset_identity": None},
            {"namespace": "EX", "release": "", "dataset_identity": None},
            {"namespace": 1, "release": "2026-01-01", "dataset_identity": None},
            {"namespace": None, "release": None, "dataset_identity": ""},
            {"namespace": None, "release": None, "dataset_identity": None},
        ],
    )
    def test_neither_arm_admits_a_partial_or_ill_typed_value(self, fields):
        with pytest.raises(MalformedContract):
            domain.VocabularyBinding(**fields)

    def test_the_binding_is_sealed(self):
        # The constructor check is worth nothing against a subclass that
        # overrides `projection`, and this is the one declaration type in the
        # module that callers construct directly — `build_snapshot` takes them as
        # keys, and `isinstance` there would admit the subclass.
        with pytest.raises(SubclassRefused):

            class Forged(domain.VocabularyBinding):  # type: ignore[misc]
                def projection(self) -> dict[str, object]:
                    return {"dataset": "0" * 64}


class TestOperatorDeclarations:
    def test_arity_must_match_arg_sorts(self, parse, testing_document):
        # ArgSort(op) is a function on Fin(arity(op)); a mismatch leaves a slot
        # with no sort or a sort with no slot.
        broken = copy.deepcopy(testing_document)
        broken["operators"]["affects"]["arity"] = 3
        with pytest.raises(MalformedContract, match="arity is 3"):
            parse(broken)

    def test_an_operator_admitting_no_layer_is_refused(self, parse, testing_document):
        # §6.2: it would make Claim uninhabited at that operator.
        broken = copy.deepcopy(testing_document)
        broken["operators"]["affects"]["layers"] = []
        with pytest.raises(MalformedContract, match="non-empty"):
            parse(broken)

    def test_a_domain_may_not_mint_a_layer(self, parse, testing_document):
        # §7.1: the layer set is base-owned but per-operator restricted. A domain
        # that could mint one would be redefining what kind of thing a claim is.
        broken = copy.deepcopy(testing_document)
        broken["operators"]["affects"]["layers"] = ["teleological"]
        with pytest.raises(MalformedContract, match="may not extend it"):
            parse(broken)

    def test_an_undeclared_arg_sort_is_refused(self, parse, testing_document):
        broken = copy.deepcopy(testing_document)
        broken["operators"]["affects"]["arg_sorts"] = ["entity", "nowhere"]
        with pytest.raises(MalformedContract, match="not a sort"):
            parse(broken)

    def test_an_undeclared_dimension_is_refused(self, parse, testing_document):
        broken = copy.deepcopy(testing_document)
        broken["operators"]["affects"]["dimensions"] = ["nowhere"]
        with pytest.raises(MalformedContract, match="not a dimension"):
            parse(broken)

    def test_an_undeclared_restriction_sort_is_refused(self, parse, testing_document):
        broken = copy.deepcopy(testing_document)
        broken["dimensions"]["population"]["restriction_sort"] = "nowhere"
        with pytest.raises(MalformedContract, match="not a sort"):
            parse(broken)

    def test_sign_apt_must_be_a_boolean(self, parse, testing_document):
        broken = copy.deepcopy(testing_document)
        broken["operators"]["affects"]["sign_apt"] = "yes"
        with pytest.raises(MalformedContract, match="true or false"):
            parse(broken)

    def test_an_unknown_operator_field_is_refused(self, parse, testing_document):
        broken = copy.deepcopy(testing_document)
        broken["operators"]["affects"]["polarity"] = "positive"
        with pytest.raises(MalformedContract, match="unknown field"):
            parse(broken)


class TestSortReferences:
    """Design §4.1–§4.2 (biology pack): a bare name is this contract's; a
    namespaced name is another contract's and is deferred to compile."""

    def test_a_namespaced_reference_is_deferred_to_compile(self, parse, testing_document):
        crossing = copy.deepcopy(testing_document)
        crossing["operators"]["affects"]["arg_sorts"] = ["entity", "other/thing"]
        crossing["dimensions"]["population"]["restriction_sort"] = "other/cohort"
        contract = parse(crossing)
        assert contract.operators["affects"].arg_sorts == ("entity", "other/thing")
        assert contract.dimensions["population"].restriction_sort == "other/cohort"
        # As written, in the schema projection too (§4.5).
        assert contract.operators["affects"].schema_projection()["arg_sorts"] == ["entity", "other/thing"]

    def test_a_bare_undeclared_name_is_still_refused(self, parse, testing_document):
        broken = copy.deepcopy(testing_document)
        broken["operators"]["affects"]["arg_sorts"] = ["entity", "thing"]
        with pytest.raises(MalformedContract, match="not a sort this contract declares"):
            parse(broken)

    def test_own_namespace_is_refused(self, parse, testing_document):
        broken = copy.deepcopy(testing_document)
        broken["operators"]["affects"]["arg_sorts"] = ["entity", "testing/outcome"]
        with pytest.raises(MalformedContract, match="own namespace"):
            parse(broken)

    def test_the_base_namespace_is_refused(self, parse, testing_document):
        broken = copy.deepcopy(testing_document)
        broken["dimensions"]["population"]["restriction_sort"] = "science/cohort"
        with pytest.raises(MalformedContract, match="declares no claim vocabulary"):
            parse(broken)

    def test_a_malformed_reference_is_refused(self, parse, testing_document):
        for bad in ("Other/thing", "other/", "/thing", "a/b/c"):
            broken = copy.deepcopy(testing_document)
            broken["operators"]["affects"]["arg_sorts"] = ["entity", bad]
            with pytest.raises(MalformedContract):
                parse(broken)


class TestTheBaseContractIssuesNoOperator:
    def test_a_domain_contract_named_science_is_refused(self, parse, testing_document):
        # §7.1: operators are domain-issued without exception. A base-issued one
        # would sit outside the closure walk every other operator goes through.
        broken = copy.deepcopy(testing_document)
        broken["contract"] = "science"
        with pytest.raises(MalformedContract, match="domain-issued without exception"):
            parse(broken)


class TestSuccession:
    """§8.3's adopted rules, refused at contract load.

    Every case below goes through `parse_domain_contract`, not through
    `check_succession` directly. The check being *reachable* is not the property
    that matters; the property is that no contract reaches a caller without it.
    """

    @pytest.fixture()
    def genesis(self, parse, testing_document):
        return parse(testing_document)

    @staticmethod
    def successor_document(document, predecessor, **sections):
        successor = copy.deepcopy(document)
        successor["lineage"] = {"successor": predecessor.content_identity}
        successor["version"] = predecessor.version + 1
        successor.update(sections)
        return successor

    def test_genesis_is_compared_against_nothing(self, parse, testing_document):
        assert parse(testing_document, predecessor=None).predecessor is None

    def test_genesis_with_a_predecessor_supplied_is_refused(self, parse, testing_document, genesis):
        with pytest.raises(SuccessionViolation, match="declares genesis"):
            parse(testing_document, predecessor=genesis)

    def test_a_successor_with_no_predecessor_supplied_is_refused(self, parse, testing_document, genesis):
        # Skipping the check would let a redefinition through on the evidence
        # that nobody looked — the corpus's own recurring error, inverted.
        document = self.successor_document(testing_document, genesis)
        with pytest.raises(SuccessionViolation, match="two-contract check"):
            parse(document, predecessor=None)

    def test_an_additive_successor_is_accepted(self, parse, testing_document, genesis):
        operators = copy.deepcopy(testing_document["operators"])
        operators["precedes"] = {
            "arity": 2,
            "arg_sorts": ["entity", "entity"],
            "sign_apt": False,
            "layers": ["structural"],
            "dimensions": [],
        }
        successor = parse(self.successor_document(testing_document, genesis, operators=operators), predecessor=genesis)
        assert set(successor.operators) == {"affects", "subtype-of", "correlates-with", "measured-by", "precedes"}

    def test_an_editorial_change_is_accepted_and_moves_contract_identity(self, parse, testing_document, genesis):
        operators = copy.deepcopy(testing_document["operators"])
        operators["affects"]["description"] = "Reworded. Meaning-bearing fields untouched."
        successor = parse(self.successor_document(testing_document, genesis, operators=operators), predecessor=genesis)
        assert successor.content_identity != genesis.content_identity

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("arity", 1),
            ("arg_sorts", ["outcome", "entity"]),
            ("sign_apt", False),
            ("layers", ["structural"]),
            ("dimensions", ["population"]),
        ],
    )
    def test_redefining_a_declared_schema_is_refused(self, parse, testing_document, genesis, field, value):
        operators = copy.deepcopy(testing_document["operators"])
        operators["affects"][field] = value
        if field == "arity":
            operators["affects"]["arg_sorts"] = ["entity"]
        document = self.successor_document(testing_document, genesis, operators=operators)
        with pytest.raises(SuccessionViolation, match="different canonical schema projection"):
            parse(document, predecessor=genesis)

    def test_succession_covers_dimensions(self, parse, testing_document, genesis):
        dimensions = copy.deepcopy(testing_document["dimensions"])
        dimensions["population"]["restriction_sort"] = "entity"
        document = self.successor_document(testing_document, genesis, dimensions=dimensions)
        with pytest.raises(SuccessionViolation, match="dimension:population"):
            parse(document, predecessor=genesis)

    def test_succession_covers_sorts(self, parse, testing_document, genesis):
        sorts = copy.deepcopy(testing_document["sorts"])
        sorts["entity"]["vocabulary"] = {"namespace": "EX", "release": "2027-01-01"}
        document = self.successor_document(testing_document, genesis, sorts=sorts)
        with pytest.raises(SuccessionViolation, match="sort:entity"):
            parse(document, predecessor=genesis)

    def test_dropping_a_declaration_is_refused(self, parse, testing_document, genesis):
        operators = copy.deepcopy(testing_document["operators"])
        del operators["subtype-of"]
        document = self.successor_document(testing_document, genesis, operators=operators)
        with pytest.raises(SuccessionViolation, match="drops claim-vocabulary"):
            parse(document, predecessor=genesis)

    def test_a_mismatched_predecessor_identity_is_refused(self, parse, testing_document, genesis):
        document = copy.deepcopy(testing_document)
        document["lineage"] = {"successor": "f" * 64}
        document["version"] = 2
        with pytest.raises(SuccessionViolation, match="content identity is"):
            parse(document, predecessor=genesis)

    def test_the_scope_is_claim_vocabulary_and_nothing_else(self, genesis):
        # §8.3's scope restriction: an unscoped "every identifier" would have
        # this design quietly deciding facet versioning, which D §12 leaves open.
        assert all(key.split(":")[0] in {"sort", "dimension", "operator"} for key in genesis.claim_vocabulary())


class TestRetirementIsOneWay:
    """`retired` sits outside the canonical schema projection, so the schema
    comparison cannot see it. That is correct — inside, retiring an identifier
    would itself read as a redefinition and be refused — but it means retirement
    needs a rule of its own beside the schema check, not instead of it.
    """

    @pytest.fixture()
    def genesis(self, parse, testing_document):
        return parse(testing_document)

    @pytest.fixture()
    def tombstoned(self, parse, testing_document, genesis):
        operators = copy.deepcopy(testing_document["operators"])
        operators["affects"]["retired"] = True
        document = TestSuccession.successor_document(testing_document, genesis, operators=operators)
        return document, parse(document, predecessor=genesis)

    def test_retiring_is_permitted(self, tombstoned):
        _, contract = tombstoned
        assert contract.operators["affects"].retired is True
        assert contract.retired_identifiers() == frozenset({"operator:affects"})

    def test_un_retiring_is_refused(self, parse, tombstoned):
        document, contract = tombstoned
        revived = copy.deepcopy(document)
        revived["operators"]["affects"]["retired"] = False
        revived["lineage"] = {"successor": contract.content_identity}
        revived["version"] = contract.version + 1
        with pytest.raises(SuccessionViolation, match="un-retires operator:affects"):
            parse(revived, predecessor=contract)

    def test_dropping_the_retired_field_entirely_is_also_un_retiring(self, parse, tombstoned):
        # The default is `false`, so an omission is a resurrection written a
        # second way. Catching only the explicit spelling would leave the easier
        # one open.
        document, contract = tombstoned
        revived = copy.deepcopy(document)
        del revived["operators"]["affects"]["retired"]
        revived["lineage"] = {"successor": contract.content_identity}
        revived["version"] = contract.version + 1
        with pytest.raises(SuccessionViolation, match="un-retires operator:affects"):
            parse(revived, predecessor=contract)

    @pytest.mark.parametrize(("section", "name"), [("dimensions", "setting"), ("sorts", "outcome")])
    def test_it_covers_dimensions_and_sorts_too(self, parse, testing_document, genesis, section, name):
        retired = copy.deepcopy(testing_document[section])
        retired[name]["retired"] = True
        document = TestSuccession.successor_document(testing_document, genesis, **{section: retired})
        contract = parse(document, predecessor=genesis)

        revived = copy.deepcopy(document)
        revived[section][name]["retired"] = False
        revived["lineage"] = {"successor": contract.content_identity}
        revived["version"] = contract.version + 1
        with pytest.raises(SuccessionViolation, match=f"un-retires {section[:-1]}:{name}"):
            parse(revived, predecessor=contract)

    def test_dropping_a_tombstone_is_refused(self, parse, tombstoned):
        # A tombstone is what makes a historical claim still typeable.
        document, contract = tombstoned
        dropped = copy.deepcopy(document)
        del dropped["operators"]["affects"]
        dropped["lineage"] = {"successor": contract.content_identity}
        dropped["version"] = contract.version + 1
        with pytest.raises(SuccessionViolation, match="drops claim-vocabulary"):
            parse(dropped, predecessor=contract)

    def test_a_tombstone_may_not_be_redefined(self, parse, tombstoned):
        # Retirement freezes the declaration; it does not exempt it. A historical
        # claim is typed against the frozen retired declaration (§7.3a), so an
        # edit to one changes what that claim means.
        document, contract = tombstoned
        edited = copy.deepcopy(document)
        edited["operators"]["affects"]["arity"] = 1
        edited["operators"]["affects"]["arg_sorts"] = ["entity"]
        edited["lineage"] = {"successor": contract.content_identity}
        edited["version"] = contract.version + 1
        with pytest.raises(SuccessionViolation, match="different canonical schema projection"):
            parse(edited, predecessor=contract)


class TestDomainFacets:
    def test_the_testing_contract_declares_two_namespaced_facets(self, parse, testing_document):
        contract = parse(testing_document)
        assert set(contract.facets) == {"testing/axis", "testing/annotation"}
        assert contract.facets["testing/axis"].attaches_to == ("dataset",)
        assert contract.facets["testing/annotation"].attaches_to == ("dataset", "proposition")

    def test_a_domain_declaring_kinds_or_relations_is_refused(self, parse, testing_document):
        for section in ("kinds", "relations"):
            doc = copy.deepcopy(testing_document)
            doc[section] = {}
            with pytest.raises(MalformedContract, match=f"a domain contract declares no {section}"):
                parse(doc)

    def test_a_domain_facet_requires_attaches_to_and_fields(self, parse, testing_document):
        doc = copy.deepcopy(testing_document)
        del doc["facets"]["axis"]["attaches_to"]
        with pytest.raises(MalformedContract, match="attaches_to"):
            parse(doc)

    def test_a_domain_facet_may_not_declare_a_shape(self, parse, testing_document):
        doc = copy.deepcopy(testing_document)
        doc["facets"]["axis"]["shape"] = "schema"
        with pytest.raises(MalformedContract, match="unknown key"):
            parse(doc)

    def test_facets_enter_the_content_identity(self, parse, testing_document):
        before = parse(testing_document).content_identity
        doc = copy.deepcopy(testing_document)
        doc["facets"]["axis"]["fields"]["axis"]["required"] = False
        assert parse(doc).content_identity != before

    def test_a_contract_without_facets_still_loads(self, parse, testing_document):
        doc = copy.deepcopy(testing_document)
        del doc["facets"]
        assert parse(doc).facets == {}


class TestTheLoadBoundary:
    def test_reading_a_file_runs_the_succession_check(self, tmp_path, base_contract, parse, testing_document):
        # The gap this closes: a loader that parsed without checking would let a
        # malformed successor through the boundary most callers actually use.
        genesis = parse(testing_document)
        operators = copy.deepcopy(testing_document["operators"])
        operators["affects"]["arity"] = 1
        operators["affects"]["arg_sorts"] = ["entity"]
        document = TestSuccession.successor_document(testing_document, genesis, operators=operators)

        path = tmp_path / "successor.yaml"
        path.write_text(yaml.safe_dump(document), encoding="utf-8")
        with pytest.raises(SuccessionViolation, match="different canonical schema projection"):
            domain.load_domain_contract(path, base=base_contract, predecessor=genesis)

    def test_the_predecessor_has_no_default(self, base_contract, testing_contract_path):
        # An omission must not be spellable: a default would make the check
        # skippable by saying nothing, and an unperformed check reporting success
        # is the failure this corpus names most often.
        with pytest.raises(TypeError):
            domain.load_domain_contract(testing_contract_path, base=base_contract)  # type: ignore[call-arg]
        with pytest.raises(TypeError):
            domain.parse_domain_contract({}, source="<test>", base=base_contract)  # type: ignore[call-arg]


class TestParallelGenesis:
    def test_a_second_genesis_in_one_namespace_is_not_prevented(self, parse, testing_document):
        # §8.3 rules this an escape hatch and says so: the rules enforce
        # immutability *within a declared lineage*, not across a namespace.
        # Closing it needs pin-transition validation or a namespace authority —
        # governance, not typing — and ρC1 leaves it open. Asserted here so the
        # hole is visible in the suite rather than only in prose.
        first = parse(testing_document)
        forked = copy.deepcopy(testing_document)
        forked["operators"]["affects"]["arity"] = 1
        forked["operators"]["affects"]["arg_sorts"] = ["entity"]
        second = parse(forked)  # also genesis, same namespace, incompatible schema

        assert first.namespace == second.namespace
        assert first.claim_vocabulary() != second.claim_vocabulary()


def test_a_domain_contract_cannot_claim_the_coordination_namespace(base_contract, testing_document):
    testing_document["contract"] = "coordination"
    with pytest.raises(MalformedContract, match="reserved"):
        domain.parse_domain_contract(
            testing_document,
            source="<test>",
            base=base_contract,
            predecessor=None,
        )
