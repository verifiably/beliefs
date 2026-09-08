"""Run `build_claim` over every proposition in a corpus. **Run by hand.**

    uv run python tools/type_corpus_claims.py <plan.yaml> <corpus-dir>

Ledger item 11. The corpus survey established that of 337 structured
propositions across eight proto-science corpora, 307 are mm30's — so the
calculus cannot be validated against the corpus it was fitted to, and the other
two corpora carrying a subject/predicate/object triple use one operator between
them. This tool is the measurement that replaces the disposition record's
hand-typing, whose own §2.1 scope rule said it must: *"the vertical slice must
replace judgment with an executable constructor before any coverage number here
is treated as a property of the system rather than of the exercise."*

Nothing here runs in CI, for the reason the survey gives: the corpora live
outside this repository and change under their own authors. The predicates that
decide an outcome are covered by `tests/test_typing_exercise.py`.

**What is fitted and what is tested** — the distinction this whole exercise
turns on, since a contract authored from a corpus types that corpus by
construction, and a number produced that way measures the author rather than the
calculus.

*Fitted, and therefore not evidence.* The operator names, their `sign_apt`
flags, and their admitted layer sets are read off the corpus's own predicate,
polarity and `claim_layer` fields. A record cannot refuse on any of them,
because the contract was written from them. Arity is fitted twice over: a
subject/object corpus has exactly arity 2 to offer.

*Fitted upstream, which is the harder case to notice.* The predecessor system
enforces the polarity/predicate partition on construction, again in a corpus
check, and again by auto-writing the sign-less value. No corpus can hold a
counterexample, so measuring that partition measures a validator. It is named
here because an earlier version of this file listed it as tested.

*Tested, because the corpus had no say in it.*

1. **Sorts.** `ArgSort(op) : Fin(arity(op)) → Sort` is one sort per slot. mm30's
   terms carry a `<kind>:` prefix but nothing constrains which kinds an operator
   relates, and `affects` is written across all four combinations of its two.
   Refusals here are the calculus meeting a corpus that never sorted.
2. **The layer vocabulary.** A domain *selects* from the base contract's four
   layers and may not extend them (§7.1). A corpus `claim_layer` value with no
   base counterpart has nowhere to go, and no contract edit can give it one.
3. **Whether a claim was recorded at all.** A constructor reads front matter. A
   claim that exists only in a title is not reachable from what the record
   states, and this is where the hand-typed figures and a measured one part.
4. **Whether a qualifier is ever recorded.** No corpus records one, and no plan
   could make it so — `dimensions: {}` throughout is a measured absence.

**Two sortings, both reported.** For a corpus whose terms carry kind prefixes,
one plan declares a single sort covering every term and another declares the
per-slot sorts each operator most often relates. The first measures whether the
rest of the calculus fits once sorts are made vacuous; the second measures what
a sorted vocabulary costs. Reporting either alone would hide the other.

**A plan never defaults.** Every corpus value it cannot map is reported as an
unmapped value against the field it came from, never silently dropped or
coerced. The two failures a typing exercise must not confuse are *the
vocabulary is incomplete* and *the calculus refused*, and a default would
convert the first into the second's absence.

**Stop rule, inherited from the disposition record's §5.5 and unchanged.** No
belief is computed and no persistence boundary is crossed. This tool reads and
prints; it writes nothing.
"""

from __future__ import annotations

import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from beliefs.claim import Referent, build_claim
from beliefs.contract import load_base_contract
from beliefs.contract.domain import parse_domain_contract
from beliefs.errors import ClaimError
from beliefs.profile import compile_profile, shipped_domain_contract

FRONTMATTER = "---"

TRIPLE = ("subject", "predicate", "object")

BASE_CONTRACT = Path(__file__).resolve().parents[2] / "contracts" / "science" / "CONTRACT.yaml"


@dataclass
class Record:
    """One proposition, and what typing it produced."""

    path: str
    outcome: str
    detail: str = ""


