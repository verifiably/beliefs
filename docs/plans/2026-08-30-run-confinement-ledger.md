# Run-confinement slice — execution ledger

Plan: `docs/superpowers/plans/2026-08-30-run-confinement.md`
Specification: `docs/superpowers/specs/2026-08-30-run-confinement-design.md`
Frozen cut: `docs/designs/2026-08-30-conformance-cut-13.md`
Freeze hash: <filled in Step 5>

Rulings are written at task boundaries, never rewritten after the fact.

## Rulings

1. **R1 — the host's confinement substrate is a prerequisite, not a
   dependency.** bubblewrap 0.12 with `--info-fd`, unprivileged user
   namespaces, and glibc's `ld.so --list` are checked before intent and
   refused pre-intent when absent; nothing under `/usr` is edited or
   vendored.
2. **R2 — the ext4 recertification on kernel 7.1.11 is a discharge
   prerequisite of the aggregate runner only.** The confined arms run under
   `tmp_path`; the cut-12 prefix needs the certified tuple. No atoms change
   ships in this branch.
