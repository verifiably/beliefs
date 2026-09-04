"""Bound reads through a published epoch: §8.3's resolution and §8.4's edges.

**Every answer names the publication it came from.** A read through an epoch is
not a read of the world; it is a read of what one publication observed, over
the coverage that publication declared. So every answer carries
`BoundStamp(packaging_identity, coverage)`, and the stamp means exactly "from
this publication over this declared coverage" and nothing more. Nothing here
measures how much has changed since capture, and nothing here is allowed to
imply that nothing has.

**Absence and ignorance are different answers.** `NotPresent` says "this
epoch recorded that address and the corpus carrying it is not here";
`Unknown` says "this epoch never observed it at all". A retired address is
*recorded*, so its corpus going away is the first of those and never the
second. And neither is ever how ambiguity or corruption is reported: a
duplicate carrier, an unreadable manifest, or a present carrier that does not
produce the mapped `uid` raises `ResolutionRefused`, because an answer that let
corruption look like absence would be worse than no answer.

**Coreference edges answer only where the inputs are established.** The
querying world's span is the live `corpus_id` set the registry reduces to — not
the roots it happens to be configured with — and an edge is `active` or
`inactive` only where the coreference receipt validated *and* the epoch's
coverage contains that whole span. Anything else is `indeterminate`, and an
expansion that would traverse such an edge refuses by name rather than
quietly treating it as inactive.
"""

from __future__ import annotations

import inspect
import os
from dataclasses import FrozenInstanceError, fields
from pathlib import Path
from types import ModuleType

import pytest
from nodes.core.errors import NodesError
from nodes.core.node import Node
from pydantic import ValidationError as PydanticValidationError
from test_world_build import ALPHA, BETA, GAMMA, corpus_at, sample_nodes, slug_for
from test_world_receipts import (
    corpora,
    document,
    hold_shipped,
    publish,
    published_world,
    repackage,
    world_over,
)
from yaml import YAMLError

from beliefs import stored
from beliefs.errors import ResolutionRefused, SemanticHashMissing, SemanticHashStale
from beliefs.world import epoch, read, registry

# --- the harness -------------------------------------------------------------
#
# `test_world_receipts` owns world construction, publication and repackaging;
# what this module adds is the two corpus shapes the read surface needs and
# nothing else — a record answering to a retired address, and the lookups that
# turn a published address map into the arguments of a read.

RETIRED = "dataset:withdrawn"


def nodes_with_retired_address(slug: str) -> tuple[Node, ...]:
    """The sample corpus, plus one record answering to a retired address.

    §7.2 puts every `deprecated_ids` entry in the published address map, which
    is what makes a retired address survive its corpus: the answer is a
    publication member rather than a corpus-local redirect. Exactly one corpus
    carries it, because `derive.address_map` refuses a repeated address even
    when the two claims agree.
    """
    successor = stored.dataset_node(f"{slug}-successor", title=f"dataset {slug} successor")
    return (*sample_nodes(slug), successor.model_copy(update={"deprecated_ids": [RETIRED]}))


def recorded(published: epoch.Epoch) -> dict[str, tuple[str, str]]:
    """The epoch's address map, as `address -> (corpus_id, uid)`."""
    return {
        entry["address"]: (entry["corpus_id"], entry["uid"])
        for entry in document(published, "address-map.yaml")["addresses"]
    }


def an_address_in(published: epoch.Epoch, corpus_id: str) -> str:
    """One recorded address the named corpus carries. Sorted, so an arm that
    fails names the same address every run."""
    return min(
        address for address, (carrier, _uid) in recorded(published).items() if carrier == corpus_id
    )


def retired_world(tmp_path: Path):
    """Two covered corpora, the first of which carries a retired address.

    Two rather than one, because the arms below have to show that one corpus
    going absent is a statement about *that* corpus: with a single covered
    corpus, "recorded but absent" and "the epoch answers nothing" are the same
    observation.
    """
    coverage = (ALPHA, BETA)
    roots = corpora(
        tmp_path,
        {
            ALPHA: nodes_with_retired_address(slug_for(ALPHA, coverage)),
            BETA: sample_nodes(slug_for(BETA, coverage)),
        },
    )
    world = world_over(tmp_path, roots)
    bindings = hold_shipped(world)
    return world, bindings, roots, publish(world, coverage, bindings)


