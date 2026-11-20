import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import traceback

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "profile-padding"))
from compare import VERSION, configure_runtime, get_tools, prepare_helpers, run

WINDOWS = os.name == "nt"
DARWIN = sys.platform == "darwin"
EXE = ".exe" if WINDOWS else ""


def text(*args):
    return subprocess.check_output(args, text=True).strip()


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_compiler(src, build, jobs):
    cc, cxx = ("cl", "cl") if WINDOWS else ("clang", "clang++")
    arm64_bootstrap = WINDOWS and os.environ.get("ARCH") == "arm64"
    if arm64_bootstrap:
        # Native MSVC 14.52 ICEs on baseline clang/lib/Analysis/Consumed.cpp.
        cc = cxx = shutil.which("clang-cl.exe") or str(Path(os.environ["ProgramFiles"]) / "LLVM/bin/clang-cl.exe")
        print(text(cc, "--version"), flush=True)
    release = "/O1 /DNDEBUG" if WINDOWS else "-O1 -g0 -DNDEBUG"
    args = [
        "cmake", "-S", src / "llvm", "-B", build, "-G", "Ninja",
        "-DCMAKE_BUILD_TYPE=Release", f"-DCMAKE_C_COMPILER={cc}", f"-DCMAKE_CXX_COMPILER={cxx}",
        f"-DCMAKE_C_FLAGS_RELEASE={release}", f"-DCMAKE_CXX_FLAGS_RELEASE={release}",
        "-DLLVM_ENABLE_PROJECTS=clang", "-DLLVM_TARGETS_TO_BUILD=Native",
        "-DLLVM_PARALLEL_LINK_JOBS=1", "-DLLVM_INCLUDE_BENCHMARKS=OFF",
        "-DLLVM_ENABLE_ZSTD=OFF", "-DLLVM_ENABLE_LIBXML2=OFF", "-DLLVM_ENABLE_ZLIB=OFF",
        "-DCLANG_INCLUDE_TESTS=OFF", "-DCLANG_ENABLE_STATIC_ANALYZER=OFF", "-DCLANG_ENABLE_CIR=OFF",
        "-DLLVM_OMIT_EXPORTS_FROM_CONFIG=ON", f"-DPython3_EXECUTABLE={sys.executable}",
    ]
    if DARWIN:
        args.append(f"-DDEFAULT_SYSROOT={text('xcrun', '--show-sdk-path')}")
    if arm64_bootstrap:
        triple = "aarch64-pc-windows-msvc"
        args += [f"-DCMAKE_C_COMPILER_TARGET={triple}", f"-DCMAKE_CXX_COMPILER_TARGET={triple}",
                 f"-DLLVM_HOST_TRIPLE={triple}"]
    subprocess.run(args, check=True)
    targets = ["clang", "clang-resource-headers", "opt", "llvm-config", "FileCheck",
               "not", "count", "split-file", "llvm-profdata", "llvm-readobj", "llvm-cov"]
    if WINDOWS:
        targets.append("KillTheDoctor")
    subprocess.run(["cmake", "--build", build, "--parallel", str(jobs), "--target", *targets],
                   check=True)
    # Driver aliases may be separate install/build targets.
    alias = build / "bin" / ("clang-cl.exe" if WINDOWS else "clang++")
    if not alias.exists():
        os.link(build / "bin" / ("clang" + EXE), alias)
    elif not WINDOWS and alias.is_symlink():
        assert alias.resolve() == (build / "bin/clang").resolve()
    elif digest(alias) != digest(build / "bin" / ("clang" + EXE)):
        alias.unlink()
        os.link(build / "bin" / ("clang" + EXE), alias)


def llvm_lit(src, tools, out, changes):
    suite = Path("llvm/test/Instrumentation/InstrProfiling")
    cases = {suite / name for name in ("comdat.ll", "platform.ll", "profiling.ll", "mcdc.ll")}
    cases.update(p for p in changes if p.is_relative_to("llvm/test") and p.suffix == ".ll")
    lit = next(p for p in (tools / "bin/llvm-lit", tools / "bin/llvm-lit.py") if p.exists())
    paths = sorted(src / p for p in cases if (src / p).is_file())
    result = out / "llvm-lit.json"
    run([sys.executable, lit, "-sv", "-o", result, *paths], out / "llvm-lit.log")
    tests = json.loads(result.read_text())["tests"]
    if len(tests) != len(paths) or any(t["code"] != "PASS" for t in tests):
        raise RuntimeError(f"LLVM lit did not execute all {len(paths)} checks: {result}")


