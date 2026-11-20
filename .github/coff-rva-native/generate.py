"""Reproduce the two snapshots using Clang and the candidate's instrprof pass."""
from pathlib import Path
import re
import subprocess
import sys

here = Path(__file__).resolve().parent
test = here.parents[1] / "compiler-rt/test/profile/Windows/instrprof-record-padding.c"
clang, opt = sys.argv[1:]
for arch, target in [("arm64", "aarch64"), ("x64", "x86_64")]:
    pre = subprocess.check_output(
        [clang, f"--target={target}-pc-windows-msvc", "-fms-runtime-lib=dll", "-O0",
         "-fdebug-compilation-dir=.", "-fcoverage-compilation-dir=.", f"-ffile-prefix-map={test.parent}=.",
         "-fprofile-instr-generate", "-mllvm", "-enable-value-profiling",
         "-Xclang", "-disable-llvm-passes", "-S", "-emit-llvm", test.name, "-o", "-"],
        cwd=test.parent,
    )
    ir = subprocess.check_output([opt, "-passes=instrprof", "-S", "-o", "-"], input=pre).decode().replace("\r\n", "\n")
    assert str(test.parent) not in ir and not re.search(r'\b[A-Za-z]:[\\/]', ir)
    assert ir.count('section ".lprfr$M"') == ir.count('section ".lprfd$0"') == 2
    (here / (arch+".ll")).write_bytes(ir.encode())
