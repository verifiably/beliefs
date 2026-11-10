"""Pack declarations fold explicit bindings and compile typed restrictions."""

import pytest

from beliefs.contract.domain import parse_domain_contract
from beliefs.errors import MalformedContract, ProfileError
from beliefs.profile import compile_profile


@pytest.fixture()
def parse(base_contract):
    def read(document):
        return parse_domain_contract(document, source="<pack>", base=base_contract, predecessor=None)

    return read


def test_measurements_fold_over_packs(parse, testing_document, base_contract):
    testing = parse(testing_document)
    other = parse(
        {
            "contract": "other",
            "version": 1,
            "lineage": "genesis",
            "sorts": {},
            "dimensions": {},
            "measurements": {"testing/entity": ["testing/score"]},
        }
    )
    profile = compile_profile(base_contract, [testing, other])
    assert profile.measurements["testing/entity"] == frozenset({"testing/abundance", "testing/count", "testing/score"})
    assert profile.compiled_identity == compile_profile(base_contract, [other, testing]).compiled_identity
    assert profile.admits_measurement("testing/entity", "testing/count")


def test_an_unlisted_binding_is_not_admitted(parse, testing_document, base_contract):
    profile = compile_profile(base_contract, [parse(testing_document)])
    assert profile.measurements["testing/cohort"] == frozenset()
    assert not profile.admits_measurement("testing/cohort", "testing/score")
    assert not profile.admits_measurement("testing/missing", "testing/score")


def test_aspect_sorts_per_quantity_kind(parse, testing_document, base_contract):
    profile = compile_profile(base_contract, [parse(testing_document)])
    assert profile.aspect_sorts("testing/energy") == frozenset({"testing/energy-aspect"})
    assert profile.aspect_sorts("testing/duration") == frozenset()


@pytest.mark.parametrize(
    "table,key,values",
    [
        ("measurements", "entity", ["missing"]),
        ("measurements", "missing", []),
        ("aspects", "missing", ["entity"]),
        ("aspects", "energy", ["missing"]),
    ],
)
def test_pack_table_references_resolve_at_compile(parse, testing_document, base_contract, table, key, values):
    testing_document[table][key] = values
    with pytest.raises(ProfileError, match="missing"):
        compile_profile(base_contract, [parse(testing_document)])


@pytest.mark.parametrize(
    "restriction",
    [
        {"form": "term", "sort": "level"},
        {"form": "interval", "quantity_kind": "duration"},
        {"form": "time-interval"},
        {"form": "rule", "classes": "level"},
        {"form": "union", "of": {"form": "interval", "quantity_kind": "duration"}},
    ],
)
def test_dimension_restriction_forms(parse, testing_document, base_contract, restriction):
    testing_document["dimensions"]["follow-up"]["restriction"] = restriction
    profile = compile_profile(base_contract, [parse(testing_document)])
    compiled = profile.dimensions["testing/follow-up"].restriction
    assert compiled is not None
    assert compiled.form == restriction["form"]
    if compiled.form == "interval":
        assert compiled.quantity_kind == "testing/duration"
    if compiled.form == "union":
        assert compiled.of is not None
        assert compiled.of.quantity_kind == "testing/duration"
    assert profile.dimensions["testing/follow-up"].restriction_sort == "testing/level"


@pytest.mark.parametrize(
    "restriction",
    [
        {"form": "term"},
        {"form": "interval"},
        {"form": "rule"},
        {"form": "union"},
        {"form": "union", "of": {"form": "union", "of": {"form": "time-interval"}}},
        {"form": "term", "sort": "entity"},
        {"form": "time-interval", "sort": "level"},
    ],
)
def test_malformed_restrictions_refuse(parse, testing_document, restriction):
    testing_document["dimensions"]["follow-up"]["restriction"] = restriction
    with pytest.raises(MalformedContract):
        parse(testing_document)


def test_restriction_is_required_only_on_applicability(parse, testing_document):
    del testing_document["dimensions"]["follow-up"]["restriction"]
    with pytest.raises(MalformedContract):
        parse(testing_document)
    testing_document["dimensions"].pop("follow-up")
    testing_document["dimensions"]["population"]["restriction"] = {"form": "time-interval"}
    with pytest.raises(MalformedContract):
        parse(testing_document)


def test_union_term_keeps_the_interim_sort(parse, testing_document):
    testing_document["dimensions"]["follow-up"]["restriction"] = {
        "form": "union",
        "of": {"form": "term", "sort": "entity"},
    }
    with pytest.raises(MalformedContract, match="restriction_sort"):
        parse(testing_document)


def test_pack_provenance_survives_folding(parse, testing_document, base_contract):
    from beliefs.corpus import _registers_report
    from beliefs.register import AssumptionsRegister, RegisterEntry

    testing = parse(testing_document)
    other = parse(
        {
            "contract": "other",
            "version": 1,
            "lineage": "genesis",
            "sorts": {},
            "dimensions": {},
            "measurements": {"testing/method": ["testing/score"]},
            "aspects": {"testing/energy": ["testing/level"]},
        }
    )
    profile = compile_profile(base_contract, [testing, other])
    assert profile.aspect_sorts("testing/energy") == frozenset({"testing/energy-aspect", "testing/level"})
    projected = profile.projection()
    assert projected == compile_profile(base_contract, [other, testing]).projection()
    assert isinstance(projected["aspects"], dict)
    assert set(projected["aspects"]) == {"other:testing/energy", "testing:testing/energy"}
    entry = RegisterEntry("collapsed", "licensed", "unestablished")
    register = AssumptionsRegister(
        describes=f"testing:{testing.content_identity}",
        previous=None,
        entries={"measurement:testing/method": entry, "aspect:testing/level": entry},
    )
    findings = _registers_report(
        {"register": register}, {"testing": testing.content_identity, "other": other.content_identity}, profile
    )
    assert {f.detail for f in findings if f.code == "register-entry-unknown"} == {
        "measurement:testing/method",
        "aspect:testing/level",
    }


@pytest.mark.parametrize(
    "table,key,value",
    [
        ("measurements", "entity", "count"),
        ("measurements", "entity", ["count", "count"]),
        ("aspects", "energy", ["level", "level"]),
        ("aspects", "energy", [None]),
    ],
)
def test_pack_values_are_lists_of_distinct_references(parse, testing_document, table, key, value):
    testing_document[table][key] = value
    with pytest.raises(MalformedContract):
        parse(testing_document)


@pytest.mark.parametrize(
    "restriction", [{"form": "interval", "quantity_kind": "missing"}, {"form": "rule", "classes": "missing"}]
)
def test_restriction_references_resolve_at_compile(parse, testing_document, base_contract, restriction):
    testing_document["dimensions"]["follow-up"]["restriction"] = restriction
    with pytest.raises(ProfileError, match="missing"):
        compile_profile(base_contract, [parse(testing_document)])
