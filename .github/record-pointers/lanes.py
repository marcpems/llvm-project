import json
import subprocess

arches = {"windows-11-arm": "arm64", "windows-2025": "x64", "ubuntu-24.04": "x64", "macos-15": "arm64"}
requested = subprocess.check_output(
    ["git", "log", "-1", "--format=%(trailers:key=CI-Lanes,valueonly,separator=%x2c)"], text=True
).strip()
lanes = []
for spec in (requested.split(",") if requested else arches):
    runner, _, mode = spec.strip().partition(":")
    mode = mode or "full"
    intel_control = runner == "macos-15-intel" and mode == "runtime"
    if (runner not in arches and not intel_control) or mode not in ("full", "runtime") or mode == "runtime" and runner.startswith("windows"):
        raise ValueError(f"Unknown CI lane: {spec}")
    lane = {"runner": runner, "arch": "x64" if intel_control else arches[runner], "mode": mode}
    if lane in lanes:
        raise ValueError(f"Duplicate CI lane: {spec}")
    lanes.append(lane)
print(json.dumps(lanes))
