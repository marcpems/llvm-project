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
