"""F5: effect guards precede effects under their owner lock, including inherited locks."""

import ast
from pathlib import Path
from typing import TypeGuard

import beliefs

# Inspect the imported package so a sabotaged package copy is actually judged.
SRC = Path(beliefs.__file__).resolve().parent
MODULES = ("corpus.py", "relocation.py", "root.py", "holdings/boundary.py")
EFFECTS = {"_settle", "recover", "add", "execute", "_execute", "_execute_fulfilling", "execute_fulfilling", "execute_fulfilling_guarded", "append_intent", "publish_fulfilling", "_store_append_intent", "_store_publish_fulfilling"}
HELPERS = {
    "commit_fulfilling",
    "_add_locked",
    "_replace_locked",
    "_delete_locked",
    "_revise_dataset_locked",
    "_append_operation_intent",
    "_publish_operation_report",
}
GUARDS = {"_require_pins_agree", "require_pins_agree"}
# These methods inherit the root lock; every production caller is checked below.
INHERITED = {("corpus.py", name) for name in HELPERS} | {("root.py", "_execute"), ("root.py", "_execute_fulfilling")}
# Set insertion has no corpus effect. Keep receiver names explicit.
READ_ONLY = {"finding_reasons", "findings", "seen_ids", "seen_uids", "seen_paths", "seen_deprecated_ids"}
# Generic executor/lifecycle primitives have no profile. The holdings primitive is
# only wired through the seam whose policy boundary is checked separately below.
PRIMITIVES = {("root.py", "init_world_root"), ("root.py", "_store_publish_fulfilling"), ("root.py", "_store_append_intent")}


def name(call):
    return getattr(call.func, "attr", getattr(call.func, "id", ""))


def calls(node):
    return [item for item in ast.walk(node) if isinstance(item, ast.Call)]


def is_effect(call):
    if name(call) not in EFFECTS | HELPERS:
        return False
    return not (isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name) and call.func.value.id in READ_ONLY)


def lock_scope(node: ast.AST) -> TypeGuard[ast.With]:
    return isinstance(node, ast.With) and any(
        (isinstance(item.context_expr, ast.Attribute) and item.context_expr.attr == "_operation")
        or (isinstance(item.context_expr, ast.Call) and name(item.context_expr) in {"_both_locks", "_operation_lock_for", "corpus_lock"})
        for item in node.items
    )


def first_guards(body):
    result = []
    for statement in body:
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant):
            continue  # A docstring is not an effect.
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call) and name(statement.value) in GUARDS:
            result.append(statement.value)
        else:
            break
    return result


def violations(module, tree):
    failures = []
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    for fn in [item for item in ast.walk(tree) if isinstance(item, ast.FunctionDef)]:
        effects = [call for call in calls(fn) if is_effect(call)]
        if not effects:
            continue
        key = module, fn.name
        parent = parents[fn]
        if module == "corpus.py" and isinstance(parent, ast.ClassDef):
            if parent.name == "_SettlingHold" and fn.name == "__enter__":
                # Context entry is effectful: the raw lock and pin guard must
                # dominate settlement, including entry through _both_locks.
                guarded = next((node for node in fn.body if isinstance(node, ast.Try)), None)
                if (ast.unparse(fn.body[0]) != "self._lock.__enter__()"
                        or guarded is None or not first_guards(guarded.body)
                        or any(call not in calls(guarded) for call in effects)
                        or any(call.lineno <= first_guards(guarded.body)[-1].lineno for call in effects)):
                    failures.append("corpus.py:__enter__: recovery lacks prior check under raw lock")
                continue
            if parent.name == "CorpusWriter" and fn.name == "_settle":
                # The only caller is the checked context entry. Recovery can
                # change pins; its result must be checked before rebuilding or
                # claiming settlement. This route has no independent raw lock.
                guards = [call for call in calls(fn) if name(call) in GUARDS]
                reconstruct = [call for call in calls(fn) if name(call) == "_reconstruct"]
                clears = [node for node in ast.walk(fn) if isinstance(node, ast.Assign)
                          and any(ast.unparse(target) == "state.unresolved" for target in node.targets)]
                if (len(guards) != 1 or len(reconstruct) != 1 or len(clears) != 1
                        or not all(call.lineno < guards[0].lineno < reconstruct[0].lineno < clears[0].lineno for call in effects)):
                    failures.append("corpus.py:_settle: recovery result cleared without a post-recovery pin check")
                continue
        # DurableOperationPort.execute is policy, DurableExecutor.execute is the primitive.
        if isinstance(parent, ast.ClassDef) and module == "corpus.py":
            if parent.name == "_RoutedExecutor" and fn.name == "execute":
                # Executor primitive: callers are guarded; fulfilling publication is checked separately.
                assert any(name(call) == "commit_fulfilling" for call in calls(fn))
                continue
            if parent.name == "OperationWrites" and fn.name == "add":
                assert ast.unparse(fn.body[-1]) == "return self._run(lambda: self._writer.add(node))"
                continue
        if key in PRIMITIVES or (module == "root.py" and fn.name == "execute" and isinstance(parent, ast.ClassDef) and parent.name == "DurableExecutor"):
            continue
        if key in INHERITED:
            if not first_guards(fn.body):
                failures.append(f"{module}:{fn.name}: inherited lock lacks first pin check")
            continue
        for effect in effects:
            ancestor = parents[effect]
            while ancestor is not fn and not lock_scope(ancestor):
                ancestor = parents[ancestor]
            guards = first_guards(ancestor.body) if lock_scope(ancestor) else []
            if not guards or any(guard.lineno >= effect.lineno for guard in guards):
                failures.append(f"{module}:{fn.name}:{effect.lineno}: effect lacks prior check under lock")
            if module == "relocation.py" and guards:
                assert isinstance(ancestor, ast.With)
                lock = ancestor.items[0].context_expr
                assert isinstance(lock, ast.Call)
                if {ast.unparse(g.func.value) for g in guards} != {ast.unparse(arg) for arg in lock.args}:
                    failures.append(f"{module}:{fn.name}: both locked writers must recheck")
    return failures


