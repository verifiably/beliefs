# D1's cross-repository negative — design

**Status:** draft 2026-09-12, awaiting review. Task: beliefs-928881. Cut: 26, to be
frozen after this design clears.
**Sources:** `../../designs/2026-08-04-domain-extension-boundary-design.md` row D1;
`../../plans/2026-09-08-conformance-cut-22-results.md` §2 and §5;
`../../plans/2026-08-29-implementation-roadmap.md` `domain-boundary`.

## 1. Problem

D1 says `nodes` assigns no domain semantics. Cut 20 selected the row's inspection arm —
no `nodes` API among `Registry.register`, `KindSpec` and `ShapeSpec` takes a `domain`,
`contract` or `vocabulary` argument — and deferred the negative twice (cuts 20 and 22)
with the same reason: "add a `nodes` code path that reads a facet key's namespace and
behaves differently for `biology/` → refused" runs in another repository's tree. It is
the last open clause of `domain-boundary`.

Two things are missing, and the first is the one the deferrals hid. **There is no check
that would refuse such a path.** Signature inspection cannot see a branch on a string;
a grep for domain names is ruled out by the row itself, because `nodes`' own fixtures
carry `biology/gene-axis` and `HGNC:7296` as opaque payload and a conforming tree would
fail it. So the negative has nothing to be refused *by*, and before a harness can mutate
`nodes` there has to be a behavioural check that a domain-aware path breaks. The second
missing piece is the harness: N2 copies `python/src/beliefs`, applies a sabotage there,
and runs the checks in a subprocess with the copy first on `PYTHONPATH`; it has no notion
of a sabotage that lands in a package from another repository.

## 2. Decisions

- **The check is an invariance, not an inspection.** `nodes` assigns no domain semantics
  iff its behaviour does not depend on what a namespaced facet name says. Stated as a
  property: for every bijective renaming ρ of namespace tokens that avoids `nodes`' own
  built-in facet names, every public `nodes` operation commutes with ρ. A code path that
  branches on `biology/` is exactly a failure of this commutation, and nothing in a
  conforming tree fails it. Rejected: an AST scan of `nodes` for string comparisons
  against facet keys — it names the mechanism rather than the property, misses a table
  lookup or a regex, and would flag `nodes`' legitimate handling of its built-in names.
- **The positive check lives in Beliefs, over the installed `nodes`.** D1 is Science's
  guarantee about its dependency; the check that discharges it is Science's, run against
  whatever `nodes` the environment resolves — locally the sibling editable checkout, in CI
  the default branch. Rejected: a `nodes`-side test — it would be `nodes` attesting to
  itself, and the row calls for the *independent* conformance check.
- **The negative is an N2 arm whose sabotage lands in `nodes`.** N2's method is the
  right one — copy, mutate, run each check as one test function in a subprocess, score
  sound/vacuous/mixed/uncollected/stale — and it extends by one field: a sabotage names
  its package. Rejected: a separate harness for cross-repository arms; it would re-derive
  N2's five findings and its aggregation guard, and the first version of N2 is the record
  of how those get got wrong.
- **`nodes` commits to the property in its standard and adds no code.** The `nodes`-local
  gate the task names is an amendment to STANDARD §2.3 stating that facet names outside
  the built-in set are opaque to the kernel, plus a row in the write-plan seam's §8
  amendment record citing this harness. The Beliefs harness mutates a *copy* of the
  package; the `nodes` tree gains no domain-aware path, production or test. Rejected:
  landing the sabotage as a `nodes` test fixture — it would put the forbidden path in
  the forbidden tree.
- **The `nodes` checkout is read, never written.** The harness resolves the package from
  the interpreter (`importlib.util.find_spec("nodes.core")`), copies it, and mutates the
  copy. Staleness for a `nodes` arm is read from that same resolved tree. No path to a
  sibling checkout is hard-coded; CI's layout and the local layout both resolve.

## 3. The property

Let B be `nodes`' built-in facet names — today `membership`, `edges`, `order`, `keys`
(STANDARD §5) — and let a *namespaced* name be one matching `^[^/]+/[^/]+$`. A renaming
ρ is a bijection on namespace tokens; ρ(node) renames every namespaced facet name's
token in `facets`, and ρ(spec) does the same in a `KindSpec`'s and `ShapeSpec`'s
`required_facets` and `optional_facets`. Because a namespaced name contains `/` and no
built-in name does, ρ never touches B.

`nodes` **assigns no domain semantics** iff, for every ρ:

1. `node_from_markdown(node_to_markdown(ρ(n))) == ρ(node_from_markdown(node_to_markdown(n)))`
   and `node_from_bytes` agrees — the boundary parser and serializer commute with ρ.
2. `to_canonical(ρ(n)) == ρ(to_canonical(n))` as structures — the canonical projection
   commutes with ρ. (Canonical *bytes* are not compared: key order under ρ may change,
   and that is the projection sorting, not interpreting.)
3. `Registry.validate` raises on `(ρ(spec), ρ(n))` iff it raises on `(spec, n)`, with the
   same error class, and `Registry.check` returns ρ-equal violations.
4. A corpus written with a plan of `ρ(n)` and reopened yields `ρ` of what the same plan of
   `n` yields, through `get`, `all` and the structural index.

The positive check asserts 1–4 over: the biology pack's gene-axis fixture
(`fixtures/gene_phf19.*` in `nodes`, `biology/gene-axis` in Beliefs), a node carrying a
built-in facet beside a namespaced one, and two renamings — one that sorts the renamed
token before every other key and one after — so that ordering effects are exercised
rather than assumed away.

## 4. Components

### 4.1 The positive check — `python/tests/acceptance/test_facet_acceptance.py`

