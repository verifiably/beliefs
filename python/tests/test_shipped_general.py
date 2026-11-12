"""Shipped `general` successor contract and canonical assumptions register."""

from __future__ import annotations

import json
import shutil
from importlib import resources
from pathlib import Path

import pytest
from conftest import REPO_ROOT

import beliefs
from beliefs import profile as profile_module
from beliefs import stored
from beliefs.contract.document import parse_document
from beliefs.errors import CanonicalTextRefused, MalformedContract, ProfileError
from beliefs.profile import (
    compile_profile,
    shipped_base,
    shipped_base_contract,
    shipped_domain_contract,
)
from beliefs.register import (
    AssumptionsRegister,
    RegisterEntry,
    register_entry_keys,
    register_from_stored,
    register_identity,
    register_projection,
)

EXPECTED_GENERAL_CONTENT_IDENTITY = "e74a497975e4a536f1bcbef26de73558d8a528276f4754082c6dd2d399f447ee"
EXPECTED_GENERAL_COMPILED_IDENTITY = "2df4e0f432ae4bd41f91a7aa76f01a7985c42b9dbb4116997a56d4a431fe202a"
EXPECTED_GENERAL_REGISTER_IDENTITY = (
    "assumptions-register:6939b589ff96806160232b13cba8b32019c7fc80caba0b4b06b9e7d676c98095"
)

EXPECTED_DEFINITIONS: dict[tuple[str, str], str] = {
    ("templates", "covaries-with"): (
        "Measured quantities of two bearers vary together within a stated population and conditioning scheme."
    ),
    ("templates", "changes-under-intervention"): (
        "Setting the intervention bearer changes a measured quantity of the response bearer under stated conditions."
    ),
    ("quantity_kinds", "relative-abundance"): (
        "Abundance of a named component relative to a procedure-specified reference total after that procedure's "
        "weighting or normalization."
    ),
    ("transformations", "identity"): "The fixed map f(x)=x on real values.",
    ("functionals", "probability-of-superiority"): (
        "P(X>Y)+0.5 P(X=Y), with X drawn from the comparison level and Y from the baseline."
    ),
    ("identification_classes", "observational"): (
        "Statistical comparison without a claimed intervention-identification license."
    ),
    ("designs", "independent-groups"): (
        "An analysis design that treats observations in its compared groups as independent sampling units."
    ),
    ("selection_mechanisms", "cohort-enrolment"): (
        "Inclusion through membership in a specified enrolled cohort and its documented eligibility process."
    ),
    ("procedure_kinds", "assay"): (
        "A specified procedure producing measurements from empirical material or observations."
    ),
    ("procedure_kinds", "estimator"): ("A specified computation producing an estimate or analysis output from inputs."),
}

