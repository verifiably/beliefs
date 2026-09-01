# Run confinement — design (the `run-confinement` slice)

**Date:** 2026-08-30
**Status:** designed and planned; not yet implemented. Conformance cut 13 is
specified in §9 and freezes before implementation. The implementation plan is
`../plans/2026-08-30-run-confinement.md`.
**Scope:** the confinement-capable boundary policy of computation §4.4b and
§7.3a — `boundary-policy/confined-v1` — executing a run inside a fresh
namespaced materialization of a digest-verified runtime artifact closure; the
receipt that observes that construction; the `clean-environment` row of
`derive_scope`; and the value-level join from a derived verification to the
record admission reads. Closes R15 in full and the confinement arms of R4, R9,
R13, R16 and R21. No store change, no `atoms` or `nodes` change, no workflow
surface beyond cut 3's single-rule adapter.

**Inherits:** computation (`../../designs/2026-08-02-computation-reproducibility-design.md`)
§4.2, §4.2c, §4.4b, §4.5, §7.3, §7.3a — the rule text this document
implements without amending. Cut 3 (`../../designs/2026-08-11-conformance-cut-3.md`)
§3 states what a scratch root is not and §4.2 names every arm deferred here.
The implementation roadmap (`../../plans/2026-08-29-implementation-roadmap.md`)
ranks this slice first in tier 1; the adoption ledger's `Current state` table
carries it as `run-confinement`.

**Sources, read at design time:** the R4, R9, R13, R15, R16 and R21 rows of
computation §10; `python/src/beliefs/boundary.py`, `adapter.py`, `recipe.py`,
`replay.py`, `verify.py`, `verification.py`, `admission.py`, `runrecord.py`;
the host at `4d29bc2` — Snakemake 8.11.4, a uv-managed CPython 3.13 with
`Py_ENABLE_SHARED=1`, bubblewrap and glibc's loader present.

---

## 1. Problem

Cut 3 built the execution boundary as **staging, not confinement**: the
engine runs as a subprocess in a `mkdtemp` scratch root, inherits the full
host environment, receives absolute host paths in its argv, and may read
anything the host user can. The consequences, each pinned by a deferred arm:

- No receipt can attest the two things §7.3's `clean-environment` row needs —
  a fresh environment instance reconstructed from the recipe, and §7.3a's
  three confinement capabilities — so `derive_scope` has no
  `clean-environment` branch (`replay.py:228`), and
  `test_clean_environment_has_no_reachable_branch` asserts the absence.
- `BoundaryPolicy.capabilities` and `BoundaryReceipt.capabilities` exist and
  are always `()`. No vocabulary constrains them.
- `lifecycle_state` admits only `clean-environment` passes
  (`verification.py:80`), but no production path carries a derived
  verification into it: the record value `admit()` reads is constructed only
  by tests. R9's *admission does not follow* and R16's *nothing is admitted*
  are therefore unfailable against boundary-produced values.
- The environment manifest (`adapter.py:157`) names the interpreter, a tree
  digest of the stdlib and every distribution RECORD — and omits everything
  the interpreter needs to *start*: the ELF loader, libc and its siblings,
  `libpython`, `pyvenv.cfg`, the native dependencies of extension modules,
  and the source trees that path-extending `.pth` files add for editable
  installs. A read-only bind of that manifest cannot run Python; a bind of
  the host prefix exposes unmanifested bytes and stays host-mutable.

## 2. Decision

**Reconstruction is fresh namespaced materialization.** §4.5 defines the
environment as held content, not an installation recipe, and §4.4b requires
executing inside those held artifacts. So a "fresh environment instance
reconstructed from the recipe" is a **fresh set of namespaces in which
exactly the digest-verified artifact closure is mounted read-only** —
not a reinstall, not a regenerated image, and not a holdings store, which
would add a requirement the design does not contain. The slice stays tier 1.

Three constraints follow and govern every section below:

1. **§7.3 is conjunctive.** The receipt must attest the fresh instance as its
   own observed fact; the three capability strings do not imply it.
2. **A read-only bind is sufficient only over verified closure bytes that
   are immutable to the sandbox.** (The trusted host can still modify them;
   §4.4.) The closure is enumerated per file, snapshotted into a
   boundary-owned directory, verified against the manifest before the bind
   and again after the process exits. Host-side mutation cannot be prevented
   by a namespace; a mutation present at either observation is caught, and
   the run is not minted (§4.4 states the threat model exactly).
3. **The receipt reports observed enforcement.** Capabilities are never
   copied from the requested policy; the fresh-instance attestation is
   observed by the boundary from its own `/proc`.

The mechanism is **bubblewrap** (`bwrap`): unprivileged user namespaces, a
declarative mount plan in argv, no daemon. A Python-native `unshare`/`mount`
implementation would make the boundary own uid mapping, `pivot_root` and
mount propagation — the component whose job is to have no holes, hand-rolled.
A container daemon would put a daemon in the trust path and make the receipt
observe the daemon's claims.

## 3. Policies and the capability vocabulary (`recipe.py`)

Two policies exist. The caller selects one; the boundary never chooses,
downgrades, or defaults.

