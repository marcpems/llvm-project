#!/usr/bin/env python3

import argparse
import json
import os
import shutil
import statistics
import subprocess
import time
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Hosted validation harness for the embed-opt-in-lit prototype."
    )
    parser.add_argument(
        "--mode",
        choices=["push-validation", "baseline-only", "worker-correctness", "worker-throughput"],
        required=True,
    )
    parser.add_argument("--lit-bin", required=True)
    parser.add_argument("--test-subset", required=True)
    parser.add_argument("--results-dir", required=True)
    parser.add_argument("--jobs", default="auto")
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument("--opt-embed")
    return parser.parse_args()


def detect_jobs(raw_value: str) -> int:
    if raw_value and raw_value not in {"auto", "12"}:
        try:
            parsed = int(raw_value)
            if parsed > 0:
                return parsed
        except ValueError:
            pass
    return os.cpu_count() or 1


def load_lit_json(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    tests = {test["name"]: test["code"] for test in data.get("tests", [])}
    return data, tests


def aggregate_stats(stats_dir: Path):
    files = sorted(stats_dir.glob("opt-dll-stats-*.json"))
    aggregate = {
        "stats_files": [str(path.name) for path in files],
        "worker_processes_reporting": len(files),
        "dll_selected": 0,
        "dll_completed": 0,
        "dll_exceptions": 0,
        "spawn_fallback": 0,
        "spawn_fallback_reasons": {},
    }
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        aggregate["dll_selected"] += int(payload.get("dll_selected", 0))
        aggregate["dll_completed"] += int(payload.get("dll_completed", 0))
        aggregate["dll_exceptions"] += int(payload.get("dll_exceptions", 0))
        aggregate["spawn_fallback"] += int(payload.get("spawn_fallback", 0))
        for reason, count in payload.get("spawn_fallback_reasons", {}).items():
            aggregate["spawn_fallback_reasons"][reason] = (
                aggregate["spawn_fallback_reasons"].get(reason, 0) + int(count)
            )
    return aggregate


def run_lit(lit_bin: str, subset: str, jobs: int, json_path: Path | None, env_overrides: dict[str, str] | None = None):
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    cmd = [lit_bin, "-j", str(jobs), "-q"]
    if json_path is not None:
        cmd.extend(["-o", str(json_path)])
    cmd.append(subset)
    start = time.perf_counter()
    completed = subprocess.run(cmd, env=env, check=False)
    elapsed = time.perf_counter() - start
    return {"returncode": completed.returncode, "elapsed": elapsed, "command": cmd}


def ensure_clean_dir(path: Path):
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def compare_correctness(results_dir: Path):
    baseline_data, baseline = load_lit_json(results_dir / "correctness_baseline.json")
    worker_data, worker = load_lit_json(results_dir / "correctness_worker.json")

    baseline_names = set(baseline)
    worker_names = set(worker)
    mismatches = [
        (name, baseline[name], worker[name])
        for name in sorted(baseline_names & worker_names)
        if baseline[name] != worker[name]
    ]
    failures = {
        "baseline_only": sorted(baseline_names - worker_names),
        "worker_only": sorted(worker_names - baseline_names),
        "code_mismatches": mismatches,
        "baseline_failing": sorted(name for name, code in baseline.items() if code != "PASS"),
        "worker_failing": sorted(name for name, code in worker.items() if code != "PASS"),
        "baseline_counts": baseline_data.get("tests_by_code", {}),
        "worker_counts": worker_data.get("tests_by_code", {}),
        "test_count": len(baseline),
    }
    return failures


def stdev_or_zero(values):
    return statistics.stdev(values) if len(values) > 1 else 0.0


def summarize_quartets(quartets):
    baseline_means = []
    worker_means = []
    for quartet in quartets:
        baseline_values = [run["elapsed"] for run in quartet["runs"] if run["kind"] == "baseline"]
        worker_values = [run["elapsed"] for run in quartet["runs"] if run["kind"] == "worker"]
        baseline_means.append(statistics.mean(baseline_values))
        worker_means.append(statistics.mean(worker_values))

    return {
        "baseline_mean": statistics.mean(baseline_means),
        "baseline_stdev": stdev_or_zero(baseline_means),
        "baseline_range": [min(baseline_means), max(baseline_means)],
        "worker_mean": statistics.mean(worker_means),
        "worker_stdev": stdev_or_zero(worker_means),
        "worker_range": [min(worker_means), max(worker_means)],
        "delta_mean": statistics.mean(worker_means) - statistics.mean(baseline_means),
    }


def write_text(path: Path, content: str):
    path.write_text(content, encoding="utf-8")


def require_opt_embed(args):
    if not args.opt_embed:
        raise SystemExit("--opt-embed is required for this mode")


def run_correctness(args, jobs: int, results_dir: Path):
    require_opt_embed(args)
    subset = args.test_subset
    worker_stats_dir = results_dir / "correctness_worker_stats"
    ensure_clean_dir(worker_stats_dir)

    baseline_run = run_lit(
        args.lit_bin, subset, jobs, results_dir / "correctness_baseline.json"
    )
    worker_run = run_lit(
        args.lit_bin,
        subset,
        jobs,
        results_dir / "correctness_worker.json",
        {
            "LIT_OPT_DLL": args.opt_embed,
            "LIT_OPT_DLL_STATS_DIR": str(worker_stats_dir),
        },
    )

    comparison = compare_correctness(results_dir)
    stats = aggregate_stats(worker_stats_dir)
    payload = {
        "jobs": jobs,
        "subset": subset,
        "baseline_run": baseline_run,
        "worker_run": worker_run,
        "comparison": comparison,
        "worker_stats": stats,
    }
    (results_dir / "correctness_summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        f"subset={subset}",
        f"jobs={jobs}",
        f"baseline_returncode={baseline_run['returncode']}",
        f"worker_returncode={worker_run['returncode']}",
        f"test_count={comparison['test_count']}",
        f"baseline_counts={comparison['baseline_counts']}",
        f"worker_counts={comparison['worker_counts']}",
        f"worker_processes_reporting={stats['worker_processes_reporting']}",
        f"dll_selected={stats['dll_selected']}",
        f"dll_completed={stats['dll_completed']}",
        f"dll_exceptions={stats['dll_exceptions']}",
        f"spawn_fallback={stats['spawn_fallback']}",
        f"spawn_fallback_reasons={stats['spawn_fallback_reasons']}",
    ]
    if comparison["baseline_only"]:
        lines.append(
            "baseline_only=" + repr(comparison["baseline_only"][:50])
        )
    if comparison["worker_only"]:
        lines.append("worker_only=" + repr(comparison["worker_only"][:50]))
    if comparison["code_mismatches"]:
        lines.append(
            "code_mismatches=" + repr(comparison["code_mismatches"][:50])
        )
    write_text(results_dir / "correctness_summary.txt", "\n".join(lines) + "\n")

    if comparison["baseline_only"] or comparison["worker_only"] or comparison["code_mismatches"]:
        raise SystemExit("Correctness mismatch detected; see correctness_summary.json")
    if stats["worker_processes_reporting"] == 0:
        raise SystemExit("No embed-opt stats were reported by worker processes")
    if stats["dll_selected"] == 0:
        raise SystemExit("Embed-opt path recorded zero DLL dispatches")


def run_baseline_only(args, jobs: int, results_dir: Path):
    subset = args.test_subset
    runs = []
    for rep in range(1, args.reps + 1):
        json_path = results_dir / f"baseline_rep{rep}.json"
        result = run_lit(args.lit_bin, subset, jobs, json_path)
        result["rep"] = rep
        runs.append(result)
    summary = {
        "jobs": jobs,
        "subset": subset,
        "runs": runs,
        "mean": statistics.mean([run["elapsed"] for run in runs]),
        "stdev": stdev_or_zero([run["elapsed"] for run in runs]),
        "range": [
            min(run["elapsed"] for run in runs),
            max(run["elapsed"] for run in runs),
        ],
    }
    (results_dir / "baseline_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )


def run_throughput(args, jobs: int, results_dir: Path):
    require_opt_embed(args)
    subset = args.test_subset
    warm_worker_stats = results_dir / "warm_worker_stats"
    ensure_clean_dir(warm_worker_stats)

    run_lit(args.lit_bin, subset, jobs, None)
    run_lit(
        args.lit_bin,
        subset,
        jobs,
        None,
        {
            "LIT_OPT_DLL": args.opt_embed,
            "LIT_OPT_DLL_STATS_DIR": str(warm_worker_stats),
        },
    )

    quartets = []
    all_stats = []
    for rep in range(1, args.reps + 1):
        stats_dir = results_dir / f"throughput_worker_stats_rep{rep}"
        ensure_clean_dir(stats_dir)
        quartet = {"rep": rep, "runs": []}
        schedule = ["baseline", "worker", "worker", "baseline"]
        for ordinal, kind in enumerate(schedule, start=1):
            json_path = results_dir / f"throughput_{kind}_rep{rep}_run{ordinal}.json"
            env = None
            if kind == "worker":
                env = {
                    "LIT_OPT_DLL": args.opt_embed,
                    "LIT_OPT_DLL_STATS_DIR": str(stats_dir),
                }
            result = run_lit(args.lit_bin, subset, jobs, json_path, env)
            result["kind"] = kind
            result["ordinal"] = ordinal
            quartet["runs"].append(result)
        stats = aggregate_stats(stats_dir)
        quartet["worker_stats"] = stats
        quartets.append(quartet)
        all_stats.append(stats)

    summary = summarize_quartets(quartets)
    aggregate = {
        "worker_processes_reporting": sum(s["worker_processes_reporting"] for s in all_stats),
        "dll_selected": sum(s["dll_selected"] for s in all_stats),
        "dll_completed": sum(s["dll_completed"] for s in all_stats),
        "dll_exceptions": sum(s["dll_exceptions"] for s in all_stats),
        "spawn_fallback": sum(s["spawn_fallback"] for s in all_stats),
        "spawn_fallback_reasons": {},
    }
    for stats in all_stats:
        for reason, count in stats["spawn_fallback_reasons"].items():
            aggregate["spawn_fallback_reasons"][reason] = (
                aggregate["spawn_fallback_reasons"].get(reason, 0) + count
            )

    payload = {
        "jobs": jobs,
        "subset": subset,
        "reps": args.reps,
        "quartets": quartets,
        "summary": summary,
        "worker_stats": aggregate,
    }
    (results_dir / "throughput_summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        f"subset={subset}",
        f"jobs={jobs}",
        f"reps={args.reps}",
        f"baseline_mean={summary['baseline_mean']:.6f}",
        f"baseline_stdev={summary['baseline_stdev']:.6f}",
        f"baseline_range=({summary['baseline_range'][0]:.6f}, {summary['baseline_range'][1]:.6f})",
        f"worker_mean={summary['worker_mean']:.6f}",
        f"worker_stdev={summary['worker_stdev']:.6f}",
        f"worker_range=({summary['worker_range'][0]:.6f}, {summary['worker_range'][1]:.6f})",
        f"delta_mean={summary['delta_mean']:.6f}",
        f"dll_selected={aggregate['dll_selected']}",
        f"dll_completed={aggregate['dll_completed']}",
        f"dll_exceptions={aggregate['dll_exceptions']}",
        f"spawn_fallback={aggregate['spawn_fallback']}",
        f"spawn_fallback_reasons={aggregate['spawn_fallback_reasons']}",
    ]
    write_text(results_dir / "throughput_summary.txt", "\n".join(lines) + "\n")

    if aggregate["dll_selected"] == 0:
        raise SystemExit("Embed-opt throughput run recorded zero DLL dispatches")


def run_push_validation(args, jobs: int, results_dir: Path):
    run_correctness(args, jobs, results_dir)
    run_throughput(args, jobs, results_dir)


def main():
    args = parse_args()
    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    jobs = detect_jobs(args.jobs)
    if args.mode == "push-validation":
        run_push_validation(args, jobs, results_dir)
    elif args.mode == "baseline-only":
        run_baseline_only(args, jobs, results_dir)
    elif args.mode == "worker-correctness":
        run_correctness(args, jobs, results_dir)
    elif args.mode == "worker-throughput":
        run_throughput(args, jobs, results_dir)
    else:
        raise SystemExit(f"unsupported mode: {args.mode}")


if __name__ == "__main__":
    main()