# --- Step 2: the resolution union ---------------------------------------------


class TestBoundResolution:
    def test_inside_coverage_absence_is_not_outside_coverage_unknown(self, tmp_path):
        """`NotPresent` and `Unknown` are two answers, and the line between
        them is what the epoch recorded — never what is here now.

        A retired address is the sharp case. It is recorded, so its corpus
        going away leaves an epoch that still knows the address existed and
        which corpus held it; saying `Unknown` there would throw away the one
        thing the publication was for.
        """
        world, _bindings, roots, published = retired_world(tmp_path)
        addresses = recorded(published)
        assert RETIRED in addresses, "a deprecated id is a recorded address (§7.2)"

        live = an_address_in(published, BETA)
        answered = read.resolve_address(world, published, live)
        assert type(answered) is read.Resolved
        assert answered.location == read.Location(BETA, addresses[live][1])

        retired = read.resolve_address(world, published, RETIRED)
        assert type(retired) is read.Resolved
        assert retired.location == read.Location(*addresses[RETIRED])

        # Nothing the epoch observed: outside coverage entirely.
        outside = read.resolve_address(world, published, "dataset:never-observed")
        assert type(outside) is read.Unknown

        # Now the corpus carrying the retired address stops being carried. The
        # epoch still records both addresses, so both are absent, not unknown.
        gone = addresses[RETIRED][0]
        (roots[gone] / "corpus.yaml").unlink()
        for address in (RETIRED, an_address_in(published, gone)):
            answer = read.resolve_address(world, published, address)
            assert type(answer) is read.NotPresent, address
            assert type(answer) is not read.Unknown, address
        # And a corpus that is still carried still answers, so the absence is
        # about that one corpus rather than about the epoch.
        standing = ALPHA if gone == BETA else BETA
        assert type(read.resolve_address(world, published, an_address_in(published, standing))) is read.Resolved
        # An address the epoch never recorded is still `Unknown` — absence of a
        # corpus does not widen what the publication observed.
        assert type(read.resolve_address(world, published, "dataset:never-observed")) is read.Unknown

    def test_resolution_refuses_every_carrier_ambiguity(self, tmp_path):
        """Ambiguity and corruption refuse. They never impersonate absence.

        Three shapes, and all three are refusals: two configured roots claiming
        one `corpus_id`, a present carrier whose manifest cannot be read, and a
        present carrier that does not produce the `uid` the epoch mapped. The
        first two are configuration faults and the third is corruption; what
        they share is that answering `NotPresent` would tell a caller the
        corpus is simply elsewhere.
        """
        roots = corpora(tmp_path, {ALPHA: sample_nodes("one")})
        duplicate = tmp_path / "duplicate"
        world = world_over(tmp_path, roots, also_configured=(duplicate,))
        bindings = hold_shipped(world)
        published = publish(world, (ALPHA,), bindings)
        address = an_address_in(published, ALPHA)
        assert type(read.resolve_address(world, published, address)) is read.Resolved

        # A present carrier that does not produce the mapped uid.
        addresses = document(published, "address-map.yaml")
        for entry in addresses["addresses"]:
            if entry["address"] == address:
                entry["uid"] = "0" * 32
        mismapped = repackage(world, published, {"address-map.yaml": addresses})
        with pytest.raises(ResolutionRefused, match="uid"):
            read.resolve_address(world, mismapped, address)

        # Two configured roots claiming one corpus id.
        corpus_at(duplicate, ALPHA)
        with pytest.raises(ResolutionRefused, match="carrier"):
            read.resolve_address(world, published, address)
        (duplicate / "corpus.yaml").unlink()
        assert type(read.resolve_address(world, published, address)) is read.Resolved

        # A present carrier whose manifest cannot be read.
        (roots[ALPHA] / "corpus.yaml").write_bytes(b"corpus_id: []\n")
        with pytest.raises(ResolutionRefused, match="manifest"):
            read.resolve_address(world, published, address)

    def test_resolution_refuses_every_present_carrier_read_fault(self, tmp_path):
        """Every member of `read._CARRIER_READ_FAULTS`, driven rather than read.

        The narrowed catch replaced a bare `except Exception`, and a narrowing
        is only as good as the list. The ambiguity arm above never reaches it —
        an unreadable *manifest* is converted earlier, by the presence
        reduction — so this is the only place the list is exercised at all, and
        it exercises **all seven** members: a tuple member with no shape behind
        it is an assertion nobody checked, which is how three escapees
        (`YAMLError`, pydantic's `ValidationError`, `UnicodeError`) shipped in
        the first place.

        Each shape asserts its own `__cause__` type, so removing a member does
        not quietly widen the escape surface — it lets that shape out raw and
        fails the `ResolutionRefused` expectation. The record is restored
        between shapes and the address re-resolves, so every refusal is
        attributable to the mutation that caused it.
        """
        roots = corpora(tmp_path, {ALPHA: sample_nodes("one")})
        world = world_over(tmp_path, roots)
        published = publish(world, (ALPHA,), hold_shipped(world))
        address = an_address_in(published, ALPHA)
        assert address == "dataset:one", "the shapes below tamper with this record by name"
        record = roots[ALPHA] / "dataset" / "one.md"
        intact = record.read_bytes()
        stamped = intact.decode("utf-8")
        digest_line = next(line for line in stamped.splitlines() if line.strip().startswith("digest:"))

        unstamped = "".join(
            line
            for line in stamped.splitlines(keepends=True)
            if "semantic-identity:" not in line and "digest:" not in line
        )
        shapes: dict[str, tuple[bytes, type[Exception]]] = {
            # A governed record whose stored stamp disagrees with the fields it
            # covers: §8.3's corruption, decided on the read path.
            "stale semantic hash": (
                stamped.replace(digest_line, digest_line[:-8] + "deadbeef").encode("utf-8"),
                SemanticHashStale,
            ),
            # A governed record carrying no stamp at all — a raw write that
            # skipped even self-stamping.
            "missing semantic hash": (unstamped.encode("utf-8"), SemanticHashMissing),
            # Front matter that is not YAML at all.
            "unparsable front matter": (b"---\nid: [\n---\n", YAMLError),
            # Front matter that parses and is not a node.
            "front matter that is not a node": (
                stamped.replace(digest_line + "\n", "").encode("utf-8"),
                PydanticValidationError,
            ),
            # A node the `nodes` store itself refuses: its own identifier rule.
            "an identifier the store refuses": (
                stamped.replace("id: dataset:one", "id: NOT A REF").encode("utf-8"),
                NodesError,
            ),
            # Bytes that are not UTF-8. Both `Store.read_file` and the index
            # rebuild decode without a wrapper, and `UnicodeError` is a
            # `ValueError` — neither `OSError` nor any of the above catches it.
            "bytes that are not UTF-8": (intact.replace(b"dataset one", b"dataset \xff\xfe"), UnicodeError),
        }
        for label, (content, cause) in shapes.items():
            record.write_bytes(content)
            with pytest.raises(ResolutionRefused, match="cannot be read") as refusal:
                read.resolve_address(world, published, address)
            assert isinstance(refusal.value.__cause__, cause), label
            record.write_bytes(intact)
            assert type(read.resolve_address(world, published, address)) is read.Resolved, label

        # And the filesystem underneath all of it.
        record.chmod(0o000)
        if os.access(record, os.R_OK):
            record.chmod(0o644)
            pytest.skip("this user reads through mode bits, so the OSError arm cannot be driven")
        with pytest.raises(ResolutionRefused, match="cannot be read") as refusal:
            read.resolve_address(world, published, address)
        assert isinstance(refusal.value.__cause__, OSError)
        record.chmod(0o644)
        assert type(read.resolve_address(world, published, address)) is read.Resolved

        # Closed against the tuple: a member with no shape driving it is the
        # gap this arm exists to prevent, so the arm fails when one is added
        # without one.
        driven = {SemanticHashStale, SemanticHashMissing, YAMLError, PydanticValidationError, NodesError}
        assert driven | {UnicodeError, OSError} == set(read._CARRIER_READ_FAULTS)