| policy | `identity` | `capabilities` |
|---|---|---|
| minimal | `boundary-policy/minimal-v1` | `()` — cut 3's policy, byte-unchanged |
| confined | `boundary-policy/confined-v1` | `("from-bundle", "closure-confined-filesystem", "network-denied")` |

`CAPABILITIES` is a closed vocabulary — §7.3a's three, spelled once. A policy
naming a string outside it is unspellable at construction.
`REQUIRED_FOR_CLEAN_ENVIRONMENT` is a **separate explicit tuple** naming
those same three; it is not derived from `CAPABILITIES`, so a capability
added later does not silently become an admission requirement.

Qualification (§7.3a) is set containment over the vocabulary and reads
nothing else: not the identity string, not any ordering. R4(d)'s arms —
*whatever its version string*, *two incomparable policies are not ranked* —
are checked over constructed policies whose identities carry decoy version
strings.

`execute_assessment_run` and `execute_production_run` gain a keyword-only
`boundary_policy: BoundaryPolicy` with **no default**; the module constant
`_POLICY` is removed. Before intent the boundary matches the supplied policy
against the two known definitions on **the entire definition — identity,
scope rule, and unique capability set together**; any mismatch is
`BoundaryPolicyUnsupported`, a request failure. The capability member is
compared as a set — frozenset(capabilities) — and the boundary carries on
with the canonical known value, so a reordered spelling of a known set is
recorded as the definition it names.
Execution never trusts caller-claimed capabilities: the definition it
recognizes decides what it will construct and observe.

