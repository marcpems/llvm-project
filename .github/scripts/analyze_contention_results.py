import argparse
import json
import math
import re
import statistics
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", required=True)
    parser.add_argument("--test-root", required=True)
    parser.add_argument("--test-subset", required=True)
    parser.add_argument("--expected-tests", type=int, default=0)
    parser.add_argument("--summary-json", required=True)
    parser.add_argument("--step-summary")
    return parser.parse_args()


def is_simple_x86_test(path: Path, text: str) -> bool:
    if path.suffix.lower() != ".ll":
        return False
    lines = text.splitlines()
    run_lines = [line for line in lines if line.lstrip().startswith("; RUN:")]
    return len(run_lines) == 1 and len(lines) < 30


def test_name_to_path(test_root: Path, full_name: str) -> Path:
    _, relative = full_name.split("::", 1)
    relative = relative.strip().replace("/", "\\")
    return test_root / relative


def summarize_rep(path: Path, test_root: Path, test_subset: str, expected_tests: int, simple_cache):
    data = json.loads(path.read_text(encoding="utf-8"))
    tests = data["tests"]
    if expected_tests and len(tests) != expected_tests:
        raise RuntimeError(
            f"{path.name}: discovered {len(tests)} tests, expected {expected_tests}"
        )

    elapsed_ms = []
    simple_elapsed_ms = []
    simple_tests = []
    simple_subset_enabled = test_subset == "CodeGen/X86"

    for test in tests:
        elapsed = test.get("elapsed")
        if elapsed is None:
            continue
        elapsed *= 1000.0
        elapsed_ms.append(elapsed)
        if simple_subset_enabled:
            source_path = test_name_to_path(test_root, test["name"])
            if source_path not in simple_cache:
                text = source_path.read_text(encoding="utf-8", errors="ignore")
                simple_cache[source_path] = is_simple_x86_test(source_path, text)
            if simple_cache[source_path]:
                simple_elapsed_ms.append(elapsed)
                simple_tests.append(test["name"])

    rep = {
        "file": path.name,
        "label": derive_label(path),
        "lit_elapsed_s": data["elapsed"],
        "discovered_tests": len(tests),
        "full_population": {
            "count": len(elapsed_ms),
            "mean_ms": statistics.mean(elapsed_ms),
            "median_ms": statistics.median(elapsed_ms),
            "sum_elapsed_s": sum(elapsed_ms) / 1000.0,
        },
    }
    if simple_subset_enabled:
        rep["simple_subset"] = {
            "count": len(simple_elapsed_ms),
            "mean_ms": statistics.mean(simple_elapsed_ms),
            "median_ms": statistics.median(simple_elapsed_ms),
            "sum_elapsed_s": sum(simple_elapsed_ms) / 1000.0,
            "first_five": simple_tests[:5],
        }
    return rep


def fmt_ms(value):
    return f"{value:.1f}"


def fmt_s(value):
    return f"{value:.3f}"


def derive_label(path: Path) -> str:
    seq_match = re.match(r"seq\d+-j(\d+)\.json$", path.name)
    if seq_match:
        return f"j{seq_match.group(1)}"
    return "rep"


def stdev_or_na(values):
    return statistics.stdev(values) if len(values) >= 2 else math.nan


def aggregate_by_label(reps):
    buckets = {}
    for rep in reps:
        bucket = buckets.setdefault(rep["label"], [])
        bucket.append(rep)

    rows = []
    for label in sorted(buckets, key=lambda s: (s != "rep", s)):
        items = buckets[label]
        row = {
            "label": label,
            "samples": len(items),
            "lit_elapsed_mean_s": statistics.mean([item["lit_elapsed_s"] for item in items]),
            "lit_elapsed_stdev_s": stdev_or_na([item["lit_elapsed_s"] for item in items]),
            "full_mean_ms_mean": statistics.mean(
                [item["full_population"]["mean_ms"] for item in items]
            ),
            "full_median_ms_mean": statistics.mean(
                [item["full_population"]["median_ms"] for item in items]
            ),
            "full_sum_elapsed_mean_s": statistics.mean(
                [item["full_population"]["sum_elapsed_s"] for item in items]
            ),
        }
        if "simple_subset" in items[0]:
            row["simple_count"] = items[0]["simple_subset"]["count"]
            row["simple_mean_ms_mean"] = statistics.mean(
                [item["simple_subset"]["mean_ms"] for item in items]
            )
            row["simple_median_ms_mean"] = statistics.mean(
                [item["simple_subset"]["median_ms"] for item in items]
            )
            row["simple_sum_elapsed_mean_s"] = statistics.mean(
                [item["simple_subset"]["sum_elapsed_s"] for item in items]
            )
        rows.append(row)
    return rows


