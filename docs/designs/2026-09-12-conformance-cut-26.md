# Conformance cut 26 — D1's cross-repository negative

**Status:** frozen and discharged 2026-09-12. D1 is closed.
**Design:** `../superpowers/specs/2026-09-12-d1-cross-repository-negative-design.md`, reviewed in two passes 2026-09-12.
**Numbered after and serialized after** cut 25, whose discharge is in the branch ancestry.
**`nodes` gate:** `nodes` commit `d8ecf664c85b7d17488de9f8884e5ba5b302c821` (STANDARD §2.3 opacity sentence; seam §8 row).

## 1. What this cut is

D1 says `nodes` assigns no domain semantics. Cut 20 read its inspection arm and
deferred the negative; cut 22 deferred it again. Both deferrals named the same
obstacle — the negative runs in another repository's tree — and neither named the
prior one: no check would refuse a `nodes` path that branches on `biology/`,
because signature inspection cannot see a branch on a string and a grep for
domain names fails a conforming tree.

This cut reads D1 in full. The design states opacity as an invariance: every
public `nodes` operation commutes with a bijective renaming of namespace tokens
that leaves the built-in facet names alone, over registries whose invariants are
the kernel's own. A portable Beliefs test asserts it over the installed package.
N2 gains a sabotage that names its package, copies `nodes`, applies a domain-aware
mutation to the copy, and proves the check fails there.

The selection rule is cut 5's: a clause is selected only when its source mutation
and every named check run inside §2. A row with any unrun arm is partial.

## 2. The boundary

In scope:

- `python/tests/test_domain_boundary.py`: the invariance check,
  `test_d1_installed_nodes_is_invariant_under_namespace_renaming`, over
  `nodes.core.frontmatter`, `projection`, `registry`, `corpus` and `write_plan`,
  with a registry holding only the built-in shapes' invariants, two renamings
  (`biology` → `aaa`, `biology` → `zzz`), and fixtures that make the
  missing-facet, unexpected-facet and raising cases non-empty.
- `python/tests/n2_arms.py`, `test_n2.py`, `arm_staleness.py`: `Sabotage.package`
  (`"beliefs"` default, `"nodes"`); the package root resolved from the
  interpreter; the copy, the mutation and the subprocess `PYTHONPATH` per package;
  `working_tree` reading a `nodes` arm from the resolved tree; one `PORTABLE_ARMS`
  tuple feeding the sabotage audit, the unsabotaged baseline and the staleness gate.
- `python/tests/n2_arms_cut26.py`: one declaration unit, D1, two arms — the
  parser sabotage and the validation sabotage — each naming the one check above;
  cut 20's inspection check co-cited.
- `python/tests/acceptance/test_n2_cut26.py` and `python/tools/cut26_acceptance.py`.
- The `nodes` repository: STANDARD §2.3's opacity sentence and the seam §8 row,
  at `d8ecf664c85b7d17488de9f8884e5ba5b302c821`. No `nodes` code.

Out of scope: any domain-aware path in the `nodes` tree; `nodes`' own suite;
extending N2's commit-pinned (`historical_tree`) staleness reading to `nodes`;
every D row other than D1. Frozen declarations and cut bodies through cut 25
remain byte-exact.

## 3. Selection

### D1 — closes

```markdown
| D1 | `nodes` assigns no domain semantics | assert `nodes` ships **no domain contract, schema, validator, or vocabulary adapter**, and that **no `nodes` API accepts** a domain, contract, or vocabulary argument; assert every domain-flavoured string in the `nodes` tree is **opaque** — its normative fixtures already carry `bio-axes` and `HGNC:7296` (`fixtures/gene_phf19.*`) purely as example payload the kernel never interprets, and that is **conforming, not a violation**; **negative:** add a `nodes` code path that reads a facet key's namespace and behaves differently for `biology/` → refused, since assigning meaning to a namespace is exactly what this row forbids. A grep for domain *names* is **not** the test and would fail against a conforming tree |
```

**Selected:** the inspection arm cut 20 selected, re-cited
(`acceptance/test_facet_acceptance.py::test_d1_installed_nodes_takes_no_domain_argument`,
unchanged); the opacity clause, as the invariance check; the negative, as two N2
arms whose sabotage lands in a copy of `nodes`:

- **D1-a** — `core/frontmatter.py`, `node_from_markdown`'s facets read, drops
  every facet whose name starts with `biology/`. Unrenamed, the gene-axis facet
  disappears at parse; renamed, it survives. Clause 1 fails.
- **D1-b** — `core/registry.py`, `validate`'s present set excludes `biology/`
  names. A required `biology/gene-axis` reads as missing unrenamed and present
  renamed. Clause 3 fails.

**Deferred:** nothing. The grep clause is honoured by its own terms: the check
never reads a name's content, so `nodes`' fixtures carrying `biology/gene-axis`
pass it.

### Boundary invariants

No verdict changes for any Beliefs record. No claim identity changes. The
installed `nodes` tree is byte-identical before and after every N2 run.

## 4. Accounting

One guarantee row is read, **1 full/closed** (D1). The frozen inventory is
**1 declaration unit** expanding to 2 one-mutation sabotage arms. The global
corpus moves to **148 of 195 rows closed, 47 open**. `domain-boundary` closes.

## 5. N2 and acceptance obligations

Every arm's `before` block occurs exactly once in the resolved `nodes` tree at
`d8ecf664c85b7d17488de9f8884e5ba5b302c821`; `test_n2.py` audits both arms at every serial run, and
`test_n2_cut26.py` audits them at the discharge. Both directions: the check
passes against the real package (`baseline`) and fails under each sabotage
(`audit`). The harness self-tests prove a `nodes` sabotage that does not apply
scores `stale`, the copy is mutated and the source is not, and the copy shadows
the installed package in the subprocess.

The runner `python/tools/cut26_acceptance.py` chains `PREFIX_RUNNERS = ("cut25_acceptance.py",)` and runs `test_n2_cut26.py`.

## 6. Second reader

Verify the fenced row byte-exact against its source table at the freeze commit;
audit every selected clause against §2; force any unrun clause to remain
deferred and its row partial. Challenge especially:

- the registry the check builds carries no consumer invariant, so a legitimate
  domain semantic cannot be mistaken for a kernel one;
- violation lists compare after renaming and re-sorting, over non-empty cases;
- each sabotage applies exactly once and the check fails under each on its own;
- the `nodes` tree is unchanged after the audit;
- STANDARD §2.3's sentence is in the `nodes` tree at the cited commit.

## 7. Limitations

- The invariance is read over `nodes.core`'s public surface named in §2; a
  domain-aware path in a surface the check does not exercise (search, similarity)
  would not be refused. Those surfaces read titles and bodies, not facet names,
  today; the limitation is stated rather than closed.
- `historical_tree` does not read `nodes`, so a commit-pinned guard cannot audit
  a `nodes` arm against a historical `nodes` tree. Cut 26 audits the working tree.
