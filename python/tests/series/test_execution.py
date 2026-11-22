"""Every executable series boundary requires freshly checked local buffers."""

from dataclasses import replace

import pytest
from fixtures_cut3 import MEMORY_PORT, SNAKEFILE_DETERMINISTIC, definition, stage

from beliefs import boundary
from beliefs.boundary import RunRefused, execute_assessment_run
from beliefs.recipe import CONFINED_POLICY, MINIMAL_POLICY
from beliefs.replay import CONTENT_EQUALITY
from beliefs.series.evidence import SeriesEvidence
from beliefs.verify import build_verification

from .test_portability import portable as portable  # noqa: PLC0414


@pytest.mark.parametrize(
    "evidence_kind,expected",
    [("complete", "passed"), ("absent", "inconclusive"), ("corrupt", "failed"), ("no-context", "inconclusive")],
)
def test_series_verification_verdicts(portable, evidence_kind, expected):
    p = portable
    evidence = p.case.evidence()
    if evidence_kind == "absent":
        evidence = None
    elif evidence_kind == "corrupt":
        p.case.buffers[next(iter(p.case.buffers))] = b"changed origin"
    args = {"profile": p.profile, "records": p.case.records} if evidence_kind != "no-context" else {}
    value = build_verification(
        p.closure,
        replace(p.closure, occurrence=replace(p.closure.occurrence, event_token="replayed-series")),
        specs=p.evidence.specs,
        held_rules={CONTENT_EQUALITY.identity: CONTENT_EQUALITY},
        contract_identity="science:" + p.profile.base_contract_identity,
        epoch="fixture-epoch",
        series_evidence=evidence,
        **args,
    )
    assert value.verdict == expected
    assert bool([d for d in value.report.diagnostics if "series" in d]) == (expected != "passed")


def launch_args(p, tmp_path):
    code, held = stage(tmp_path, snakefile=SNAKEFILE_DETERMINISTIC)
    inputs = {}
    for row in p.value.series_graph:
        if row.ref.member is not None:
            from beliefs.boundary import HeldTree

            store = held / "tree-store"
            for name, data in p.case.buffers.items():
                if name.startswith("objects/"):
                    path = store / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(data)
            inputs[row.ref.dataset] = {"series-tree": HeldTree(store, row.ref.resource)}
        else:
            path = held / (row.ref.resource.split(":")[1] + ".json")
            path.write_bytes(p.case.buffers[row.ref.resource.split(":")[1]])
            inputs[row.ref.dataset] = path
    ordinary = next(i for i in p.spec.input_roles if i.role == "observes")
    observed = held / "data.txt"
    observed.write_text("fixture observation")
    inputs[ordinary.dataset] = observed
    return {
        "spec": p.spec,
        "port": MEMORY_PORT,
        "boundary_policy": MINIMAL_POLICY,
        "definition": definition(),
        "code_roots": (code,),
        "held_inputs": inputs,
        "entrypoint": "code/workflow/Snakefile",
        "targets": ("outputs/result.txt",),
        "declared_outputs": ("outputs/result.txt",),
        "observer": "fixture",
        "started_at": "2026-11-13T00:00:00Z",
        "host_realization": "fixture",
        "scratch_base": tmp_path / "scratch",
        "series_evidence": p.case.evidence(),
        "profile": p.profile,
        "records": p.case.records,
    }


class ReachedLaunch(Exception):
    pass