def main():
    args = parse_args()
    results_dir = Path(args.results_dir)
    test_root = Path(args.test_root)
    rep_files = sorted(
        [
            path
            for path in results_dir.glob("*.json")
            if path.name not in {"summary.json", "runner-diagnostics.json"}
            and (re.match(r"rep\d+\.json$", path.name) or re.match(r"seq\d+-j\d+\.json$", path.name))
        ]
    )
    if not rep_files:
        raise RuntimeError(f"No rep*.json files found under {results_dir}")

    simple_cache = {}
    reps = [
        summarize_rep(path, test_root, args.test_subset, args.expected_tests, simple_cache)
        for path in rep_files
    ]

    summary = {
        "test_subset": args.test_subset,
        "expected_tests": args.expected_tests,
        "repetitions": reps,
        "aggregates": aggregate_by_label(reps),
    }
    summary_path = Path(args.summary_json)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "",
        "### Per-test JSON analysis",
        "",
        "| File | label | lit elapsed (s) | discovered tests | full mean (ms) | full median (ms) | full sum elapsed (s) |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for rep in reps:
        lines.append(
            "| {file} | {label} | {elapsed:.3f} | {count} | {mean} | {median} | {sum_elapsed} |".format(
                file=rep["file"],
                label=rep["label"],
                elapsed=rep["lit_elapsed_s"],
                count=rep["discovered_tests"],
                mean=fmt_ms(rep["full_population"]["mean_ms"]),
                median=fmt_ms(rep["full_population"]["median_ms"]),
                sum_elapsed=fmt_s(rep["full_population"]["sum_elapsed_s"]),
            )
        )

    if "simple_subset" in reps[0]:
        lines.extend(
            [
                "",
                "Simple-subset definition: `.ll` file with exactly one `; RUN:` line and fewer than 30 total lines.",
                "",
                "| File | label | simple count | simple mean (ms) | simple median (ms) | simple sum elapsed (s) |",
                "|---|---|---:|---:|---:|---:|",
            ]
        )
        for rep in reps:
            simple = rep["simple_subset"]
            lines.append(
                "| {file} | {label} | {count} | {mean} | {median} | {sum_elapsed} |".format(
                    file=rep["file"],
                    label=rep["label"],
                    count=simple["count"],
                    mean=fmt_ms(simple["mean_ms"]),
                    median=fmt_ms(simple["median_ms"]),
                    sum_elapsed=fmt_s(simple["sum_elapsed_s"]),
                )
            )

    if len(summary["aggregates"]) > 1 or summary["aggregates"][0]["samples"] > 1:
        lines.extend(
            [
                "",
                "Grouped means by label:",
                "",
                "| Label | samples | mean lit elapsed (s) | stdev lit elapsed (s) | mean full mean (ms) | mean full median (ms) | mean full sum elapsed (s) |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for row in summary["aggregates"]:
            stdev = "n/a" if math.isnan(row["lit_elapsed_stdev_s"]) else fmt_s(row["lit_elapsed_stdev_s"])
            lines.append(
                "| {label} | {samples} | {elapsed} | {stdev} | {full_mean} | {full_median} | {full_sum} |".format(
                    label=row["label"],
                    samples=row["samples"],
                    elapsed=fmt_s(row["lit_elapsed_mean_s"]),
                    stdev=stdev,
                    full_mean=fmt_ms(row["full_mean_ms_mean"]),
                    full_median=fmt_ms(row["full_median_ms_mean"]),
                    full_sum=fmt_s(row["full_sum_elapsed_mean_s"]),
                )
            )
        if "simple_count" in summary["aggregates"][0]:
            lines.extend(
                [
                    "",
                    "| Label | simple count | mean simple mean (ms) | mean simple median (ms) | mean simple sum elapsed (s) |",
                    "|---|---:|---:|---:|---:|",
                ]
            )
            for row in summary["aggregates"]:
                lines.append(
                    "| {label} | {count} | {mean} | {median} | {sum_elapsed} |".format(
                        label=row["label"],
                        count=row["simple_count"],
                        mean=fmt_ms(row["simple_mean_ms_mean"]),
                        median=fmt_ms(row["simple_median_ms_mean"]),
                        sum_elapsed=fmt_s(row["simple_sum_elapsed_mean_s"]),
                    )
                )

    text = "\n".join(lines) + "\n"
    print(text)
    if args.step_summary:
        summary_file = Path(args.step_summary)
        existing = ""
        if summary_file.exists():
            existing = summary_file.read_text(encoding="utf-8")
        summary_file.write_text(existing + text, encoding="utf-8")


if __name__ == "__main__":
    main()
