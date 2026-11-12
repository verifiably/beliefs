"""Explicit consumer activation, claim-identity parity and write-door admission over `general`.

`domains/general/DOMAIN.yaml` declares shared vocabulary with zero sorts and zero
instantiations. A consumer contract (`fixtures/contracts/general-consumer.yaml`,
explicitly synthetic consumer vocabulary rather than a biology pack) activates
`general` explicitly, binds its own sorts and instantiations, authors shared
claims whose canonical bytes and digests match TypeScript row-for-row, and
admits a minimal empirical `analysis-spec` citing the canonical `general`
assumptions register without fabricating any proxy, aggregate mapping or
assumption.
"""

from __future__ import annotations

import copy
import json
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest
from authority import FULL
from conftest import REPO_ROOT
from fixtures_cut3 import DATA_ADDRESS, FixtureRecords, seed_plan
from fixtures_cut4 import reopen
from profiles import pins_for

from beliefs import stored
from beliefs.applicability import Applicability
from beliefs.audit import NO_EVIDENCE, audit_corpus
from beliefs.claim import Member, Qualifier, Referent, build_claim
from beliefs.contract import load_domain_contract, parse_base_contract, parse_domain_contract
from beliefs.contract.document import parse_document
from beliefs.corpus import corpus_check
from beliefs.errors import DuplicateMember, EstimandError, MalformedRecord, ProfileError
from beliefs.estimand import (
    Control,
    MeasuredBinding,
    OutputSpec,
    RoleTermLevels,
    ValueReference,
    build_estimand,
    estimand_projection,
)
from beliefs.identity import v1
from beliefs.measurement import Measure, Observable
from beliefs.procedure import Procedure, Scale, procedure_from_stored
from beliefs.profile import (
    compile_profile,
    shipped_assumptions_register,
    shipped_base_contract,
    shipped_domain_contract,
)
from beliefs.projection import CLAIM_DOMAIN, claim_identity, project_claim
from beliefs.register import (
    AssumptionsRegister,
    RegisterEntry,
    register_entry_keys,
    register_identity,
)
from beliefs.resolution import build_snapshot
from beliefs.root import init_corpus_root, metadata_root_for, open_corpus
from beliefs.spec import RuleFixture, RuleImplementation, Seeded, SpecDraft, SpecInput, freeze

CONSUMER_CONTRACT_PATH = REPO_ROOT / "fixtures" / "contracts" / "general-consumer.yaml"
GENERAL_CONTRACT_PATH = REPO_ROOT / "domains" / "general" / "DOMAIN.yaml"
PARITY_FIXTURE_PATH = REPO_ROOT / "fixtures" / "general-claim-identity-v2.json"
HISTORICAL_BASE_V2_IDENTITY = "ca869c80b5d90807ba9c7dd4aec38b2b969df2eed0e5aec777da873da6f83ef2"
UNCONSULTED = build_snapshot(readable={})


def _load_consumer_contract():
    return load_domain_contract(CONSUMER_CONTRACT_PATH, base=shipped_base_contract(), predecessor=None)


def _load_general_consumer_profile():
    base = shipped_base_contract()
    general = shipped_domain_contract("general")
    consumer = _load_consumer_contract()
    return compile_profile(base, [general, consumer])


def _load_parity_fixture() -> tuple[str, dict[str, object]]:
    raw = PARITY_FIXTURE_PATH.read_text(encoding="utf-8")
    parsed = json.loads(raw)
    assert isinstance(parsed, dict)
    return raw, parsed


def _referent(value: dict[str, object]) -> Referent:
    sort = value["sort"]
    term = value["term"]
    assert isinstance(sort, str) and isinstance(term, str)
    return Referent(sort=sort, term=term)


def _role(value: object) -> Referent | tuple[Member, ...]:
    if isinstance(value, dict):
        return _referent(value)
    assert isinstance(value, list)
    members: list[Member] = []
    for item in value:
        assert isinstance(item, dict)
        coeff = item["coefficient"]
        assert isinstance(coeff, int)
        members.append(Member(_referent(item), coeff))
    return tuple(members)


