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
4. **R4 — the loader map is architecture-matched.** `pulp` vendors CBC solver
   binaries for foreign architectures (ELFCLASS32 and EM_AARCH64 on this
   x86-64 host) that are loadable-typed but unlistable by the native loader
   and unexecutable in the sandbox, whose closure holds no matching program
   interpreter. An ELF joins the loader listing and map only when its class,
   data encoding and machine equal the capturing interpreter's own; foreign
   files stay ordinary digest-verified rows. The probe applies the same
   predicate in-layout, so map equality still binds everything that can run.
5. **R5 — the real bwrap mount table equals the plan exactly; no amendment.**
   A live launch of the gated boundary on this host (bubblewrap 0.12,
   unprivileged user namespaces) against the executing interpreter's own
   captured closure observed, from the child's own `/proc`: every declared
   namespace (`cgroup`, `ipc`, `mnt`, `net`, `pid`, `user`, `uts`) distinct
   from the parent's, and a canonical mount table equal — row for row, in
   sorted order — to `mount_plan`'s eight planned rows (the implicit root,
   the loader, the environment, the bundle, the output, the inputs, and the
   two device exceptions). bubblewrap adds no mount the plan does not
   declare — no second root entry for its own pivot, no incidental
   `/proc` or `/dev` row. `mount_plan`'s rows and `judge_instance` need no
   amendment on this host.

   The same run's `judge_report` refused on this closure's loader map, for
   reasons outside K6's mount/namespace judgement and outside this task's
   file scope — see task 6's report for the full diagnosis. That refusal is
   not evidence against this ruling: it was reached only after
   `judge_instance` above had already passed, from the probe's later,
   separate loader-listing check.
