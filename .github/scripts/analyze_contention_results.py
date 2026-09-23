import argparse
import json
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


def summarize_rep(path: Path, test_root: Path, test_subset: str, expected_tests: int):
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
            text = source_path.read_text(encoding="utf-8", errors="ignore")
            if is_simple_x86_test(source_path, text):
                simple_elapsed_ms.append(elapsed)
                simple_tests.append(test["name"])

    rep = {
        "file": path.name,
        "lit_elapsed_s": data["elapsed"],
        "discovered_tests": len(tests),
        "full_population": {
            "count": len(elapsed_ms),
            "mean_ms": statistics.mean(elapsed_ms),
            "median_ms": statistics.median(elapsed_ms),
        },
    }
    if simple_subset_enabled:
        rep["simple_subset"] = {
            "count": len(simple_elapsed_ms),
            "mean_ms": statistics.mean(simple_elapsed_ms),
            "median_ms": statistics.median(simple_elapsed_ms),
            "first_five": simple_tests[:5],
        }
    return rep


def fmt_ms(value):
    return f"{value:.1f}"


def main():
    args = parse_args()
    results_dir = Path(args.results_dir)
    test_root = Path(args.test_root)
    rep_files = sorted(results_dir.glob("rep*.json"))
    if not rep_files:
        raise RuntimeError(f"No rep*.json files found under {results_dir}")

    reps = [
        summarize_rep(path, test_root, args.test_subset, args.expected_tests)
        for path in rep_files
    ]

    summary = {
        "test_subset": args.test_subset,
        "expected_tests": args.expected_tests,
        "repetitions": reps,
    }
    summary_path = Path(args.summary_json)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "",
        "### Per-test JSON analysis",
        "",
        "| Rep | lit elapsed (s) | discovered tests | full mean (ms) | full median (ms) |",
        "|---|---:|---:|---:|---:|",
    ]
    for index, rep in enumerate(reps, start=1):
        lines.append(
            "| {idx} | {elapsed:.3f} | {count} | {mean} | {median} |".format(
                idx=index,
                elapsed=rep["lit_elapsed_s"],
                count=rep["discovered_tests"],
                mean=fmt_ms(rep["full_population"]["mean_ms"]),
                median=fmt_ms(rep["full_population"]["median_ms"]),
            )
        )

    if "simple_subset" in reps[0]:
        lines.extend(
            [
                "",
                "Simple-subset definition: `.ll` file with exactly one `; RUN:` line and fewer than 30 total lines.",
                "",
                "| Rep | simple count | simple mean (ms) | simple median (ms) |",
                "|---|---:|---:|---:|",
            ]
        )
        for index, rep in enumerate(reps, start=1):
            simple = rep["simple_subset"]
            lines.append(
                "| {idx} | {count} | {mean} | {median} |".format(
                    idx=index,
                    count=simple["count"],
                    mean=fmt_ms(simple["mean_ms"]),
                    median=fmt_ms(simple["median_ms"]),
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