def _build_from_row(profile, claim_row: dict[str, object]):
    roles_raw = claim_row["roles"]
    qualifiers_raw = claim_row["qualifiers"]
    operator = claim_row["operator"]
    form = claim_row["form"]
    polarity = claim_row["polarity"]
    layer = claim_row["layer"]
    assert isinstance(roles_raw, dict) and isinstance(qualifiers_raw, dict)
    assert isinstance(operator, str) and isinstance(form, str) and isinstance(layer, str)
    assert polarity is None or isinstance(polarity, str)
    qualifiers: dict[str, Qualifier] = {}
    for dimension, entry in qualifiers_raw.items():
        assert isinstance(entry, dict)
        quantifier = entry["quantifier"]
        restriction = entry["restriction"]
        assert isinstance(quantifier, str) and isinstance(restriction, dict)
        qualifiers[dimension] = Qualifier(quantifier, _referent(restriction))
    return build_claim(
        profile,
        operator=operator,
        roles={name: _role(val) for name, val in roles_raw.items()},
        qualifiers=qualifiers,
        form=form,
        polarity=polarity,
        layer=layer,
    )


def _synthetic_procedures_and_records(
    *, unknown_validation: bool = False
) -> tuple[FixtureRecords, str, str, Observable]:
    records = FixtureRecords()
    observable = Observable("general/relative-abundance", "general-consumer/analyte")
    assay_id = records.put_procedure(
        Procedure(
            kind="general/assay",
            name="Synthetic relative-abundance assay",
            definition="Synthetic consumer validation scope only; does not certify a real mm30 procedure.",
            yields=(observable,),
            scale=Scale(Fraction(0), Fraction(1_000_000), "higher-is-more"),
            validated_in="unknown" if unknown_validation else {},
            compatible_with=(),
            evidence=(),
            implementation=None,
            inputs=None,
            parameters={},
            external=None,
        )
    )
    estimator_id = records.put_procedure(
        Procedure(
            kind="general/estimator",
            name="Synthetic probability-of-superiority estimator",
            definition="Synthetic consumer validation scope only; does not certify a real mm30 procedure.",
            yields=(),
            scale=None,
            validated_in={},
            compatible_with=(),
            evidence=(),
            implementation=None,
            inputs=None,
            parameters={},
            external=None,
        )
    )
    return records, assay_id, estimator_id, observable


def _synthetic_consumer_register(consumer_contract) -> AssumptionsRegister:
    entry = RegisterEntry(
        "Synthetic consumer fixture collapses only test-local distinctions.",
        "Synthetic consumer fixture licenses only integration test claims and estimands.",
        "Synthetic consumer fixture certifies no scientific domain or mm30 procedure.",
        status="provisional",
    )
    return AssumptionsRegister(
        describes=f"{consumer_contract.namespace}:{consumer_contract.content_identity}",
        previous=None,
        entries={key: entry for key in sorted(register_entry_keys(consumer_contract))},
    )


def _synthetic_rules() -> dict[str, RuleImplementation]:
    return {
        "probability-of-superiority/v1": RuleImplementation(
            identity="impl-pos-1",
            evaluate=lambda manifest: {"outcome": "supported"},
            fixtures=(RuleFixture(arguments=(None,), expected={"outcome": "supported"}),),
        ),
        "content-identity-equality/v1": RuleImplementation(
            identity="impl-eq-1",
            evaluate=lambda a, b: "passed" if a == b else "failed",
            fixtures=(RuleFixture(arguments=(1, 1), expected="passed"),),
        ),
    }


def test_consumer_requires_explicit_general_activation_and_declares_no_restricted_tables():
    base = shipped_base_contract()
    general = shipped_domain_contract("general")

    # `base + general` alone compiles cleanly with zero sorts and zero instantiations.
    alone = compile_profile(base, [general])
    assert alone.base_contract_identity == base.content_identity
    assert alone.activated_contracts == {"general": general.content_identity}
    assert alone.sorts == {}
    assert alone.instantiations == {}
    assert alone.authorable_operators() == ()

    # Consumer fixture declares none of the 14 restricted shared tables.
    consumer_raw = parse_document(
        CONSUMER_CONTRACT_PATH.read_text(encoding="utf-8"), source=str(CONSUMER_CONTRACT_PATH)
    )
    assert isinstance(consumer_raw, dict)
    restricted = {
        "templates",
        "quantity_kinds",
        "units",
        "constants",
        "conversions",
        "duration_conventions",
        "transformations",
        "functionals",
        "identification_classes",
        "designs",
        "selection_mechanisms",
        "procedure_kinds",
        "aggregation_rules",
        "assumption_kinds",
    }
    assert restricted.isdisjoint(consumer_raw.keys())

    # Omitting `general` refuses compilation; activating `general` explicitly succeeds.
    consumer = _load_consumer_contract()
    with pytest.raises(ProfileError, match="general/"):
        compile_profile(base, [consumer])

    profile = compile_profile(base, [general, consumer])
    assert profile.base_contract_identity == base.content_identity
    assert profile.activated_contracts == {
        "general": general.content_identity,
        "general-consumer": consumer.content_identity,
    }
    assert set(profile.sorts) == {
        "general-consumer/analyte",
        "general-consumer/trait",
        "general-consumer/stratum",
    }


