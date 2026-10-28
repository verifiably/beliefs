# Scoped re-review of the Important 1 fix — cut 48 (round 2)

Reviewer: claude-code/claude-fable-5-1 (fresh subagent, read-only), 2026-10-28. Range 60a43ff..345d2d4.

### Findings

#### Critical
none

#### Important
none

#### Minor
none

### Supporting trace

**Check 1 — cost removed, self-check intact.** Post-fix `_merged_capture` (`python/src/beliefs/corpus.py:1236-1260`) groups `(corpus_id, node)` pairs with no digest, then at `:1260` builds `held` with `content_identity(node) if len(claiming) > 1 else ""`. The `""` stand-in is produced only when `len(claiming) == 1`, in which case the per-address check compares a one-element uid set and a one-element content set and can never fire; it is never compared against a real digest, so two differing copies cannot look equal and two equal copies cannot look different. When `len(claiming) > 1`, every entry of that address gets a real digest, which is byte-for-byte the pre-fix comparison. The `uid-corruption` loop (`:1241-1251`) never consulted the digest before or after; the deprecated-key loop (`:1270-1287`) reads `claims[address][0][1].uid` and `holders`, both unchanged. `records` (`held[0][1]`), `holders[address]` order, and the `duplicate-location` `detail`/`message` text are unchanged, so `snapshot_standing`'s `counts` lookup (`:1326`) and the `view.py:231-233` / `read.py:414` readers see identical results. A one-holder caller and every singly-held address in a multi-holder world now digest nothing, which is what spec §4.5 ("a one-holder caller is unchanged") and the `_merged_capture` docstring claim.

**Check 2 — test honesty.** The test patches `beliefs.world.registry.content_identity`; `_merged_capture` does `from beliefs.world.registry import content_identity` at call time (`:1234`), so the patched attribute is what the fold calls. I ran the new test against the pre-fix source without touching the worktree (`git archive 60a43ff python/src` into the scratchpad, `PYTHONPATH` pointed at it, `beliefs.corpus.__file__` confirmed to resolve there): it fails at line 464 with two digests recorded for the one-holder call. Under the fix the module passes (`uv run --frozen pytest tests/test_snapshot_retraction.py -p no:cacheprovider`: 37 passed). The patch is applied after the writes, so `calls` counts only the fold's digests; `calls == []` for one holder also proves `snapshot_standing`'s chain validation (`_validated_retraction`, `_resolve_retraction_target`) digests nothing, and `sorted(calls) == [r.id, r.id]` pins exactly the shared address's two claims and excludes the singly-held counter. If a later refactor moved the import to module scope, the two-holder assertion would fail rather than pass vacuously.

**Check 3 — user-visible change / regressions.** None found. Error codes, refs, details and holder ordering are unchanged. The only behaviour difference is that a single-holder record whose canonical JSON would make `content_identity` raise no longer raises inside the merge; that restores pre-cut-48 `main` behaviour for one-holder callers, which is the spec's stated intent, not a regression.

**Check 4 — the rest of the diff.** Range `60a43ff..345d2d4` is one code commit plus two `chore(tasks)` notes. Line `:1260` is 119 characters against the project's `line-length = 120`. The commit message is a conventional `perf(corpus):` and carries no attribution trailer. The tracked tree was clean before and after my runs (`git status --porcelain` empty).

### Assessment

Important 1 resolved: **Yes**. The digest is now paid only for addresses more than one holder claims, with the merge's three refusals unchanged, and the new test proves both the one-holder zero-cost case and the exact multi-holder count, RED against `60a43ff` and GREEN at `345d2d4`.

claude-code/claude-fable-5-1
