"""No toolchain build/download. Only compile the matching profile runtime."""
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

here = Path(__file__).resolve().parent
root = here.parents[1]
src = root / "compiler-rt/lib/profile"
arch = sys.argv[1]
target = {"arm64":"aarch64", "x64":"x86_64"}[arch]
work = root / ("native-smoke-" + arch)
work.mkdir(exist_ok=True)

def run(cmd, **kw):
    p = subprocess.run(list(map(str, cmd)), cwd=work, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True, **kw)
    if p.returncode:
        raise RuntimeError(f"{cmd}\n{p.stdout}")
    return p.stdout

def llvm_toolchain():
    bins = {Path(p).parent for n in ("clang.exe", "llvm-profdata.exe") if (p := shutil.which(n))}
    bins.add(Path(os.environ["ProgramFiles"]) / "LLVM/bin")
    if "VCINSTALLDIR" in os.environ:
        bins.update(Path(os.environ["VCINSTALLDIR"]).glob("Tools/Llvm/*/bin"))
    candidates = []
    for b in bins:
        if all((b/n).is_file() for n in ("clang.exe","llvm-profdata.exe","lld-link.exe")):
            version = run([b/"clang.exe","--version"])
            print(b,version.splitlines()[0],flush=True)
            candidates.append((tuple(map(int,re.search(r"clang version (\d+)\.(\d+)\.(\d+)",version).groups())),str(b)))
    if not candidates:
        raise RuntimeError("No complete runner-provided LLVM toolchain")
    return Path(max(candidates)[1])

tools = llvm_toolchain()
clang = tools/"clang.exe"
profdata = tools/"llvm-profdata.exe"
flags = [f"--target={target}-pc-windows-msvc", "-fms-runtime-lib=dll"]
print("reader:",run([profdata,"--version"]).strip(),flush=True)
names = ["InstrProfiling", "InstrProfilingInternal", "InstrProfilingBuffer", "InstrProfilingMerge",
         "InstrProfilingMergeFile", "InstrProfilingNameVar", "InstrProfilingVersionVar", "InstrProfilingWriter",
         "InstrProfilingPlatformWindows", "InstrProfilingFile", "InstrProfilingUtil", "InstrProfilingValue", "WindowsMMap"]
objects = []
for f in [*(src/(n+".c") for n in names), src/"InstrProfilingRuntime.cpp"]:
    run([clang,*flags,"-O2","-DNDEBUG","-D_CRT_SECURE_NO_WARNINGS","-DCOMPILER_RT_HAS_ATOMICS=1",
         "-I", root/"compiler-rt/include", "-c", f,"-o",f.stem+".obj"])
    objects.append(f.stem+".obj")
run(["lib.exe","/nologo","/out:qualification-profile.lib", *objects])
ir = (here/(arch+".ll")).read_text()
assert '@__llvm_profile_record_rvas_v2 = external constant i32' in ir
for shape in ("dense","sparse"):
    text = ir
    if shape == "sparse":
        text, changes = re.subn(r'(section "\.lprf(?:d\$0|r\$M)"[^\n]*?, align )\d+', r'\g<1>128', ir)
        assert changes == 4
    (work/(shape+".ll")).write_text(text)
    run([clang,*flags,"-c",shape+".ll","-o",shape+".obj"])
    for linker in (Path(shutil.which("link.exe")),tools/"lld-link.exe"):
        stem = f"{arch}-{shape}-{linker.stem}"
        print("link and execute:",stem,str(linker),flush=True)
        exe = work/(stem+".exe")
        run([linker,"/nologo","/incremental:no","/opt:ref,icf","/nodefaultlib:clang_rt.profile.lib",
             "/defaultlib:msvcrt","/defaultlib:oldnames","/out:"+str(exe),shape+".obj","qualification-profile.lib"])
        image = exe.read_bytes()
        machine, = struct.unpack_from("<H",image,struct.unpack_from("<I",image,60)[0]+4)
        assert machine == {"arm64":0xaa64,"x64":0x8664}[arch]
        for stale in work.glob(stem+"-*.profraw"):
            stale.unlink()
        output = run([exe],env={**os.environ,"LLVM_PROFILE_FILE":str(work/(stem+"-%m.profraw"))})
        assert "LLVM Profile Error" not in output, output
        raw, = work.glob(stem+"-*.profraw")
        report = run([profdata,"show","--all-functions","--counts","--ic-targets",raw])
        print(report,flush=True)
        rows = re.findall(r"^  (\S+):\n    Hash: .*\n    Counters: \d+\n    Function count: (\d+)\n    Indirect Call Site Count: (\d+)\n    Block counts: \[(.*?)\]",report,re.M)
        assert sorted(rows) == [("callee","6","0","3"),("caller","3","1","6")], rows
        assert re.search(r"^\s*\[\s*0,\s*callee,\s*6\s*\] \(100\.00%\)",report,re.M)
        assert "Total functions: 2\n" in report
        print("PASS:", stem, "caller=3 loop=6 callee=6 branch=3 indirect=6",flush=True)
