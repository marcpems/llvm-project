# COFF record pointer validation (fork only)

The `COFF profile record pointers A/B` workflow starts on pushes to
`validation/coff-profile-record-pointers` in `marcpems/llvm-project`.
Publish the intended experiment revision **first**, put its full SHA in
`candidate.sha`, then push the validation branch. All jobs use that immutable
revision, which must descend from `f25e7ef948a05e0de2d4ec11843956be6ffdf950`.
To compare a later candidate, change only `candidate.sha` and push again.
No default-branch workflow, secrets, or write token are required.

The default is all four full builds. To avoid repeating healthy jobs, a
validation commit can select lanes using a trailer, for example
`CI-Lanes: ubuntu-24.04,macos-15:runtime`. `:runtime` is an additional
non-Windows control: it uses the checksum-verified LLVM 23.1.4 release tools
with a separately built runtime from each exact revision. It is not evidence
of a source-matched compiler or a substitute for the full build.

An optional `macos-15-intel:runtime` lane uses conda-forge's native Intel
Clang/LLVM 23.1.4 binaries: upstream publishes only Arm64 macOS archives.
The installed package URLs and compiler/runtime hashes are retained. The
Intel lane never runs a full build and does not change the default matrix.

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

Executable `llvm-cov export` records stdout, stderr and status independently
of the raw profile oracle. A matched pair of Microsoft LINK “symbol name is
empty” errors is explicitly recorded as the separate coverage-reader issue.
Windows also checks the executable's profile against its input object's MC/DC
mapping, avoiding PE section-tail padding on that separate check.

`paired-*.json` contains ten interleaved candidate/baseline samples on the
same runner and linker: instrumented hot-loop time, serialization into a
preallocated buffer, executable bytes, and observed ratios/ranges. It is
a microbenchmark, not a Rust throughput or application-wide speed estimate.