EXPECTED_ENTRIES: dict[str, RegisterEntry] = {
    "template:general/covaries-with": RegisterEntry(
        "A shared relation groups many possible measures and conditioning schemes; the estimand fixes each one.",
        "A symmetric statistical question; first use is the biology/mm30 analysis specified in the accepted "
        "measurement design section 12.",
        "Causation, mechanism, exchangeability and interchangeability of measurements are not established.",
        status="provisional",
    ),
    "template:general/changes-under-intervention": RegisterEntry(
        "The relation abstracts over interventions and mechanisms; the estimand and procedures retain the "
        "particular intervention and response.",
        "A directed causal question and the target of a narrower literature bridge; first use is the biology "
        "successor's regulates bridge in architecture section 10.2.",
        "Observational association or a literature label alone does not establish intervention validity, "
        "mechanism or empirical support.",
        status="provisional",
    ),
    "quantity-kind:general/relative-abundance": RegisterEntry(
        "Component resolution, normalization and the reference total are retained by the observable and procedure "
        "rather than this common quantity label.",
        "A dimensionless quantity kind for the mm30 RNA abundance procedure; it supersedes the provisional "
        "transcript-abundance name.",
        "This is not any generic proportion: a probability, membership fraction or power fraction is not relative "
        "abundance merely because it is unitless. Equal labels do not make denominators, RNA and protein, or "
        "quantification pipelines equivalent.",
        status="provisional",
    ),
    "transformation:general/identity": RegisterEntry(
        "No transformation is applied; upstream preprocessing remains part of the procedure.",
        "The untransformed numerical response consumed by mm30's rank analysis.",
        "Raw values are not thereby unprocessed observations or comparable across procedures.",
        status="provisional",
    ),
    "functional:general/probability-of-superiority": RegisterEntry(
        "The comparison summarizes distributions through relative ordering and half-weighted ties.",
        "The half-tie target of the mm30 midrank statistic under the complete property declaration in this design.",
        "A mean difference, causal effect, independent samples, valid uncertainty or a reported effect estimate "
        "is not established by a z statistic or p value.",
        status="provisional",
    ),
    "identification-class:general/observational": RegisterEntry(
        "The label alone does not encode a causal identification argument.",
        "Statistical-layer targets in the mm30 analysis.",
        "Causal identification is not licensed.",
        status="provisional",
    ),
    "design:general/independent-groups": RegisterEntry(
        "Pairing and repeated measures are not modeled by this design declaration.",
        "Naming the design actually used by the existing unpaired mm30 estimator.",
        "Independence is not certified; the source cohort's pairing remains a limitation to disclose.",
        status="provisional",
    ),
    "selection-mechanism:general/cohort-enrolment": RegisterEntry(
        "Recruitment and inclusion particulars stay in the analysis and procedure records.",
        "Naming the sampling mechanism for the mm30 cohort analysis.",
        "Random sampling, representativeness and absence of selection bias are not established.",
        status="provisional",
    ),
    "procedure-kind:general/assay": RegisterEntry(
        "Instrument and processing particulars stay in the procedure record.",
        "Classifying the mm30 RNA quantification procedure; fills_within_model is false.",
        "The label alone establishes neither calibration, valid scope nor a model-specification role.",
        status="provisional",
    ),
    "procedure-kind:general/estimator": RegisterEntry(
        "Algorithm, parameters, implementation and input assumptions stay in the procedure record.",
        "Classifying the mm30 Mann\u2013Whitney computation; fills_within_model is false.",
        "The kind does not prove correctness, identify a functional without its declaration, or supply "
        "empirical standing.",
        status="provisional",
    ),
}


EXPECTED_ENTRIES["assumption-kind:general/procedure-validity"] = RegisterEntry(
    "The named procedure's unknown validation domain or recorded scope gap is conditionally accepted for this target.",
    "Recording record, co_scope and dimensions under the binding-aptness interface; the first consumer is the "
    "mm30 PHF19 gene-RNA assay with no established validation domain.",
    "The assumption does not validate the procedure, supply empirical standing, establish independence or "
    "certify biological reuse.",
    status="provisional",
)


def test_top_level_package_facade_is_unchanged() -> None:
    assert not hasattr(beliefs, "shipped_assumptions_register")


def test_packaged_general_resources_match_canonical_sources_byte_for_byte() -> None:
    domain_source = REPO_ROOT / "domains/general/DOMAIN.yaml"
    register_source = REPO_ROOT / "domains/general/REGISTER.json"
    packaged_domain = resources.files("beliefs").joinpath("domains/general/DOMAIN.yaml")
    packaged_register = resources.files("beliefs").joinpath("domains/general/REGISTER.json")

    assert domain_source.read_bytes() == packaged_domain.read_bytes()
    assert register_source.read_bytes() == packaged_register.read_bytes()