# --- Step 3: the bound stamp, and what it does not claim ----------------------


class TestTheBoundStamp:
    def test_every_epoch_answer_carries_complete_bound_stamp(self, tmp_path):
        """Every answer of every shape names the publication and its whole
        coverage declaration — and keeps naming it after the world moves.

        Complete, not the covered ids alone: the stamp carries the
        `(corpus_id, corpus_state)` pairs `coverage.yaml` declares, because
        "over this coverage" is a claim about the states the epoch observed
        and an id without its state is a weaker claim wearing the same words.
        """
        world, _bindings, roots, published = retired_world(tmp_path)
        expected = read.BoundStamp(published.packaging_identity, published.coverage)
        assert published.coverage == tuple(
            (entry["corpus_id"], entry["corpus_state"])
            for entry in document(published, "coverage.yaml")["coverage"]
        )

        answers: list[read.Resolved | read.NotPresent | read.Unknown | read.EdgeAnswer] = [
            read.resolve_address(world, published, an_address_in(published, ALPHA)),
            read.resolve_address(world, published, RETIRED),
            read.resolve_address(world, published, "dataset:never-observed"),
            read.coreference_edge(world, published, "address-a", "address-b"),
        ]
        assert {type(answer) for answer in answers} == {read.Resolved, read.Unknown, read.EdgeAnswer}
        for answer in answers:
            assert answer.stamp == expected

        # The world moves underneath the publication. Every answer stays bound
        # to the epoch it came from, still declaring the states that epoch
        # observed — which are no longer the present ones.
        from test_world_receipts import extra_node

        extra_node(roots[ALPHA], "after-publication")
        moved = registry.corpus_state_identity(roots[ALPHA])
        assert moved != dict(published.coverage)[ALPHA]
        for address in (an_address_in(published, ALPHA), RETIRED, "dataset:never-observed"):
            assert read.resolve_address(world, published, address).stamp == expected
        assert read.coreference_edge(world, published, "address-a", "address-b").stamp == expected

        # And the stamp has nowhere to make a recency claim: two members, the
        # publication and its coverage, and no third one about freshness.
        assert [field.name for field in fields(read.BoundStamp)] == ["packaging_identity", "coverage"]

    def test_bound_answer_types_have_no_stampless_constructor(self, tmp_path):
        """No answer type can be built without its stamp.

        Not a convention the read functions honour — a shape. Every one of the
        four is a small frozen dataclass whose `stamp` is a required
        parameter, so an unstamped answer is unconstructible rather than
        merely unproduced.
        """
        stamp = read.BoundStamp("f" * 64, ((ALPHA, "a" * 64),))
        answer_types = (read.Resolved, read.NotPresent, read.Unknown, read.EdgeAnswer)

        for answer_type in answer_types:
            parameters = inspect.signature(answer_type).parameters
            assert "stamp" in parameters, answer_type
            assert parameters["stamp"].default is inspect.Parameter.empty, answer_type
            with pytest.raises(TypeError):
                # Deliberately omitting the required arguments: the arm exercises
                # the runtime refusal that an unstamped answer is unconstructible.
                answer_type()  # pyright: ignore[reportCallIssue]

        # Frozen, so a stamp cannot be swapped out after the fact either.
        built = read.Unknown(stamp)
        # Two more deliberate violations, exercising the frozen dataclasses' refusal.
        with pytest.raises(FrozenInstanceError):
            built.stamp = read.BoundStamp("e" * 64, ())  # pyright: ignore[reportAttributeAccessIssue]
        with pytest.raises(FrozenInstanceError):
            stamp.coverage = ()  # pyright: ignore[reportAttributeAccessIssue]

        # Small dataclasses, not a generic result framework: the union's arms
        # share no base beyond `object` and carry no machinery.
        for answer_type in answer_types:
            assert answer_type.__mro__ == (answer_type, object), answer_type
            # `dataclasses` publishes `frozen` only through this generated attribute.
            assert answer_type.__dataclass_params__.frozen  # pyright: ignore[reportAttributeAccessIssue]

    def test_belief_has_no_current_epoch_input(self):
        """No belief API accepts an epoch, a pointer, or the word `current`.

        A belief input is an explicit producer-snapshot identity and stays
        one (§7.3, §8.1). `current` is operational convenience: it names
        whichever epoch this world last published, which is a fact about this
        world's operations and not about what anyone should believe.
        """
        from beliefs import belief, closure

        for entry_point in (belief.evaluate, closure.build_closure):
            parameters = inspect.signature(entry_point).parameters
            assert not [name for name in parameters if "epoch" in name or "current" in name], entry_point

        supplied = inspect.signature(closure.build_closure).parameters["producer_snapshot_identity"]
        assert supplied.annotation == "str"
        assert supplied.default is inspect.Parameter.empty
        assert [field.name for field in fields(belief.SuppliedContext) if "epoch" in field.name] == []
        assert "producer_snapshot_identity" in [field.name for field in fields(belief.SuppliedContext)]

        # Two checks, and neither subsumes the other — they catch opposite
        # evasions, so both stay.
        #
        # The **source grep** catches an import this module's own text
        # performs, *including one inside a function body*. A function-local
        # `from beliefs.world import read` binds a local at call time and never
        # enters module globals, so the namespace walk below cannot see it; the
        # text can. It is also the only one of the two that can say anything
        # about the word `current_epoch`, which is not a name either module
        # binds but is exactly the selector §8.1 forbids belief from reaching
        # for.
        #
        # The **namespace walk** catches what the grep cannot: a name
        # re-exported into `belief` or `closure` through a third module whose
        # own source never mentions the world package. It is non-vacuous — the
        # origin sets are populated (`beliefs.lineage`, `beliefs.record` and
        # `beliefs.verification` are in both; `belief` carries a dozen more),
        # which the count below pins so a walk that silently started reading
        # nothing would fail rather than pass.
        for module in (belief, closure):
            source_file = inspect.getsourcefile(module)
            assert source_file is not None, module
            source = Path(source_file).read_text(encoding="utf-8")
            assert "beliefs.world" not in source, module
            assert "current_epoch" not in source, module
            origins = {
                value.__name__ if isinstance(value, ModuleType) else getattr(value, "__module__", "")
                for value in vars(module).values()
            }
            assert len([name for name in origins if name.startswith("beliefs.")]) >= 3, module
            assert not [name for name in origins if name.startswith("beliefs.world")], module

    def test_belief_is_invariant_to_availability_and_requires_snapshot(self, tmp_path):
        """The belief input an epoch contributes does not move with
        availability, and cannot be omitted.

        Availability is what a world can presently *resolve*: the rules it
        holds and the corpora standing where they stood. Belief is what the
        evidence *is*. Unholding every rule and moving every corpus turns all
        four receipts unresolvable and leaves the producer snapshot identity
        exactly where it was — which is the whole reason a receipt outcome is
        not a belief member.
        """
        from test_world_receipts import extra_node, outcomes

        from beliefs import closure
        from beliefs.world import derive, rules

        world, bindings, roots, published = published_world(tmp_path)
        draft = epoch._capture_build_inputs(world, coverage=frozenset({ALPHA}), bindings=bindings.by_kind())
        receipts = derive.derivation_receipts(
            snapshot=derive.producer_snapshot(draft.run("producer")),
            enumeration=derive.retraction_enumeration(draft.run("retraction-enumeration")),
            inventory=derive.certification_inventory(draft.run("certification-enumeration")),
            coreference=derive.coreference_map(draft.run("coreference-reduction")),
            corpus_states=draft.corpus_states,
            bindings=draft.bindings,
        )
        belief_input = derive.belief_input_identity(receipts)
        assert belief_input == published.receipts["producer-receipt.yaml"].subject_identity
        assert derive.BELIEF_INPUT_KIND == "producer"

        for binding in (bindings.producer, bindings.retraction, bindings.certification, bindings.coreference):
            rules.remove_rule_binding(world, binding)
        extra_node(roots[ALPHA], "after-belief")

        assert outcomes(world, published) == dict.fromkeys(epoch.DERIVATION_KINDS, "unresolvable")
        reopened = read.open_epoch(world, published.packaging_identity)
        assert reopened.receipts["producer-receipt.yaml"].subject_identity == belief_input

        # And the closure demands it explicitly: there is no default and no
        # ambient source for it to fall back to.
        with pytest.raises(TypeError, match="producer_snapshot_identity"):
            closure.build_closure(proposition="p")  # type: ignore[call-arg]
        with pytest.raises(ValueError, match=derive.BELIEF_INPUT_KIND):
            derive.belief_input_identity(())


