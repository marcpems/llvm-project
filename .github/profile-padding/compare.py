import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import struct
import subprocess
import sys
import tarfile
import time
import urllib.request


BASE = "0e82f6c20bba329eead791dd3cc75c5f71624885"
FIX = "f25e7ef948a05e0de2d4ec11843956be6ffdf950"
FILES = [
    "compiler-rt/lib/profile/InstrProfilingMerge.c",
    "compiler-rt/lib/profile/InstrProfilingPlatformWindows.c",
]
VERSION = "23.1.4"
BUNDLES = {
    ("Windows", "AMD64"): (
        "clang+llvm-23.1.4-x86_64-pc-windows-msvc.tar.zst",
        "1a3f2f998e230b5791cc4e2bfe11a1f7c07fe42c96ff44f227c9db0bedfaf091",
    ),
    ("Linux", "x86_64"): (
        "LLVM-23.1.4-Linux-X64.tar.zst",
        "efdd1dbd089b99bfcfcde7b8eb1236163f2e88df5a981cca4f783ec9cb5e0378",
    ),
    ("Linux", "aarch64"): (
        "LLVM-23.1.4-Linux-ARM64.tar.zst",
        "0975f753e0f9b5f83146a7a2f4678bc143e713496b56520716a4de047a63f99f",
    ),
    ("Darwin", "arm64"): (
        "LLVM-23.1.4-macOS-ARM64.tar.zst",
        "0f8b0db925ab54a63028d788e85b14abaa25492e9608819728c17f6786948da4",
    ),
}


