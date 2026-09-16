"""Cut 32: composite claims, row by row, over registered durable corpora.

One test per guarantee row of the composite-claims design's §8 table U, named
`test_u<n>_<slug>` and composed from the unit tests' own constructions rather
than from a second set — `test_composite.py`'s builders, `test_composite_
boundary.py`'s writer and claim helpers, `test_composite_reading.py`'s argument
bundle, `test_audit.py`'s U7 block and `test_domain_contract.py`'s `TestEdges`
— re-pointed at corpora the composition root registered on the certified
volume.

The shipped base contract is read through `importlib.resources`, i.e. from the
**package** copy, because that is the copy an N2 sabotage mutates; the
repo-root copy is the same bytes and the parity fixture holds them equal.

U10 is the exception by design: the mm30 reproduction's re-run is the driver's,
executed once against the corpus on the certified volume beside the main
checkout, and this row reads what it recorded (`state.json`, the dated addendum
§11 of `2026-09-05-mm30-reproduction.md`). It asserts nothing the record does
not carry, and skips — naming the recorded refusal — if the driver's `compose`
step refused.
"""

from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import replace
from decimal import Decimal
from importlib import resources
from pathlib import Path
from typing import Any

import pytest
import yaml
from authority import FULL
from fixtures_cut4 import raw_write, reopen
from nodes.core.relations import Relation
from profiles import FIXTURE, WITH_BIOLOGY, biology, pins_for
from test_composite_boundary import EX, GENE, IMPORT, SNAPSHOT, A, B, C, _build, _claim, _estimand, _proposition
from test_composite_reading import _inputs
from test_evaluation import EMPIRICAL, _address, _resources

from beliefs import audit as audit_module
from beliefs import stored
from beliefs.audit import NO_EVIDENCE, audit_corpus, check_composite, check_supersedes_kinds
from beliefs.belief import Belief, NoBelief, NotReached
from beliefs.claim import Referent, build_claim
from beliefs.composite import CompositeError, CompositeNode, build_composite, read_composite
from beliefs.contract import parse_base_contract, parse_domain_contract
from beliefs.contract.document import load_document
from beliefs.corpus import superseded_by
from beliefs.errors import (
    FamilyKindUnsupported,
    ImportRefused,
    MalformedContract,
    MalformedRecord,
    SignatureRefused,
    SuccessionViolation,
    SupersedeIdentityUnchanged,
)
from beliefs.estimand import Control, LevelsContrast, Measure, build_estimand
from beliefs.evaluation import evaluate_over
from beliefs.identity import v1
from beliefs.profile import compile_profile, shipped_base_contract
from beliefs.projection import claim_identity, project_claim
from beliefs.resolution import TermOutcome, build_snapshot
from beliefs.root import init_corpus_root, metadata_root_for, open_corpus

REPO_ROOT = Path(__file__).resolve().parents[3]
TS_ROOT = REPO_ROOT / "ts"
TESTS = Path(__file__).resolve().parents[1]
UNCONSULTED = build_snapshot()
ISOLATED = CompositeNode(GENE, "EX:z")


def _shipped_document() -> dict[str, Any]:
    """The package's own base contract, re-read on every call: an N2 sabotage
    mutates a copy of the package, and a module-level read would freeze the
    unsabotaged bytes into this module's import."""
    text = resources.files("beliefs").joinpath("contracts/science/CONTRACT.yaml").read_text(encoding="utf-8")
    document = yaml.safe_load(text)
    assert isinstance(document, dict)
    return document


# --- corpora on the certified volume ----------------------------------------


@pytest.fixture()
def corpora(work_directory):
    """Registered corpus roots on the certified volume, under the profile whose
    domain declares the `edges:` row every composite here is classified by."""
    roots: list[Path] = []

    def make(*, profile=WITH_BIOLOGY, authority=FULL):
        root = Path(tempfile.mkdtemp(prefix="composite-", dir=work_directory))
        roots.append(root)
        init_corpus_root(root, authority=authority)
        writer = open_corpus(root, authority=authority, profile=profile)
        writer.adopt_manifest(profile=pins_for(profile))
        return writer

    yield make
    for root in roots:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(metadata_root_for(root), ignore_errors=True)


def _seeded(writer):
    """`test_composite_boundary.py`'s `writer` fixture, on a durable root:
    a→b, b⊣c, c→a over three gene nodes."""
    _proposition(writer, "ab", _claim("EX:a", "EX:b"))
    _proposition(writer, "bc", _claim("EX:b", "EX:c", polarity="negative"))
    _proposition(writer, "ca", _claim("EX:c", "EX:a"))
    return writer


def _testing_profile():
    """The `testing` fixture contract: its `correlates-with` is a statistical
    operator with no `edges:` row, which is the undeclared-operator row."""
    from fixtures_cut3 import TESTING_PROFILE

    return TESTING_PROFILE


def _widened_profile():
    """The biology fixture with `affects` admitting the statistical layer too.

    The `edges:` row is unchanged, so `affects` still forms an edge — which is
    what makes `classify`'s layer refusal reachable at all. No shipped fixture
    operator both declares an edge and admits a second layer (`correlates-with`
    declares no edge, and `_parse_edge` refuses one for it), so the layer row
    needs a contract of its own rather than a second operator.
    """
    document = load_document(FIXTURE, source=str(FIXTURE))
    assert isinstance(document, dict)
    document["description"] = "fixture, layers widened"
    document["operators"]["affects"]["layers"] = ["causal", "statistical"]
    base = shipped_base_contract()
    return compile_profile(base, [parse_domain_contract(document, source="<widened>", base=base, predecessor=None)])


def _estimand_with(claim, identification: str):
    """`test_composite_boundary._estimand`, with the identification term named:
    U8's admitted-set arm needs two assessments whose terms differ."""
    estimand, _ = build_estimand(
        WITH_BIOLOGY,
        claim,
        snapshot=UNCONSULTED,
        contrast=LevelsContrast(slot=0, baseline=Referent("biology/level", "EX:lo"), comparison=Referent("biology/level", "EX:hi")),
        measure=Measure(quantity=Referent("biology/measure", "EX:expr"), scale="additive"),
        reference=Decimal(0),
        control=Control(identification=Referent("biology/identification", identification), conditioning=()),
    )
    return estimand


