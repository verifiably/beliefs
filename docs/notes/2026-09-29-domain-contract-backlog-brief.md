# Domain-contract backlog brief — 2026-09-29

## Problem

Four domain ideas ask when to extend the contract and where to enforce it:
lineage-inherited empirical standing (`beliefs-8ecbb5`), declared relation
endpoints (`beliefs-e803cc`), a time-series dataset facet (`beliefs-f484a7`),
and shipped-pack succession (`beliefs-dc42bf`). Keep extensions tied to an
observed consumer while making the endpoint-policy decision answerable.
Goal: `beliefs-d58675`. This is a scoping handoff, not an approved design.

## Current behaviour and evidence

Evidence was read in the main checkout at `90cf0ca`; no runtime probe was run.

- The completed `beliefs-18b03d` worked example and
  `docs/designs/2026-09-12-estimand-typing-design.md` Appendix A.3 place
  surrogates in run output bytes, not held datasets. The pilot therefore does
  not reach lineage-inherited standing. Its API checks landed in `5774dcd`
  and `1e07c61` (`python/tests/test_estimand_natural_systems.py`); these test
  estimand construction, not a complete pilot execution.
- `python/src/beliefs/profile.py` compiles base relation declarations.
  `corpus.py` has specific checks for `assesses` target kind, composite
  members, and `supersedes` same-kind; `audit.py` contains corresponding
  specialized checks. No general sources/targets validator was found on the
  shared refusal path. Frozen composite-claims limitation 17 and the guide
  describe the general gap; their summary is not a complete current inventory.
- `domains/biology/DOMAIN.yaml` supplies a dataset `gene-axis` facet, the
  proposed time-series facet's analogy. The local pilot fixture declares a
  claim vocabulary, not a time-series facet reader. The external framing and
  `ns-437ab5` registration were not read in this fixed-checkout pass, so
  their present findings and pack-home decision remain unknown.
- `profile.shipped_domain_contract` still supplies `predecessor=None`;
  `contract/domain.py:check_succession` refuses a successor without its
  predecessor. Composite-claims limitation 18 remains applicable. Existing
  alternatives already validate explicit predecessor chains:
  `python/tools/reproduction/vocabulary.py` loads mm30's frozen predecessors,
  and `profile._shipped_coordination` loads shipped v1 before v2 (`a312745`).
  `python/tests/test_shipped_biology.py` covers the current packaged genesis.

## Constraints

The adoption ledger and roadmap remain authoritative; this pass adds no
implementation lane. Preserve acquisition-only standing, contract identities,
frozen evidence, and the domain boundary. A domain cannot add base relation
signatures. The existing contract-cut task `beliefs-eacbe2` owns the eventual
contract decisions; the distribution idea `beliefs-abf8e8` requires an observed
second consumer. Neither is rewritten here. Open tasks and existing handoffs
were searched; no overlapping open endpoint-inventory research was found.

## Alternatives

1. **Keep current behavior pending measured need.** Recommended for lineage,
   the time-series facet, and pack succession; their concrete wake conditions
   are recorded below. The pilot already fits the existing model.
2. **Put a general endpoint check at the compiled-profile/shared corpus seam.**
   Current lean if the inventory supports it: declarations and specialized
   refusals already meet there. First settle target resolution, import-order
   behavior and audit correspondence; this is not an implementation decision.
3. **Enforce endpoints in the substrate or a later registry boundary.** The
   guide names these alternatives. They require evidence that the boundary has
   the necessary contract and resolution context; do not create another layer
   merely to hold the check.

## Unanswered questions

- Which signatures and entry routes actually enforce endpoints, and what do
  missing or cross-corpus targets do? `beliefs-9c375c` will inventory and probe
  them; contract-cut design review owns any subsequent policy choice.
- Does a consumer need held derived datasets to carry observation standing?
  Its worked workflow must demonstrate this; the current surrogate example does not.
- Does a real dataset reader need time axis, interval and units as a facet,
  and where does the pack belong? A worked consumer example and the external
  registration owner must supply the evidence before `beliefs-f484a7` wakes.
- Which shipped declaration needs a successor? Once one exists, its pack owner
  and design review can choose explicit predecessor files or a manifest; the
  current mm30 case already uses corpus-local succession.

## Proposed decomposition

- `beliefs-9c375c` — P3, small, mid complexity, direct: inventory endpoint checks
  and record two representative probes, with a policy recommendation. Its
  completion must add a finding note to `beliefs-e803cc` in the same commit.
- `beliefs-e803cc` — briefed, remains an idea awaiting that evidence. No
  implementation task or extra design task is filed before the inventory.
- `beliefs-8ecbb5` — shelved until a workflow requires standing for a held
  derived dataset or reusable surrogate bank.
- `beliefs-f484a7` — shelved until a worked reader requires the facet and
  `ns-437ab5` establishes the pack owner and home.
- `beliefs-dc42bf` — shelved until a concrete shipped-pack successor declaration
  is required; then design a chain preserving existing content identities.

All four members retain their original bodies and sources under `beliefs-d58675`;
endpoint scoping context is appended to its body. `beliefs-7c98bc` (stored kernel
edges) was read as related context and remains untouched: it needs its own
consumer measurement, not automatic inclusion in endpoint enforcement.