# --- Step 4: edge state and expansion -----------------------------------------
#
# The shipped capture pass records no coreference attestation — §13 defers that
# stored kind — so a coreference map built from a real corpus is empty and
# every edge in it is `inactive`. An arm that only ever saw an empty map would
# pin half the contract. So these arms bind a *sibling implementation* of the
# coreference rule that reduces `produces` edges into pairs: no coreference
# fixture carries a record with a `produces` edge, so the successor satisfies
# every normative fixture, and on a real corpus it publishes a genuinely
# non-empty reduction whose receipt validates.

COREFERENCE_ANCHOR = '        attestation = record["coreference"]\n'
COREFERENCE_ARM = (
    '        for dataset in record["produces"]:\n'
    '            pair = tuple(sorted((record["address"], dataset)))\n'
    '            units.setdefault(pair, set()).add((1, record["address"], dataset))\n'
)


def coreference_successor():
    from beliefs.world import rules

    bundle = next(
        candidate for candidate in rules.shipped_rule_bundles() if candidate.symbol == "reduce_coreference"
    )
    source = bundle.implementation.decode("utf-8")
    assert source.count(COREFERENCE_ANCHOR) == 1
    source = source.replace(COREFERENCE_ANCHOR, COREFERENCE_ARM + COREFERENCE_ANCHOR)
    return rules.RuleBundle(bundle.symbol, bundle.fixtures, source.encode("utf-8"))