@pytest.mark.parametrize("route", ["plain", "confined", "replay"])
@pytest.mark.parametrize("condition", ["missing", "copied", "planning-copy", "graph", "valid"])
def test_every_launch_route_checks_staged_series(portable, tmp_path, monkeypatch, condition, route):
    p = portable
    args = launch_args(p, tmp_path / "run")
    launches = []

    def launch(*args, **kwargs):
        launches.append(kwargs.get("cwd", kwargs.get("plan")))
        raise ReachedLaunch

    monkeypatch.setattr(boundary, "run_engine", launch)
    monkeypatch.setattr(boundary, "launch_confined", launch)
    if route == "confined":
        args["boundary_policy"] = CONFINED_POLICY
        monkeypatch.setattr(boundary, "require_host", lambda: None)
        monkeypatch.setattr(boundary, "materialize_snapshot", lambda captured, root: root)
    if condition == "graph":
        from beliefs.identity import v1
        from beliefs.spec import SPEC_DOMAIN, frozen_projection, restore

        from .fixtures import raw_object

        body = raw_object(v1.encode(frozen_projection(p.spec)))
        table_row = next(row for row in body["estimand"]["series_graph"] if row["format"] == "science.series-table.v2")
        table_row["terms"] = sorted(set(table_row["terms"]) | {"testing/entity"})
        args["spec"] = restore(v1.digest(SPEC_DOMAIN, body), v1.encode(body), profile=p.profile)
    if condition == "missing":
        args["series_evidence"] = SeriesEvidence({}, {})
    if condition in {"copied", "planning-copy"}:
        original = boundary._stage_inputs
        copies = []
        table = next(row.ref for row in p.value.series_graph if row.format == "science.series-table.v2")
        basename = args["held_inputs"][table.dataset].name

        def substitute(*args, **kwargs):
            result = original(*args, **kwargs)
            copies.append(args[2])
            if len(copies) == (1 if condition == "copied" else 2):
                (args[2] / "inputs" / basename).write_bytes(b"substituted staged table")
            return result

        monkeypatch.setattr(boundary, "_stage_inputs", substitute)

    def invoke():
        if route != "replay":
            return execute_assessment_run(**args)
        from hashlib import sha256

        from beliefs.replay import replay

        original = replace(
            p.closure,
            recipe=replace(
                p.closure.recipe,
                inputs=tuple(
                    replace(i, content="sha256:" + sha256(args["held_inputs"][i.dataset].read_bytes()).hexdigest())
                    for i in p.closure.recipe.inputs
                ),
            ),
        )
        return replay(original, **{key: value for key, value in args.items() if key != "boundary_policy"})

    if condition == "valid":
        with pytest.raises(ReachedLaunch):
            invoke()
        assert len(launches) == 1
    else:
        result = invoke()
        assert isinstance(result, RunRefused)
        assert launches == []


def test_series_verification_checks_input_content_as_well_as_dataset_roles(portable):
    p = portable
    dataset = p.value.series_graph[0].ref.dataset
    replayed = replace(
        p.closure,
        recipe=replace(
            p.closure.recipe,
            inputs=tuple(
                replace(i, content="sha256:" + "f" * 64) if i.dataset == dataset else i for i in p.closure.recipe.inputs
            ),
        ),
    )
    result = build_verification(
        p.closure,
        replayed,
        specs=p.evidence.specs,
        held_rules={CONTENT_EQUALITY.identity: CONTENT_EQUALITY},
        contract_identity="science:" + p.profile.base_contract_identity,
        epoch="fixture",
        series_evidence=p.case.evidence(),
        profile=p.profile,
        records=p.case.records,
    )
    assert result.verdict == "failed"
    assert any("series" in d and "content" in d for d in result.report.diagnostics)


@pytest.mark.parametrize("portable", ["tree"], indirect=True)
@pytest.mark.parametrize("condition", ["member", "manifest", "oversized-manifest"])
def test_tree_staging_checks_members_and_explicit_manifest(portable, tmp_path, monkeypatch, condition):
    from beliefs.tree import object_path

    p = portable
    args = launch_args(p, tmp_path / "run")
    root = next(row.ref for row in p.value.series_graph if row.ref.member is not None)
    if condition == "manifest":
        del p.case.buffers[object_path(root.resource)]
    elif condition == "oversized-manifest":
        held = args["held_inputs"][root.dataset]["series-tree"]
        (held.store_root / object_path(root.resource)).write_bytes(b" " * (16 * 1024 * 1024 + 1))
    else:
        original = boundary._stage_inputs

        def substitute(*a, **kw):
            result = original(*a, **kw)
            (a[2] / "inputs" / "series-tree" / root.member).write_bytes(b"changed staged member")
            return result

        monkeypatch.setattr(boundary, "_stage_inputs", substitute)

    def forbidden(*a, **kw):
        raise AssertionError("invalid series reached a launch")

    monkeypatch.setattr(boundary, "run_engine", forbidden)
    result = execute_assessment_run(**args)
    assert isinstance(result, RunRefused)
    assert "series" in result.reason


