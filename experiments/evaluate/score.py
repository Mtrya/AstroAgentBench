"""Call an unmodified benchmark verifier and expose its native metrics to Harbor."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys


TEXT_METRICS = {
    "spot5": {"computed_profit": "Computed Profit", "computed_weight": "Computed Weight", "computed_selected": "Selected Photos"},
    "satnet": {"score_hours": "Total tracking hours", "n_tracks": "Tracks", "n_satisfied_requests": "Satisfied requests", "u_rms": "U_rms", "u_max": "U_max"},
}


def parse_report(benchmark: str, stdout: str, returncode: int) -> dict:
    if returncode not in (0, 1):
        raise RuntimeError(f"Verifier exited with {returncode}; inspect verifier.stderr")
    if benchmark in TEXT_METRICS:
        status = re.search(r"^Status:\s*(VALID|INVALID)\s*$", stdout, re.MULTILINE)
        if status is None:
            raise ValueError("Verifier output has no validity status")
        metrics = {}
        for name, label in TEXT_METRICS[benchmark].items():
            match = re.search(rf"^{re.escape(label)}:\s*([-+\d.eE]+)", stdout, re.MULTILINE)
            if match is None:
                raise ValueError(f"Verifier output has no {label}")
            metrics[name] = float(match.group(1))
        report = {"valid": status.group(1) == "VALID", "metrics": metrics}
    else:
        report = json.loads(stdout)
        if benchmark == "revisit_constellation":
            report["valid"] = report["is_valid"]
    if type(report.get("valid")) is not bool or not isinstance(report.get("metrics"), dict):
        raise ValueError("Verifier output must contain valid and metrics")
    if report["valid"] != (returncode == 0):
        raise ValueError("Verifier validity and exit status disagree")
    return report


def score(task_tests: Path, solution_dir: Path, output: Path) -> dict:
    profile = json.loads((task_tests / "profile.json").read_text())
    benchmark = profile["benchmark"]
    output.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(task_tests / "task-config.json", output / "task-config.json")
    # One required filename makes missing/ambiguous submissions explicit.
    solution = solution_dir / profile["solution_filename"]
    if not solution.is_file():
        report = {"valid": False, "metrics": {}, "errors": [f"Missing {solution.name}"], "status": "missing_solution"}
    else:
        command = [sys.executable, *profile["verifier_command"], str(task_tests / "case"), str(solution.resolve())]
        if benchmark in TEXT_METRICS:
            command.append("--verbose")
        result = subprocess.run(command, cwd=task_tests, capture_output=True, text=True)
        (output / "verifier.stdout").write_text(result.stdout)
        (output / "verifier.stderr").write_text(result.stderr)
        report = parse_report(benchmark, result.stdout, result.returncode)
        report["status"] = "valid" if report["valid"] else "invalid"
    (output / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    rewards = {"valid": float(report["valid"])}
    for metric in profile["metrics"]:
        value = report["metrics"].get(metric["name"])
        if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
            rewards[f"{benchmark}/{metric['name']}"] = value
    (output / "reward.json").write_text(json.dumps(rewards, indent=2, allow_nan=False) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tests", type=Path, default=Path("/tests"))
    parser.add_argument("--solution", type=Path, default=Path("/workspace/solution"))
    parser.add_argument("--output", type=Path, default=Path("/logs/verifier"))
    args = parser.parse_args()
    score(args.tests.resolve(), args.solution.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