@dataclass
class Result:
    corpus: str
    plan: str
    propositions: int = 0
    records: list[Record] = field(default_factory=list)
    # Field values the plan could not map, by field. Kept per value rather than
    # per record: the vocabulary question is *which terms are missing*, and a
    # count of records answers a different one.
    unmapped: defaultdict[str, Counter[str]] = field(default_factory=lambda: defaultdict(Counter))

    def outcomes(self) -> Counter[str]:
        return Counter(record.outcome for record in self.records)


def read_propositions(root: Path) -> list[tuple[str, dict]]:
    """Every `kind: proposition` record under `entities/`, with its front matter.

    A parse failure raises rather than being skipped. The survey counts and names
    them because it reports shares of a denominator; here a dropped record would
    silently improve a typing yield, which is worse than a crash.
    """
    entities = root / "entities"
    if not entities.is_dir():
        raise SystemExit(f"{root} has no entities/ directory; it is not a corpus")
    found: list[tuple[str, dict]] = []
    for path in sorted(entities.rglob("*.md")):
        text = path.read_text(errors="replace")
        if not text.startswith(FRONTMATTER):
            continue
        block = text.split(FRONTMATTER, 2)
        if len(block) < 3:
            raise SystemExit(f"{path}: unterminated frontmatter")
        front = yaml.safe_load(block[1])
        if not isinstance(front, dict):
            raise SystemExit(f"{path}: frontmatter is {type(front).__name__}, not a mapping")
        if front.get("kind") == "proposition":
            found.append((str(path.relative_to(root)), front))
    return found


def sort_of(value: str) -> str | None:
    """The sort a term names by its `<kind>:` prefix, or `None` if it names none.

    A corpus term carries its sort in a prefix or does not carry one at all.
    `concept:progression-free-survival` says `concept`; `KPZ` says nothing, and
    guessing a sort for it would invent the one fact the slot needs.
    """
    head, colon, tail = value.partition(":")
    if not colon or not head or not tail:
        return None
    return head


def type_record(profile, plan: dict, front: dict, result: Result) -> Record:
    """Attempt one record, and say precisely why if it does not type.

    The order of checks is the order in which a fact goes missing, so the outcome
    names the *first* thing that was not there — a record with neither a
    predicate nor a mappable layer is reported against the triple, because until
    there is an operator there is nothing for a layer to be admitted by.
    """
    path = front.get("id", "?")
    missing = [part for part in TRIPLE if not (isinstance(front.get(part), str) and front[part].strip())]
    if missing:
        return Record(path, "no-claim-recorded", f"no {', '.join(missing)}")

    subject, predicate, obj = (front[part].strip() for part in TRIPLE)

    subject_kind, object_kind = sort_of(subject), sort_of(obj)
    for slot, (value, kind) in enumerate(((subject, subject_kind), (obj, object_kind))):
        if kind is None:
            return Record(path, "unsorted-referent", f"slot {slot}: {value!r} carries no `<kind>:` prefix")
    operator = plan["operators"].get((predicate, subject_kind, object_kind))
    if operator is None:
        operator = plan["operators"].get((predicate, None, None))
    if operator is None:
        shape = f"{predicate} {subject_kind}→{object_kind}"
        result.unmapped["shape"][shape] += 1
        return Record(path, "unmapped-shape", shape)

    raw_layer = front.get("claim_layer")
    if not isinstance(raw_layer, str) or not raw_layer.strip():
        return Record(path, "no-layer-recorded", "")
    layer = plan["layers"].get(raw_layer.strip())
    if layer is None:
        result.unmapped["claim_layer"][raw_layer.strip()] += 1
        return Record(path, "unmapped-layer", raw_layer.strip())

    # Polarity is absent-or-present rather than mapped-or-not, because a
    # sign-inapt operator takes `None` and a *missing* field is a different fact
    # from a field saying the operator has no sign to assert.
    raw_polarity = front.get("polarity")
    if raw_polarity is None:
        polarity = None
    elif not isinstance(raw_polarity, str) or raw_polarity.strip() not in plan["polarities"]:
        result.unmapped["polarity"][str(raw_polarity)] += 1
        return Record(path, "unmapped-polarity", str(raw_polarity))
    else:
        polarity = plan["polarities"][raw_polarity.strip()]

    args = []
    for value, local in ((subject, subject_kind), (obj, object_kind)):
        assert local is not None
        sort = plan["sorts"].get(local)
        if sort is None:
            result.unmapped["sort"][local] += 1
            return Record(path, "unmapped-sort", local)
        args.append(Referent(sort=sort, term=value))

    try:
        build_claim(profile, operator=operator, args=tuple(args), layer=layer, polarity=polarity)
    except ClaimError as exc:
        return Record(path, f"refused-{type(exc).__name__}", str(exc).split(".")[0])
    return Record(path, "typed", operator)