def test_shipped_general_contract_has_exact_eleven_rows_definitions_and_properties() -> None:
    contract = shipped_domain_contract("general")
    assert shipped_domain_contract("general") is contract
    assert contract.namespace == "general"
    assert contract.version == 2
    assert contract.predecessor == "cd89bb6dbf4d28a13b04ca89ddd35d9a4da83bace06e8265ee60048fd0dec48f"
    assert contract.content_identity == EXPECTED_GENERAL_CONTENT_IDENTITY

    # Empty required sections and zero unshipped candidate families in genesis.
    for empty_attr in (
        "sorts",
        "dimensions",
        "instantiations",
        "bridges",
        "estimands",
        "duration_conventions",
        "aggregation_rules",
        "measurements",
        "aspects",
        "units",
        "constants",
        "conversions",
    ):
        assert dict(getattr(contract, empty_attr)) == {}, empty_attr

    assert set(contract.templates) == {"covaries-with", "changes-under-intervention"}
    assert set(contract.quantity_kinds) == {"relative-abundance"}
    assert set(contract.transformations) == {"identity"}
    assert set(contract.functionals) == {"probability-of-superiority"}
    assert set(contract.identification_classes) == {"observational"}
    assert set(contract.designs) == {"independent-groups"}
    assert set(contract.selection_mechanisms) == {"cohort-enrolment"}
    assert set(contract.procedure_kinds) == {"assay", "estimator"}

    covaries = contract.templates["covaries-with"]
    assert covaries.definition == EXPECTED_DEFINITIONS[("templates", "covaries-with")]
    assert set(covaries.roles) == {"parties"}
    parties = covaries.roles["parties"]
    assert (parties.arity, parties.min, parties.max, parties.coefficients, parties.constraint) == (
        "many",
        2,
        2,
        False,
        (),
    )
    assert covaries.sign_apt is True
    assert covaries.layers == ("statistical",)
    assert covaries.forms == ("polar", "null")
    assert covaries.edge is None
    assert covaries.external is None

    intervention = contract.templates["changes-under-intervention"]
    assert intervention.definition == EXPECTED_DEFINITIONS[("templates", "changes-under-intervention")]
    assert set(intervention.roles) == {"intervention", "response"}
    for role_name in ("intervention", "response"):
        role = intervention.roles[role_name]
        assert (role.arity, role.min, role.max, role.coefficients, role.constraint) == ("one", 1, 1, False, ())
    assert intervention.sign_apt is True
    assert intervention.layers == ("causal",)
    assert intervention.forms == ("polar", "null")
    assert intervention.edge == ("intervention", "response")
    assert intervention.external is None

    rel_abundance = contract.quantity_kinds["relative-abundance"]
    assert rel_abundance.dimension == "dimensionless"

    identity_tx = contract.transformations["identity"]
    assert (identity_tx.kind, identity_tx.domain, identity_tx.fixed, identity_tx.invertible) == (
        "identity",
        "real",
        True,
        True,
    )

    pos = contract.functionals["probability-of-superiority"]
    assert pos.schema_projection() == {
        "form": "contrast",
        "arity": "two",
        "response_transformation": "invariant-strictly-increasing",
        "reversal": "complement",
        "response_reversal": "complement",
        "exchange": "not-applicable",
        "ties": "midrank",
        "output": "dimensionless",
        "domain": "unit-interval",
        "null": "half",
        "increment": "none",
        "uncertainty": "exact",
        "parameters": "not-applicable",
    }

    assert contract.identification_classes["observational"].licenses_layers == ("statistical",)
    assert contract.procedure_kinds["assay"].fills_within_model is False
    assert contract.procedure_kinds["estimator"].fills_within_model is False

    # Verify exact editorial definitions and explicit empty sorts/dimensions in the source document.
    raw = parse_document(
        (REPO_ROOT / "domains/general/DOMAIN.yaml").read_text(encoding="utf-8"),
        source="domains/general/DOMAIN.yaml",
    )
    assert isinstance(raw, dict)
    assert raw["sorts"] == {}
    assert raw["dimensions"] == {}
    for (section, name), expected_def in EXPECTED_DEFINITIONS.items():
        section_map = raw[section]
        assert isinstance(section_map, dict)
        entry_map = section_map[name]
        assert isinstance(entry_map, dict)
        assert entry_map["definition"] == expected_def
        assert "external" not in entry_map