The match covers **`identity`, `scope_rule` and the capability set
together**. `scope_rule` enters verification evidence (`verify.py` copies it
from the original run's policy into every verification), so an arbitrary
value under a known identity would mislabel the derivation. `capabilities`
must be **unique** at construction — a duplicate entry is unspellable — so
that no set comparison can be satisfied by a tuple that is not the set it
names.

## 4. The runtime artifact closure (`adapter.py`, `recipe.py`)

### 4.1 The manifest

`EnvironmentManifest` becomes a per-file table. Each row is
`(sandbox path, kind, content)` where `kind ∈ {file, symlink}` and `content`
is the file's digest or the symlink's target. The identity is the fold over
the sorted rows under the domain **`science.environment.v2`** — a new version,
because the row shape changed and the identity-version rule forbids
reshaping rows under `v1`. Previously persisted runs retain their addresses;
newly captured recipes move. Nothing pins a real environment identity in any
fixture or contract.

**The capture plan is ephemeral.** The capture produces, beside the
manifest, a *capture plan* mapping each sandbox path to its host source; the
plan lives only in the boundary for the duration of one run and never enters
a manifest or a recipe. Otherwise the installation location of Python on
this host would be part of every recipe identity. Host paths do enter the
**occurrence** through the receipt's `scratch_mapping` and `mounts` members
(§6.3), which are identity-bearing for the run address — that is §4.2c's
rule: the host mapping is an observation of this execution, never a member
of what a replay must reconstruct.

### 4.2 Enumeration

The closure is discovered, not declared, by walking from the executing
interpreter:

| component | enumeration | sandbox path |
|---|---|---|
| interpreter | `sys.executable` resolved through its symlink chain; each link a `symlink` row, the final binary a `file` row | `/science/env/python/bin/…` |
| `libpython`, stdlib, platstdlib | every regular file under the prefix's `lib/`, individually; `__pycache__` excluded | `/science/env/python/lib/…` |
| distributions | every RECORD entry, individually, as today; derived caches excluded | `/science/env/site/…` |
| `.pth` path lines | each path-extending line of every `.pth` in site-packages is followed and its tree captured (regular files; `__pycache__`, `.git` excluded). This checkout's editable `science`, `nodes-core` and `atoms-core` are captured this way. The `.pth` file's own host bytes are **not** copied — its sandbox form is rendered (§5.2). A `.pth` containing only `import` lines is an ordinary artifact. A **mixed** file, with both `import` and path lines, is **refused** (`ClosureUnsupported`): rendering it would turn executable import lines into rendered, non-held code. A RECORD entry ending in .pth is skipped by the RECORD walk and handled here. For an import-only .pth, each imported top-level module must be a closure member; a site-packages module the file names that no RECORD lists (this host's _virtualenv.py, written by uv) is captured as /science/env/site/<name>.py; a named module absent from site-packages is ClosureUnsupported | `/science/env/path/<n>/…`, where `<n>` is canonical — the `.pth` file's sandbox path under `/science/env/site` joined to the line's ordinal within the file, e.g. `/science/env/path/_science.pth/0` — so the same closure lays out identically on every host |
| native closure | for the interpreter, `libpython`, every `.so` under `lib-dynload` and every `.so` a RECORD lists: `PT_INTERP` (read from the ELF header) and the transitive `DT_NEEDED` set, resolved by **the loader itself** (`ld.so --list`) so that what is manifested is what `execve` maps; `linux-vdso` excluded by name | loader at its `PT_INTERP` path; libraries at `/science/env/lib/<soname>` |

`PT_INTERP`, the Python version directory name, and every ABI-specific path
are **read from the captured artifacts**; nothing in the boundary spells an
architecture or a Python version. Every symlink row's target is itself part
of the closure — a file row, a symlink row, or a directory some row lies
under — and is captured when the link is; a relative target that stays
under the link's own root keeps its relative text, any other in-closure
target is rewritten to the target's sandbox path, and a target outside
every root is ClosureUnsupported. sys.executable is followed link by link
(add_chain): each link a symlink row, the terminal binary the interpreter
row. Every sandbox path is normalized — absolute, no ., .. or empty
components — and the manifest refuses any other spelling, so a snapshot
join can never leave the snapshot.

**Refusals discovered during capture** are post-intent, `ClosureUnsupported`:
two libraries with one SONAME; a symlink whose target resolves outside the
closure; a `.pth` line the boundary cannot follow (relative, nonexistent,
or not a directory); a non-ELF `PT_INTERP`; an artifact the loader cannot
list. Only the loader diagnostic interface itself (`ld.so --list` callable)
is a pre-intent host prerequisite.

`require_executing_environment` keeps its meaning: the manifest captured now
must equal the recipe's. A glibc update on this host therefore moves the
environment identity and refuses execution of older recipes here — the
correct answer under §4.5.

### 4.3 The snapshot

The confined boundary never mounts a host prefix. It materializes the closure
into a boundary-owned **snapshot** keyed by environment identity,
`<scratch_base>/environments/<environment_identity>/`, laid out as the
sandbox paths (so `/science/env/lib/libc.so.6` is
`<snapshot>/science/env/lib/libc.so.6`), by copying exactly the manifested
files and creating exactly the manifested symlinks. The snapshot also
holds the rendered rows of §5.2 — pyvenv.cfg, the venv symlinks, the
rewritten .pth files — because each is a pure function of the manifest, so
the whole of /science/env is one read-only bind. Verification checks
manifested rows by digest and rendered rows by expected content, and
refuses any other file.

**Publication is atomic and the loser is specified.** The snapshot is built
into a sibling temporary directory, verified file by file against the
manifest, and published by `rename`. If the rename finds a winner already
published, the temporary build is discarded and the **winner is verified**;
a winner that matches is reused, and one that does not is
`SnapshotMismatch`. An existing snapshot that fails verification is likewise
`SnapshotMismatch` — it is **never deleted and rebuilt**, because a
corrupt shared snapshot is evidence, not a cache miss, and deleting it under
a concurrent run is a race.

### 4.4 Integrity, before and after

Immediately before the bind, the boundary digests the **bundle**, the
**snapshot** and the **staged inputs** against their recorded identities.
Immediately after the sandboxed process exits — **before the trace, the
realized seeds or any output is read** — it digests all three again. Any
difference at either point is `ClosureMutated`: no run is minted. This is
R15's mutation-after-capture arm.

**Threat model, stated exactly.** The boundary **trusts the host and the
boundary owner**. Detection covers a mutation **present at either
observation** — an edit made after capture and before the bind, or one left
in place at exit. It does not cover a host writer that modifies a file, lets
the child read it, and restores it before the post-exit check; both
observations pass. Closing that window would require genuinely immutable
materialization — a different and substantially larger piece of work — and
this slice does not claim it. The two observations are what R15's arm asks
for: a bundled file edited after capture yields no run under the unchanged
`code_identity`.

**Cost, stated.** A cache hit costs three full digest passes over the
closure — the host capture, the snapshot verification materialize_snapshot
performs (the pre-bind observation), and the post-exit check — against
today's two (capture and require_executing_environment); the confined path
does not call require_executing_environment, because the recipe's manifest
is that single capture by construction, and no other pass over the
snapshot exists. A cache miss adds one copy of the closure. The bundle and
inputs were already digested at capture and are digested twice more.

## 5. The confined execution (`confinement.py`, `boundary.py`)

### 5.1 Sandbox layout

| sandbox path | content | mount |
|---|---|---|
| <PT_INTERP> | the loader, at the path the interpreter's ELF header names, from the snapshot | ro-bind |
| /science/env/ | the snapshot: interpreter prefix, site-packages, .pth trees, native libraries under lib/, and the rendered venv | ro-bind |
| `/science/bundle/` | the captured code bundle | ro-bind |
| `/science/out/` | the boundary-owned output root: the scratch root's `out/` | bind, rw |
| `/science/out/inputs/` | the staged held inputs, where cut 3's workflows already resolve them | ro-bind over the rw root |
| `/dev/null`, `/dev/urandom` | kernel substrate, declared by name — Snakemake imports `multiprocessing`, which needs `urandom` | dev-bind |

PYTHONPATH is not part of the closure and is cleared; a module reachable on
the host only through it is not reachable in the sandbox (a limitation,
§9.3).

After the layout, `--remount-ro /`: bubblewrap's implicit root tmpfs is
otherwise writable. No `/proc`, no `/tmp`, no `/etc`, no home, no
`ld.so.cache`. Nothing undeclared is readable and one location is writable.

### 5.2 Rendered, not held

Three things exist only in the sandbox and are configuration the boundary
renders from the layout — the rule cut 3 set for engine configuration:

- `/science/env/venv/pyvenv.cfg` with `home = /science/env/python/bin`;
  `/science/env/venv/bin/python` → the base interpreter, rendered only
  when the interpreter's symlink chain did not already capture that path
  as a manifest row; the venv's `site-packages` → `/science/env/site`;
- every path-extending `.pth` file, rewritten to its `/science/env/path/<n>`
  target;
- the explicit environment and the fixed hostname (§5.4).

They are recorded in the receipt's `rendered_environment` member. The
manifest holds artifacts only.

### 5.3 Cache-independent loader plan

The sandbox has no `ld.so.cache`. Resolution proceeds `DT_RPATH` →
`LD_LIBRARY_PATH` → `DT_RUNPATH` → cache (absent) → defaults (empty), so the
explicit environment sets `LD_LIBRARY_PATH=/science/env/lib`. A flat
directory is valid only when SONAMEs are collision-free (§4.2 refuses
otherwise) **and** an in-layout `ld.so --list` of the interpreter and every
extension resolves each SONAME to the sandbox file whose digest the manifest
records; the probe (§6.2) performs that check and refuses the layout when it
fails. The host listing runs the loader under an empty environment — no
ambient LD_LIBRARY_PATH or LD_PRELOAD. One resolution context is supplied
explicitly, never ambiently: the directories named by the capturing
interpreter binary's own DT_RPATH or DT_RUNPATH entries, $ORIGIN-expanded
against the binary's real location, deduplicated in order, are passed to
the loader as its --library-path argument — the main executable's RPATH is
inherited process-wide at runtime, so a listing that predicts runtime
resolution must model exactly that inheritance and nothing more. The
libraries it resolves join the closure as ordinary captured rows, wherever
their own registered root places them — not always the flat
/science/env/lib. Because of that, the declared LD_LIBRARY_PATH=/science/env/lib
alone cannot stand in for the interpreter's RPATH in-layout: `ld.so --list`'s
--library-path replaces LD_LIBRARY_PATH for that invocation rather than
supplementing it, and echoes back whatever
directory string it was given verbatim, the probe's listing supplies
--library-path as /science/env/lib followed by the in-layout interpreter's
own $ORIGIN-expanded RPATH/RUNPATH directories, each normalized so the
loader's echo matches the host's own realpath-derived record — the host
against the host's own paths, the probe against the in-layout copy under
/science/env — so both listings model the one RPATH inheritance the
runtime actually has (ruling R6). The capture retains the
expected map as rows (ELF sandbox path, SONAME, resolved sandbox path)
over every loadable ELF (ET_EXEC or ET_DYN) under /science/env of the
closure's own architecture — an ELF is listed only when its class, data
encoding and machine equal the capturing interpreter binary's; a
foreign-architecture file (a vendored solver for another platform, say)
stays an ordinary digest-verified row outside the map, and could not
execute in the sandbox regardless, its program interpreter being outside
the closure — closed to a fixpoint over the libraries it adds. Per-ELF
equality ranges over every such architecture-matched loadable ELF, not
only ones with a dependency of their own: an ELF that resolves zero
further NEEDED entries stays a key of the map with an empty resolution —
an attested observation, not an omission (ruling R6). The probe lists the
same set in-layout and the boundary requires its report to equal the map exactly:
the same ELFs, the same SONAMEs per ELF, the same resolved path, the
manifest's digest; a nonzero loader exit, an unresolved or unparsable
line, an omitted or extra entry each refuse.

### 5.4 Process discipline

`bwrap --unshare-all --die-with-parent --new-session --hostname science
--chdir /science/out`, uid and gid mapped to the caller. `--clearenv`, then
exactly:

```
PATH=/science/env/venv/bin
LD_LIBRARY_PATH=/science/env/lib
PYTHONDONTWRITEBYTECODE=1
PYTHONHASHSEED=0
PYTHONNOUSERSITE=1
PYTHONSAFEPATH=1
SCIENCE_TRACE_FILE=/science/out/.trace/events
HOME=/science/out/.home
PWD=/science/out
LC_CTYPE=C.UTF-8
```

bubblewrap sets PWD to the --chdir target and CPython's locale coercion
sets LC_CTYPE=C.UTF-8 when it is unset, so both are declared explicitly
and exact equality holds; HOME is declared because with it unset Snakemake
expands ~ to a literal directory under the working directory.

`stdin` is `DEVNULL`. The trace directory moves inside the output root —
today it is `mkdtemp(dir=scratch.parent)`, outside every bind — and `.trace/`
is an intermediate, excluded from the manifest like `.seeds`. No other
variable exists to be read: §4.4b's *reads an environment variable* gap
closes by exact environment equality, which the probe checks.

### 5.5 Argv

`build_argv` becomes policy-neutral: it takes the interpreter path, the
snakefile path and the directory explicitly, and the minimal policy supplies
host paths while the confined policy supplies sandbox paths. The confined
inner argv is `/science/env/venv/bin/python -m snakemake --snakefile
/science/bundle/<entrypoint> --directory /science/out --cores <n>
--force-use-threads …` with sandbox paths only, so R21(c)'s two differently
mounted scratch roots produce byte-equal inner argv and differ only in the
receipt's host mapping. Snakemake 8's local executor otherwise spawns
every run: job as a fresh python -m snakemake through /bin/sh
(shell=True); in-process execution keeps the closure shell-free. The
minimal policy's argv is byte-unchanged.

Rules stay `run:`. There is no shell in the closure; a `shell:` rule fails
closed as an undeclared read of `/bin/sh`. That is a stated limitation of
`confined-v1`, not something worked around.

### 5.6 Sequence

For `confined-v1`, `_execute_run` proceeds:

1. **pre-intent:** host prerequisites (§8's `ConfinementUnavailable` list);
   the policy matched against the known definitions; the existing
   `_preflight` refusals;
2. **intent appended** — from here every exit either mints the run or
   fulfils the intent with a refusal;
3. scratch root; bundle capture; environment capture (§4.2); snapshot
   get-or-build and publish (§4.3); input staging; pre-bind integrity
   (§4.4: the bundle's fold and the staged inputs' fingerprint; the
   snapshot's pass is the get-or-build verification);
4. the gated launch (§6): probe, boundary-side inspection, `GO`, engine;
5. post-exit integrity (§4.4); then trace, realized seeds, manifest, mint.

The minimal policy's sequence is cut 3's, unchanged.

## 6. The gated launch and the receipt (`confinement.py`, `recipe.py`)

### 6.1 One sandbox, gated by the probe

A separate "identical" sandbox proves nothing about the engine's. And
`--info-fd` fires before `--block-fd`'s hold point, while the blocked child
still sees the host mount table. So the probe gates the engine's **own**
process:

1. bwrap starts with `--info-fd`; its command is the held `beliefs.probe`,
   run from `/science/env/path/<n>` like any held module, with two inherited
   descriptors named on its own argv (`--report-fd`, `--go-fd`, never the
   environment): `REPORT` (probe → boundary: the probe's JSON report
   followed by the `READY` line, one pipe) and `GO` (boundary → probe).
2. After bubblewrap completes the layout, the probe performs its checks
   (§6.2), writes its report and then `READY` on `REPORT`, and waits on
   `GO`.
3. The boundary reads the child pid from the info fd and inspects **that
   child** from its own `/proc`: `/proc/<child>/ns/{mnt,pid,net,ipc,uts,
   user,cgroup}` — each must differ from `/proc/self/ns/*` — and
   `/proc/<child>/mountinfo`, **canonicalized** to rows of
   `(mountpoint, role, ro|rw)` where role names a planned bind, the implicit
   root, or a declared device exception. The canonical set must **equal** the
   planned mount table: no extra, no missing, no `rw` where `ro` was planned.
   Canonical rows preserve multiplicity — a stacked or duplicate mount is a
   row of its own and fails equality — and each observed mountpoint is
   classified into its planned role, an unplanned one taking the role
   unplanned; the receipt's instance carries these observed rows, never the
   plan's.
4. On success the boundary writes `GO`; the probe **closes both `REPORT`
   and `GO`** and then `execve`s the engine — same pid,
   namespaces, mounts and environment, and no gate authority inherited. On
   any failure the boundary closes `GO`, the probe exits, and the run is
   refused `ConfinementNotEstablished`.

### 6.2 The probe's checks

| what | checks |
|---|---|
| filesystem | opening `/etc/passwd` and `/tmp` raises `ENOENT`; creating a file under `/`, `/science/bundle`, `/science/env` and `/science/out/inputs` raises `EROFS`; creating one under `/science/out` succeeds (Path.touch) and is removed (unlink) |
| environment | `os.environ` equals the declared set exactly; `os.uname().nodename == "science"`; `os.getcwd() == "/science/out"` |
| network | an IPv4 connect to a non-loopback documentation address (192.0.2.1) fails with ENETUNREACH; an IPv6 socket either cannot be created (EAFNOSUPPORT) or its connect to 2001:db8::1 fails unreachable. Loopback is not evidence — the sandbox owns its own lo. DNS failure is not evidence and is not checked. |
| loader plan | the in-layout ld.so --list of every loadable ELF under /science/env reports, per ELF, its exit status and each SONAME's resolved path and digest; the boundary requires equality with the captured map (§5.3) |

### 6.3 What the receipt attests

`BoundaryReceipt` gains members present only for the confined policy:

| member | content | source |
|---|---|---|
| `capabilities` | the subset of §3's vocabulary whose evidence all passed | `closure-confined-filesystem` and `network-denied` from the probe report plus the namespace inspection; `from-bundle` from the observed `/science/bundle` mount, the canonical inner argv naming an entrypoint under it, and `validate_entrypoint`'s existing check — never from the policy |
| `instance` | the seven namespace facts (each `distinct`), the canonical observed mount table, `mount_plan_identity` (digest of the canonical plan), and `environment_identity` — the identity of the **verified snapshot** whose directory the observed mount plan binds at `/science/env`, read from the snapshot's own key, not copied from the recipe; §7.1 then compares it to the recipe's | boundary-side inspection |
| `rendered_environment` | §5.2's rendered facts and the explicit environment | rendering |
| `argv` | the canonical **inner** engine argv, sandbox paths only | rendering |
| `rendered_config` | the engine config, as today | rendering |
| `scratch_mapping`, `mounts` | the host scratch root and the host source of every bind — the only place a host path appears (§4.2c) | the boundary |

Because `confined-v1` was requested, a probe check that fails is not "a
capability absent from the receipt"; it is `ConfinementNotEstablished`. The
graded case — a valid run that cannot reach `clean-environment` — is reached
by **selecting `minimal-v1`**, whose receipt carries `capabilities=()` and no
`instance`.

**Two receipt domains.** The minimal receipt keeps cut 3's four members and
its identity under `science.boundary-receipt.v1`, projection byte-unchanged.
The confined receipt is a different shape and takes a successor domain,
**`science.boundary-receipt.v2`** — the same identity-version rule that
minted `science.environment.v2`; adding members under `v1` would reshape it.
Previously persisted run addresses remain stable. A newly executed
minimal-policy run does **not** keep its cut-3 address, because its
environment identity has moved to `v2` (§4.1); what stays byte-stable is
the minimal receipt projection alone.

**And a run domain.** `RunClosure.address()` embeds the full receipt
projection (`recipe.py:495`), so a confined receipt reshapes the run
projection too. Minimal runs stay under `science.run.v1`; a confined run
takes **`science.run.v2`**. The dispatch is by **exact receipt shape** — a
`v2` receipt makes a `v2` run — in both `RunClosure.address()` and
`runrecord.py`'s wire recomputation, so a decoded record recomputes under
the domain its receipt shape names and no other.

**Validation.** `BoundaryReceipt.__post_init__` and `runrecord.py`'s wire
validator accept the two spellings by domain: minimal (`v1`, four members)
and confined (`v2`, all members present). A confined receipt whose `instance.mount_plan_identity`
does not equal the digest recomputed from its own canonical observed mounts
is malformed — the field is evidence, and evidence that cannot be checked
is dead. `runrecord.py` changes only for the receipt variants and canonical
reprojection; per-file manifest validation is `recipe.py`'s and
`adapter.py`'s, because the durable run projection carries the environment
**identity** only.

## 7. Scope derivation and the admission join (`replay.py`, `verify.py`)

### 7.1 The fourth row

```
conformance fails on either side                            → not-certified
recipes equal and qualifies(replayed.receipt, env identity) → clean-environment
recipes equal                                               → same-environment
spec and observes equal, code differs, lineage certified    → independent-implementation
otherwise                                                   → not-certified
```

`qualifies(receipt, environment_identity)` holds when `receipt.instance` is
present, `REQUIRED_FOR_CLEAN_ENVIRONMENT ⊆ set(receipt.capabilities)`, and
`receipt.instance.environment_identity == environment_identity`, where the
caller passes `replayed.recipe.environment.identity()`. Equal recipes already
imply equal `boundary_policy` members, so a minimal original can never pair
with a confined replay into `clean-environment`; the whole recipe is the
confined one. The row reads the **replay's** receipt because §7.3's
requirement is that the replay ran through the boundary.

`test_clean_environment_has_no_reachable_branch` is retired in the same
change. Its inverse — the branch exists and is reached only through a
qualifying receipt — is an R4 arm.

### 7.2 The join

```python
def admission_record(derived: AssessmentVerification) -> Verification:
    return Verification(
        ref=derived.identity(),
        assessment=derived.assessment,
        scope=derived.scope,
        verdict=derived.verdict,
        supersedes=derived.supersedes,
    )
```

Total over `AssessmentVerification`; no caller-supplied field. A
`DatasetProductionVerification` is refused early with
`NotAnAssessmentVerification` — a production verification has no assessment
to admit. Durable publication of verification records crosses the
persistence seam and is a roadmap finding (§10), not this slice's work.

### 7.3 End to end

The acceptance arms run: confined run → confined replay → `build_verification`
→ `admission_record` → `admit()` and `belief.evaluate` over the derived record
and the run's own observations.

| verdict / scope | outcome asserted |
|---|---|
| `passed` / `clean-environment` | `Admitted`; belief evaluates over the admitted assessment |
| `inconclusive` (an output made unreadable — R9) | `AdmissionRefused`, verification-state reason; admission does not follow |
| `not-certified` (one execution non-conforming — R16) | `AdmissionRefused`; `belief.evaluate` returns the same `NoBelief` outcome as before the verification existed. No belief digest exists on that path, so none is asserted unchanged |

**R16's mechanism.** `cores` is boundary-supplied scheduling metadata and not
a recipe member (R21(a) pins this), yet Snakemake 8.11.4 exposes it to a
`run:` rule as `workflow.cores`. The fixture workflow records its realized
`model-initialization` seed as the planned seed when `workflow.cores == 1`
and the planned seed plus one otherwise — a deliberate misuse of scheduling
metadata that conformance is there to catch. Executed at `cores=1` and
replayed at `cores=2` it yields **equal recipes and two qualifying receipts**
(the receipts differ by `--cores` in the inner argv), equivalent outputs, and
exactly one non-conforming execution. Nothing is mutated after minting.

## 8. Refusals (`errors.py`)

| error | stage | when | `RunRefused.reason` |
|---|---|---|---|
| `ConfinementUnavailable` | pre-intent only | `bwrap` absent or without `--info-fd`; user namespaces disabled; `ld.so --list` not callable | `confinement-unavailable` |
| `BoundaryPolicyUnsupported` | pre-intent | the supplied policy matches neither known definition on the entire definition — identity, scope rule, and unique capability set | `boundary-policy-unsupported` |
| `ClosureUnsupported` | post-intent | SONAME collision; symlink escaping the closure; unfollowable `.pth` line; non-ELF `PT_INTERP`; unlistable artifact | `closure-unsupported` |
| `SnapshotMismatch` | post-intent | an existing or freshly built snapshot disagrees with the manifest; a concurrent winner disagrees | `snapshot-mismatch` |
| `ClosureMutated` | post-intent | bundle, snapshot or staged inputs differ between the pre-bind and post-exit digests | `closure-mutated` |
| `ConfinementNotEstablished` | post-intent | a namespace equal to the parent's; canonical mounts ≠ plan; any probe check failed; the probe did not report `READY`; any launch or protocol failure after intent — bubblewrap gone, an unstartable process, malformed info or report, a closed descriptor — with the child terminated and reaped and every descriptor closed on every failure path | `confinement-not-established` |
| `NotAnAssessmentVerification` | `admission_record` | a production verification offered to the join | — (not a run refusal) |

Post-intent refusals fulfil the intent with an unfulfilling act-report and
mint no run — cut 3's T2 shape.

**The stable-reason mechanism.** `str(error)` carries diagnostics and
preserves nothing stable. Each new exception therefore carries a **`reason`
attribute** holding the fixed string in the table's last column, with its
message free to carry the diagnostic detail; `_execute_run` maps that
attribute into `RunRefused.reason` and the message into a new
**in-memory-only `RunRefused.detail`** member. The durable `RunRefusal` and
the act-report retain **only the stable reason**: a durable detail member
would reshape the act-report and force an identity successor for a
diagnostic string. Errors without the attribute keep today's `str(error)`
path, with `detail` empty.
`OSError`s raised inside `confinement.py` — a failed copy, rename, bind, or
descriptor read — are **wrapped at that boundary** into the named error
whose stage they belong to, so no raw `OSError` reaches `_execute_run` from
the confined path. `execution-failed` is unchanged; an
in-sandbox `ImportError` from a module outside the closure surfaces through
it, and R13's negative asserts a refusal — not an absent member, and not the
engine's stderr, which would widen `RunRefusal` for nothing.

A capability lost **after** intent — bubblewrap removed mid-run, a namespace
that cannot be created — is an execution refusal. There is no path from a
confined request to a minimal execution.

## 9. Conformance cut 13

### 9.1 Selection

| row | arms in cut 13 | banked |
|---|---|---|
| **R15** | edit a bundled file after capture → no run (`closure-mutated`); undeclared file read fails closed; undeclared network fetch fails closed; the receipt names the capabilities actually in force; negative: `minimal-v1` runs validly and cannot reach `clean-environment` | **closes** |
| **R4** | the `clean-environment` row of the walk, reached only through a qualifying receipt; negative (d): a policy missing a capability derives `same-environment`; a policy with every capability qualifies whatever its version string; two incomparable policies are not ranked | **closes** |
| **R9** | *admission does not follow*: an `inconclusive` verification from a confined pair is refused by `admit()` | **closes** |
| **R13** | negative: an import resolving outside the bundle and the held environment is refused | **closes** |
| **R16** | *nothing is admitted*: a `not-certified` pair with qualifying receipts admits nothing and yields the same `NoBelief` outcome (§7.3's mechanism) | remains **part** — family, multi-stream, definition-equality and execution-coverage arms are `workflow-surface`'s |
| **R21** | negative (b): a write outside the output root fails closed; negative (c): two differently mounted scratch roots yield equal recipe identities and `clean-environment` stays reachable, each mapping only in its receipt | remains **part** — the two-target arm and negative (d) are `workflow-surface`'s |

### 9.2 Where the arms live

**Portable suite** (no host prerequisite): the vocabulary and
`REQUIRED_FOR_CLEAN_ENVIRONMENT`; policy spellability; the
two-known-definitions match; `qualifies` over constructed receipts,
including the decoy version string and the incomparable pair;
`derive_scope`'s fourth row over value fixtures; `admission_record` and its
refusal; receipt validation, including a `mount_plan_identity` disagreeing
with its mounts; manifest rows, symlink escape, SONAME collision and `.pth`
handling over synthetic closures; canonical mount comparison over synthetic
`mountinfo`; the minimal receipt's byte-stable projection.

**Acceptance tier** (`tests/acceptance/`), behind a **confinement gate**
that errors and never skips, on the certified-tuple gate's pattern: `bwrap`
with `--info-fd`, user namespaces enabled, `ld.so --list` callable. Every arm
that executes under `confined-v1` lives here: R15's arms, R4's live
derivation and graded run, R9 and R16 end to end, R13's out-of-closure
import, R21(b) and (c). These arms need **no durable root**. The aggregate
runner `tools/cut13_acceptance.py` does, because it executes the cut-12
prefix first — so the ext4 recertification on kernel 7.1.11 is a
**discharge prerequisite** for cut 13, though not an implementation
dependency of anything in this slice.

**N2**: `n2_arms_cut13.py` declares every selected arm with its sabotage in
`boundary.py`, `confinement.py`, `replay.py`, `verify.py` or `recipe.py`;
`test_n2_cut13.py` and `tools/cut13_acceptance.py` follow the cut-12 pattern
with `PREFIX_RUNNERS = ("cut12_acceptance.py",)`.

### 9.3 Limitations, banked as unrun by design

- `shell:` rules under `confined-v1`: no shell is in the closure.
- Two confined runs racing to publish one snapshot: covered by §4.3's
  atomic publish and loser rule, not by a test that races them.
- Host-side mutation is detected at two observations, not prevented (§4.4's
  threat model): a modify-read-restore sequence between them passes both
  checks. The host and boundary owner are trusted; R15's arm — a mutation
  present at an observation yields no run — is what is claimed.
- An N2 sabotage of probe.py does not reach the sandbox, whose beliefs
  tree is the closure's own copy; every cut-13 arm sabotages host-side
  code.
- PYTHONPATH is not captured (§5.1).

## 10. What changes elsewhere

- `test_capability_boundary.py`'s `RAW_WRITE_ALLOWLIST` is compared for
  equality. `beliefs/confinement.py` is the third byte-writing module —
  `copy2`, `write_text`, `symlink_to` (manifested and rendered symlinks),
  `rename` (publication), and `rmtree` (discarding a losing temporary build)
  — and the allowlist gains exactly that entry in the same change, a claim
  weighed as its docstring asks. A primitive the implementation turns out
  not to need is removed from the entry, never left as slack.
- beliefs/probe.py is the fourth raw-write surface, {touch, unlink}: its
  one write check touches and removes a file under the output root with
  inventoried operations, so the equality allowlist weighs it rather than
  a raw os.open escaping the inventory.
- `adapter.py`: `capture_environment` becomes the closure walk; `build_argv`
  takes interpreter and paths explicitly; `run_engine` remains the only
  **Snakemake engine-launch** subprocess for the minimal policy (the `v2`
  environment capture invokes `ld.so --list`, a second subprocess site in
  `adapter.py`), and the gated confined launch is `confinement.py`'s.
- `fixtures_cut3.py`: every `run_*` helper passes `boundary_policy=MINIMAL`
  explicitly.
- `science.environment.v2` is minted; `v1` is retired with its shape.
- Ledger: `run-confinement` closes at banking; a new finding records that
  **verification publication** crosses the persistence seam and no boundary
  names it; the roadmap is re-ranked at cut 13 with `workflow-surface` as
  row 1, and Appendix A regenerated by `roadmap_status.py`.
- The host: the confined-arm tests need only the confinement gate —
  bubblewrap, user namespaces, `ld.so --list`. The aggregate
  `tools/cut13_acceptance.py` runner also needs the recertified
  durable-prefix host, because it executes the cut-12 prefix; the ext4
  recertification on kernel 7.1.11 is therefore a discharge prerequisite
  and not this slice's implementation dependency (§9.2).

## 11. Alternatives rejected

- **Reconstruction as reinstallation** — a holdings-backed environment
  rebuild. Adds a store the design does not contain; §4.5 defines the
  environment as held content.
- **Mounting the host prefix read-only** — exposes unmanifested bytes and
  stays host-mutable; the manifest would not describe what is reachable.
- **A twin probe sandbox** — proves nothing about the engine's own
  namespaces; and `--info-fd` fires before the mount table is final.
- **Receipt capabilities copied from the policy** — an assertion, not an
  observation; §7.3 says which the receipt is.
- **`REQUIRED_FOR_CLEAN_ENVIRONMENT = frozenset(CAPABILITIES)`** — a future
  optional capability would become an admission requirement silently.
- **Deleting and rebuilding a mismatching snapshot** — destroys evidence and
  races concurrent runs.
- **Immutable materialization** to close the modify-read-restore window —
  substantially different work; the slice trusts the host owner and says so
  (§4.4).
- **Extending `science.boundary-receipt.v1` with the confined members** —
  reshapes a versioned identity; `v2` is minted instead (§6.3).
- **R16 by post-built fixture mutation** — the arm would then not be about a
  boundary-produced execution.
- **Durable verification publication in this slice** — crosses the
  persistence seam; recorded as a roadmap finding instead.

## 12. Verification

The slice is done when: the portable suite passes with its count reported
from the summary line; the confined-arm tests pass on a host meeting the
confinement gate alone; `tools/cut13_acceptance.py` exits 0 on a host that
meets the confinement gate **and** carries the recertified durable prefix,
running the cut-12 prefix, the confined arms and the N2 audit in order,
never skipping; every arm in `n2_arms_cut13.py` audits `sound`; Ruff
and Pyright are clean; and the results record, the ledger row, and the
roadmap re-ranking land in the banking change.
