# Conformance cut 20 — discharge results

**Date:** 2026-09-07
**Subject:** facet contracts (`../designs/2026-09-05-facet-contracts-design.md`),
measured against the whole frozen cut at `5fa48a6`
(`../designs/2026-09-05-conformance-cut-20.md`).

Cut 20 froze on 2026-09-06. Its entire file, including the historical status
header, remains byte-identical with SHA-256
`3bf154b032c696c1b62954936262ff14137b1af055cc887c49fc0aa60b70cac5`.
The original implementation and acceptance work is the final Task 15 commit
`d5e203c1bb2f03a89a7c10c96625589d03074717`, whose parents are the lane tip
`6f9756f` and the actual merged-main tip `4f1b15a`. Later main commits through
`f29cabc`, including CI and hook changes, are outside this merge.

## Result

The certified aggregate passed the full prefix cut 17 → 18 → 19, followed by
cut 20's final phases. Its declared accounting is **12 real N2 arms over 18
declaration units**: 16 guarantee rows, one parity fixture, and one read-boundary
invariant, with **15 rows full/closed and 1 partial**. The final phases passed **17 durable checks plus 5 N2,
inventory, freeze, baseline, and sabotage checks**. This discharges
facet-contracts slice 1. The biology pack remains open as slice 2, and frozen
cut 21 remains separately undischarged.

The successful aggregate command was:

```sh
cd python
uv run --frozen python tools/cut20_acceptance.py
```

It ran on the certified tuple: kernel `7.2.2-arch1-1`, ext4 mounted
`rw,noatime,data=ordered`. No capability waiver, skip, xdist, or modified
`PYTEST_ADDOPTS` was used.

The final repository gates on the repaired final source passed:

- `just check`: Ruff clean, Pyright 0 errors and 0 warnings, TypeScript typecheck
  and Biome clean, `tasks check` 0 errors and 0 warnings;
- `just test`: **4030 Python tests passed** serially and **135 TypeScript tests
  passed in 7 files**.

The aggregate candidate and final gate source differ only by restoration of the
deliberately missing `profile` argument in one portable negative test,
`test_profile_agreement.py`. That file is outside every cut-20 acceptance and
N2 input; the executed aggregate inputs were unchanged. The
final gate before/after source snapshots were byte-identical. After those gates,
only Task 15 metadata changed before `d5e203c1` was committed.

## Fresh step-3 reproduction

The fresh preserved corpus root is
`.mm30-reproduction/cut20-5a59a71aa79f47fa81005573ab26e0e4`.
Against base pin
`science:3d91abefa054c86e661d423a1c155e5330f9de07901bb1a4b1d7254a47c6374b`,
the old `{boundary, source, asserted_by}` payload was refused as
`FacetPayloadRefused` for unknown keys, with corpus/store content and chain tip
unchanged. The declared payload was admitted with:

```json
{"attested_by":"mm30-reproduction","locator":"accession:GSE179929"}
```

It produced dataset
`dataset:sha256:a6bf229ef0abd8e11f0b7f017cbdb6977395e23d83fb122fcf141f723ba1e448`;
the held 6,154,181-byte input has digest
`sha256:c74ea661e636ab670315f722cbad2d9c1154dbbc114012180d48c623850a31a5`.
The refusal had no effects; the valid declaration and actor were admitted in the
new root.

## Scope and concerns

This discharge records the implemented facet-contract slice and its durable
evidence. It does not claim the biology pack, cut 21, later main CI/hook work, or
the still-open questions about lineage-inherited standing, relation endpoint
enforcement, facet succession governance, and domain distribution.

## Remaining boundary

`domain-boundary` remains open only for slice 2, the biology pack. Cut 20 leaves
`D3` with `world-resolution`; it also leaves every other boundary and guarantee
remainder outside the facet-contracts selection where the cut-19 result placed
it. `verification-publication` remains a separate boundary under undischarged
cut 21.


## Final integration verification — 2026-09-07

The review repairs landed on the feature branch in `863977136a5076574f2371b084e7104ce8259c9d`:
pin checks now precede unresolved-root recovery and settlement claims;
foreign-base reporting and direct effects fail closed; attended sessions
validate profile/adopted-pin compatibility before ledger creation; and both
parsers refuse explicit null kind-facet mappings. The lossy-rendering oracle
now asserts its specific refusal, and canonical arm formatting preserves the
exact declaration values, checks, order and accounting.

The repaired candidate passed the complete serial and certified gates:

| Gate | Result |
|---|---|
| `just test` | 4048 Python passed in 1251.66s; 137 TypeScript passed |
| `just check` | Ruff, Pyright, TypeScript and Biome clean; tasks 0 errors / 0 warnings |
| `cd python && uv run --frozen python tools/cut20_acceptance.py` | Complete cut 17 → 18 → 19 prefix, including 27 session checks, then 17 durable cut-20 checks + 5 final N2/inventory/freeze checks; exit 0 in 1158.08s |

The two added session checks prove that mismatching pins leave a real pending
registration, staged recovery bytes and the session ledger untouched through
ordinary and session-mediated entry. Restoring valid pins permits recovery
and continuation. Cut 20 still declares **12 sabotages / 18 units / 16 guarantee
rows plus parity and boundary**, with 15 rows full/closed and D1 partial. Its
whole frozen file retains the SHA-256 recorded above.

These runs used the existing installed environment with explicit
`UV_NO_SYNC=1` and `PYTEST_ADDOPTS='-o tmp_path_retention_policy=failed'`.
Normal frozen synchronization refused an external metadata-only rename from
`atoms-core` to `verifiably-atoms`; the refusal is retained as failed evidence.
The 65 installed distributions matched the frozen lock, including atoms-core
0.1.0 and nodes-core 0.1.1. Dependency synchronization is not claimed green.
No capability waiver or xdist was used. The certified tuple remained kernel
`7.2.2-arch1-1`, ext4 `rw,noatime,data=ordered`.

The exact tested source boundary was base
`3199bb4bf347c5b01789906a8c9a768ce3ef9029` plus the staged repair, with SHA-256
`dceced331dce5b323d6c8a462a34577914f4ea897afe6d90f1dde5eae1b6a2c4`
over its sorted JSON file-to-SHA-256 map. Before/after snapshots for every gate
match for beliefs source/HEAD, installed versions, dependency runtime bytes
and tuple. External runtime source hashes were:

- atoms: `92346d69455eb78ccf440939fe22e3a6e5903d32917d643d3b4d84f65cb41914`;
- nodes: `ba34dabb8ba00e24de623bb59b16348962d9ca17ee0aa47f0c23012ddd5e6ba1`.

Atoms HEAD moved from `066744b` to `7113450` during the full suite and to
`faeccd9` during the aggregate. Those changes affected packaging metadata, CI,
guidance, tasks and atoms-only test files; imported runtime bytes stayed
unchanged. Beliefs does not execute those external test files. Nodes remained
at `f107de8`.
Logs, per-file hashes, installed paths/versions and before/after snapshots are
retained in `.superpowers/sdd/2026-09-05-facet-contracts/final-fix-gates/`.
Only the CLI task closure/notes differ between the tested source map and the
repair commit. This subsequent evidence amendment changes this document only;
it is covered by the focused design-corpus and guide checks. No executable or
test input changed after the gates.

The original Task 15 discharge and fresh step-3 reproduction above remain
historical evidence. Main landing and cut 21 remain pending; biology slice 2
remains open.