def test_general_parity_fixture_reproduces_every_row_and_pins_compiled_identity():
    profile = _load_general_consumer_profile()
    raw, fixture = _load_parity_fixture()

    assert raw.isascii()
    assert fixture["claim_domain"] == CLAIM_DOMAIN
    assert fixture["identity_contract"] == "science.identity.v1"
    assert fixture["base_contract"] == "contracts/science/CONTRACT.yaml"
    assert fixture["domain_contracts"] == [
        "domains/general/DOMAIN.yaml",
        "fixtures/contracts/general-consumer.yaml",
    ]
    assert fixture["profile_compiled_identity"] == profile.compiled_identity

    vector = fixture["vector"]
    assert isinstance(vector, list) and len(vector) >= 8
    names = [row["name"] for row in vector if isinstance(row, dict)]
    assert len(names) == len(set(names))

    reversed_rows = {"same-sort-parties-reversed", "cross-sort-parties-reversed"}
    non_reversed_digests = [
        row["digest"] for row in vector if isinstance(row, dict) and row["name"] not in reversed_rows
    ]
    assert len(non_reversed_digests) == len(set(non_reversed_digests))

    by_name: dict[str, dict[str, object]] = {}
    for row in vector:
        assert isinstance(row, dict)
        name = row["name"]
        claim_spec = row["claim"]
        assert isinstance(name, str) and isinstance(claim_spec, dict)
        by_name[name] = row
        claim = _build_from_row(profile, claim_spec)
        projected = project_claim(claim)
        assert projected == row["projection"]
        assert v1.encode(projected).decode("utf-8") == row["canonical_bytes"]
        assert claim_identity(claim) == row["digest"]

    for forward_name, reversed_name in (
        ("same-sort-parties-forward", "same-sort-parties-reversed"),
        ("cross-sort-parties-forward", "cross-sort-parties-reversed"),
    ):
        assert by_name[forward_name]["projection"] == by_name[reversed_name]["projection"]
        assert by_name[forward_name]["canonical_bytes"] == by_name[reversed_name]["canonical_bytes"]
        assert by_name[forward_name]["digest"] == by_name[reversed_name]["digest"]


def test_symmetric_parties_order_invariance_and_duplicate_after_nfc_refusal():
    profile = _load_general_consumer_profile()
    assert profile.base_contract_identity == shipped_base_contract().content_identity

    # Same-sort symmetric `parties` order invariance.
    forward = build_claim(
        profile,
        operator="general/covaries-with",
        roles={
            "parties": (
                Member(Referent("general-consumer/analyte", "SYN:analyte-b")),
                Member(Referent("general-consumer/analyte", "SYN:analyte-a")),
            )
        },
        form="polar",
        polarity="positive",
        layer="statistical",
    )
    reversed_parties = build_claim(
        profile,
        operator="general/covaries-with",
        roles={
            "parties": (
                Member(Referent("general-consumer/analyte", "SYN:analyte-a")),
                Member(Referent("general-consumer/analyte", "SYN:analyte-b")),
            )
        },
        form="polar",
        polarity="positive",
        layer="statistical",
    )
    assert claim_identity(forward) == claim_identity(reversed_parties)
    assert project_claim(forward) == project_claim(reversed_parties)

    # Cross-sort symmetric `parties` order invariance (`analyte` + `stratum` and `analyte` + `trait`).
    for left, right in (
        (
            Referent("general-consumer/stratum", "SYN:arm-high"),
            Referent("general-consumer/analyte", "SYN:analyte-a"),
        ),
        (
            Referent("general-consumer/trait", "SYN:trait-y"),
            Referent("general-consumer/analyte", "SYN:analyte-a"),
        ),
    ):
        cross_fwd = build_claim(
            profile,
            operator="general/covaries-with",
            roles={"parties": (Member(left), Member(right))},
            form="polar",
            polarity="positive",
            layer="statistical",
        )
        cross_rev = build_claim(
            profile,
            operator="general/covaries-with",
            roles={"parties": (Member(right), Member(left))},
            form="polar",
            polarity="positive",
            layer="statistical",
        )
        assert claim_identity(cross_fwd) == claim_identity(cross_rev)
        assert project_claim(cross_fwd) == project_claim(cross_rev)

    # Duplicate-after-NFC referents in `parties` refuse at `build_claim`.
    composed = Referent("general-consumer/analyte", "SYN:caf\u00e9")
    decomposed = Referent("general-consumer/analyte", "SYN:cafe\u0301")
    assert composed.term != decomposed.term
    with pytest.raises(DuplicateMember):
        build_claim(
            profile,
            operator="general/covaries-with",
            roles={"parties": (Member(composed), Member(decomposed))},
            form="polar",
            polarity="positive",
            layer="statistical",
        )


