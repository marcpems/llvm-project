# COFF record pointer validation (fork only)

The `COFF profile record pointers A/B` workflow starts on pushes to
`validation/coff-profile-record-pointers` in `marcpems/llvm-project`.
Publish the intended experiment revision **first**, put its full SHA in
`candidate.sha`, then push the validation branch. All jobs use that immutable
revision, which must descend from `f25e7ef948a05e0de2d4ec11843956be6ffdf950`.
To compare a later candidate, change only `candidate.sha` and push again.
No default-branch workflow, secrets, or write token are required.

Each native Windows Arm64/x64, Linux x64 and macOS Arm64 job builds only the
host backend, Clang and the selected LLVM tools. It reuses the Ninja directory
for the candidate and builds a separate profile runtime with each Clang.
Cold builds are subject to standard hosted disk and six-hour job limits.

Per-phase artifacts record source SHA, compiler version, driver command,
selected runtime hash, lit results, raw/indexed profiles, MC/DC coverage,
and executable/object sizes. The executable runs twice into a shared `%m`
file; independent runs merged with `llvm-profdata` must produce the same
counts and bitmap. Windows uses both Microsoft LINK and LLD; Linux uses
BFD and LLD; macOS uses the SDK's native linker. The actual driver
invocation is checked, not inferred from a flag.

`paired-*.json` contains ten interleaved candidate/baseline samples on the
same runner and linker: instrumented hot-loop time, serialization into a
preallocated buffer, executable bytes, and observed ratios/ranges. It is
a microbenchmark, not a Rust throughput or application-wide speed estimate.