def profile_lit(src, tools, rt, out, changes, ldflag):
    root = Path("compiler-rt/test/profile")
    cases = {"instrprof-value-prof.c"}
    if WINDOWS:
        cases |= {"Windows/instrprof-name-padding.c", "Windows/instrprof-merge-bitmap-padding.c"}
    for p in changes:
        if not p.is_relative_to(root) or p.suffix not in (".c", ".cpp", ".test", ".ll"):
            continue
        rel = p.relative_to(root)
        if "Inputs" not in rel.parts and (WINDOWS or rel.parts[0] != "Windows"):
            if (src / p).is_file():
                cases.add(rel.as_posix())
    wrapper = out / "lit"
    wrapper.mkdir()
    sites = list((rt / "test/profile").glob("*/lit.site.cfg.py"))
    if DARWIN:
        native_sites = ("Profile-x86_64",) if platform.machine() == "x86_64" else ("Profile-arm64", "Profile-aarch64")
        sites = [p for p in sites if p.parent.name in native_sites]
    site, = sites
    has_external_lld = WINDOWS and bool(shutil.which("lld-link.exe"))
    lld_config = "config.has_lld = True\n" if has_external_lld else ""
    (wrapper / "lit.site.cfg.py").write_text(
        f"config.llvm_tools_dir = {str(tools / 'bin')!r}\n"
        f"{lld_config}"
        f"lit_config.load_config(config, {str(site)!r})\n"
    )
    filt = " :: (?:" + "|".join(re.escape(c) for c in sorted(cases)) + ")$"
    result = out / "profile-lit.json"
    run([sys.executable, src / "llvm/utils/lit/lit.py", "-sv", "-o", result,
         "--filter", filt, f'-Dappend_target_cflags="{ldflag}"', wrapper], out / "profile-lit.log")
    passed = {t["name"].split(" :: ", 1)[-1] for t in json.loads(result.read_text())["tests"]
              if t["code"] == "PASS"}
    if passed != cases:
        raise RuntimeError(f"Profile lit did not pass exactly the selected cases: {cases ^ passed}")


def linkers():
    if WINDOWS:
        if not shutil.which("lld-link.exe"):
            llvm = Path(os.environ["ProgramFiles"]) / "LLVM/bin"
            os.environ["PATH"] += os.pathsep + str(llvm)
        if not shutil.which("lld-link.exe"):
            raise RuntimeError("lld-link.exe is not installed")
        return {"LINK": "-fuse-ld=link.exe", "lld-link": "-fuse-ld=lld"}
    drivers = {"ld": text("xcrun", "--find", "ld")} if DARWIN else {
        "ld.bfd": shutil.which("ld.bfd"), "ld.lld": shutil.which("ld.lld")}
    if not all(drivers.values()):
        raise RuntimeError(f"Missing native linker: {drivers}")
    return {name: f"--ld-path={path}" for name, path in drivers.items()}