def linked_nodes(slug: str) -> tuple[Node, ...]:
    """One dataset and the two runs producing it — a three-endpoint chain once
    the reduction above turns each `produces` edge into a pair."""
    dataset = stored.dataset_node(slug, title=f"dataset {slug}")
    return (
        dataset,
        stored.run_node(slug, title=f"run {slug}", spec=f"analysis-spec:{slug}", produces=[dataset.id]),
        stored.run_node(
            f"{slug}-two", title=f"run {slug} two", spec=f"analysis-spec:{slug}-two", produces=[dataset.id]
        ),
    )


def coreference_world(
    tmp_path: Path,
    placement: dict[str, tuple[Node, ...]],
    coverage: tuple[str, ...],
    *,
    also_configured: tuple[Path, ...] = (),
):
    """A world publishing a non-empty, validating coreference reduction."""
    from beliefs.world import rules

    roots = corpora(tmp_path, placement)
    world = world_over(tmp_path, roots, also_configured=also_configured)
    shipped = hold_shipped(world)
    bindings = epoch.DerivationBindings(
        producer=shipped.producer,
        retraction=shipped.retraction,
        certification=shipped.certification,
        coreference=rules.install_rule_binding(world, coreference_successor()),
    )
    return world, bindings, roots, publish(world, coverage, bindings)


