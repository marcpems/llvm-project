# COFF record discovery: Windows measurements

Candidate `aaf1bc5225963d48fb9658023185ddc8243046ea`, baseline `f25e7ef948a05e0de2d4ec11843956be6ffdf950`.
Same pre-lowering IR and backend; source-matched baseline and candidate `opt -passes=instrprof`, respective compiler-rt archives. Windows Arm64 host; x64 programs under emulation. Explicit invocations of Microsoft LINK 14.52.37029.0 and LLD 23.1.4.

Counts and function identities match for every row using unchanged llvm-profdata. On-disk PE sizes (not RSS); wall timings separate the instrumented workload and raw serialization into preallocated memory. Percentages are median within-pair changes over ten alternating pairs, not total application slowdowns. Results on a shared host are descriptive.

| Target | Workload | Linker | Records | EXE baseline -> candidate (bytes) | Change | Raw change | Hot time | Buffer serialization |
|---|---|---|---:|---|---:|---:|---:|---:|
| Arm64 | 1026-record synthetic | link | 1026 | 153088 -> 161792 | +8704 (+5.69%) | +0 | -2.0% | -15.7% |
| Arm64 | 1026-record synthetic | lld-link | 1026 | 152064 -> 160768 | +8704 (+5.72%) | +0 | -0.3% | -5.4% |
| Arm64 | LLVM Itanium demangler | link | 738 | 299520 -> 306176 | +6656 (+2.22%) | +0 | -0.7% | +23.3% |
| Arm64 | LLVM Itanium demangler | lld-link | 738 | 293376 -> 300032 | +6656 (+2.27%) | +0 | +0.6% | +23.1% |
| x64 | 1026-record synthetic | link | 1026 | 161280 -> 168448 | +7168 (+4.44%) | +0 | -3.2% | +1.8% |
| x64 | 1026-record synthetic | lld-link | 1026 | 160768 -> 168448 | +7680 (+4.78%) | +0 | -3.2% | -2.2% |
| x64 | LLVM Itanium demangler | link | 738 | 266240 -> 272384 | +6144 (+2.31%) | +0 | +19.1% | +17.1% |
| x64 | LLVM Itanium demangler | lld-link | 738 | 265728 -> 272896 | +7168 (+2.70%) | +0 | -2.1% | -12.1% |

The demangler's short unpinned intervals varied substantially between runs. As a sensitivity check, we repeated the same ten alternating pairs with eight times as many demangles and buffer writes per timed block. With unrestricted scheduling the Arm64 serialization medians were still +18.9% (LINK) and +9.8% (LLD). Binding **only the benchmark thread** to the same eligible logical CPU greatly reduced dispersion:

| Target | Linker | Demangling (median paired change) | Buffer serialization (median paired change) | Serialization paired range |
|---|---|---:|---:|---:|
| Arm64, native | LINK | +0.13% | -0.21% | -2.98% to +2.71% |
| Arm64, native | LLD | -0.02% | +0.89% | -0.42% to +1.72% |
| x64, emulated | LINK | -1.80% | -1.16% | -7.33% to +3.07% |
| x64, emulated | LLD | +0.29% | -0.66% | -1.44% to -0.04% |

These are steady-state measurements of ordinary linked layouts, not an assurance of zero overhead for sparse or reordered records. Forced noncontiguous records take the packing path, which copies records and adjusts their relative fields. Raw profile size and decoded counts were unchanged for these layouts too.

The demangler `.obj` grew by 39,815 bytes on each target (5.54% Arm64, 6.49% x64), and its mapped PE size grew by 4,096 to 8,192 bytes depending on target and linker. The RVA slots added no loader relocations in forced-rebase DLL tests. The index is not size-neutral even though it uses only four bytes per record in the final image.