def test_parties_member_bindings_select_response_and_grouping_independently_of_order():
    profile = _load_general_consumer_profile()
    records, assay_id, _estimator_id, observable = _synthetic_procedures_and_records()

    analyte_ref = Referent("general-consumer/analyte", "SYN:analyte-a")
    stratum_high = Referent("general-consumer/stratum", "SYN:arm-high")
    stratum_low = Referent("general-consumer/stratum", "SYN:arm-low")

    forward_claim = build_claim(
        profile,
        operator="general/covaries-with",
        roles={"parties": (Member(stratum_high), Member(analyte_ref))},
        form="polar",
        polarity="positive",
        layer="statistical",
    )
    reversed_claim = build_claim(
        profile,
        operator="general/covaries-with",
        roles={"parties": (Member(analyte_ref), Member(stratum_high))},
        form="polar",
        polarity="positive",
        layer="statistical",
    )

    measure = Measure(observable, None, assay_id, "ratio", "level", "general/identity", assay_id)
    bindings = {
        "response": MeasuredBinding("parties", analyte_ref, measure, None, None),
        "grouping": RoleTermLevels("parties", stratum_high, (stratum_low, stratum_high)),
    }
    control = Control("general/observational", (), "general/independent-groups", "general/cohort-enrolment")

    est_fwd, _ = build_estimand(
        profile,
        forward_claim,
        snapshot=UNCONSULTED,
        form="contrast",
        functional="general/probability-of-superiority",
        bindings=bindings,
        outputs={"estimate": OutputSpec("dimensionless", "unit-interval")},
        reference=ValueReference(Decimal("0.5")),
        control=control,
        uncertainty="interval",
        assumptions=(),
        calibration=None,
        applicability=Applicability({}),
        records=records,
    )
    est_rev, _ = build_estimand(
        profile,
        reversed_claim,
        snapshot=UNCONSULTED,
        form="contrast",
        functional="general/probability-of-superiority",
        bindings=bindings,
        outputs={"estimate": OutputSpec("dimensionless", "unit-interval")},
        reference=ValueReference(Decimal("0.5")),
        control=control,
        uncertainty="interval",
        assumptions=(),
        calibration=None,
        applicability=Applicability({}),
        records=records,
    )
    assert estimand_projection(est_fwd) == estimand_projection(est_rev)

    # Naming a member absent from `parties` refuses.
    with pytest.raises(EstimandError):
        build_estimand(
            profile,
            forward_claim,
            snapshot=UNCONSULTED,
            form="contrast",
            functional="general/probability-of-superiority",
            bindings={
                "response": MeasuredBinding(
                    "parties",
                    Referent("general-consumer/analyte", "SYN:absent"),
                    measure,
                    None,
                    None,
                ),
                "grouping": bindings["grouping"],
            },
            outputs={"estimate": OutputSpec("dimensionless", "unit-interval")},
            reference=ValueReference(Decimal("0.5")),
            control=control,
            uncertainty="interval",
            assumptions=(),
            calibration=None,
            applicability=Applicability({}),
            records=records,
        )


