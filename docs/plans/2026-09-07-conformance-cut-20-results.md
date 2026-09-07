# Conformance cut 20 — discharge results

**Date:** 2026-09-07
**Subject:** facet contracts (`../designs/2026-09-05-facet-contracts-design.md`),
measured against the whole frozen cut at `5fa48a6`
(`../designs/2026-09-05-conformance-cut-20.md`).

Cut 20 froze on 2026-09-06. Its entire file, including the historical status
header, remains byte-identical with SHA-256
`3bf154b032c696c1b62954936262ff14137b1af055cc887c49fc0aa60b70cac5`.
The implementation and acceptance work is the final Task 15 commit
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