def test_shipped_general_register_matches_inventory_and_stored_round_trip() -> None:
    contract = shipped_domain_contract("general")
    register = profile_module.shipped_assumptions_register("general")
    assert profile_module.shipped_assumptions_register("general") is register
    assert isinstance(register, AssumptionsRegister)
    assert register.describes == f"general:{contract.content_identity}"
    assert register.previous == "assumptions-register:02642579cb0fe2330553586e4c22d56f76a227e14b0d2fe849c6917992c3dbf9"
    assert set(register.entries) == register_entry_keys(contract)
    assert len(register.entries) == 11
    assert dict(register.entries) == EXPECTED_ENTRIES
    assert all(entry.status == "provisional" for entry in register.entries.values())
    assert register_identity(register) == EXPECTED_GENERAL_REGISTER_IDENTITY

    raw_json = json.loads((REPO_ROOT / "domains/general/REGISTER.json").read_text(encoding="utf-8"))
    assert raw_json == register_projection(register)
    assert raw_json["previous"] == register.previous

    node = stored.assumptions_register_node(register)
    assert node.id == EXPECTED_GENERAL_REGISTER_IDENTITY
    assert node.body == ""
    assert register_from_stored(node) == register


def test_general_activation_is_explicit_and_compiles_alone() -> None:
    assert shipped_base().activated_contracts == {}
    compiled = compile_profile(shipped_base_contract(), [shipped_domain_contract("general")])
    assert compiled.activated_contracts == {"general": EXPECTED_GENERAL_CONTENT_IDENTITY}
    assert compiled.compiled_identity == EXPECTED_GENERAL_COMPILED_IDENTITY


@pytest.mark.parametrize(
    "namespace",
    ["", "unknown", "testing", "../general", "general/sub", "general.bad"],
)
def test_unknown_and_traversal_namespaces_refuse_with_resource_path(namespace: str) -> None:
    with pytest.raises(ProfileError, match="domains/.*/REGISTER\\.json"):
        profile_module.shipped_assumptions_register(namespace)
    with pytest.raises(ProfileError, match="ships no domain contract"):
        shipped_domain_contract(namespace)


@pytest.mark.parametrize(
    "cause",
    [
        OSError("cannot read domain resource"),
        UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte"),
        CanonicalTextRefused("invalid canonical domain text"),
        MalformedContract("invalid domain contract"),
        ProfileError("missing domain contract"),
    ],
)
def test_domain_binding_errors_name_the_register_resource(monkeypatch: pytest.MonkeyPatch, cause: Exception) -> None:
    def broken_domain(namespace: str) -> None:
        assert namespace == "general"
        raise cause

    monkeypatch.setattr(profile_module, "_shipped_domain_history", broken_domain)
    profile_module.shipped_assumptions_register.cache_clear()
    try:
        with pytest.raises(ProfileError, match=r"beliefs/domains/general/REGISTER\.json") as caught:
            profile_module.shipped_assumptions_register("general")
        assert caught.value.__cause__ is cause
    finally:
        profile_module.shipped_assumptions_register.cache_clear()


def test_broken_package_register_bindings_refuse_with_profile_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    contract = shipped_domain_contract("general")
    valid_projection = register_projection(profile_module.shipped_assumptions_register("general"))

    pkg_dir = tmp_path / "domains" / "general"
    pkg_dir.mkdir(parents=True)
    shutil.copytree(REPO_ROOT / "domains/general", pkg_dir, dirs_exist_ok=True)

    monkeypatch.setattr(resources, "files", lambda _pkg: tmp_path)

    # Stale describes digest refuses.
    stale = {**valid_projection, "describes": f"general:{'0' * 64}"}
    (pkg_dir / "REGISTER.json").write_text(json.dumps(stale), encoding="utf-8")
    profile_module.shipped_assumptions_register.cache_clear()
    profile_module._shipped_domain_history.cache_clear()
    with pytest.raises(ProfileError, match="domains/general/REGISTER\\.json"):
        profile_module.shipped_assumptions_register("general")

    # Missing coverage row refuses.
    raw_entries = valid_projection["entries"]
    assert isinstance(raw_entries, dict)
    entries_copy: dict[str, object] = dict(raw_entries)
    entries_copy.pop("design:general/independent-groups")
    incomplete = {**valid_projection, "entries": entries_copy}
    (pkg_dir / "REGISTER.json").write_text(json.dumps(incomplete), encoding="utf-8")
    profile_module.shipped_assumptions_register.cache_clear()
    profile_module._shipped_domain_history.cache_clear()
    with pytest.raises(ProfileError, match="domains/general/REGISTER\\.json"):
        profile_module.shipped_assumptions_register("general")

    # Duplicate JSON keys in REGISTER.json refuse even when post-deduplication keys match coverage.
    orig_reg_text = (REPO_ROOT / "domains/general/REGISTER.json").read_text(encoding="utf-8")
    target_snippet = '"design:general/independent-groups": {'
    dup_entry = (
        '"design:general/independent-groups": {\n'
        '      "collapses": "shadow",\n'
        '      "licenses": "shadow",\n'
        '      "not_established": "shadow",\n'
        '      "status": "provisional"\n'
        "    },\n    " + target_snippet
    )
    (pkg_dir / "REGISTER.json").write_text(orig_reg_text.replace(target_snippet, dup_entry, 1), encoding="utf-8")
    profile_module.shipped_assumptions_register.cache_clear()
    profile_module._shipped_domain_history.cache_clear()
    with pytest.raises(ProfileError, match="domains/general/REGISTER\\.json.*duplicate"):
        profile_module.shipped_assumptions_register("general")

    # Restore clean cache at teardown.
    profile_module.shipped_assumptions_register.cache_clear()
    profile_module._shipped_domain_history.cache_clear()
    assert contract.namespace == "general"


