# Run-confinement slice — execution ledger

Plan: `docs/superpowers/plans/2026-08-30-run-confinement.md`
Specification: `docs/superpowers/specs/2026-08-30-run-confinement-design.md`
Frozen cut: `docs/designs/2026-08-30-conformance-cut-13.md`
Freeze hash: fa89241

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
3. **R3 — the interpreter's DT_RPATH is supplied to the host listing
   explicitly, not ambiently.** uv's python-build-standalone CPython carries
   `DT_RPATH=$ORIGIN/../lib` on the interpreter executable alone; `_tkinter`
   resolves `libtcl9.0.so` only through that process-wide inheritance, which a
   per-file `ld.so --list` under an empty environment cannot see. The listing
   therefore takes the interpreter binary's $ORIGIN-expanded RPATH/RUNPATH
   directories as an explicit `--library-path` argument (spec §5.3 as amended);
   the environment stays empty, and the resolved libraries are ordinary closure
   rows under /science/env/lib. Wrongness is caught closed: a row the sandbox
   cannot resolve fails the probe's map-equality gate.