@pytest.mark.parametrize("unknown_validation", [False, True])
def test_empirical_general_write_door_round_trip(certified_work: Path, unknown_validation: bool):
    """Minimal empirical write-door round-trip on the certified volume.

    Synthetic validation scope only: holds the canonical `general` assumptions
    register, a complete synthetic consumer register, and synthetic assay and
    estimator procedures; authors a procedure-scale `general/relative-abundance`
    response with `general/identity`, `general/observational` /
    `general/independent-groups` / `general/cohort-enrolment` control, and
    `general/probability-of-superiority` without fabricating any proxy,
    aggregate mapping or assumption.
    """
    consumer = _load_consumer_contract()
    profile = _load_general_consumer_profile()
    records, assay_id, estimator_id, observable = _synthetic_procedures_and_records(
        unknown_validation=unknown_validation
    )

    root = certified_work / "general-write-door"
    try:
        init_corpus_root(root, authority=FULL)
        writer = open_corpus(root, authority=FULL, profile=profile)
        writer.adopt_manifest(profile=pins_for(profile))

        general_reg = shipped_assumptions_register("general")
        expected_general_reg_id = register_identity(general_reg)
        general_reg_node = writer.add(stored.assumptions_register_node(general_reg))
        assert general_reg_node.id == expected_general_reg_id
        records.nodes[general_reg_node.id] = general_reg_node

        consumer_reg = _synthetic_consumer_register(consumer)
        consumer_reg_node = writer.add(stored.assumptions_register_node(consumer_reg))
        records.nodes[consumer_reg_node.id] = consumer_reg_node

        assay_node = writer.add(records.read(assay_id))
        estimator_node = writer.add(records.read(estimator_id))
        assert assay_node.id == assay_id
        assert estimator_node.id == estimator_id

        analyte_ref = Referent("general-consumer/analyte", "SYN:analyte-a")
        stratum_high = Referent("general-consumer/stratum", "SYN:arm-high")
        stratum_low = Referent("general-consumer/stratum", "SYN:arm-low")
        claim = build_claim(
            profile,
            operator="general/covaries-with",
            roles={"parties": (Member(analyte_ref), Member(stratum_high))},
            form="polar",
            polarity="positive",
            layer="statistical",
        )
        prop = writer.add(
            stored.proposition_node("general-prop-1", title="Synthetic general covariance", claim=project_claim(claim))
        )

        measure = Measure(observable, None, assay_id, "ratio", "level", "general/identity", assay_id)
        estimand, _ = build_estimand(
            profile,
            claim,
            snapshot=UNCONSULTED,
            form="contrast",
            functional="general/probability-of-superiority",
            bindings={
                "response": MeasuredBinding("parties", analyte_ref, measure, None, None),
                "grouping": RoleTermLevels("parties", stratum_high, (stratum_low, stratum_high)),
            },
            outputs={"estimate": OutputSpec("dimensionless", "unit-interval")},
            reference=ValueReference(Decimal("0.5")),
            control=Control("general/observational", (), "general/independent-groups", "general/cohort-enrolment"),
            uncertainty="interval",
            assumptions=(),
            calibration=None,
            applicability=Applicability({}),
            records=records,
        )
        if unknown_validation:
            (instance,) = estimand.assumptions
            assert instance.kind == "general/procedure-validity"
            assert instance.particulars == {"record": assay_id, "co_scope": "unknown", "dimensions": ""}
        else:
            assert estimand.assumptions == ()
        assert estimand.calibration is None

        draft = SpecDraft(
            target=prop.id,
            estimand=estimand,
            method="Synthetic Mann-Whitney / exact half-tie probability-of-superiority validation.",
            assumptions="Synthetic consumer validation scope only; independent strata observations.",
            falsification="Probability-of-superiority interval fails to clear 0.5.",
            input_roles=(SpecInput(role="observes", dataset=DATA_ADDRESS, mode="observation"),),
            applicability=Applicability({}),
            interpretation_rule="probability-of-superiority/v1",
            equivalence_rule="content-identity-equality/v1",
            parameters={"alpha": Decimal("0.05")},
            nondeterminism=Seeded(plan=seed_plan()),
            registers=(general_reg_node.id, consumer_reg_node.id),
            standing="empirical",
            model=None,
        )
        spec = freeze(
            draft,
            held_rules=_synthetic_rules(),
            profile=profile,
            claim=claim,
            records=records,
            rule_procedures={"probability-of-superiority/v1": estimator_id},
        )
        spec_node = writer.add(stored.analysis_spec_node(spec))

        reopened = reopen(root)
        restored_spec = stored.analysis_spec_value(reopened.get(spec_node.id), profile=profile)
        assert restored_spec == spec
        restored_assay = procedure_from_stored(reopened.get(assay_id))
        assert restored_assay.validated_in == ("unknown" if unknown_validation else {})
        assert expected_general_reg_id in restored_spec.registers
        assert set(restored_spec.registers) == {general_reg_node.id, consumer_reg_node.id}
        assert {dep.id for dep in restored_spec.assessed_target.dependencies} == {
            assay_id,
            estimator_id,
            general_reg_node.id,
            consumer_reg_node.id,
        }
        assert corpus_check(reopened, profile) == ()
        assert audit_corpus(reopened, evidence=NO_EVIDENCE, profile=profile) == ()
    finally:
        import shutil

        shutil.rmtree(metadata_root_for(root), ignore_errors=True)