@pytest.mark.parametrize("confined", [False, True])
def test_execution_rechecks_the_original_staged_copy_after_planning(portable, tmp_path, monkeypatch, confined):
    from types import SimpleNamespace

    p = portable
    args = launch_args(p, tmp_path / "run")
    roots, launches = [], []
    original = boundary._stage_inputs
    table = next(row.ref for row in p.value.series_graph if row.format == "science.series-table.v2")
    basename = args["held_inputs"][table.dataset].name

    def stage_inputs(*a, **kw):
        result = original(*a, **kw)
        roots.append(a[2])
        return result

    def planning(*a, **kw):
        launches.append("planning")
        assert len(launches) == 1, "execution launched on a changed series copy"
        (roots[0] / "inputs" / basename).write_bytes(b"changed after planning copy")
        return SimpleNamespace(returncode=0, output="") if confined else (0, "")

    monkeypatch.setattr(boundary, "_stage_inputs", stage_inputs)
    monkeypatch.setattr(boundary, "read_plan", lambda path, **kwargs: ())
    monkeypatch.setattr(boundary, "check_checkpoint_declaration", lambda *a: None)
    monkeypatch.setattr(boundary, "resolve_targets", lambda *a: ())
    if confined:
        args["boundary_policy"] = CONFINED_POLICY
        monkeypatch.setattr(boundary, "require_host", lambda: None)
        monkeypatch.setattr(boundary, "materialize_snapshot", lambda captured, root: root)
        monkeypatch.setattr(boundary, "check_closure_intact", lambda **kw: None)
        monkeypatch.setattr(boundary, "_confined_attestation", lambda **kw: p.closure.occurrence.receipt.planning)
        monkeypatch.setattr(boundary, "launch_confined", planning)
    else:
        monkeypatch.setattr(boundary, "run_engine", planning)
    result = execute_assessment_run(**args)
    assert isinstance(result, RunRefused)
    assert "series" in result.reason and launches == ["planning"]


@pytest.mark.parametrize("condition", ["agree", "absent", "corrupt"])
def test_audit_verification_preserves_missing_evidence_as_unchecked(portable, condition):
    from beliefs.audit import check_verification
    from beliefs.verify import publication_node

    from .test_portability import run_publication

    p = portable
    replayed = replace(p.closure, occurrence=replace(p.closure.occurrence, event_token="replayed-series"))
    derived = build_verification(
        p.closure,
        replayed,
        specs=p.evidence.specs,
        held_rules={CONTENT_EQUALITY.identity: CONTENT_EQUALITY},
        contract_identity="science:" + p.profile.base_contract_identity,
        epoch="fixture",
        series_evidence=p.case.evidence(),
        profile=p.profile,
        records=p.case.records,
    )
    p.writer.add(run_publication(replayed))
    node = publication_node(derived, assessment_ref=p.assessment.id)
    supplied = p.case.evidence() if condition != "absent" else None
    if condition == "corrupt":
        p.case.buffers[next(iter(p.case.buffers))] = b"wrong origin"
    evidence = replace(p.evidence, held_rules={CONTENT_EQUALITY.identity: CONTENT_EQUALITY}, series_evidence=supplied)
    result = check_verification(p.writer.read_view, node, evidence=evidence, profile=p.profile)
    assert result.checked == (condition != "absent")
    assert (result.contradiction is not None) == (condition == "corrupt")