def run(args, log, *, env=None, check=True, timeout=900):
    args = [str(arg) for arg in args]
    started = time.monotonic()
    with log.open("w", encoding="utf-8") as output:
        output.write(json.dumps(args) + "\n")
        output.flush()
        result = subprocess.run(
            args, stdout=output, stderr=subprocess.STDOUT, env=env, timeout=timeout
        )
    print(f"{log.name}: exit {result.returncode} ({time.monotonic() - started:.1f}s)", flush=True)
    if check and result.returncode:
        print(log.read_text(encoding="utf-8", errors="replace")[-12000:], flush=True)
        raise RuntimeError(f"Command failed; see {log}")
    return result.returncode


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def sha(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def get_tools(work):
    name, digest = BUNDLES[(platform.system(), platform.machine())]
    archive = work / name
    url = f"https://github.com/llvm/llvm-project/releases/download/llvmorg-{VERSION}/{name}"
    print(f"Downloading official tool bundle: {url}", flush=True)
    urllib.request.urlretrieve(url, archive)
    if sha(archive) != digest:
        raise RuntimeError("LLVM release archive checksum mismatch")
    destination = work / "toolchain"
    destination.mkdir()
    with tarfile.open(archive, "r|zst") as tar:
        for member in tar:
            parts = Path(member.name).parts
            relative = parts[1:]
            keep = not relative or relative[0] in ("bin", "include")
            if relative and relative[0] == "lib":
                keep = len(relative) == 1 or relative[1] in ("clang", "cmake")
                keep |= ".so" in parts[-1] or parts[-1].endswith(".dylib")
            if keep and not member.name.endswith((".pdb", ".debug")):
                tar.extract(member, destination, filter="data")
    archive.unlink()
    clangs = list(destination.glob("*/bin/clang.exe" if os.name == "nt" else "*/bin/clang"))
    if len(clangs) != 1:
        raise RuntimeError(f"Expected one extracted Clang, found {clangs}")
    return clangs[0].parent.parent


def configure_runtime(root, build, tools, llvm_cmake, triple, logs, jobs):
    windows = os.name == "nt"
    cc = tools / "bin" / ("clang-cl.exe" if windows else "clang")
    cxx = tools / "bin" / ("clang-cl.exe" if windows else "clang++")
    options = [
        "cmake", "-G", "Ninja", "-S", root / "compiler-rt", "-B", build,
        "-DCMAKE_BUILD_TYPE=Release",
        f"-DCMAKE_C_COMPILER={cc}", f"-DCMAKE_CXX_COMPILER={cxx}",
        f"-DCMAKE_C_COMPILER_TARGET={triple}", f"-DCMAKE_CXX_COMPILER_TARGET={triple}",
        f"-DLLVM_CMAKE_DIR={llvm_cmake}", "-DLLVM_OMIT_EXPORTS_FROM_CONFIG=ON",
        f"-DLLVM_EXTERNAL_LIT={root / 'llvm/utils/lit/lit.py'}",
        f"-DCOMPILER_RT_TEST_COMPILER={tools / 'bin' / ('clang.exe' if windows else 'clang')}",
        f"-DPython3_EXECUTABLE:FILEPATH={sys.executable}",
        "-DCOMPILER_RT_DEFAULT_TARGET_ONLY=ON", "-DCOMPILER_RT_INCLUDE_TESTS=ON",
        "-DCOMPILER_RT_BUILD_PROFILE=ON",
    ]
    for component in ("BUILTINS", "SANITIZERS", "XRAY", "LIBFUZZER", "MEMPROF",
                      "CTX_PROFILE", "COPYPROF", "ORC", "GWP_ASAN"):
        options.append(f"-DCOMPILER_RT_BUILD_{component}=OFF")
    if platform.system() == "Darwin":
        options.extend(["-DCOMPILER_RT_ENABLE_IOS=OFF", "-DCOMPILER_RT_ENABLE_WATCHOS=OFF",
                        "-DCOMPILER_RT_ENABLE_TVOS=OFF"])
    run(options, logs / "configure.log")
    run(["cmake", "--build", build, "--target", "profile", "compiler-rt-headers",
         "--parallel", jobs], logs / "build.log")


def prepare_helpers(root, tools, work, jobs, supplied_cmake):
    extension = ".exe" if os.name == "nt" else ""
    names = ["FileCheck", "not", "count", "split-file"]
    if os.name == "nt":
        names.append("KillTheDoctor")
    missing = [name for name in names if not (tools / "bin" / (name + extension)).exists()]
    llvm_cmake = supplied_cmake or tools / "lib/cmake/llvm"
    if missing or not (llvm_cmake / "LLVMConfig.cmake").exists():
        build = work / "helpers"
        cc = tools / "bin" / ("clang-cl.exe" if os.name == "nt" else "clang")
        cxx = tools / "bin" / ("clang-cl.exe" if os.name == "nt" else "clang++")
        run(["cmake", "-G", "Ninja", "-S", root / "llvm", "-B", build,
             "-DCMAKE_BUILD_TYPE=Release", f"-DCMAKE_C_COMPILER={cc}",
             f"-DCMAKE_CXX_COMPILER={cxx}", "-DLLVM_TARGETS_TO_BUILD=Native",
             "-DLLVM_INCLUDE_BENCHMARKS=OFF", "-DLLVM_ENABLE_ZLIB=OFF",
             "-DLLVM_ENABLE_ZSTD=OFF", "-DLLVM_ENABLE_LIBXML2=OFF",
             f"-DPython3_EXECUTABLE:FILEPATH={sys.executable}"], work / "helpers-configure.log")
        if missing:
            run(["cmake", "--build", build, "--target", *missing, "--parallel", jobs],
                work / "helpers-build.log")
            for name in missing:
                shutil.copy2(build / "bin" / (name + extension), tools / "bin")
        llvm_cmake = build / "lib/cmake/llvm"
    return llvm_cmake


def probe(root, build, tools, triple, logs, linker):
    output = logs / "mcdc"
    output.mkdir()
    suffix = ".exe" if os.name == "nt" else ""
    clang = tools / "bin" / ("clang.exe" if os.name == "nt" else "clang")
    profdata = tools / "bin" / ("llvm-profdata" + suffix)
    cov = tools / "bin" / ("llvm-cov" + suffix)
    binary = output / ("mcdc-values" + suffix)
    resource = Path(subprocess.check_output([str(clang), "-print-resource-dir"], text=True).strip())
    common = [f"--target={triple}", f"-resource-dir={build}", "-nobuiltininc",
              "-idirafter", resource / "include"]
    if os.name == "nt":
        common.extend(["-fms-runtime-lib=dll", f"--ld-path={linker}"])
    source = root / ".github/profile-padding/mcdc-values.c"
    flags = ["-O0", "-fprofile-instr-generate", "-fcoverage-mapping", "-fcoverage-mcdc",
             "-mllvm", "-enable-value-profiling"]
    commands = {}

    def step(name, args, env=None):
        code = run(args, output / f"{name}.log", env=env, check=False, timeout=90)
        commands[name] = code
        return code == 0

    def finish(reason=None):
        result = {"passed": reason is None, "reason": reason, "commands": commands}
        (output / "result.json").write_text(json.dumps(result, indent=2))
        return result

    if not step("compile", [clang, *common, *flags, source, "-o", binary]):
        return finish("MC/DC/value-profile compilation failed")
    env = dict(os.environ, LLVM_PROFILE_FILE=str(output / "shared-%m.profraw"))
    for index, arguments in enumerate(([], ["second"]), 1):
        if not step(f"shared-run-{index}", [binary, *arguments], env):
            return finish(f"Repeated runtime profiling failed on run {index}")
    profiles = list(output.glob("shared-*.profraw"))
    if len(profiles) != 1:
        return finish(f"Expected one shared profile, found {len(profiles)}")
    header = struct.unpack("<19Q", profiles[0].read_bytes()[:152])
    layout = {"raw_version": header[1] & 0xFFFFFFFF, "bitmap_bytes": header[7],
              "bitmap_padding": header[8], "uniform_counters": header[9]}
    (output / "layout.json").write_text(json.dumps(layout, indent=2))
    if layout["raw_version"] != 11 or not layout["bitmap_bytes"] or not layout["bitmap_padding"]:
        return finish(f"Probe did not exercise expected nonempty, padded bitmap: {layout}")
    merged = output / "runtime.profdata"
    if not step("merge-shared", [profdata, "merge", "-o", merged, profiles[0]]):
        return finish("Shared runtime profile could not be decoded")
    env["LLVM_PROFILE_FILE"] = str(output / "oracle-%p.profraw")
    for index, arguments in enumerate(([], ["second"]), 1):
        if not step(f"oracle-run-{index}", [binary, *arguments], env):
            return finish("Independent-profile execution failed")
    oracle_raw = list(output.glob("oracle-*.profraw"))
    if len(oracle_raw) != 2:
        return finish("Expected two independent oracle profiles")
    oracle = output / "oracle.profdata"
    if not step("merge-oracle", [profdata, "merge", "-o", oracle, *oracle_raw]):
        return finish("Independent-profile offline merge failed")
    texts = []
    for name, profile in (("runtime", merged), ("oracle", oracle)):
        if not step(name + "-show", [profdata, "show", "--all-functions", "--counts",
                                    "--ic-targets", "--text", profile]):
            return finish("Profile inspection failed")
        text = (output / f"{name}-show.log").read_text().split("\n", 1)[1]
        # Equal-count indirect targets have no defined display order.
        text = re.sub(r"(?m)(?:(?:left|right):[0-9]+\n)+",
                      lambda match: "".join(sorted(match[0].splitlines(keepends=True))), text)
        texts.append(text)
    if texts[0] != texts[1]:
        return finish("Runtime merging differs from the independent offline-merge oracle")
    if not re.search(r"left:4\b", texts[0]) or not re.search(r"right:4\b", texts[0]):
        return finish("Expected both indirect targets with four calls each")
    if not step("coverage", [cov, "show", binary, f"-instr-profile={merged}", "--show-mcdc", source]):
        return finish("MC/DC coverage decoding failed")
    coverage = (output / "coverage.log").read_text()
    if not re.search(r"MC/DC Coverage for Decision:\s*100", coverage):
        return finish("Expected complete MC/DC decision coverage")
    optimized = output / ("profile-use" + suffix)
    if not step("profile-use-build", [clang, *common, "-O2",
                                     f"-fprofile-instr-use={merged}",
                                     "-mllvm", "-enable-value-profiling",
                                     "-Werror=profile-instr-out-of-date",
                                     source, "-o", optimized]):
        return finish("Profile-use compilation failed")
    for index, arguments in enumerate(([], ["second"]), 1):
        if not step(f"profile-use-run-{index}", [optimized, *arguments]):
            return finish("Profile-use execution failed")
        actual = (output / f"profile-use-run-{index}.log").read_text().split("\n", 1)[1]
        expected = (output / f"oracle-run-{index}.log").read_text().split("\n", 1)[1]
        if actual != expected:
            return finish("Profile-use output changed")
    return finish()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--tools", type=Path)
    parser.add_argument("--llvm-cmake", type=Path)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--target")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=False)
    tools = args.tools.resolve() if args.tools else get_tools(work)
    os.environ["PATH"] = str(tools / "bin") + os.pathsep + os.environ["PATH"]
    if os.name == "nt":
        os.environ["PATH"] += os.pathsep + r"C:\Program Files\Git\usr\bin"
        import ctypes
        ctypes.windll.kernel32.SetErrorMode(0x0001 | 0x0002)
    else:
        import resource
        resource.setrlimit(resource.RLIMIT_CORE, (0, resource.getrlimit(resource.RLIMIT_CORE)[1]))
    clang = tools / "bin" / ("clang.exe" if os.name == "nt" else "clang")
    version = subprocess.check_output([str(clang), "--version"], text=True)
    if VERSION not in version:
        raise RuntimeError(f"Expected Clang {VERSION}, found {version}")
    triple = args.target or subprocess.check_output([str(clang), "-print-target-triple"], text=True).strip()
    linker = shutil.which("link.exe") if os.name == "nt" else None
    if os.name == "nt" and (not linker or "Visual Studio" not in linker):
        raise RuntimeError(f"Microsoft developer environment is required: {linker}")
    llvm_cmake = prepare_helpers(root, tools, work, args.jobs, args.llvm_cmake)
    original = {name: (root / name).read_bytes() for name in FILES}
    for name, data in original.items():
        if data.replace(b"\r\n", b"\n") != git(root, "show", f"{FIX}:{name}"):
            raise RuntimeError(f"Unexpected runtime source changes: {name}")
    report = {"base": BASE, "fix": FIX, "harness_commit": git(root, "rev-parse", "HEAD").decode().strip(),
              "system": platform.platform(), "machine": platform.machine(), "compiler": version,
              "triple": triple, "linker": linker, "phases": {},
              "runner": os.environ.get("RUNNER_NAME"),
              "run_id": os.environ.get("GITHUB_RUN_ID")}
    try:
        for phase, revision in (("before", BASE), ("after", FIX)):
            logs = work / phase
            logs.mkdir()
            for name in FILES:
                (root / name).write_bytes(git(root, "show", f"{revision}:{name}"))
            build = work / f"build-{phase}"
            configure_runtime(root, build, tools, llvm_cmake, triple, logs, args.jobs)
            sites = list((build / "test/profile").glob("*/lit.site.cfg.py"))
            if len(sites) != 1:
                raise RuntimeError(f"Expected one native profile suite: {sites}")
            wrapper = logs / "lit"
            wrapper.mkdir()
            (wrapper / "lit.site.cfg.py").write_text(
                f"config.llvm_tools_dir = {str(tools / 'bin')!r}\n"
                f"lit_config.load_config(config, {str(sites[0])!r})\n"
            )
            extra = [f"-Dappend_target_cflags=--target={triple} --ld-path=\"{linker}\""] if linker else []
            suite_code = run([sys.executable, root / "llvm/utils/lit/lit.py",
                              "-v", "-j", args.jobs,
                              "-o", logs / "lit.json", *extra, wrapper],
                             logs / "suite.log", check=False)
            if not (logs / "lit.json").exists():
                raise RuntimeError((logs / "suite.log").read_text())
            tests = json.loads((logs / "lit.json").read_text())["tests"]
            report["phases"][phase] = {
                "suite_exit": suite_code,
                "tests": {test["name"]: test["code"] for test in tests},
                "mcdc": probe(root, build, tools, triple, logs, linker),
            }
            (work / "results.json").write_text(json.dumps(report, indent=2))
    finally:
        for name, data in original.items():
            (root / name).write_bytes(data)
    before = report["phases"]["before"]["tests"]
    after = report["phases"]["after"]["tests"]
    if before.keys() != after.keys():
        raise RuntimeError("Test inventories differ")
    bad = {"FAIL", "UNRESOLVED", "TIMEOUT"}
    report["regressions"] = [name for name in before if after[name] in bad and before[name] not in bad]
    report["improvements"] = [name for name in before if before[name] in bad and after[name] not in bad]
    report["unchanged_failures"] = [name for name in before if before[name] in bad and after[name] in bad]
    report["status_changes"] = {name: [before[name], after[name]] for name in before if before[name] != after[name]}
    report["counts"] = {
        phase: {code: list(data["tests"].values()).count(code) for code in sorted(set(data["tests"].values()))}
        for phase, data in report["phases"].items()
    }
    (work / "results.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({key: report[key] for key in ("counts", "regressions", "improvements",
                                                  "unchanged_failures", "status_changes")}, indent=2))
    if report["regressions"] or not report["phases"]["after"]["mcdc"]["passed"]:
        raise RuntimeError("Comparison found regressions or the patched MC/DC probe failed")


if __name__ == "__main__":
    main()
