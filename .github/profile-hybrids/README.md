# Hybrid COFF profile replay

This validation-only job builds the profile archive from each pinned compiler-rt
revision. It compiles checked-in **text IR** using the same official Arm64
Clang 23.1.4 backend on a standard `windows-11-arm` runner. It does not rebuild
the frontend or LLVM pass on the runner.

The IR was generated from the adjacent C fixtures using Clang 23.1.4 with
`-fprofile-instr-generate -Xclang -disable-llvm-passes`, then `opt
-passes=instrprof -S` built from `f25e7ef948a05e0de2d4ec11843956be6ffdf950`
(baseline) or `aaf1bc5225963d48fb9658023185ddc8243046ea` (published
candidate). `entry.c` targets Arm64EC and `leaf.c` targets x64 at `-O2`.
`probe.c` targets AArch64 and Arm64EC at `-O1`, with `VIEW=native` or `ec`
and value profiling enabled. Only source/debug locations and module labels
were normalized. EC lowering is identical and therefore stored once.

* **Mixed EXE:** link an EC caller with an ordinary x64 leaf. The baseline
  must link, run and decode `main=1` and `leaf=3` under both linkers. Published
  candidate objects must fail to link specifically for the missing v2 ABI
  marker. The reader-only fix at `be719854d4e4acff4a8752bbd0a5f2bec76e84d7`
  uses the same candidate objects (its emitter change is comments only) and
  unmodified runtimes from that commit. It must link and reproduce baseline counts.
* **Arm64X DLL:** combine genuine native and EC objects and their per-view
  runtimes. Native and x64 processes load the same DLL, select distinct exports,
  serialize a buffer, and emit a raw profile. Validate dispatch count 7, target
  counts 4 and 3, and both indirect targets in each indexed profile. Microsoft
  LINK must pass. LLD 23.1.4 may produce a zero-counter raw profile even at
  baseline; record that exact diagnostic per view, never as a decode pass.

The artifact contains tool versions, IR/runtime SHA-256 digests, phase/linker/
view results and decoded counts; no toolchains or executables are published.
Green means the expected compatibility **failure** was reproduced, not that
the published candidate supports arbitrary Arm64EC/Arm64X inputs.
