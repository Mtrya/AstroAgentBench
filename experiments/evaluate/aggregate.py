"""Summarize Harbor trials without combining unlike benchmark scores."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tomllib


def rows(job: Path) -> list[dict]:
    output = []
    for path in sorted(job.glob("*/result.json")):
        trial = json.loads(path.read_text())
        task = Path(trial["task_id"]["path"])
        # Prepared tasks travel with results when archiving a run.
        recorded = path.parent / "verifier/task-config.json"
        task_config = json.loads(recorded.read_text()) if recorded.is_file() else tomllib.loads((task / "task.toml").read_text())
        report_path = path.parent / "verifier/report.json"
        report = json.loads(report_path.read_text()) if report_path.is_file() else None
        output.append({
            "trial": trial["trial_name"],
            "task": task_config["metadata"],
            "system": trial["agent_info"],
            "settings": {"task": task_config, "trial": trial["config"]},
            "status": "error" if trial.get("exception_info") else (report["status"] if report else "unscored"),
            "started_at": trial["started_at"],
            "finished_at": trial["finished_at"],
            "timing": {key: trial.get(key) for key in ("environment_setup", "agent_setup", "agent_execution", "verifier")},
            "metrics": report["metrics"] if report else {},
            "valid": report["valid"] if report else None,
            "error": trial.get("exception_info"),
            "artifacts": str(path.parent / "artifacts"),
        })
    if not output:
        raise ValueError(f"No trial results in {job}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(row, allow_nan=False) + "\n" for row in rows(args.job)))


if __name__ == "__main__":
    main()