def _seed_assessment(writer, proposition_ref: str, *, slug: str, letter: str, outcome: str, estimand) -> str:
    """`test_evaluation.seed_assessed_proposition` with the observed dataset
    named, so two assessments of one proposition can rest on different bytes."""
    address = _address(letter)
    if not writer.read_view.holds(address):
        writer.add(stored.dataset_node(title=f"d-{letter}", resources=_resources(letter), empirical_observation=EMPIRICAL))
    run = writer.add(stored.run_node(f"run-{slug}", title=slug, spec=f"spec-{slug}", observes=[address]))
    assessment = writer.add(
        stored.assessment_node(
            slug, title=slug, spec=f"spec-{slug}", run=run.id, proposition=proposition_ref,
            outcome=outcome, interpretation_rule="rule-1", estimand=estimand, applicability={},
        )
    )
    value = stored.assessment_value(writer.read_view.get(assessment.id), profile=writer.profile)
    writer.add(
        stored.verification_node(
            f"v-{slug}", title=slug, assessment=value.identity(), assessment_ref=assessment.id,
            scope="clean-environment", verdict="passed",
        )
    )
    return address


def _typed_assessment(writer, slug: str, target: str):
    """Otherwise valid evidence: an attested, held-shaped dataset, an observing
    run, and an assessment typed under the fixture profile. Only the `assesses`
    target is in question — the eligibility predicate admits it."""
    address = _address("a")
    if not writer.read_view.holds(address):
        writer.add(stored.dataset_node(title="d-a", resources=_resources("a"), empirical_observation=EMPIRICAL))
    run = writer.add(stored.run_node(f"run-{slug}", title=slug, spec=f"spec-{slug}", observes=[address]))
    return stored.assessment_node(
        slug, title=slug, spec=f"spec-{slug}", run=run.id, proposition=target, outcome="supported",
        interpretation_rule="rule-1", estimand=_estimand(_claim("EX:a", "EX:b")), applicability={},
    )