def test_series_input_check_preserves_dataset_resource_repetition(portable):
    from beliefs import stored

    p = portable
    dataset = p.value.series_graph[0].ref.dataset
    declaration = stored.dataset_declaration(p.case.records.read(dataset))
    digest = declaration.resources[0].digest
    repeated = stored.dataset_node(
        title="Same content set", resources=({"name": "a", "digest": digest}, {"name": "b", "digest": digest})
    )
    assert repeated.id == dataset
    p.case.records.nodes[dataset] = repeated
    result = build_verification(
        p.closure,
        p.closure,
        specs=p.evidence.specs,
        held_rules={CONTENT_EQUALITY.identity: CONTENT_EQUALITY},
        contract_identity="science:" + p.profile.base_contract_identity,
        epoch="fixture",
        series_evidence=p.case.evidence(),
        profile=p.profile,
        records=p.case.records,
    )
    assert result.verdict == "passed"


def test_verification_reports_incompatible_frozen_series_modes_as_failed(portable):
    from beliefs.identity import v1
    from beliefs.spec import SPEC_DOMAIN, frozen_projection, restore

    p = portable
    from .fixtures import raw_object

    body = raw_object(v1.encode(frozen_projection(p.spec)))
    # A portable, structurally coherent spec can carry a byte-incompatible mode.
    table = next(row.ref.dataset for row in p.value.series_graph if row.format == "science.series-table.v2")
    for entry in body["input_roles"]:
        if entry["dataset"] == table:
            entry["mode"] = "annotation"
    spec = restore(v1.digest(SPEC_DOMAIN, body), v1.encode(body), profile=p.profile)
    original = replace(p.closure, recipe=replace(p.closure.recipe, spec_identity=spec.identity))
    result = build_verification(
        original,
        original,
        specs={spec.identity: spec},
        held_rules={CONTENT_EQUALITY.identity: CONTENT_EQUALITY},
        contract_identity="science:" + p.profile.base_contract_identity,
        epoch="fixture",
        series_evidence=p.case.evidence(),
        profile=p.profile,
        records=p.case.records,
    )
    assert result.verdict == "failed"
    assert any("series" in diagnostic and "mode" in diagnostic for diagnostic in result.report.diagnostics)


from .test_anchor_coherence import linked_portable as linked_portable  # noqa: PLC0414
from .test_anchor_coherence import profiles as profiles  # noqa: PLC0414


@pytest.mark.parametrize("route", ["plain", "replay"])
def test_retained_class_checked_at_launch_without_claim(linked_portable, tmp_path, monkeypatch, route):
    from beliefs.replay import replay

    p = linked_portable
    args = launch_args(p, tmp_path / "linked-run")

    def never_launch(*args, **kwargs):
        pytest.fail("a linked class with no retained event reached the engine")

    monkeypatch.setattr(boundary, "run_engine", never_launch)
    if route == "plain":
        result = execute_assessment_run(**args)
    else:
        result = replay(p.closure, **{key: value for key, value in args.items() if key != "boundary_policy"})
    assert isinstance(result, RunRefused)
    assert "retained" in str(result)


@pytest.mark.parametrize("available,expected", [(True, "failed"), (False, "inconclusive")])
def test_retained_class_verification_without_claim(linked_portable, available, expected):
    p = linked_portable
    value = build_verification(
        p.closure,
        replace(p.closure, occurrence=replace(p.closure.occurrence, event_token="linked-replay")),
        specs=p.evidence.specs,
        held_rules={CONTENT_EQUALITY.identity: CONTENT_EQUALITY},
        contract_identity="science:" + p.profile.base_contract_identity,
        epoch="fixture",
        profile=p.profile,
        records=p.case.records,
        series_evidence=p.case.evidence() if available else None,
    )
    assert value.verdict == expected
    assert any("retained" in message for message in value.report.diagnostics) == available