def run(plan_path: Path, corpus: Path) -> Result:
    text = plan_path.read_text(encoding="utf-8")
    if "{{CONCEPTS}}" in text:
        from reproduction import vocabulary

        document = vocabulary._document(plan_path)
    else:
        document = yaml.safe_load(text)
    base = load_base_contract(BASE_CONTRACT)
    contract = parse_domain_contract(document["contract"], source=f"{plan_path}: contract", base=base, predecessor=None)
    profile = compile_profile(base, [*(shipped_domain_contract(name) for name in document.get("also", [])), contract])

    plan = document["plan"]
    # Local names are namespaced here, once, so the plan file stays readable and
    # the term identifiers a claim actually carries are still what reaches
    # `build_claim`. A plan naming term identifiers directly would repeat the
    # contract's namespace on every line and drift from it silently.
    def term(name: str) -> str:
        return name if "/" in name else contract.term(name)

    raw_operators = plan.get("operators") or {}
    if isinstance(raw_operators, dict):
        rows = {(predicate, None, None): term(name) for predicate, name in raw_operators.items()}
    else:
        rows = {(row["predicate"], row["subject"], row["object"]): term(row["operator"]) for row in raw_operators}
    resolved = {
        "operators": rows,
        "sorts": {k: term(v) for k, v in (plan.get("sorts") or {}).items()},
        "layers": dict(plan.get("layers") or {}),
        "polarities": dict(plan.get("polarities") or {}),
    }

    result = Result(corpus=corpus.name, plan=plan_path.stem)
    for path, front in read_propositions(corpus):
        result.propositions += 1
        record = type_record(profile, resolved, front, result)
        record.path = path
        result.records.append(record)
    return result


def report(result: Result) -> None:
    outcomes = result.outcomes()
    typed = outcomes.get("typed", 0)
    total = result.propositions

    print(f"# {result.corpus} — typing exercise ({result.plan})\n")
    print(f"{total} proposition record(s); **{typed} typed**.\n")

    print("| outcome | n | share |")
    print("|---|---|---|")
    for outcome, n in outcomes.most_common():
        print(f"| `{outcome}` | {n} | {n / total:.0%} |" if total else f"| `{outcome}` | {n} | — |")

    if result.unmapped:
        print("\n## Values the plan does not map\n")
        print("Vocabulary work, not a refusal by the calculus — the two are never merged.\n")
        for field_name, values in sorted(result.unmapped.items()):
            named = ", ".join(f"`{v}` x{n}" for v, n in values.most_common())
            print(f"- **{field_name}**: {named}")

    refusals = [r for r in result.records if r.outcome.startswith("refused-")]
    if refusals:
        print("\n## Refusals, by record\n")
        for record in refusals[:20]:
            print(f"- `{record.path}` — {record.outcome}: {record.detail}")
        if len(refusals) > 20:
            print(f"- …and {len(refusals) - 20} more")

    by_operator = Counter(r.detail for r in result.records if r.outcome == "typed")
    if by_operator:
        print("\n## Typed, by operator\n")
        for operator, n in by_operator.most_common():
            print(f"- `{operator}` {n}")


USAGE = "usage: type_corpus_claims.py <plan.yaml> <corpus-dir>"

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(USAGE)
    report(run(Path(sys.argv[1]).expanduser(), Path(sys.argv[2]).expanduser()))
