"""Generate a benchmark TU, then compare two builds of it on the SAME runner.

python paired.py generate probe.c
Build probe.c twice at -O2 -fprofile-instr-generate, linking respective runtimes.
python paired.py compare base.exe candidate.exe results.json
"""
import argparse
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import tempfile


def generate(path):
    preamble = r"""
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#ifdef _WIN32
#include <windows.h>
#define NOINLINE __declspec(noinline)
static double now(void) {
    LARGE_INTEGER ticks, hz;
    if (!QueryPerformanceCounter(&ticks) || !QueryPerformanceFrequency(&hz)) abort();
    return (double)ticks.QuadPart / hz.QuadPart;
}
#else
#include <time.h>
#define NOINLINE __attribute__((noinline))
static double now(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts)) abort();
    return ts.tv_sec + ts.tv_nsec / 1e9;
}
#endif
extern uint64_t __llvm_profile_get_size_for_buffer(void);
extern int __llvm_profile_write_buffer(char *);
"""
    functions = [
        f"NOINLINE unsigned f{i}(unsigned x) {{ return x * 33u + {i}u; }}\n"
        for i in range(1024)
    ]
    calls = "".join(f"x = f{i}(x);\n" for i in range(len(functions)))
    code = preamble + "".join(functions) + r"""
int main(void) {
    volatile unsigned sink;
    unsigned x = 1;
    double start = now();
    for (unsigned i = 0; i < 131072; ++i) {
""" + calls + r"""
    }
    sink = x;
    double hot = now() - start;
    uint64_t bytes = __llvm_profile_get_size_for_buffer();
    char *buf = (char *)malloc((size_t)bytes);
    if (!buf || !bytes || __llvm_profile_write_buffer(buf)) return 1;
    start = now();
    for (unsigned i = 0; i < 131072; ++i) {
        if (__llvm_profile_write_buffer(buf)) return 2;
    }
    double writes = now() - start;
    free(buf);
    if (printf("%.9f %.9f %llu %u\n", hot, writes, (unsigned long long)bytes, sink) < 0) return 3;
    return 0;
}
"""
    path.write_text(code, encoding="ascii")


def compare(base, candidate, output):
    binaries = {"base": base.resolve(), "candidate": candidate.resolve()}
    observations = []
    with tempfile.TemporaryDirectory(dir=output.resolve().parent) as d:
        for pair in range(-1, 10):  # Discard one warm-up pair; balance run order.
            order = ("base", "candidate") if pair % 2 == 0 else ("candidate", "base")
            row = {}
            for label in order:
                raw = Path(d) / f"{label}-{pair}.profraw"
                env = {**os.environ, "LLVM_PROFILE_FILE":str(raw)}
                hot, writes, n, checksum = subprocess.check_output(
                    [str(binaries[label])], env=env, text=True
                ).strip().split()
                if not raw.stat().st_size:
                    raise ValueError(f"{label} produced no profile")
                row[label] = dict(hot=float(hot), serialize=float(writes),
                                  buffer_bytes=int(n), checksum=int(checksum))
            if row["base"]["checksum"] != row["candidate"]["checksum"]:
                raise ValueError("Workload result differs")
            if pair >= 0:
                observations.append(row)
    stats = {}
    for key in ["hot","serialize"]:
        ratios = [r["candidate"][key]/r["base"][key] for r in observations]
        stats[key] = dict(base_median_s=statistics.median(r["base"][key] for r in observations),
                          candidate_median_s=statistics.median(r["candidate"][key] for r in observations),
                          median_paired_percent=(statistics.median(ratios)-1)*100,
                          paired_percent_range=[(v-1)*100 for v in [min(ratios),max(ratios)]])
    results = dict(host=platform.platform(), machine=platform.machine(),
                   exe_bytes={k:v.stat().st_size for k,v in binaries.items()},
                   measurements=observations, summary=stats)
    output.write_text(json.dumps(results,indent=2))
    print(json.dumps(results["summary"],indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="cmd",required=True)
    commands.add_parser("generate").add_argument("path",type=Path)
    c = commands.add_parser("compare")
    for arg in ("base","candidate","output"):
        c.add_argument(arg,type=Path)
    args = parser.parse_args()
    if args.cmd == "generate":
        generate(args.path)
    else:
        compare(args.base,args.candidate,args.output)
