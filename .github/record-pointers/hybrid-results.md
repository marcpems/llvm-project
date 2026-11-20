# Windows hybrid profiling: Arm64EC and Arm64X

This comparison covers the [repaired draft](https://github.com/llvm/llvm-project/commit/be719854d4e4acff4a8752bbd0a5f2bec76e84d7) versus its prerequisite, `f25e7ef948`. The earlier draft `aaf1bc5225` is a separate control. Tests ran on Windows on Arm64, using Clang 23.1.4 frontend/backend, baseline or draft `opt -passes=instrprof`, source-built profile runtimes, Microsoft LINK 14.52.37029.0, LLD 23.1.4, and matching `llvm-profdata`. This tests the runtime sources, not whether an LLVM distribution ships an Arm64EC archive.

## What actually works

| Configuration | Microsoft LINK | LLD |
|---|---|---|
| Standalone Arm64EC executable using an EC runtime | Passed: all 516 function records, branch counts and indirect targets (48 and 16 calls) matched baseline | Passed the same checks |
| Arm64EC caller plus instrumented x64 object, EC runtime | Earlier draft failed to link; repaired version passed, including three indirect calls in **each direction** | Same failure before the repair; same exact counts after |
| Arm64X DLL with native Arm64 and Arm64EC objects | Passed independently in native Arm64 and x64 processes loading the **same DLL** | Baseline **and** repaired version produced malformed profiles in both views |
| Same Arm64X DLL with an extra indexed x64 object on the EC side | Earlier draft failed to link; repair restored both views, with three native records and four EC-view records | Repair restores linking, **not** profile validity |

EC code still emits legacy records. Ordinary x64 inputs can emit an RVA index before the compiler knows they will be linked into an EC image. The earlier EC runtime lacked its required marker; the repair enables the **reader**, not EC emission. Merely defining the symbol would have allowed the link while losing x64 records.

For the Microsoft-linked composite, each process resolved the same exported name to its intended implementation. We reserved the DLL's preferred base to force relocation, then reset and dumped three times in each process. The raw record count equaled the number of distinct expected names; indirect targets accumulated to **12 and 9** in each view with no foreign-view records. Unchanged raw lengths were 512 bytes per view for the two-ABI case and 512 / 624 bytes for the native / EC views with the additional x64 input.

For LLD, the map and raw header explain the failure: the baseline sorted both runtimes' profile bounds and data together. Each view saw records from the other view and a zero sentinel as a function record (`llvm-profdata`: “number of counters is zero”). Microsoft LINK separated the contributions by view. The index is not a substitute for that separation. No useful LLD composite profile-write timing is claimed.

## Cost against the prerequisite baseline

The timings are changes in median paired **elapsed time**. “Workload” excludes profile output. “Buffer write” measures repeated serialization to preallocated memory, not link time, disk I/O, or the application's end-to-end wall time.

| Instrumented image / executing view | Linker | PE bytes: baseline → repaired | Workload | Buffer write |
|---|---|---:|---:|---:|
| Arm64EC-only executable, 516 records | LINK | 297,472 → 301,568 (+1.38%) | +1.33% | +0.92% |
| Arm64EC-only executable, 516 records | LLD | 297,984 → 301,568 (+1.20%) | −0.22% | +1.50% |
| Arm64X DLL, native Arm64 view | LINK | 413,184 → 425,472 (+2.97%) | −0.14% | +1.15% |
| Same DLL, EC view in x64 process | LINK | same file | +0.01% | −7.02% |
| Arm64X DLL with extra x64 object, native view | LINK | 413,184 → 425,472 (+2.97%) | +0.08% | +5.29% |
| Same three-ABI DLL, EC view in x64 process | LINK | same file | −1.39% | **+19.45%** |
| Arm64X DLL, either view | LLD | 400,896 → 409,088 (+2.04%) | not qualified | not qualified |

**Interpretation:** Arm64EC-only instrumented objects and raw profiles did not grow: the added bytes in the executable are runtime code, not index entries for EC functions. The original draft before the reader repair had zero executable growth for that fixture; that version could not link the mixed EC/x64 case. For Arm64X, there is one PE on disk, not a separate size increase per view.

The EC benchmark used 12 CPU-pinned, order-balanced samples per variant/linker; cached file-write medians were +5.10% / +6.79% (LINK / LLD), with individual pairs ranging from negative to strongly positive. The composite benchmark used ten alternating CPU-pinned pairs per view, with 2,000,000 indirect dispatches and 500,000 buffer writes per timed block. The composite profiles are intentionally small. The +19.45% row ranged from +17.90% to +20.89%; it is a repeatable serialization cost **in that mixed fixture**, not a 19% application slowdown. These are not end-to-end compiler or Cargo build benchmarks.
