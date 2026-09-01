# Run-confinement slice — execution ledger

Plan: `docs/superpowers/plans/2026-08-30-run-confinement.md`
Specification: `docs/designs/2026-08-30-run-confinement-design.md`
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
6. **R6 — the two loader listings model the same inheritance.** The live
   smoke run showed the declared LD_LIBRARY_PATH cannot stand in for the
   interpreter's DT_RPATH in-layout (libtcl9 resolves at registered-root
   paths), and that a zero-dependency ELF vanished from the host map while
   the probe listed it. Both sides now supply the interpreter binary's
   $ORIGIN-expanded RPATH directories as an explicit --library-path, and
   map equality ranges over every architecture-matched loadable ELF, an
   empty resolution map being an attested observation, not an omission.
7. **R7 — the frozen-file pins are re-pinned across the rename.** Commit
   5a02ca2 renamed the package science→beliefs after cuts 8–12 froze,
   rewriting the frozen arms files' import strings without maintaining the
   FROZEN_PRIOR_CUT_FILES digests; test_n2_cut12.py has failed identically
   since, latent because acceptance modules are excluded from the ordinary
   run. Every pinned file was diffed against its own freeze commit and shows
   only the mechanical rename; the pins now name the post-rename bytes. The
   guard is restored, no frozen cut body was edited, and the drift and its
   cause are recorded here rather than papered over.
8. **R8 — the N2 harness names the audited package, not this package.**
   Cut 6's audit runs the arms against a pre-rename historical archive by
   monkeypatching test_n2.PACKAGE; 5a02ca2 hardcoded the sabotage copy's
   destination to the literal "beliefs", so that audit collection-failed
   (exit 4) with every check uncollected, latent behind the acceptance
   exclusion. The helper now derives the name from PACKAGE.name — the
   contract it had before the rename — changing nothing for audits of the
   current package. No frozen declaration file was edited.
9. **R9 — R7's re-pin ran to its transitive fixpoint.** Rounds 3 and 4 of
   task 9 extended R7's re-pin beyond its first report-derived scope: every
   FROZEN_PRIOR_CUT_FILES table (cuts 7-13) was swept, and the one
   transitive pin (test_n2_cut9.py's pin on test_n2_cut8.py's own bytes,
   moved by the audited table edit d0206c8) was re-pinned as
   CUT8_AUDIT_REPIN_COMMIT. Per-file drift verification and the pin graph
   are recorded in the task-9 report and the commits e38ac40, d0206c8,
   e053211; the graph terminates in one hop, nothing pins test_n2_cut9.py
   or later.
10. **R10 — discharged at `ef118c5` on linux/linux-4, kernel 7.1.11-arch1-1,
    ext4 device 259:2 at `/mnt/ssd`, `flush-honoring-disk.v1`, bubblewrap
    0.12.0.** The certified cut-13 runner exited 0 across all eleven pytest
    phases in the cut5→cut13 chain, 247 passed, 0 failed. The portable suite
    exited 0 at 2850 passed in 864.15s (0:14:24); Ruff reported all checks
    passed. Pyright reported 31 errors, all confined to this branch's own
    added or modified test files and none in `src/beliefs/` — the same
    slice-wide test-typing debt task 9's review flagged (Finding 1),
    disclosed here rather than fixed, since it bears on no declared unit's
    correctness. The three phase summaries and the complete host tuple are
    in `2026-09-01-conformance-cut-13-results.md`.