def test_base_v2_to_v3_two_field_transition_preserves_claim_identity():
    base_path = REPO_ROOT / "contracts" / "science" / "CONTRACT.yaml"
    v3_doc = parse_document(base_path.read_text(encoding="utf-8"), source=str(base_path))
    assert isinstance(v3_doc, dict)

    v2_doc = copy.deepcopy(v3_doc)
    assert v2_doc["version"] == 3
    v2_doc["version"] = 2
    kinds = v2_doc["kinds"]
    assert isinstance(kinds, dict)
    reg_kind = kinds["assumptions-register"]
    assert isinstance(reg_kind, dict)
    assert reg_kind["domain"] == "science.assumptions-register.v2"
    reg_kind["domain"] = "science.assumptions-register.v1"

    old_base = parse_base_contract(v2_doc, source="<derived-base-v2>")
    new_base = shipped_base_contract()
    assert old_base.content_identity == HISTORICAL_BASE_V2_IDENTITY
    assert new_base.content_identity != HISTORICAL_BASE_V2_IDENTITY

    # This isolates the historical base-v2-to-v3 transition using the original general genesis.
    genesis_path = (
        GENERAL_CONTRACT_PATH.parent
        / "history"
        / "cd89bb6dbf4d28a13b04ca89ddd35d9a4da83bace06e8265ee60048fd0dec48f"
        / "DOMAIN.yaml"
    )
    general_doc = parse_document(genesis_path.read_text(encoding="utf-8"), source=str(genesis_path))
    consumer_doc = parse_document(
        CONSUMER_CONTRACT_PATH.read_text(encoding="utf-8"), source=str(CONSUMER_CONTRACT_PATH)
    )

    general_under_old = parse_domain_contract(
        general_doc, source=str(GENERAL_CONTRACT_PATH), base=old_base, predecessor=None
    )
    consumer_under_old = parse_domain_contract(
        consumer_doc, source=str(CONSUMER_CONTRACT_PATH), base=old_base, predecessor=None
    )
    general_under_new = parse_domain_contract(
        general_doc, source=str(GENERAL_CONTRACT_PATH), base=new_base, predecessor=None
    )
    consumer_under_new = parse_domain_contract(
        consumer_doc, source=str(CONSUMER_CONTRACT_PATH), base=new_base, predecessor=None
    )

    old_profile = compile_profile(old_base, [general_under_old, consumer_under_old])
    new_profile = compile_profile(new_base, [general_under_new, consumer_under_new])
    assert old_profile.base_contract_identity == HISTORICAL_BASE_V2_IDENTITY
    assert new_profile.base_contract_identity == new_base.content_identity
    assert old_profile.base_contract_identity != new_profile.base_contract_identity
    assert old_profile.compiled_identity != new_profile.compiled_identity

    _raw, fixture = _load_parity_fixture()
    vector = fixture["vector"]
    assert isinstance(vector, list)
    for row in vector:
        assert isinstance(row, dict)
        claim_spec = row["claim"]
        assert isinstance(claim_spec, dict)
        old_claim = _build_from_row(old_profile, claim_spec)
        new_claim = _build_from_row(new_profile, claim_spec)
        assert project_claim(old_claim) == project_claim(new_claim)
        assert v1.encode(project_claim(old_claim)) == v1.encode(project_claim(new_claim))
        assert claim_identity(old_claim) == claim_identity(new_claim)

    # New v2 register IDs and dependent frozen-spec IDs differ from v1; shipped caches stay untouched.
    v1_like_reg_id = "assumptions-register:" + v1.digest(
        "science.assumptions-register.v1",
        {
            "describes": f"general-consumer:{consumer_under_old.content_identity}",
            "entries": {
                "sort:general-consumer/analyte": {
                    "collapses": "c",
                    "licenses": "l",
                    "not_established": "u",
                }
            },
        },
    )
    v2_reg = AssumptionsRegister(
        describes=f"general-consumer:{consumer_under_new.content_identity}",
        previous=None,
        entries={"sort:general-consumer/analyte": RegisterEntry("c", "l", "u", status="provisional")},
    )
    v2_reg_established = AssumptionsRegister(
        describes=f"general-consumer:{consumer_under_new.content_identity}",
        previous=None,
        entries={"sort:general-consumer/analyte": RegisterEntry("c", "l", "u", status="established")},
    )
    v2_reg_id = register_identity(v2_reg)
    v2_established_id = register_identity(v2_reg_established)
    assert v1_like_reg_id != v2_reg_id
    assert v2_reg_id != v2_established_id

    # No v1 register reader exists: a v1-shaped stored register payload is refused.
    from beliefs.register import register_from_stored

    v1_shaped_node = stored.assumptions_register_node(v2_reg).model_copy(deep=True)
    del v1_shaped_node.facets["assumptions-register"]["entries"]["sort:general-consumer/analyte"]["status"]
    with pytest.raises(MalformedRecord):
        register_from_stored(v1_shaped_node)

    records, assay_id, estimator_id, observable = _synthetic_procedures_and_records()
    v2_reg_node = stored.assumptions_register_node(v2_reg)
    v2_est_node = stored.assumptions_register_node(v2_reg_established)
    records.nodes[v2_reg_node.id] = v2_reg_node
    records.nodes[v2_est_node.id] = v2_est_node
    analyte_ref = Referent("general-consumer/analyte", "SYN:analyte-a")
    stratum_high = Referent("general-consumer/stratum", "SYN:arm-high")
    stratum_low = Referent("general-consumer/stratum", "SYN:arm-low")
    claim = build_claim(
        new_profile,
        operator="general/covaries-with",
        roles={"parties": (Member(analyte_ref), Member(stratum_high))},
        form="polar",
        polarity="positive",
        layer="statistical",
    )
    estimand, _ = build_estimand(
        new_profile,
        claim,
        snapshot=UNCONSULTED,
        form="contrast",
        functional="general/probability-of-superiority",
        bindings={
            "response": MeasuredBinding(
                "parties",
                analyte_ref,
                Measure(observable, None, assay_id, "ratio", "level", "general/identity", assay_id),
                None,
                None,
            ),
            "grouping": RoleTermLevels("parties", stratum_high, (stratum_low, stratum_high)),
        },
        outputs={"estimate": OutputSpec("dimensionless", "unit-interval")},
        reference=ValueReference(Decimal("0.5")),
        control=Control("general/observational", (), "general/independent-groups", "general/cohort-enrolment"),
        uncertainty="interval",
        assumptions=(),
        calibration=None,
        applicability=Applicability({}),
        records=records,
    )
    spec_provisional = freeze(
        SpecDraft(
            target="proposition:1",
            estimand=estimand,
            method="m",
            assumptions="a",
            falsification="f",
            input_roles=(SpecInput(role="observes", dataset=DATA_ADDRESS, mode="observation"),),
            applicability=Applicability({}),
            interpretation_rule="probability-of-superiority/v1",
            equivalence_rule="content-identity-equality/v1",
            parameters={"alpha": Decimal("0.05")},
            nondeterminism=Seeded(plan=seed_plan()),
            registers=(v2_reg_id,),
            standing="empirical",
            model=None,
        ),
        held_rules=_synthetic_rules(),
        profile=new_profile,
        claim=claim,
        records=records,
        rule_procedures={"probability-of-superiority/v1": estimator_id},
    )
    spec_established = freeze(
        SpecDraft(
            target="proposition:1",
            estimand=estimand,
            method="m",
            assumptions="a",
            falsification="f",
            input_roles=(SpecInput(role="observes", dataset=DATA_ADDRESS, mode="observation"),),
            applicability=Applicability({}),
            interpretation_rule="probability-of-superiority/v1",
            equivalence_rule="content-identity-equality/v1",
            parameters={"alpha": Decimal("0.05")},
            nondeterminism=Seeded(plan=seed_plan()),
            registers=(v2_established_id,),
            standing="empirical",
            model=None,
        ),
        held_rules=_synthetic_rules(),
        profile=new_profile,
        claim=claim,
        records=records,
        rule_procedures={"probability-of-superiority/v1": estimator_id},
    )
    assert spec_provisional.identity != spec_established.identity
    assert shipped_base_contract().version == 3