def test_every_effect_and_inherited_lock_route_rechecks_before_effects():
    failures = []
    for module in MODULES:
        failures.extend(violations(module, ast.parse((SRC / module).read_text())))
    assert failures == [], "\n".join(failures)


def test_holdings_uses_one_guarded_intent_and_publication_route_and_the_shared_lock():
    tree = ast.parse((SRC / "holdings/boundary.py").read_text())
    sites = {method: [] for method in ("append_intent", "publish_fulfilling")}
    for fn in tree.body:
        if isinstance(fn, ast.FunctionDef):
            for call in calls(fn):
                if name(call) in sites:
                    sites[name(call)].append(fn.name)
    assert sites == {"append_intent": ["_append"], "publish_fulfilling": ["_publish_record"]}
    root = ast.parse((SRC / "root.py").read_text())
    seam = next(call for call in calls(root) if name(call) == "StoreActSeam")
    assert {key.arg: ast.unparse(key.value) for key in seam.keywords if key.arg in {"corpus_lock", "append_intent", "publish_fulfilling"}} == {
        "corpus_lock": "_holdings_corpus_lock", "append_intent": "_store_append_intent", "publish_fulfilling": "_store_publish_fulfilling",
    }
    adapter = next(fn for fn in root.body if isinstance(fn, ast.FunctionDef) and fn.name == "_holdings_corpus_lock")
    assert any(lock_scope(node) and ast.unparse(node.items[0].context_expr) == "_operation_lock_for(root)" for node in ast.walk(adapter))


def test_inventory_detects_late_checks_and_missing_lock_ownership():
    valid = "def add(self, node):\n    with self._operation:\n        self._require_pins_agree()\n        self._corpus.add(node)\n"
    assert violations("corpus.py", ast.parse(valid)) == []
    late = valid.replace("        self._require_pins_agree()\n", "") + "        self._require_pins_agree()\n"
    assert violations("corpus.py", ast.parse(late))
    unlocked = valid.replace("    with self._operation:\n", "").replace("        ", "    ")
    assert violations("corpus.py", ast.parse(unlocked))


def test_local_finding_aggregation_is_not_a_corpus_effect():
    assert violations("corpus.py", ast.parse("def check():\n    finding_reasons = bearer_or_retrieval.setdefault(key, set())\n    finding_reasons.add(reason)\n")) == []
    assert violations("corpus.py", ast.parse("def add():\n    self._corpus.add(node)\n"))



def test_context_entry_and_recovery_are_in_the_effect_inventory():
    source = (SRC / "corpus.py").read_text()
    tree = ast.parse(source)
    settlement_sites = [call for call in calls(tree) if name(call) == "_settle"]
    assert len(settlement_sites) == 1  # __enter__ owns all settlement.
    assert is_effect(settlement_sites[0])
    assert violations("corpus.py", tree) == []
    for before, after in (
        ("            self._writer._require_pins_agree()\n", ""),
        ("        self._lock.__enter__()\n", "        pass\n"),
        ("        self._require_pins_agree()\n        self._reconstruct()", "        self._reconstruct()"),
    ):
        assert before in source
        assert violations("corpus.py", ast.parse(source.replace(before, after)))
    assert violations("corpus.py", ast.parse("def unguarded(writer):\n    writer._settle()\n"))
    root = ast.parse((SRC / "root.py").read_text())
    factory = next(node for node in root.body if isinstance(node, ast.ClassDef) and node.name == "_DurableExecutorFactory")
    recover = next(node for node in factory.body if isinstance(node, ast.FunctionDef) and node.name == "recover")
    assert any(name(call) == "read_chain" for call in calls(recover))