`test_d1_installed_nodes_is_invariant_under_namespace_renaming`, beside cut 20's
`test_d1_installed_nodes_takes_no_domain_argument`. One test function, parametrized over
the renamings; N2 names it as a check. It imports only `nodes.core`'s public surface —
`frontmatter`, `projection`, `registry`, `corpus`, `write_plan` — and builds its own
registry, so it does not depend on a Beliefs profile. Helpers `_rename_node` and
`_rename_spec` implement ρ. The test passes on a conforming `nodes` and is expected to
pass on every `nodes` that keeps STANDARD §2.3's amended sentence; it is not a test of
Beliefs.

### 4.2 The harness — `python/tests/n2_arms.py`, `test_n2.py`, `arm_staleness.py`

`Sabotage` gains `package: str = "beliefs"`; the only other value is `"nodes"`. The
`module` field stays a path under the package root — for `nodes`, under `src/nodes`, so
`core/frontmatter.py`.

`test_n2` resolves each package root once: Beliefs as today; `nodes` from
`importlib.util.find_spec("nodes.core").submodule_search_locations[0]`'s parent, which is
the `src/nodes` directory of whatever checkout the interpreter installed. `_sabotage`
copies the arm's package root and applies the mutation to the copy. `_run_check` puts the
copy's parent first on `PYTHONPATH` for either package — `nodes` is a namespace package,
so the copy's `nodes/core` shadows the installed one and everything else still resolves.
The subprocess's `PYTHONPATH` therefore holds at most one scratch directory; a sabotage
is in one package or the other.

`arm_staleness.working_tree` takes the package into account the same way: a `nodes`
arm's `before` block is counted in the resolved `nodes` tree. `historical_tree` — reading
a Beliefs commit — is not extended: a `nodes` sabotage has no Beliefs commit to read
from, and the guard's `CUTN_SOURCE_COMMIT` mechanism stays Beliefs-only. A cut carrying a
`nodes` arm records, in its results, the `nodes` commit the discharge resolved; that is
the arm's pin, human-read, and §4.5 says where it goes.

Two harness self-tests, in `test_n2.py` beside the existing ones: a `nodes` sabotage
whose `before` does not occur scores `stale`, and after a `nodes` arm runs, the resolved
`nodes` tree is byte-identical to before (the copy was mutated, never the source).

### 4.3 The negative arm — cut 26's declaration file

Two sabotages, each a domain-aware path, each an exact `before` block that occurs once:

- `core/frontmatter.py`, at `node_from_markdown`'s facets read: drop every facet whose
  name starts with `biology/`. Under ρ the `biology/` facet is renamed away and survives;
  unrenamed it is dropped — clause 1 fails, and clause 4 fails through the boundary.
- `core/registry.py`, at `validate`'s `present = set(node.facets)`: exclude `biology/`
  names from `present`. A required `biology/` facet reads as missing unrenamed and as
  present under ρ — clause 3 fails.

Each arm names the one check in §4.1. Both must score `sound`: the check passes against
the real package and fails under each sabotage. The exact `before`/`after` text is fixed
at the cut freeze against the `nodes` commit then resolved, and the results record that
commit.

### 4.4 The `nodes`-local gate — in the `nodes` repository

- STANDARD §2.3 gains one sentence: facet names outside the built-in set (§5) are opaque
  to the kernel — no kernel behaviour depends on a name's content beyond equality and
  ordering, and in particular no namespace token selects a code path. This is a
  statement of what is already true, versioned so that it is a guarantee.
- The write-plan executor seam's §8 amendment record gains a row: Science's D1 negative
  mutates a scratch copy of the installed package under Beliefs' N2 harness; the `nodes`
  tree gains nothing; the property it checks is the §2.3 sentence. `nodes`-side review
  only — no consumer-exercised path changes.
- One `nodes` task carries both edits; Beliefs' cut 26 depends on it and cites the
  `nodes` commit.

No `nodes` code changes. The gate is the owner's approval of the two edits above; this
design is the request.

### 4.5 Cut 26 — `docs/designs/2026-09-12-conformance-cut-26.md`

Reads D1 in full: the cut 20 inspection arm re-cited, the §4.1 check selected, the §4.3
negative selected. One declaration unit, two sabotage arms. Discharged on the required
tuple through the serial gate; the results document records the `nodes` commit, the N2
verdicts, and the ledger and roadmap rows moving `domain-boundary` to closed. Frozen
declarations and cut bodies through cut 25 stay byte-exact.

## 5. Testing the tooling

- The harness self-tests in §4.2.
- Under the fast loop, N2 is excluded as today; the §4.1 check runs there and in CI on
  every push, so a `nodes` regression against §2.3 surfaces on the next Beliefs run
  rather than at a discharge.
- In CI, `nodes` is checked out at its default branch, so the negative runs there too;
  a `stale` verdict on a `nodes` arm is CI saying `nodes` moved under the frozen
  sabotage, which is the finding the arm exists to make visible.

## 6. Sequencing

1. This design reviewed.
2. The `nodes` task lands STANDARD §2.3 and the seam row; its commit is recorded.
3. Cut 26 design written and frozen, with the sabotage text fixed against that commit.
4. §4.1 check (red against a sabotaged copy by hand, green against the tree), then the
   §4.2 harness with its self-tests, then the §4.3 declaration file and live guard.
5. Serial gate on the required tuple; results document; ledger and roadmap; task done.

## 7. Out of scope

- Any domain-aware path in `nodes`, production or test.
- `nodes`' own test suite; the check runs from Beliefs.
- Extending N2's historical (commit-pinned) staleness reading to `nodes`.
- Reading any D-row other than D1; `domain-boundary`'s other rows are closed at cuts 20
  and 22.
