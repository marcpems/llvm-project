import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess

BASE = "f25e7ef948a05e0de2d4ec11843956be6ffdf950"
CANDIDATE = "aaf1bc5225963d48fb9658023185ddc8243046ea"
FIXED = "be719854d4e4acff4a8752bbd0a5f2bec76e84d7"
HERE = Path(__file__).resolve().parent
ROOT = Path.cwd()
WORK = ROOT / "work"
OUT = ROOT / "results"
TOOLS = Path(os.environ["LLVM_TOOLS"]).resolve()
VC = Path(os.environ["VCToolsInstallDir"])
SDK = Path(os.environ["WindowsSdkDir"]) / "Lib" / os.environ["WindowsSDKLibVersion"].strip("\\/")
LINK = VC / "bin/Hostarm64/arm64/link.exe"
MARKER = "__llvm_profile_record_rvas_v2"
TRIPLES = dict(native="aarch64", ec="arm64ec", x64="x86_64")
report = {"candidate": CANDIDATE, "fixed": FIXED, "base": BASE, "fixtures": {}, "archives": {}, "rows": []}


def save():
    (OUT / "results.json").write_text(json.dumps(report, indent=2))


def digest(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def run(args, *, env=None, check=True):
    result = subprocess.run(list(map(str, args)), env=env, cwd=WORK, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, errors="replace", timeout=180)
    if check and result.returncode:
        raise RuntimeError(f"{Path(args[0]).name} exit {result.returncode}:\n{result.stdout[-3000:]}")
    return result


def libs(arch):
    roots = {"native": ["arm64"], "ec": ["arm64ec", "arm64", "x64"], "x64": ["x64"]}[arch]
    paths = [VC / "lib" / t for t in roots]
    for t in roots:
        if t != "arm64ec":
            paths.extend([SDK / "ucrt" / t, SDK / "um" / t])
    if not all(p.is_dir() for p in paths):
        raise RuntimeError(f"VC/SDK libraries are incomplete for {arch}")
    return {**os.environ, "LIB": os.pathsep.join(map(str, paths))}


def clang(arch):
    return [TOOLS / "clang.exe", f"--target={TRIPLES[arch]}-pc-windows-msvc", "-fms-runtime-lib=static"]


def runtime(repo, phase, arch):
    src = repo / "compiler-rt/lib/profile"
    cmake = (src / "CMakeLists.txt").read_text()
    sources = re.findall(r"^\s+(\w+\.(?:cpp|c))\s*$", cmake.split("if(FUCHSIA OR UNIX)")[0], re.M)
    if len(set(sources)) != 21 or len(sources) != 21:
        raise RuntimeError(f"Unexpected Windows profile source inventory: {sources}")
    out = WORK / f"{phase}-{arch}-rt"
    out.mkdir()
    def build(n):
        run([TOOLS / "clang-cl.exe", f"--target={TRIPLES[arch]}-pc-windows-msvc", "/nologo", "/c",
             "/DWIN32", "/D_WINDOWS", "/O2", "/Ob2", "/DNDEBUG", "/MT", "-fno-lto",
             "-DCOMPILER_RT_HAS_ATOMICS=1", "-Wno-ignored-attributes",
             "/I" + str(repo / "compiler-rt/lib"), "/I" + str(repo / "compiler-rt/include"),
             src / n, "/Fo" + str(out / (n + ".obj"))])

    with concurrent.futures.ThreadPoolExecutor(4) as pool:
        list(pool.map(build, sources))
    archive = out / "profile.lib"
    run([LINK.with_name("lib.exe"), "/nologo", "/machine:" + ("arm64ec" if arch == "ec" else "arm64"),
         "/out:" + str(archive), *sorted(out.glob("*.obj"))])
    report["archives"][out.name] = digest(archive)
    return archive


def decode(exe, args, tag):
    raw = WORK / (tag + ".profraw")
    run([exe, *args], env={**os.environ, "LLVM_PROFILE_FILE": str(raw)})
    indexed = WORK / (tag + ".profdata")
    merged = run([TOOLS / "llvm-profdata.exe", "merge", "--failure-mode=any", raw, "-o", indexed], check=False)
    if merged.returncode:
        if "number of counters is zero" in merged.stdout:
            return {"decode": "malformed instrumentation profile data: number of counters is zero"}
        raise RuntimeError(merged.stdout)
    counts = run([TOOLS / "llvm-profdata.exe", "show", "--all-functions", "--counts", "--ic-targets", indexed]).stdout
    (OUT / (tag + ".txt")).write_text(counts)
    return {"decode": "pass", "raw_bytes": raw.stat().st_size, "counts": counts}


def main():
    if platform.machine().lower() not in ("arm64", "aarch64"):
        raise RuntimeError("A native Windows Arm64 runner is required")
    for p in (WORK, OUT):
        p.mkdir()
    report["compiler_version"] = run([TOOLS / "clang.exe", "--version"]).stdout.splitlines()[0]
    if "23.1.4" not in report["compiler_version"]:
        raise RuntimeError("Wrong backend")
    report["link_version"] = run([LINK, "/?"], check=False).stdout.splitlines()[0]
    report["lld_version"] = run([TOOLS / "lld-link.exe", "--version"]).stdout.strip()
    for phase in ("base", "candidate"):
        for unit, arch in (("entry", "ec"), ("leaf", "x64"), ("native", "native"), ("ec", "ec")):
            ir = HERE / "ir" / ((unit if unit in ("entry", "ec") else phase + "-" + unit) + ".ll")
            text = ir.read_text()
            indexed = phase == "candidate" and arch != "ec"
            if any((s in text) != indexed for s in (".lprfr$M", MARKER)):
                raise RuntimeError(f"Wrong lowering in {ir.name}")
            report["fixtures"][ir.name] = digest(ir)
            run([*clang(arch), "-O1" if unit in ("native", "ec") else "-O2",
                 "-c", ir, "-o", f"{phase}-{unit}.obj"])
    for arch, view in (("native", 1), ("ec", 2)):
        run([*clang(arch), "-O2", f"-DVIEW={arch}", f"-DID={view}", "-c", HERE / "bridge.c",
             "-o", f"bridge-{arch}.obj"])
    for arch in ("native", "x64"):
        run([*clang(arch), "-O2", "-c", HERE / "host.c", "-o", f"host-{arch}.obj"])
        run([LINK, "/nologo", f"/out:host-{arch}.exe", f"host-{arch}.obj", "kernel32.lib", "libcmt.lib", "oldnames.lib"],
            env=libs(arch))
    for phase, rev in (("base", BASE), ("candidate", CANDIDATE), ("fixed", FIXED)):
        gen = "candidate" if phase == "fixed" else phase
        repo = ROOT / phase
        if run(["git", "-C", repo, "rev-parse", "HEAD"]).stdout.strip() != rev:
            raise RuntimeError("Wrong runtime source")
        run(["git", "-C", repo, "diff", "--quiet", rev, "--", "compiler-rt"])
        ec = runtime(repo, phase, "ec")
        native = runtime(repo, phase, "native")
        for linker, ld in (("LINK", LINK), ("LLD", TOOLS / "lld-link.exe")):
            tag = f"{phase}-{linker}"
            common = [ld, "/nologo", "/incremental:no", "/opt:ref,icf", "/nodefaultlib:clang_rt.profile.lib",
                      "/defaultlib:libcmt", "/defaultlib:oldnames"]
            mixed = run([*common, "/machine:arm64ec", "/out:" + tag + ".exe", gen + "-entry.obj",
                         gen + "-leaf.obj", ec], env=libs("ec"), check=False)
            row = {"case": "EC caller + x64 leaf", "phase": phase, "linker": linker, "link_rc": mixed.returncode}
            report["rows"].append(row)
            if phase == "candidate":
                if not mixed.returncode or MARKER not in mixed.stdout or not re.search("undefined|unresolved", mixed.stdout, re.I):
                    raise RuntimeError("Expected the published candidate's unresolved ABI marker only")
                symbols = re.findall(r"(?:undefined|unresolved external) symbol:?\s+([#\w]+)", mixed.stdout, re.I)
                if not symbols or any(s.lstrip("#") != MARKER for s in symbols):
                    raise RuntimeError("Unexpected additional unresolved symbol")
                row["expected_unresolved"] = symbols
            else:
                if mixed.returncode:
                    raise RuntimeError(mixed.stdout)
                decoded = decode(WORK / (tag + ".exe"), [], tag + "-mixed")
                counts = decoded.pop("counts")
                for fn, nc, fc, blocks in (("leaf", 2, 3, 1), ("main", 2, 1, 3)):
                    if not re.search(rf"  {fn}:\n(?:[^\n]*\n){{1,4}}?    Counters: {nc}\n    Function count: {fc}\n(?:    Indirect Call Site Count: \d+\n)?    Block counts: \[{blocks}\]", counts):
                        raise RuntimeError(f"Incorrect {fn} counts")
                row.update(decoded)
            save()
            dll = WORK / (tag + ".dll")
            run([*common, "/machine:arm64x", "/dll", "/out:" + str(dll),
                 "/libpath:" + str(VC / "lib/arm64ec"), gen + "-native.obj", "bridge-native.obj",
                 gen + "-ec.obj", "bridge-ec.obj", native, ec, "kernel32.lib"], env=libs("native"))
            headers = run([TOOLS / "llvm-readobj.exe", "--file-headers", "--coff-load-config", "--coff-exports", dll]).stdout
            if "HybridObject {" not in headers or headers.count("Name: view_id") != 2:
                raise RuntimeError("Not a two-view ARM64X DLL")
            for arch, view, expected in (("native", 1, "native"), ("x64", 2, "ec")):
                decoded = decode(WORK / f"host-{arch}.exe", [dll, str(view)], tag + "-" + arch)
                counts = decoded.pop("counts", "")
                if counts:
                    rows = re.findall(r"^  (\S+):\n    Hash: .*\n    Counters: (\d+)\n    Function count: (\d+)\n    Indirect Call Site Count: (\d+)\n    Block counts: \[(.*?)\]", counts, re.M)
                    if sorted(rows) != sorted([(expected+"_alpha","1","4","0",""), (expected+"_beta","1","3","0",""),
                                               (expected+"_dispatch","2","7","1","4")]):
                        raise RuntimeError("Wrong composite counts")
                    targets = re.findall(r"\[\s*0,\s*(\S+),\s*(\d+) \]", counts)
                    if sorted(targets) != [(expected+"_alpha","4"), (expected+"_beta","3")]:
                        raise RuntimeError("Wrong composite indirect targets")
                elif linker != "LLD":
                    raise RuntimeError("Microsoft LINK composite profile did not decode")
                report["rows"].append(dict(case="ARM64X DLL", phase=phase, linker=linker, view=arch, **decoded))
                save()
    for view in ("native", "x64"):
        outcomes = [r["decode"] for r in report["rows"] if r.get("view") == view and r["linker"] == "LLD"]
        if outcomes[0] == "pass" and any(v != "pass" for v in outcomes[1:]):
            raise RuntimeError("Candidate-only LLD composite decode regression")
    print(json.dumps(report["rows"], indent=2))


if __name__ == "__main__":
    main()