def probe(cc, profdata, cov, rt, triple, linker, ldflag, out, bench, phase, readobj):
    resource = Path(text(cc, "-print-resource-dir"))
    common = [f"--target={triple}", f"-resource-dir={rt}", "-nobuiltininc",
              "-idirafter", resource / "include"]
    if WINDOWS:
        common.append("-fms-runtime-lib=dll")
    src = HERE.parent / "profile-padding/mcdc-values.c"
    binary = out / ("probe" + EXE)
    flags = ["-O0", "-fprofile-instr-generate", "-fcoverage-mapping", "-fcoverage-mcdc"]
    obj = out / "probe.o"
    run([cc, *common, *flags, "-c", src, "-o", obj], out / "compile.log")
    args = [cc, *common, ldflag, "-fprofile-instr-generate", obj, "-o", binary]
    trace = subprocess.check_output([*args, "-###"], text=True, stderr=subprocess.STDOUT)
    (out / "driver-trace.txt").write_text(trace)
    line = trace.splitlines()[-1].strip()
    executable = Path(json.JSONDecoder().raw_decode(line)[0])
    if WINDOWS:
        if executable.stem.lower() != linker.lower():
            raise RuntimeError(f"Wrong linker selected: {executable} instead of {linker}")
        if not executable.is_absolute():
            resolved = shutil.which(str(executable))
            if not resolved:
                raise RuntimeError(f"Cannot resolve {executable}")
            executable = Path(resolved)
        if linker == "LINK" and "microsoft visual studio" not in str(executable).lower():
            raise RuntimeError(f"Not the Microsoft linker: {executable}")
    elif executable.resolve() != Path(ldflag.split("=", 1)[1]).resolve():
        raise RuntimeError(f"Wrong linker selected: {executable} instead of {ldflag}")
    archives = [p for p in rt.glob("lib/**/*profile*") if p.suffix in (".lib", ".a")]
    unescape = lambda s: s.replace("\\\\", "/").replace("\\", "/").lower()
    selected = [p for p in archives if unescape(str(p)) in unescape(line)]
    if len(selected) != 1:
        raise RuntimeError(f"Expected link with one just-built runtime, got {selected}: {line}")
    run(args, out / "link.log")
    for mode, pattern in (("runtime", "shared-%m"), ("offline", "separate")):
        for i, argv in enumerate(([], ["second"])):
            path = out / ((pattern if mode == "runtime" else f"{pattern}-{i}") + ".profraw")
            run([binary, *argv], out / f"{mode}-{i}.log",
                env={**os.environ, "LLVM_PROFILE_FILE": str(path)})
        raws = sorted(out.glob(("shared-*" if mode == "runtime" else "separate-*") + ".profraw"))
        if len(raws) != (1 if mode == "runtime" else 2):
            raise RuntimeError(f"Wrong number of raw profiles: {raws}")
        indexed = out / f"{mode}.profdata"
        run([profdata, "merge", "-o", indexed, *raws], out / f"{mode}-merge.log")
        rendered = text(profdata, "show", "--all-functions", "--counts", "--text", indexed)
        (out / f"{mode}.txt").write_text(rendered)
    if (out / "runtime.txt").read_bytes() != (out / "offline.txt").read_bytes():
        raise RuntimeError("Runtime-merged profile differs from independent offline merge")
    indexed = out / "runtime.profdata"
    if not re.search(r"Function count:\s*2\b", text(profdata, "show", "--function=main", indexed)):
        raise RuntimeError("Expected main to execute twice")
    with (out / "binary-export.json").open("w") as export, (out / "binary-export.stderr").open("w") as err:
        export_code = subprocess.run([cov, "export", binary, f"-instr-profile={indexed}"],
                                     stdout=export, stderr=err).returncode
    diagnostic = (out / "binary-export.stderr").read_text(errors="replace")
    export_status = ("passed" if export_code == 0 else
                     "known COFF coverage reader: empty name" if WINDOWS and linker == "LINK"
                     and "symbol name is empty" in diagnostic else "unexpected failure")
    (out / "export-status.json").write_text(json.dumps({"exit": export_code, "status": export_status}))
    print(f"{phase} {linker}: executable llvm-cov export: {export_status}", flush=True)
    # PE section end padding in some LINK versions also affects the unrelated
    # coverage-mapping reader. Decode the same mapping from its input object.
    coverage = text(cov, "show", obj if WINDOWS else binary, f"-instr-profile={indexed}", "--show-mcdc", src)
    (out / "coverage.txt").write_text(coverage)
    if not re.search(r"MC/DC Coverage for Decision:\s*100", coverage):
        raise RuntimeError("Expected complete MC/DC coverage")
    optimized = out / ("profile-use" + EXE)
    run([cc, *common, ldflag, "-O2", f"-fprofile-instr-use={indexed}",
         "-Werror=profile-instr-out-of-date", "-Werror=profile-instr-unprofiled",
         src, "-o", optimized], out / "profile-use.log")
    for i, argv in enumerate(([], ["second"])):
        expected = (out / f"offline-{i}.log").read_text().splitlines()[-1]
        if text(optimized, *argv) != expected:
            raise RuntimeError("Profile-use binary output changed")
    provenance = {
        "compiler_sha256": digest(cc), "runtime": str(selected[0]),
        "runtime_sha256": digest(selected[0]), "linker_command": line,
    }
    if bench is None:
        (out / "provenance.json").write_text(json.dumps(provenance, indent=2))
        return
    obj = out / "bench.o"
    executable = out / ("bench" + EXE)
    run([cc, *common, "-O2", "-fprofile-instr-generate", "-c", bench, "-o", obj],
        out / "bench-compile.log")
    run([cc, *common, ldflag, "-fprofile-instr-generate", obj, "-o", executable],
        out / "bench-link.log")
    if WINDOWS:
        sections = text(readobj, "--sections", obj)
        (out / "object-sections.txt").write_text(sections)
        expected = phase == "candidate"
        if ".lprfp$M" in sections:
            raise RuntimeError("Unexpected v1 pointer slots in the compact-ABI comparison")
        for section in (".lprfr$M", ".lprfd$0"):
            if (section in sections) != expected:
                raise RuntimeError(f"Unexpected {phase} COFF layout for {section}")
    provenance.update(object_bytes=obj.stat().st_size, exe_bytes=executable.stat().st_size)
    (out / "provenance.json").write_text(json.dumps(provenance, indent=2))