def test_general_successor_preserves_exact_genesis_and_adds_only_validity():
    from hashlib import sha256

    from beliefs.contract.shipped import load_domain_history

    current = shipped_domain_contract("general")
    assert current.version == 2
    root = REPO_ROOT / "domains/general"
    history = load_domain_history(
        "general", base=shipped_base_contract(), read_text=lambda path: (root / path).read_text()
    )
    assert len(history) == 2
    old, new = history
    assert old.contract.content_identity == "cd89bb6dbf4d28a13b04ca89ddd35d9a4da83bace06e8265ee60048fd0dec48f"
    assert new.contract == current
    assert new.contract.predecessor == old.contract.content_identity
    assert (
        new.register.previous == "assumptions-register:02642579cb0fe2330553586e4c22d56f76a227e14b0d2fe849c6917992c3dbf9"
    )
    expected_bytes = {
        "DOMAIN.yaml": "d5e7ec6c792d12d9afb08cdc58f7ce15f8512d09f525769e6ee75369841ac6a7",
        "REGISTER.json": "96946aaf8ee11ede7ecddbafd27348600dce9ecac35a236342389c1807d12c24",
    }
    for name, digest in expected_bytes.items():
        original = (root / old.directory / name).read_bytes()
        assert sha256(original).hexdigest() == digest
        assert (REPO_ROOT / "python/src/beliefs/domains/general" / old.directory / name).read_bytes() == original
    old_doc = parse_document((root / old.directory / "DOMAIN.yaml").read_text(), source="<genesis>")
    new_doc = parse_document((root / "DOMAIN.yaml").read_text(), source="<successor>")
    assert isinstance(old_doc, dict) and isinstance(new_doc, dict)
    assert set(new_doc) == set(old_doc) | {"assumption_kinds"}
    for key, value in old_doc.items():
        if key not in {"version", "lineage"}:
            assert new_doc[key] == value
    assert set(new.register.entries) - set(old.register.entries) == {"assumption-kind:general/procedure-validity"}
    for key, entry in old.register.entries.items():
        assert new.register.entries[key] == entry
    assert set(current.assumption_kinds) == {"procedure-validity"}
    assert set(current.assumption_kinds["procedure-validity"].particulars) == {"record", "co_scope", "dimensions"}
    assert new_doc["assumption_kinds"]["procedure-validity"]["definition"] == (
        "An explicit assumption that a named procedure is valid in the target scope when its validation scope "
        "is unknown or does not establish applicability there."
    )
    assert new.register.entries["assumption-kind:general/procedure-validity"] == RegisterEntry(
        "The named procedure's unknown validation domain or recorded scope gap is conditionally accepted for this target.",
        "Recording record, co_scope and dimensions under the binding-aptness interface; the first consumer is the "
        "mm30 PHF19 gene-RNA assay with no established validation domain.",
        "The assumption does not validate the procedure, supply empirical standing, establish independence or "
        "certify biological reuse.",
        status="provisional",
    )