def pairs_of(published: epoch.Epoch) -> list[list[str]]:
    return [entry["endpoints"] for entry in document(published, "coreference-map.yaml")["pairs"]]


class TestCoreferenceEdges:
    def test_coreference_nonvalidated_outcomes_are_indeterminate(self, tmp_path):
        """`refuted`, `unresolvable` and `malformed` all answer the same way.

        The coreference receipt carries no semantic identity and is never a
        belief input, so there is no partial credit to give: any outcome other
        than ``validated`` leaves every edge the map covers `indeterminate`,
        and an expansion through one refuses.
        """
        from beliefs.world import rules

        world, bindings, _roots, published = coreference_world(
            tmp_path, {ALPHA: linked_nodes("a")}, (ALPHA,)
        )
        assert pairs_of(published) == [["dataset:a", "run:a"], ["dataset:a", "run:a-two"]]
        assert read.validate_receipt(world, published, "coreference-reduction").outcome == "validated"

        active = read.coreference_edge(world, published, "run:a", "dataset:a")
        assert active.state == "active"
        assert read.coreference_edge(world, published, "run:a", "run:a-two").state == "inactive"
        assert read.expand_coreference(world, published, "run:a") == ("dataset:a", "run:a-two")

        from beliefs.world import derive

        carriers: dict[str, epoch.Epoch] = {}
        # refuted: a pair the covered corpus does not support, with a receipt
        # whose subject identity matches the map, so nothing is malformed.
        reduction = document(published, "coreference-map.yaml")
        reduction["pairs"] = [
            *reduction["pairs"],
            {"endpoints": ["invented-a", "invented-b"], "balance": 1, "distinct_key_count": 1},
        ]
        carriers["refuted"] = repackage(
            world,
            published,
            {
                "coreference-map.yaml": reduction,
                "coreference-receipt.yaml": dict(
                    document(published, "coreference-receipt.yaml"),
                    subject=derive.subject_identity("coreference-reduction", reduction),
                ),
            },
        )
        # malformed: a key outside the closed set the kind declares.
        carriers["malformed"] = repackage(
            world,
            published,
            {
                "coreference-receipt.yaml": dict(
                    document(published, "coreference-receipt.yaml"), invented="value"
                )
            },
        )

        for outcome, carrier in carriers.items():
            assert read.validate_receipt(world, carrier, "coreference-reduction").outcome == outcome
            for left, right in (("run:a", "dataset:a"), ("run:a", "run:a-two")):
                answer = read.coreference_edge(world, carrier, left, right)
                assert answer.state == "indeterminate", (outcome, left, right)
                assert answer.receipt_outcome == outcome
                assert answer.missing_coverage == ()
            with pytest.raises(read.EdgeIndeterminate) as refusal:
                read.expand_coreference(world, carrier, "run:a")
            assert refusal.value.receipt_outcome == outcome
            assert outcome in str(refusal.value)

        # unresolvable: the exact pair is no longer held here.
        rules.remove_rule_binding(world, bindings.coreference)
        assert read.validate_receipt(world, published, "coreference-reduction").outcome == "unresolvable"
        answer = read.coreference_edge(world, published, "run:a", "dataset:a")
        assert answer.state == "indeterminate"
        assert answer.receipt_outcome == "unresolvable"
        with pytest.raises(read.EdgeIndeterminate, match="unresolvable"):
            read.expand_coreference(world, published, "run:a")

        assert read.EDGE_STATES == ("active", "inactive", "indeterminate")

    def test_refuted_coreference_is_nonbelief_indeterminate(self, tmp_path):
        """A refuted coreference receipt makes edges indeterminate and moves
        no belief.

        The two halves are the point. §7.5 gives the coreference receipt no
        semantic identity and no belief member, so refuting it cannot reach the
        producer snapshot; and §8.4 gives a non-validated receipt no partial
        edge reading, so it cannot answer either.
        """
        from beliefs.world import derive

        world, _bindings, _roots, published = coreference_world(
            tmp_path, {ALPHA: linked_nodes("a")}, (ALPHA,)
        )
        reduction = {
            "pairs": [{"endpoints": ["invented-a", "invented-b"], "balance": -1, "distinct_key_count": 1}]
        }
        refuted = repackage(
            world,
            published,
            {
                "coreference-map.yaml": reduction,
                "coreference-receipt.yaml": dict(
                    document(published, "coreference-receipt.yaml"),
                    subject=derive.subject_identity("coreference-reduction", reduction),
                ),
            },
        )
        assert read.validate_receipt(world, refuted, "coreference-reduction").outcome == "refuted"

        # Every edge the map covers, and every edge it does not.
        for left, right in (("invented-a", "invented-b"), ("run:a", "dataset:a"), ("x", "y")):
            assert read.coreference_edge(world, refuted, left, right).state == "indeterminate"

        # Belief is untouched: the producer receipt still validates and the
        # belief input is the same identity it was.
        assert read.validate_receipt(world, refuted, "producer").outcome == "validated"
        assert (
            refuted.receipts["producer-receipt.yaml"].subject_identity
            == published.receipts["producer-receipt.yaml"].subject_identity
        )
        # And the receipt shape has nowhere to put a belief member for any
        # kind, which is what makes the guarantee structural.
        assert [field.name for field in fields(derive.DerivationReceipt)] == [
            "kind",
            "subject_identity",
            "corpus_states",
            "rule_identity",
            "implementation_identity",
            "enumeration",
            "inventory",
        ]
        assert derive.BELIEF_INPUT_KIND != "coreference-reduction"

    def test_unreadable_manifest_leaves_edges_indeterminate_rather_than_raising(self, tmp_path):
        """§8.4 promises a state for every edge, so a corrupt manifest cannot
        answer with an exception.

        The companion of `test_unreadable_carrier_manifest_is_unresolvable_...`
        in `test_world_receipts.py`: that arm pins the outcome, this one pins
        that the outcome is what the two queries actually see, including the
        expansion that refuses by name rather than by whatever the registry
        happened to raise.
        """
        world, _bindings, roots, published = coreference_world(
            tmp_path, {ALPHA: linked_nodes("a")}, (ALPHA,)
        )
        assert read.coreference_edge(world, published, "run:a", "dataset:a").state == "active"

        (roots[ALPHA] / "corpus.yaml").write_bytes(b"corpus_id: []\n")

        answer = read.coreference_edge(world, published, "run:a", "dataset:a")
        assert answer.state == "indeterminate"
        assert answer.receipt_outcome == "unresolvable"
        with pytest.raises(read.EdgeIndeterminate, match="unresolvable"):
            read.expand_coreference(world, published, "run:a")

    def test_edge_indeterminate_names_missing_span_and_receipt_outcome(self, tmp_path):
        """The refusal names every unestablished input, by name.

        The span is the registry's live set. A configured carrier root for a
        corpus this world never admitted is not part of it — a world does not
        widen its own span by being pointed at a directory — and a corpus that
        has been retired leaves it, which is what makes wider epoch coverage
        acceptable rather than merely tolerated.
        """
        from beliefs.world import rules

        gamma_root = corpus_at(tmp_path / "configured-gamma", GAMMA, sample_nodes("g"))
        world, bindings, _roots, published = coreference_world(
            tmp_path,
            {ALPHA: linked_nodes("a"), BETA: linked_nodes("b")},
            (ALPHA,),
            also_configured=(gamma_root,),
        )
        assert [corpus_id for corpus_id, _state in published.coverage] == [ALPHA]
        assert read.validate_receipt(world, published, "coreference-reduction").outcome == "validated"

        # BETA is live and uncovered; GAMMA is carried and not admitted, so it
        # is not part of this world's span at all.
        answer = read.coreference_edge(world, published, "run:a", "dataset:a")
        assert answer.state == "indeterminate"
        assert answer.missing_coverage == (BETA,)
        assert answer.receipt_outcome is None
        with pytest.raises(read.EdgeIndeterminate) as refusal:
            read.expand_coreference(world, published, "run:a")
        assert refusal.value.missing_coverage == (BETA,)
        assert refusal.value.receipt_outcome is None
        assert BETA in str(refusal.value)
        assert GAMMA not in str(refusal.value)

        # Both unestablished inputs at once, and both named.
        rules.remove_rule_binding(world, bindings.coreference)
        answer = read.coreference_edge(world, published, "run:a", "dataset:a")
        assert answer.missing_coverage == (BETA,)
        assert answer.receipt_outcome == "unresolvable"
        with pytest.raises(read.EdgeIndeterminate) as both:
            read.expand_coreference(world, published, "run:a")
        assert both.value.missing_coverage == (BETA,)
        assert both.value.receipt_outcome == "unresolvable"
        assert BETA in str(both.value) and "unresolvable" in str(both.value)

        # Wider coverage is accepted: an epoch over both corpora keeps
        # answering once BETA leaves the live set.
        rules.install_rule_binding(world, coreference_successor())
        wider = publish(world, (ALPHA, BETA), bindings)
        assert [corpus_id for corpus_id, _state in wider.coverage] == [ALPHA, BETA]
        assert read.coreference_edge(world, wider, "run:a", "dataset:a").state == "active"
        world.retire(BETA)
        assert registry._live_corpus_ids(world.registry()) == (ALPHA,)
        widest = read.coreference_edge(world, wider, "run:a", "dataset:a")
        assert widest.state == "active"
        assert widest.missing_coverage == ()
        assert read.expand_coreference(world, wider, "run:a") == ("dataset:a", "run:a-two")