def _vitest(module: str) -> None:
    completed = subprocess.run(
        ["npx", "vitest", "run", module],
        cwd=TS_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


# --- U1 ---------------------------------------------------------------------


def test_u1_grammar_kind_and_relations(corpora):
    """U1: the grammar, the kind and the two relations, in both implementations;
    an unknown shape, a missing grammar and a `composes` signature outside
    `composite → proposition` refuse at parse."""
    base = shipped_base_contract()
    assert base.composite_grammar.version == 1 and base.composite_grammar.shapes == ("dag",)
    kind = base.kinds["composite"]
    assert kind.role == "world" and kind.domain == "science.composite.v1"
    assert kind.facets["composite"].required and kind.facets["composite"].covered
    assert not kind.facets["display"].covered
    assert len([k for k in base.kinds.values() if k.role == "world"]) == 14
    composes = base.relations["composes"]
    assert (composes.group, composes.sources, composes.targets, composes.same_kind) == ("world", ("composite",), ("proposition",), False)
    supersedes = base.relations["supersedes"]
    assert set(supersedes.sources) == set(supersedes.targets) == {"proposition", "composite"} and supersedes.same_kind
    # `assesses` keeps its one target kind — the boundary invariant U4 rests on.
    assert base.relations["assesses"].targets == ("proposition",)
    writer = corpora()
    assert writer.profile.composite_grammar == base.composite_grammar

    document = _shipped_document()
    missing = copy.deepcopy(document)
    del missing["composite_grammar"]
    with pytest.raises(MalformedContract, match="composite_grammar"):
        parse_base_contract(missing, source="<missing>")
    unknown = copy.deepcopy(document)
    unknown["composite_grammar"]["shapes"] = ["dag", "pag"]
    with pytest.raises(MalformedContract, match="pag"):
        parse_base_contract(unknown, source="<shape>")
    unequal = copy.deepcopy(document)
    unequal["relations"]["composes"]["same_kind"] = True
    with pytest.raises(MalformedContract, match="same_kind"):
        parse_base_contract(unequal, source="<composes>")
    # The signature rule itself: every pair below names declared kinds, so
    # kind-existence admits each one and only `composes`' own signature refuses.
    for sources, targets in ((["composite", "proposition"], ["proposition"]), (["composite"], ["proposition", "composite"]), (["proposition"], ["composite"])):
        signature = copy.deepcopy(document)
        signature["relations"]["composes"]["sources"] = sources
        signature["relations"]["composes"]["targets"] = targets
        with pytest.raises(MalformedContract, match="one signature and no other"):
            parse_base_contract(signature, source="<composes>")
    # And the kind-existence refusal beside it, which is a different rule.
    unknown_kind = copy.deepcopy(document)
    unknown_kind["relations"]["composes"]["targets"] = ["structure"]
    with pytest.raises(MalformedContract, match="not a kind this contract declares"):
        parse_base_contract(unknown_kind, source="<composes>")

    # The TypeScript half runs the same three signature mutations against the
    # same shipped bytes and matches the same message.
    _vitest("tests/declarations.test.ts")


# --- U2 ---------------------------------------------------------------------


def test_u2_edges_declared_and_never_redefined(corpora, base_contract, testing_document):
    """U2: `test_domain_contract.TestEdges`, plus the compiled keying and the
    durable corpus's own pinned profile."""

    def parse(document, predecessor=None):
        return parse_domain_contract(document, source="<t>", base=base_contract, predecessor=predecessor)

    genesis = parse(copy.deepcopy(testing_document))
    assert set(genesis.edges) == {"affects"}
    assert (genesis.edges["affects"].cause, genesis.edges["affects"].effect) == (0, 1)
    assert ("edge:affects", genesis.edges["affects"]) in genesis._declarations()
    assert genesis.claim_vocabulary()["edge:affects"] == {"cause": 0, "effect": 1}

    profile = compile_profile(base_contract, [genesis])
    edge = profile.edges["testing/affects"]
    assert (edge.operator, edge.cause, edge.effect, edge.retired, edge.contract) == ("testing/affects", 0, 1, False, "testing")
    assert "testing/correlates-with" not in profile.edges
    assert "affects" not in profile.edges  # keyed by namespaced operator, never the bare name
    writer = corpora()
    assert writer.profile.edges["biology/affects"].cause == 0

    without = copy.deepcopy(testing_document)
    del without["edges"]
    assert parse(without).edges == {}

    undeclared = copy.deepcopy(testing_document)
    undeclared["edges"]["regulates"] = {"cause": 0, "effect": 1}
    with pytest.raises(MalformedContract, match="regulates"):
        parse(undeclared)
    foreign = copy.deepcopy(testing_document)
    foreign["edges"]["biology/affects-molecular-entity-molecular-entity"] = {"cause": 0, "effect": 1}
    with pytest.raises(MalformedContract, match="own"):
        parse(foreign)
    non_causal = copy.deepcopy(testing_document)
    non_causal["edges"]["correlates-with"] = {"cause": 0, "effect": 1}
    with pytest.raises(MalformedContract, match="causal"):
        parse(non_causal)
    for body in ({"cause": 0, "effect": 0}, {"cause": 0, "effect": 2}, {"cause": -1, "effect": 1}, {"cause": True, "effect": 1}, {"cause": 0}, {"cause": 0, "effect": 1, "sign": "+"}):
        malformed = copy.deepcopy(testing_document)
        malformed["edges"]["affects"] = body
        with pytest.raises(MalformedContract):
            parse(malformed)

    redefining = copy.deepcopy(testing_document)
    redefining["lineage"] = {"successor": genesis.content_identity}
    redefining["edges"]["affects"] = {"cause": 1, "effect": 0}
    with pytest.raises(SuccessionViolation, match="edge:affects"):
        parse(redefining, predecessor=genesis)
    dropping = copy.deepcopy(testing_document)
    dropping["lineage"] = {"successor": genesis.content_identity}
    del dropping["edges"]
    with pytest.raises(SuccessionViolation, match="edge:affects"):
        parse(dropping, predecessor=genesis)
    retiring = copy.deepcopy(testing_document)
    retiring["lineage"] = {"successor": genesis.content_identity}
    retiring["edges"]["affects"]["retired"] = True
    assert "edge:affects" in parse(retiring, predecessor=genesis).retired_identifiers()


# --- U3 ---------------------------------------------------------------------


def _hand_built(writer, members, refs, *, nodes=(A, B, C), slug="x"):
    """A stored composite whose facet says what the constructor would refuse:
    built from an admissible one, then re-pointed and re-stamped."""
    node = stored.composite_node(_build(writer, ["proposition:ab"], nodes=nodes, slug=slug), title=slug)
    node.facets[stored.COMPOSITE_FACET]["members"] = sorted(members)
    ordered = dict(zip(members, refs, strict=True))
    node.relations = [Relation(source=node.id, predicate=stored.COMPOSES, target=ordered[m]) for m in sorted(members)]
    stored.stamp_semantic_identity(node)
    return node


def test_u3_form_classification_and_vocabulary_arms(corpora):
    """U3: every form and classification row refused at construction and at
    `add`; the vocabulary halves — the boundary checks form only, the
    constructor and the reading resolve nodes under their caller's snapshot."""
    writer = _seeded(corpora())
    view = writer.read_view

    def build(**kwargs):
        arguments: dict[str, Any] = {"shape": "dag", "snapshot": SNAPSHOT, "slug": "x"}
        arguments.update(kwargs)
        return build_composite(WITH_BIOLOGY, writer.read_view, **arguments)

    # --- form, at construction ---------------------------------------------
    for nodes, members, code in (
        ([], [], "composite-nodes-empty"),
        ([A, A], [], "composite-duplicate"),
        ([A, B], ["proposition:ab", "proposition:ab"], "composite-duplicate"),
        ([A], ["proposition:ab"], "composite-member-outside-nodes"),
        ([A, B], ["proposition:missing"], "composite-member-unresolvable"),
        ([A, B, C], ["proposition:ab", "proposition:bc", "proposition:ca"], "composite-cyclic"),
    ):
        with pytest.raises(CompositeError) as caught:
            build(nodes=nodes, members=members)
        assert caught.value.code == code, code
    with pytest.raises(CompositeError) as caught:
        build(shape="pag", nodes=[A], members=[])
    assert caught.value.code == "composite-shape"
    dataset = writer.add(stored.dataset_node(title="d", resources=[{"name": "m", "digest": "sha256:" + "1" * 64}]))
    with pytest.raises(CompositeError) as caught:
        build(nodes=[A, B], members=[dataset.id])
    assert caught.value.code == "composite-member-kind"

    # --- admitted: nodes and no members, and a negative member as a signed edge
    empty, receipt = build(nodes=[A, B], members=[])
    assert empty.edges == () and empty.facet.members == () and set(receipt.outcomes) == {"node:0", "node:1"}
    chain = _build(writer, ["proposition:ab", "proposition:bc"])
    assert {(e.cause, e.effect, e.sign) for e in chain.edges} == {(A, B, "positive"), (B, C, "negative")}
    minted = writer.add(stored.composite_node(chain, title="a→b⊣c"))
    assert {r.target for r in view.get(minted.id).relations} == {"proposition:ab", "proposition:bc"}

    # --- the same rows at `add`, re-derived from the stored record ----------
    cycle = _hand_built(
        writer,
        [claim_identity(_claim("EX:a", "EX:b")), claim_identity(_claim("EX:b", "EX:c", "negative")), claim_identity(_claim("EX:c", "EX:a"))],
        ["proposition:ab", "proposition:bc", "proposition:ca"],
        slug="cyc",
    )
    with pytest.raises(CompositeError) as caught:
        writer.add(cycle)
    assert caught.value.code == "composite-cyclic"
    outside = stored.composite_node(_build(writer, ["proposition:ab"], slug="out"), title="out")
    outside.facets[stored.COMPOSITE_FACET]["nodes"] = [{"sort": GENE, "term": "EX:c"}]
    stored.stamp_semantic_identity(outside)
    with pytest.raises(CompositeError) as caught:
        writer.add(outside)
    assert caught.value.code == "composite-member-outside-nodes"
    shape = stored.composite_node(_build(writer, ["proposition:ab"], slug="shp"), title="shp")
    shape.facets[stored.COMPOSITE_FACET]["shape"] = "pag"
    stored.stamp_semantic_identity(shape)
    with pytest.raises(CompositeError) as caught:
        writer.add(shape)
    assert caught.value.code == "composite-shape"

    # The duplicate node, the duplicate member and the empty node set at `add`.
    # §4.2 step 1 is the facet decode, and it is the step that owns these three:
    # the boundary reads the stored facet before it re-derives anything, so a
    # facet that is not a facet refuses under the decode's own code and no
    # `composite-*` classification is reached. The code is therefore
    # `MalformedRecord`, not the constructor's — measured, and recorded in the
    # cut document's §8.4.
    for mutate, defect in (
        (lambda f: f.__setitem__("nodes", [{"sort": GENE, "term": "EX:a"}, {"sort": GENE, "term": "EX:a"}]), "distinct"),
        (lambda f: f.__setitem__("members", sorted(f["members"]) * 2), "sorted and distinct"),
        (lambda f: f.__setitem__("nodes", []), "at least one node"),
    ):
        record = stored.composite_node(_build(writer, ["proposition:ab"], slug="frm"), title="frm")
        mutate(record.facets[stored.COMPOSITE_FACET])
        stored.stamp_semantic_identity(record)
        with pytest.raises(MalformedRecord, match=defect):
            writer.add(record)

    # --- an undeclared operator: `correlates-with` declares no `edges:` row --
    testing = corpora(profile=_testing_profile())
    entity, outcome = CompositeNode("testing/entity", "EX:a"), CompositeNode("testing/outcome", "EX:y")
    stat = build_claim(
        testing.profile, operator="testing/correlates-with",
        args=(Referent("testing/entity", "EX:a"), Referent("testing/outcome", "EX:y")),
        layer="statistical", polarity="positive",
    )
    declared = build_claim(
        testing.profile, operator="testing/affects",
        args=(Referent("testing/entity", "EX:a"), Referent("testing/outcome", "EX:y")),
        layer="causal", polarity="positive",
    )
    testing.add(stored.proposition_node("stat", title="stat", claim=project_claim(stat)))
    testing.add(stored.proposition_node("aff", title="aff", claim=project_claim(declared)))
    with pytest.raises(CompositeError) as caught:
        build_composite(testing.profile, testing.read_view, shape="dag", nodes=[entity, outcome], members=["proposition:stat"], snapshot=UNCONSULTED, slug="x")
    assert caught.value.code == "composite-member-undeclared"
    # And at `add`: built over the operator that does declare an edge, then
    # re-pointed at the one that does not, so the boundary's own `classify` is
    # what refuses rather than the constructor's.
    admissible, _ = build_composite(testing.profile, testing.read_view, shape="dag", nodes=[entity, outcome], members=["proposition:aff"], snapshot=UNCONSULTED, slug="u")
    undeclared = stored.composite_node(admissible, title="u")
    undeclared.facets[stored.COMPOSITE_FACET]["members"] = [claim_identity(stat)]
    undeclared.relations = [Relation(source=undeclared.id, predicate=stored.COMPOSES, target="proposition:stat")]
    stored.stamp_semantic_identity(undeclared)
    with pytest.raises(CompositeError) as caught:
        testing.add(undeclared)
    assert caught.value.code == "composite-member-undeclared"

    # --- a declared edge's operator asserted at another layer ---------------
    widened = corpora(profile=_widened_profile())
    at_layer = build_claim(
        widened.profile, operator="biology/affects",
        args=(Referent(GENE, "EX:a"), Referent(GENE, "EX:b")), layer="statistical", polarity="positive",
    )
    _proposition(widened, "causal", _claim("EX:a", "EX:b"))
    widened.add(stored.proposition_node("stat", title="stat", claim=project_claim(at_layer)))
    with pytest.raises(CompositeError) as caught:
        build_composite(widened.profile, widened.read_view, shape="dag", nodes=[A, B], members=["proposition:stat"], snapshot=UNCONSULTED, slug="x")
    assert caught.value.code == "composite-member-layer"
    value, _ = build_composite(widened.profile, widened.read_view, shape="dag", nodes=[A, B], members=["proposition:causal"], snapshot=UNCONSULTED, slug="l")
    stored_layer = stored.composite_node(value, title="l")
    stored_layer.facets[stored.COMPOSITE_FACET]["members"] = [claim_identity(at_layer)]
    stored_layer.relations = [Relation(source=stored_layer.id, predicate=stored.COMPOSES, target="proposition:stat")]
    stored.stamp_semantic_identity(stored_layer)
    with pytest.raises(CompositeError) as caught:
        widened.add(stored_layer)
    assert caught.value.code == "composite-member-layer"

    # --- vocabulary: construction and reading refuse, `add` admits ----------
    excluding = build_snapshot(readable={EX: ["EX:a", "EX:b", "EX:c"]})
    with pytest.raises(CompositeError) as caught:
        build_composite(WITH_BIOLOGY, view, shape="dag", nodes=[A, B, ISOLATED], members=["proposition:ab"], snapshot=excluding, slug="iso")
    assert caught.value.code == "composite-node-not-member" and "EX:z" in str(caught.value)
    isolated, receipt = build_composite(WITH_BIOLOGY, view, shape="dag", nodes=[A, B, ISOLATED], members=["proposition:ab"], snapshot=UNCONSULTED, slug="iso")
    assert receipt.outcomes["node:2"] == TermOutcome.NOT_CONSULTED and receipt.snapshot_identity == UNCONSULTED.identity
    held = writer.add(stored.composite_node(isolated, title="iso"))  # the boundary holds no snapshot (§4.2 step 1)
    assert writer.read_view.get(held.id).kind == "composite"
    address = _seed_assessment(writer, "proposition:ab", slug="a-ab", letter="a", outcome="supported", estimand=_estimand(_claim("EX:a", "EX:b")))
    with pytest.raises(CompositeError) as caught:
        read_composite(writer.read_view, held.id, **{**_inputs(writer, address), "resolution": excluding})
    assert caught.value.code == "composite-node-not-member"
    reading = read_composite(writer.read_view, held.id, **{**_inputs(writer, address), "resolution": UNCONSULTED})
    assert reading.node_outcomes["node:2"] == TermOutcome.NOT_CONSULTED


# --- U4 ---------------------------------------------------------------------


def test_u4_belief_inert(corpora):
    """U4: minting, superseding and deleting a composite naming a proposition
    moves no byte of that proposition's belief input digest, and `assesses`
    cannot target a composite — at `add` and at `import_bundle` alike."""
    writer = _seeded(corpora())
    address = _seed_assessment(writer, "proposition:ab", slug="a-ab", letter="a", outcome="supported", estimand=_estimand(_claim("EX:a", "EX:b")))

    def digest() -> str:
        answer = evaluate_over(writer.read_view, "proposition:ab", **_inputs(writer, address))
        assert isinstance(answer, Belief), answer
        return answer.belief_input_digest

    before = digest()
    first = writer.add(stored.composite_node(_build(writer, ["proposition:ab"], slug="v1"), title="v1"))
    assert digest() == before
    second = writer.supersede(stored.composite_node(_build(writer, ["proposition:ab", "proposition:bc"], slug="v2"), title="v2"), of=first.id)
    assert digest() == before
    writer.delete(second.id)
    assert digest() == before

    # The declaration itself: one target kind, in the contract this corpus pins.
    assert shipped_base_contract().relations["assesses"].targets == ("proposition",)

    # Otherwise eligible evidence, refused on the target's kind alone.
    assessment = _typed_assessment(writer, "a-x", first.id)
    assert stored.assessment_value(assessment, profile=writer.profile).proposition == first.id
    with pytest.raises(SignatureRefused, match="assesses-target-kind"):
        writer.add(assessment)
    other = corpora()
    members = tuple(n for n in writer.read_view.iter_stored() if n.kind in {"proposition", "composite", "dataset", "run"}) + (assessment,)
    with pytest.raises(ImportRefused, match="assesses-target-kind"):
        other.import_bundle(members, **IMPORT)

    # And a target that resolves nowhere: a `composite:future` may not establish
    # the edge by arriving second.
    unresolvable = _typed_assessment(writer, "a-y", "composite:future")
    with pytest.raises(SignatureRefused, match="assesses-target-unresolvable"):
        writer.add(unresolvable)
    third = corpora()
    bundle = tuple(n for n in writer.read_view.iter_stored() if n.kind in {"proposition", "dataset", "run"}) + (unresolvable,)
    with pytest.raises(ImportRefused, match="assesses-target-unresolvable"):
        third.import_bundle(bundle, **IMPORT)


# --- U5 ---------------------------------------------------------------------


def test_u5_identity(corpora):
    """U5: content identity over the covered facet — authoring order does not
    move it, a node with no member does, display prose does not."""
    writer = _seeded(corpora())
    view = writer.read_view
    one, _ = build_composite(WITH_BIOLOGY, view, shape="dag", nodes=[C, B, A], members=["proposition:bc", "proposition:ab"], snapshot=SNAPSHOT, slug="one")
    two, _ = build_composite(WITH_BIOLOGY, view, shape="dag", nodes=[A, B, C], members=["proposition:ab", "proposition:bc"], snapshot=SNAPSHOT, slug="two")
    three, _ = build_composite(WITH_BIOLOGY, view, shape="dag", nodes=[A, B, C, ISOLATED], members=["proposition:ab", "proposition:bc"], snapshot=UNCONSULTED, slug="three")
    assert one.identity == two.identity != three.identity
    plain = stored.composite_node(two, title="a plain title")
    prose = stored.composite_node(two, title="an altogether different display title")
    assert stored.stored_semantic_hash(plain) == stored.stored_semantic_hash(prose) == two.identity


# --- U6 ---------------------------------------------------------------------


def test_u6_boundary_resolution_and_identity(corpora):
    """U6: each `composes` target resolves to a proposition whose semantic
    identity equals the facet's member at that position — through `add` and
    through `import_bundle`."""
    writer = _seeded(corpora())

    def stored_composite(mutate, slug):
        node = stored.composite_node(_build(writer, ["proposition:ab"], slug=slug), title=slug)
        mutate(node)
        stored.stamp_semantic_identity(node)
        return node

    dataset = writer.add(stored.dataset_node(title="d", resources=[{"name": "m", "digest": "sha256:" + "1" * 64}]))
    rows = (
        ("swapped", lambda n: n.relations.__setitem__(0, Relation(source=n.id, predicate=stored.COMPOSES, target="proposition:bc")), "composite-member-mismatch"),
        ("dataset", lambda n: n.relations.__setitem__(0, Relation(source=n.id, predicate=stored.COMPOSES, target=dataset.id)), "composite-member-kind"),
        ("missing", lambda n: n.relations.__setitem__(0, Relation(source=n.id, predicate=stored.COMPOSES, target="proposition:missing")), "composite-member-unresolvable"),
        ("popped", lambda n: n.relations.pop(), "composite-relations-mismatch"),
        ("extra", lambda n: n.relations.append(Relation(source=n.id, predicate=stored.COMPOSES, target="proposition:bc")), "composite-relations-mismatch"),
    )
    for slug, mutate, code in rows:
        node = stored_composite(mutate, slug)
        with pytest.raises(CompositeError) as caught:
            writer.add(node)
        assert caught.value.code == code, slug
        other = corpora()
        members = tuple(n for n in writer.read_view.iter_stored() if n.kind in {"proposition", "dataset"}) + (node,)
        with pytest.raises(ImportRefused, match=code) as refused:
            other.import_bundle(members, **IMPORT)
        assert refused.value.member == node.id


# --- U7 ---------------------------------------------------------------------


def test_u7_audit_codes(corpora):
    """U7: the four composite codes and `supersedes-cross-kind`, as
    contradictions rather than malformedness, with the record read again."""
    writer = _seeded(corpora())
    minted = writer.add(stored.composite_node(_build(writer, ["proposition:ab", "proposition:bc"]), title="g"))

    def codes():
        return sorted((f.code, f.ref) for f in audit_corpus(reopen(writer.root), evidence=NO_EVIDENCE, profile=writer.profile))

    assert codes() == []

    cross = writer.read_view.get("proposition:ab")
    cross.relations.append(Relation(source=cross.id, predicate=stored.SUPERSEDES, target=minted.id))
    raw_write(writer.root, cross)
    assert ("supersedes-cross-kind", "proposition:ab") in codes()
    assert check_supersedes_kinds(reopen(writer.root), reopen(writer.root).get("proposition:ab"), profile=writer.profile) is not None

    mismatched = writer.read_view.get("proposition:bc")
    mismatched.facets[stored.PROPOSITION_FACET]["polarity"] = "positive"
    stored.stamp_semantic_identity(mismatched)
    raw_write(writer.root, mismatched)
    found = codes()
    assert ("composite-member-mismatch", minted.id) in found
    assert not any(code in audit_module.MALFORMEDNESS_CODES for code, _ in found)

    second = _seeded(corpora())
    other = second.add(stored.composite_node(_build(second, ["proposition:ab", "proposition:bc"]), title="g"))
    relations = second.read_view.get(other.id)
    relations.relations.pop()
    raw_write(second.root, relations)
    assert ("composite-relations-mismatch", other.id) in sorted(
        (f.code, f.ref) for f in audit_corpus(reopen(second.root), evidence=NO_EVIDENCE, profile=second.profile)
    )

    third = _seeded(corpora())
    deleted = third.add(stored.composite_node(_build(third, ["proposition:ab", "proposition:bc"]), title="g"))
    third.delete("proposition:bc")
    findings = sorted((f.code, f.ref) for f in audit_corpus(reopen(third.root), evidence=NO_EVIDENCE, profile=third.profile))
    assert ("composite-member-unresolvable", deleted.id) in findings
    assert not any(code in audit_module.MALFORMEDNESS_CODES for code, _ in findings)

    # "No longer classifies", as U7's verification column names it: retire the
    # `edges:` row by successor and audit. `check_composite` is called directly
    # because the corpus pins the predecessor contract, and `audit_corpus` under
    # the successor would report `profile-mismatch` and stop before the arm this
    # row is about — the classification, not the pins.
    fourth = _seeded(corpora())
    retired_composite = fourth.add(stored.composite_node(_build(fourth, ["proposition:ab", "proposition:bc"]), title="g"))
    document = load_document(FIXTURE, source=str(FIXTURE))
    assert isinstance(document, dict)
    successor = copy.deepcopy(document)
    successor["description"] = "fixture"
    successor["lineage"] = {"successor": biology("fixture").content_identity}
    successor["edges"]["affects"]["retired"] = True
    base = shipped_base_contract()
    retired = compile_profile(base, [parse_domain_contract(successor, source="<retired>", base=base, predecessor=biology("fixture"))])
    outcome = check_composite(reopen(fourth.root), reopen(fourth.root).get(retired_composite.id), profile=retired)
    assert outcome.checked and outcome.contradiction is not None
    assert outcome.contradiction.code == "composite-malformed"
    assert "composite-member-retired" in outcome.contradiction.detail
    # Read again, under the profile the corpus pins: the record is a record, and
    # the contradiction is the successor's reading of it, not damage to it.
    assert check_composite(reopen(fourth.root), reopen(fourth.root).get(retired_composite.id), profile=fourth.profile).contradiction is None

    # The same code from the other direction — a raw edit that drops a node the
    # members name — so `composite-malformed` is read through `audit_corpus`'s
    # own dispatch too, and not only through `check_composite`.
    fifth = _seeded(corpora())
    stale = fifth.add(stored.composite_node(_build(fifth, ["proposition:ab", "proposition:bc"]), title="g"))
    node = fifth.read_view.get(stale.id)
    node.facets[stored.COMPOSITE_FACET]["nodes"] = [{"sort": GENE, "term": "EX:a"}, {"sort": GENE, "term": "EX:b"}]
    stored.stamp_semantic_identity(node)
    raw_write(fifth.root, node)
    reported = {f.code: f for f in audit_corpus(reopen(fifth.root), evidence=NO_EVIDENCE, profile=fifth.profile)}
    assert "composite-malformed" in reported and "composite-member-outside-nodes" in reported["composite-malformed"].detail
    # Read again, by the dispatch the audit shares with `_recompute`.
    outcome = check_composite(reopen(fifth.root), reopen(fifth.root).get(stale.id), profile=fifth.profile)
    assert outcome.checked and outcome.contradiction is not None


# --- U8 ---------------------------------------------------------------------

_READING_SCRIPT = """
import sys
sys.path.insert(0, {tests!r})
from profiles import WITH_BIOLOGY
from test_composite_reading import _inputs
from beliefs.composite import read_composite
from beliefs.corpus import ReadView
from beliefs.identity import v1
from pathlib import Path


class _Writer:
    def __init__(self, root):
        self.root = Path(root)
        self.profile = WITH_BIOLOGY

    @property
    def read_view(self):
        return ReadView.opened_at(self.root)


writer = _Writer(sys.argv[1])
reading = read_composite(writer.read_view, sys.argv[2], **_inputs(writer, sys.argv[3]))
sys.stdout.buffer.write(v1.encode(reading.projection()))
"""


def _read_in_a_fresh_process(root: Path, ref: str, address: str) -> bytes:
    environment = {**os.environ, "PYTHONPATH": os.pathsep.join([str(TESTS), os.environ.get("PYTHONPATH", "")])}
    completed = subprocess.run(
        [sys.executable, "-c", _READING_SCRIPT.format(tests=str(TESTS)), str(root), ref, address],
        cwd=REPO_ROOT / "python",
        check=False,
        capture_output=True,
        env=environment,
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    return completed.stdout


def test_u8_reading_equals_the_wrapper(corpora):
    """U8: every row's belief **equals** `evaluate_over`'s answer for that
    member under the same arguments, the identification column is drawn from
    the same traced admission, and two processes agree byte for byte."""
    writer = _seeded(corpora())
    ac2 = writer.supersede(stored.proposition_node("ca2", title="ca2", claim=project_claim(_claim("EX:c", "EX:a", "negative"))), of="proposition:ca")
    address = _seed_assessment(writer, "proposition:ab", slug="a-ab", letter="a", outcome="supported", estimand=_estimand(_claim("EX:a", "EX:b")))
    minted = writer.add(stored.composite_node(_build(writer, ["proposition:ab", "proposition:bc"]), title="g"))

    reading = read_composite(writer.read_view, minted.id, **_inputs(writer, address))
    assert reading.identity == stored.stored_semantic_hash(writer.read_view.get(minted.id))
    by_ref = {row.ref: row for row in reading.rows}
    for ref, row in by_ref.items():
        assert row.belief == evaluate_over(writer.read_view, ref, **_inputs(writer, address)), ref
    assert isinstance(by_ref["proposition:ab"].belief, Belief)
    assert by_ref["proposition:ab"].identification == ("EX:observational",)
    assert by_ref["proposition:bc"].belief == NoBelief("no-eligible-assessment")
    assert by_ref["proposition:bc"].identification == ()
    assert {row.role.sign for row in reading.rows} == {"positive", "negative"}
    assert reading.standing.state == "active"

    # A superseded member reads its successors and a belief.
    superseded = read_composite(
        writer.read_view,
        writer.add(stored.composite_node(_build(writer, ["proposition:ab", "proposition:ca"], slug="s"), title="s")).id,
        **_inputs(writer, address),
    )
    row = next(r for r in superseded.rows if r.ref == "proposition:ca")
    assert row.resolution.state == "superseded" and row.resolution.successors == (ac2.id,)
    # The row's belief is the evaluator's own answer for that member, like every
    # other row: succession moves the resolution column, never the belief column.
    assert row.belief == evaluate_over(writer.read_view, "proposition:ca", **_inputs(writer, address))

    # --- the withholding arms ----------------------------------------------
    unheld = read_composite(writer.read_view, minted.id, **_inputs(writer, address, hold=False))
    unheld_row = next(r for r in unheld.rows if r.ref == "proposition:ab")
    assert unheld_row.belief == evaluate_over(writer.read_view, "proposition:ab", **_inputs(writer, address, hold=False))
    assert isinstance(unheld_row.belief, NoBelief) and unheld_row.identification == ()
    no_policy = read_composite(writer.read_view, minted.id, **_inputs(writer, address, with_policy=False))
    no_policy_row = next(r for r in no_policy.rows if r.ref == "proposition:ab")
    assert no_policy_row.belief == NoBelief("unavailable-policy-unheld")
    assert no_policy_row.identification == NotReached()  # never `{}`

    # --- a member whose inputs sit in an absent corpus ----------------------
    absent_arguments = _inputs(writer, address)
    absent_arguments["context"] = replace(
        absent_arguments["context"],
        snapshot=replace(absent_arguments["context"].snapshot, not_present={address: "corpus-elsewhere"}),
    )
    absent = read_composite(writer.read_view, minted.id, **absent_arguments)
    absent_row = next(r for r in absent.rows if r.ref == "proposition:ab")
    assert absent_row.belief == evaluate_over(writer.read_view, "proposition:ab", **absent_arguments)
    assert isinstance(absent_row.belief, NoBelief) and absent_row.belief.reason == "unavailable-corpus-absent"

    # --- the admitted set is not the digest's keyed set ---------------------
    _seed_assessment(
        writer, "proposition:ab", slug="a-other", letter="b", outcome="supported",
        estimand=_estimand_with(_claim("EX:a", "EX:b"), "EX:experimental"),
    )
    only_a = read_composite(writer.read_view, minted.id, **_inputs(writer, address))
    only_a_row = next(r for r in only_a.rows if r.ref == "proposition:ab")
    assert only_a_row.belief == evaluate_over(writer.read_view, "proposition:ab", **_inputs(writer, address))
    assert only_a_row.identification == ("EX:observational",)  # the `b`-held assessment is keyed, not admitted

    # --- two admitted `inconclusive` assessments keep their terms -----------
    inconclusive = _seeded(corpora())
    address_i = _seed_assessment(inconclusive, "proposition:bc", slug="i-1", letter="a", outcome="inconclusive", estimand=_estimand(_claim("EX:b", "EX:c", polarity="negative")))
    _seed_assessment(inconclusive, "proposition:bc", slug="i-2", letter="a", outcome="inconclusive", estimand=_estimand_with(_claim("EX:b", "EX:c", polarity="negative"), "EX:experimental"))
    two_way = inconclusive.add(stored.composite_node(_build(inconclusive, ["proposition:bc"]), title="i"))
    row = read_composite(inconclusive.read_view, two_way.id, **_inputs(inconclusive, address_i)).rows[0]
    assert row.belief == NoBelief("no-directional-outcome")
    assert row.identification == ("EX:experimental", "EX:observational")

    # --- one admission per member, and no `admit` of the reading's own ------
    _assert_one_admission(writer, minted.id, address)

    # --- a memberless composite, and an unresolvable member ----------------
    memberless, _ = build_composite(WITH_BIOLOGY, writer.read_view, shape="dag", nodes=[A, ISOLATED], members=[], snapshot=UNCONSULTED, slug="m")
    empty = writer.add(stored.composite_node(memberless, title="m"))
    empty_reading = read_composite(writer.read_view, empty.id, **{**_inputs(writer, address), "resolution": UNCONSULTED})
    assert empty_reading.rows == ()
    assert empty_reading.node_outcomes == {"node:0": TermOutcome.NOT_CONSULTED, "node:1": TermOutcome.NOT_CONSULTED}
    assert v1.encode(empty_reading.projection())

    # --- two processes, byte for byte --------------------------------------
    first = _read_in_a_fresh_process(writer.root, minted.id, address)
    assert first == _read_in_a_fresh_process(writer.root, minted.id, address)
    assert first == v1.encode(read_composite(writer.read_view, minted.id, **_inputs(writer, address)).projection())

    writer.delete("proposition:bc")
    with pytest.raises(CompositeError) as caught:
        read_composite(writer.read_view, minted.id, **_inputs(writer, address))
    assert caught.value.code == "composite-member-unresolvable"


def _assert_one_admission(writer, ref: str, address: str) -> None:
    """`test_composite_reading`'s two traps: the identification column is read
    from the one traced admission, never from a second `belief.admitted` pass
    and never from an `admit` call of the reading's own."""
    from beliefs import admission as admission_module
    from beliefs import belief as belief_module

    admitted_calls: list[int] = []
    admit_calls: list[int] = []
    original_admitted, original_admit = belief_module.admitted, belief_module.admit

    def trap_admitted(*args, **kwargs):
        admitted_calls.append(1)
        return original_admitted(*args, **kwargs)

    def trap_admit(*args, **kwargs):
        admit_calls.append(1)
        return original_admit(*args, **kwargs)

    belief_module.admitted, belief_module.admit = trap_admitted, trap_admit
    admission_module.admit = trap_admit
    try:
        read_composite(writer.read_view, ref, **_inputs(writer, address))
    finally:
        belief_module.admitted, belief_module.admit = original_admitted, original_admit
        admission_module.admit = original_admit
    assert admitted_calls == [1, 1], admitted_calls  # one per member, from the evaluator
    assert admit_calls == [1, 1], admit_calls  # `ab`'s two distinct assessments; `bc` has none


# --- U9 ---------------------------------------------------------------------


def test_u9_supersession(corpora, base_contract):
    """U9: the family calls, the shared refusal path for `add` and
    `import_bundle` in both directions, the audited raw pair, and `same_kind`
    refused on unequal endpoint sets by both parsers."""
    writer = _seeded(corpora())
    first = writer.add(stored.composite_node(_build(writer, ["proposition:ab"], slug="v1"), title="v1"))
    second = writer.supersede(stored.composite_node(_build(writer, ["proposition:ab", "proposition:bc"], slug="v2"), title="v2"), of=first.id)
    assert superseded_by(writer.read_view, first.id) == (second.id,)
    assert any(r.predicate == stored.SUPERSEDES and r.target == first.id for r in writer.read_view.get(second.id).relations)
    with pytest.raises(SupersedeIdentityUnchanged):
        writer.supersede(stored.composite_node(_build(writer, ["proposition:ab", "proposition:bc"], slug="v3"), title="v3"), of=second.id)
    with pytest.raises(FamilyKindUnsupported):
        writer.supersede(stored.proposition_node("p2", title="p2", claim=project_claim(_claim("EX:a", "EX:c"))), of=first.id)

    for direction in ("composite-over-proposition", "proposition-over-composite"):
        staging = _seeded(corpora())
        held = staging.add(stored.composite_node(_build(staging, ["proposition:ab"], slug="v1"), title="v1"))
        if direction == "composite-over-proposition":
            record = stored.composite_node(_build(staging, ["proposition:bc"], slug="v2"), title="v2")
            target = "proposition:ab"
        else:
            record = stored.proposition_node("p2", title="p2", claim=project_claim(_claim("EX:a", "EX:c")))
            target = held.id
        record.relations.append(Relation(source=record.id, predicate=stored.SUPERSEDES, target=target))
        stored.stamp_semantic_identity(record)
        with pytest.raises(SignatureRefused, match="supersedes-cross-kind"):
            staging.add(record)
        other = corpora()
        members = tuple(n for n in staging.read_view.iter_stored() if n.kind in {"proposition", "composite"}) + (record,)
        with pytest.raises(ImportRefused, match="supersedes-cross-kind") as caught:
            other.import_bundle(members, **IMPORT)
        assert caught.value.member == record.id

    raw = _seeded(corpora())
    composite = raw.add(stored.composite_node(_build(raw, ["proposition:ab"], slug="v1"), title="v1"))
    node = raw.read_view.get("proposition:ab")
    node.relations.append(Relation(source=node.id, predicate=stored.SUPERSEDES, target=composite.id))
    raw_write(raw.root, node)
    assert ("supersedes-cross-kind", "proposition:ab") in sorted(
        (f.code, f.ref) for f in audit_corpus(reopen(raw.root), evidence=NO_EVIDENCE, profile=raw.profile)
    )

    document = _shipped_document()
    document["relations"]["composes"]["same_kind"] = True
    with pytest.raises(MalformedContract, match="same_kind"):
        parse_base_contract(document, source="<same-kind>")
    _vitest("tests/declarations.test.ts")


# --- U10 --------------------------------------------------------------------


def test_u10_reproduction():
    """U10: the driver's own recorded state, read by name. The reproduction
    step is the driver's and is not re-run here."""
    from reproduction.paths import STATE

    assert STATE.is_file(), (
        f"the mm30 reproduction's recorded state is not at {STATE}; set SCIENCE_MM30_ROOT to the work root "
        "beside the main checkout. This is an error and not a skip: the row is read from the driver's run."
    )
    state = json.loads(STATE.read_text(encoding="utf-8"))
    if "composite_refusal" in state:
        pytest.skip(f"the reproduction's compose step refused: {state['composite_refusal']} — U10's arm is unrun and the row partial")
    assert state["reading_equal"] is True
    assert state["composite_receipt"] == {"node:0": "not-consulted", "node:1": "member", "node:2": "member"}
    rows = state["reading_rows"]
    assert rows["proposition:concept-disease-stage-affects-protein-phf19"][0] == "positive"
    assert rows["proposition:protein-phf19-affects-concept-overall-survival"][0] == "negative"
    assert rows["proposition:concept-disease-stage-affects-protein-phf19"][1:] == ["NoBelief", ["identification:observational"]]
    assert rows["proposition:protein-phf19-affects-concept-overall-survival"][1:] == ["NoBelief", []]
    assert state["belief_answer"]["kind"] == "NoBelief" and state["belief_answer"]["reason"] == "no-directional-outcome"
    assert state["corpus_check_findings"] == 0 and state["audit_findings"] == 0
