"""E6: hold every write entry point closed statically (design §5)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

import beliefs

PACKAGE = Path(beliefs.__file__).resolve().parent

PRIMITIVE_ATTRIBUTES = frozenset(
    {
        "append_intent",
        "execute",
        "execute_fulfilling",
        "publish_fulfilling",
        "store_write",
        "store_delete",
        "store_move",
    }
)
PRIMITIVE_NAMES = frozenset(
    {
        "register_root",
        "_replicate_root_callback",
        "_fork_root_callback",
        "_resume_fork_root_callback",
        "_grant_read_serviceability_callback",
        "_migrate_root_to_lifecycle_v3_callback",
    }
)
PRIMITIVE_IMPLEMENTATIONS = frozenset(
    {
        "corpus.py:_RoutedExecutor.execute",
        "root.py:DurableOperationPort.append_intent",
        "root.py:DurableOperationPort.execute",
        "root.py:DurableOperationPort._execute",
        "root.py:DurableOperationPort.execute_fulfilling",
        "root.py:DurableOperationPort._execute_fulfilling",
        "root.py:DurableExecutor.execute",
        "root.py:_mapped_submit.submit",
        "root.py:_store_append_intent",
        "root.py:_store_publish_fulfilling",
        "root.py:_store_write",
        "root.py:_store_delete",
        "root.py:_store_move",
        "root.py:_fork_resume",
    }
)

WRITE_ENTRY_POINTS: dict[str, str] = {
    "corpus.py:CorpusWriter.add": "corpus-write",
    "corpus.py:CorpusWriter.retract": "corpus-write",
    "corpus.py:CorpusWriter.supersede": "corpus-write",
    "corpus.py:CorpusWriter.revise": "corpus-write",
    "corpus.py:CorpusWriter.mint_coordination": "corpus-write",
    "corpus.py:CorpusWriter.revise_coordination": "corpus-write",
    "corpus.py:CorpusWriter.import_bundle": "corpus-write",
    "corpus.py:CorpusWriter.adopt_manifest": "lifecycle",
    "corpus.py:CorpusWriter._add_locked": "corpus-write",
    "corpus.py:CorpusWriter._replace_locked": "corpus-write",
    "corpus.py:CorpusWriter._delete_locked": "corpus-write",
    "corpus.py:CorpusWriter._append_operation_intent": "corpus-write",
    "corpus.py:CorpusWriter._publish_operation_report": "corpus-write",
    "boundary.py:execute_assessment_run": "run",
    "boundary.py:execute_production_run": "run",
    "holdings/boundary.py:_publish": "holdings",
    "holdings/boundary.py:recheck": "holdings",
    "holdings/boundary.py:_append": "holdings",
    "holdings/boundary.py:write": "holdings",
    "holdings/boundary.py:delete": "holdings",
    "holdings/boundary.py:move": "holdings",
    "world/registry.py:World._terminal": "registry",
    "world/registry.py:_locked_admit": "registry",
    "world/anchors.py:_anchor_heads": "registry",
    "world/epoch.py:build_epoch": "epoch",
    "world/epoch.py:delete_epoch": "epoch",
    "world/rules.py:install_rule_binding": "epoch",
    "world/rules.py:remove_rule_binding": "epoch",
    "root.py:init_corpus_root": "lifecycle",
    "root.py:init_world_root": "lifecycle",
    "root.py:init_store_root": "lifecycle",
    "root.py:replicate_root": "lifecycle",
    "root.py:migrate_root_to_lifecycle_v3": "lifecycle",
    "root.py:restore_root.grant": "lifecycle",
    "root.py:fork_corpus": "lifecycle",
    "root.py:fork_store": "lifecycle",
}

SEAM_MODULES = (
    "corpus.py",
    "boundary.py",
    "replay.py",
    "root.py",
    "holdings/boundary.py",
    "world/registry.py",
    "world/epoch.py",
    "world/rules.py",
    "world/anchors.py",
    "relocation.py",
)
READ_ONLY_ACTOR_EXCEPTIONS = frozenset(
    {"root.py:audit_log", "holdings/boundary.py:intent_payload"}
)
ACTOR_BEARING_RECORDS = frozenset(
    {
        "AdmissionRecord",
        "StatusRecord",
        "AnchorActOrigin",
        "EpochDeletionReport",
        "Occurrence",
        "OperationIntent",
        "AssessmentRunIntent",
        "ActReport",
        "RunRefused",
    }
)
EFFECTS_BEFORE_CHECK = PRIMITIVE_ATTRIBUTES | PRIMITIVE_NAMES | {
    "mkdir",
    "write_bytes",
    "write_text",
    "unlink",
    "rmdir",
    "rmtree",
    "rename",
    "symlink_to",
    "chmod",
    "touch",
    "makedirs",
    "remove",
    "copy",
    "copy2",
    "copytree",
    "move",
}
RUN_FAMILY_TRY_SHAPE = frozenset(
    {"boundary.py:execute_assessment_run", "boundary.py:execute_production_run"}
)


def modules() -> list[Path]:
    return sorted(PACKAGE.rglob("*.py"))


def relative(path: Path) -> str:
    return path.relative_to(PACKAGE).as_posix()


def parsed(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _is_primitive_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name):
        return func.id in PRIMITIVE_NAMES
    if isinstance(func, ast.Attribute):
        if func.attr in PRIMITIVE_ATTRIBUTES:
            return True
        return (
            func.attr == "add"
            and isinstance(func.value, ast.Attribute)
            and func.value.attr == "_corpus"
        )
    return False


def definitions(tree: ast.Module):
    """Return every qualified definition, including nested definitions."""
    found = []

    def walk(node: ast.AST, scope: tuple[str, ...]) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                found.append((".".join((*scope, child.name)), child))
                walk(child, (*scope, child.name))
            elif isinstance(child, ast.ClassDef):
                walk(child, (*scope, child.name))
            else:
                walk(child, scope)

    walk(tree, ())
    return found


def _own_statements(function: ast.AST):
    """Yield nodes owned by a definition, excluding nested definitions."""
    for child in ast.iter_child_nodes(function):
        if isinstance(
            child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Lambda
        ):
            continue
        yield child
        yield from _own_statements(child)


def primitive_callers(tree: ast.Module, module: str) -> set[str]:
    return {
        f"{module}:{name}"
        for name, function in definitions(tree)
        if any(_is_primitive_call(node) for node in _own_statements(function))
    }


def _require_statement(statement: ast.stmt) -> ast.Call | None:
    if (
        isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Call)
        and isinstance(statement.value.func, ast.Attribute)
        and statement.value.func.attr == "require"
    ):
        return statement.value
    return None


def _family_literal(call: ast.Call) -> str | None:
    if (
        call.args
        and isinstance(call.args[0], ast.Constant)
        and isinstance(call.args[0].value, str)
    ):
        return call.args[0].value
    return None


def _run_shape(statement: ast.stmt) -> ast.Call | None:
    if not isinstance(statement, ast.Try) or statement.orelse or statement.finalbody:
        return None
    if len(statement.body) != 1 or len(statement.handlers) != 1:
        return None
    call = _require_statement(statement.body[0])
    handler = statement.handlers[0]
    if (
        call is None
        or not isinstance(handler.type, ast.Name)
        or handler.type.id != "PermitExceeded"
        or handler.name is None
        or len(handler.body) != 1
        or not isinstance(handler.body[0], ast.Return)
    ):
        return None
    value = handler.body[0].value
    if not (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id == "RunRefused"
    ):
        return None
    return call


def _has_effect(statement: ast.stmt) -> bool:
    for node in ast.walk(statement):
        if isinstance(node, ast.Call):
            func = node.func
            name = (
                func.id
                if isinstance(func, ast.Name)
                else func.attr
                if isinstance(func, ast.Attribute)
                else None
            )
            if name in EFFECTS_BEFORE_CHECK or _is_primitive_call(node):
                return True
    return False


def requires_before_writing(
    function: ast.AST, family: str, *, run_shape: bool
) -> str | None:
    body = list(function.body)  # type: ignore[attr-defined]
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]
    for statement in body:
        call = _require_statement(statement)
        if call is None and run_shape:
            call = _run_shape(statement)
        if call is not None:
            literal = _family_literal(call)
            if literal is None:
                return "the family is not a string literal"
            if literal != family:
                return f"requires {literal!r}, inventoried as {family!r}"
            return None
        if _has_effect(statement):
            return f"an effect precedes the check: {ast.dump(statement)[:80]}"
        if any(
            _require_statement(candidate) is not None
            for candidate in ast.walk(statement)
            if isinstance(candidate, ast.stmt) and candidate is not statement
        ):
            return "the check is nested, not a top-level statement"
    return "no require statement"


def actor_parameters(tree: ast.Module, module: str) -> set[str]:
    found = set()
    for name, function in definitions(tree):
        params = function.args
        every = [*params.posonlyargs, *params.args, *params.kwonlyargs]
        if any(param.arg == "actor" for param in every):
            found.add(f"{module}:{name}")
    return found


def authority_constructions(tree: ast.Module) -> int:
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "Authority"
    )


def test_the_inventory_is_closed_in_both_directions():
    found: set[str] = set()
    defined: set[str] = set()
    for module in modules():
        tree, name = parsed(module), relative(module)
        found |= primitive_callers(tree, name)
        defined |= {f"{name}:{qualified}" for qualified, _ in definitions(tree)}
    present = {name for name in defined if name in PRIMITIVE_IMPLEMENTATIONS}
    assert present == PRIMITIVE_IMPLEMENTATIONS, (
        "implementation exclusions name definitions the tree lacks: "
        f"{sorted(PRIMITIVE_IMPLEMENTATIONS - defined)}"
    )
    callers = found - PRIMITIVE_IMPLEMENTATIONS
    assert callers == set(WRITE_ENTRY_POINTS), (
        f"uninventoried primitive callers: {sorted(callers - set(WRITE_ENTRY_POINTS))}; "
        f"inventoried definitions calling no primitive: {sorted(set(WRITE_ENTRY_POINTS) - callers)}"
    )


def test_every_entry_point_requires_before_it_writes():
    failures = []
    for module in modules():
        name = relative(module)
        for qualified, function in definitions(parsed(module)):
            key = f"{name}:{qualified}"
            if key not in WRITE_ENTRY_POINTS:
                continue
            reason = requires_before_writing(
                function,
                WRITE_ENTRY_POINTS[key],
                run_shape=key in RUN_FAMILY_TRY_SHAPE,
            )
            if reason is not None:
                failures.append(f"{key}: {reason}")
    assert failures == []


def test_the_run_shape_is_admitted_only_for_the_run_family():
    assert RUN_FAMILY_TRY_SHAPE == frozenset(
        key for key, family in WRITE_ENTRY_POINTS.items() if family == "run"
    )


def test_no_entry_point_or_public_seam_function_takes_an_actor():
    offending: set[str] = set()
    for module in modules():
        name = relative(module)
        found = actor_parameters(parsed(module), name)
        offending |= {key for key in found if key in WRITE_ENTRY_POINTS}
        if name in SEAM_MODULES:
            public = {
                key
                for key in found
                if not key.split(":")[1].split(".")[-1].startswith("_")
            }
            records = {
                key
                for key in public
                if key.split(":")[1].split(".")[0] in ACTOR_BEARING_RECORDS
            }
            offending |= public - records - READ_ONLY_ACTOR_EXCEPTIONS
    assert offending == set(), sorted(offending)
    present = set()
    for module in modules():
        present |= {
            key
            for key in actor_parameters(parsed(module), relative(module))
            if key in READ_ONLY_ACTOR_EXCEPTIONS
        }
    assert present == READ_ONLY_ACTOR_EXCEPTIONS


def test_authority_is_constructed_only_in_permit():
    definitions = {
        relative(module)
        for module in modules()
        if any(
            isinstance(node, ast.ClassDef) and node.name == "Authority"
            for node in ast.walk(parsed(module))
        )
    }
    assert definitions == {"permit.py"}
    for module in modules():
        count = authority_constructions(parsed(module))
        assert count == 0 or relative(module) == "permit.py", (
            f"{relative(module)} constructs an Authority"
        )


SATISFIED = '''
def act(ctx, node):
    ctx.authority.require("corpus-write", (node.kind,))
    with ctx.lock:
        return ctx._corpus.add(node)
'''
SATISFIED_WITH_PARSING = '''
def act(ctx, records):
    bundle = tuple(records)
    kinds = tuple(record.kind for record in bundle)
    ctx.authority.require("corpus-write", kinds)
    ctx.port.append_intent(b"x")
'''
SATISFIED_RUN = '''
def execute(port):
    try:
        port.authority.require("run", ("run", "act-report"))
    except PermitExceeded as exceeded:
        return RunRefused("permit-exceeded", None, None, None, str(exceeded))
    actor = port.authority.actor
    port.append_intent(b"x")
'''
OFFENDERS = {
    "no require": ("act", '''
def act(ctx, node):
    ctx.port.append_intent(b"x")
'''),
    "require after the append": ("act", '''
def act(ctx, node):
    ctx.port.append_intent(b"x")
    ctx.authority.require("corpus-write")
'''),
    "require under an if": ("act", '''
def act(ctx, node):
    if node is not None:
        ctx.authority.require("corpus-write")
    ctx.port.append_intent(b"x")
'''),
    "require behind flag and": ("act", '''
def act(ctx, node, flag):
    flag and ctx.authority.require("corpus-write")
    ctx.port.append_intent(b"x")
'''),
    "mkdir before the require": ("act", '''
def act(ctx, root):
    root.mkdir(parents=True, exist_ok=True)
    ctx.authority.require("lifecycle")
    register_root(root)
'''),
    "wrong family": ("act", '''
def act(ctx, node):
    ctx.authority.require("run")
    ctx.port.append_intent(b"x")
'''),
    "family not a literal": ("act", '''
def act(ctx, node, family):
    ctx.authority.require(family)
    ctx.port.append_intent(b"x")
'''),
    "try with a second statement": ("execute", '''
def execute(port):
    try:
        port.authority.require("run")
        port.append_intent(b"x")
    except PermitExceeded as exceeded:
        return RunRefused("permit-exceeded", None, None, None, str(exceeded))
'''),
    "handler without a binding": ("execute", '''
def execute(port):
    try:
        port.authority.require("run")
    except PermitExceeded:
        return RunRefused("permit-exceeded", None, None, None, "")
    port.append_intent(b"x")
'''),
    "handler does more than return": ("execute", '''
def execute(port):
    try:
        port.authority.require("run")
    except PermitExceeded as exceeded:
        port.append_intent(b"x")
        return RunRefused("permit-exceeded", None, None, None, str(exceeded))
    port.append_intent(b"x")
'''),
}


def _only_definition(source: str, name: str):
    return dict(definitions(ast.parse(source)))[name]


def test_the_satisfied_modules_pass():
    assert (
        requires_before_writing(
            _only_definition(SATISFIED, "act"), "corpus-write", run_shape=False
        )
        is None
    )
    assert (
        requires_before_writing(
            _only_definition(SATISFIED_WITH_PARSING, "act"),
            "corpus-write",
            run_shape=False,
        )
        is None
    )
    assert (
        requires_before_writing(
            _only_definition(SATISFIED_RUN, "execute"), "run", run_shape=True
        )
        is None
    )
    assert primitive_callers(ast.parse(SATISFIED), "m.py") == {"m.py:act"}


@pytest.mark.parametrize("label", sorted(OFFENDERS))
def test_each_offender_is_caught(label):
    name, source = OFFENDERS[label]
    family = (
        "run"
        if name == "execute"
        else "lifecycle"
        if "mkdir" in label
        else "corpus-write"
    )
    assert (
        requires_before_writing(
            _only_definition(source, name), family, run_shape=name == "execute"
        )
        is not None
    ), label


def test_the_run_shape_under_a_non_run_family_is_caught():
    assert (
        requires_before_writing(
            _only_definition(SATISFIED_RUN, "execute"), "run", run_shape=False
        )
        is not None
    )


def test_an_actor_parameter_is_caught_and_a_read_only_exception_must_exist():
    tree = ast.parse("def act(ctx, *, actor):\n    ctx.port.append_intent(b'x')\n")
    assert actor_parameters(tree, "m.py") == {"m.py:act"}
    assert authority_constructions(ast.parse("a = Authority(p, 'x')")) == 1