def compare_exports(out, linker):
    states = [json.loads((out / phase / linker / "export-status.json").read_text())["status"]
              for phase in ("base", "candidate")]
    if "unexpected failure" in states or (states[0] == "passed" and states[1] != "passed"):
        raise RuntimeError(f"Executable coverage-export discrepancy for {linker}: {states}")


def main():
    src = Path("src").resolve()
    tools = Path("b").resolve()
    out = Path("results").resolve()
    out.mkdir(exist_ok=True)
    base, candidate = os.environ["BASE"], os.environ["CANDIDATE"]
    jobs = min(4, os.cpu_count() or 2)
    if DARWIN:
        jobs = min(jobs, 3)
    if WINDOWS:
        git_usr = Path(os.environ["ProgramFiles"]) / "Git/usr/bin"
        os.environ["PATH"] += os.pathsep + str(git_usr)
    if DARWIN:
        os.environ["SDKROOT"] = text("xcrun", "--show-sdk-path")
    quick = os.environ.get("VALIDATION_MODE") == "runtime"
    if quick:
        if WINDOWS:
            raise RuntimeError("The fixed release compiler is only a non-Windows control")
        cache = Path("release-tools").resolve()
        cache.mkdir()
        packaged = os.environ.get("RELEASE_TOOLCHAIN_DIR")
        tools = Path(packaged).resolve() if packaged else get_tools(cache)
        os.environ["PATH"] = str(tools / "bin") + os.pathsep + os.environ["PATH"]
        cc = tools / "bin/clang"
        if f"clang version {VERSION}" not in text(cc, "--version"):
            raise RuntimeError("Unexpected release compiler identity")
        llvm_cmake = prepare_helpers(src, tools, cache, jobs, None)
    else:
        llvm_cmake = tools / "lib/cmake/llvm"
    changes = [Path(p) for p in text("git", "-C", src, "diff", "--diff-filter=AMR",
                                     "--name-only", base, candidate).splitlines()]
    drivers = linkers()
    bench = None if quick else out / "bench.c"
    if bench:
        subprocess.run([sys.executable, HERE / "paired.py", "generate", bench], check=True)
    failures = []

    def check(label, fn, *args):
        try:
            fn(*args)
        except Exception:
            failures.append(label)
            trace = traceback.format_exc()
            print(trace, flush=True)
            with (out / "failures.log").open("a") as f:
                f.write(f"{label}:\n{trace}\n")

    for phase, rev in (("base", base), ("candidate", candidate)):
        logs = out / phase
        logs.mkdir()
        subprocess.run(["git", "-C", src, "checkout", "--detach", rev], check=True)
        if text("git", "-C", src, "rev-parse", "HEAD") != rev:
            raise RuntimeError("Source revision mismatch")
        print(f"{phase}: {rev}, {shutil.disk_usage(src).free // 2**30} GiB free", flush=True)
        (logs / "source.txt").write_text(rev + "\n")
        if not quick:
            build_compiler(src, tools, jobs)
        cc = tools / "bin" / ("clang" + EXE)
        triple = text(cc, "-print-target-triple")
        arch = os.environ["ARCH"]
        allowed = {"arm64": {"aarch64", "arm64"}, "x64": {"x86_64", "amd64"}}[arch]
        if triple.split("-")[0].lower() not in allowed or platform.machine().lower() not in allowed:
            raise RuntimeError(f"Not native {arch}: {triple}, host {platform.machine()}")
        (logs / "clang-version.txt").write_text(text(cc, "--version"))
        if not quick:
            check(f"{phase} LLVM lit", llvm_lit, src, tools, logs, changes)
        rt = Path("rt-" + phase).resolve()
        configure_runtime(src, rt, tools, llvm_cmake, triple, logs, jobs)
        for linker, ldflag in drivers.items():
            directory = logs / linker
            directory.mkdir()
            check(f"{phase} {linker} profile lit", profile_lit, src, tools, rt, directory, changes, ldflag)
            check(f"{phase} {linker} probe", probe, cc, tools / "bin" / ("llvm-profdata" + EXE),
                  tools / "bin" / ("llvm-cov" + EXE), rt, triple, linker, ldflag, directory, bench,
                  phase, tools / "bin" / ("llvm-readobj" + EXE))
    for linker in drivers:
        check(f"{linker} executable export", compare_exports, out, linker)
        if not quick:
            check(f"{linker} paired measurements", subprocess.check_call,
                  [sys.executable, HERE / "paired.py", "compare", out / "base" / linker / ("bench" + EXE),
                   out / "candidate" / linker / ("bench" + EXE), out / f"paired-{linker}.json"])
    if failures:
        raise SystemExit("Failed: " + ", ".join(failures))


if __name__ == "__main__":
    main()
