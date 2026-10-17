"""Export canonical cases as a Harbor registry with benchmark/split and smoke subsets."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path

from experiments.evaluate.prepare import ROOT, prepare


def export(output: Path, version: str, image: str, *, repo: Path = ROOT) -> list[dict]:
    output.mkdir(parents=True, exist_ok=False)
    subsets = defaultdict(list)
    smoke = []
    families = json.loads((repo / "benchmarks/finished_benchmarks.json").read_text())["benchmarks"]
    for family in families:
        benchmark = family["name"]
        dataset = repo / "benchmarks" / benchmark / "dataset"
        index = json.loads((dataset / "index.json").read_text())
        smoke_count = 0
        for case in index["cases"]:
            split, case_id = case["split"], case["case_id"]
            name = f"{benchmark}-{split}-{case_id}"
            is_smoke = f"{split}/{case_id}" == index["example_smoke_case"]
            prepare(benchmark, split, case_id, output / "tasks" / name, image=image,
                    reference_solution=dataset / "example_solution.json" if is_smoke else None, repo=repo)
            task = {"name": name, "path": f"tasks/{name}"}
            subsets[f"{benchmark}-{split}"].append(task)
            if is_smoke:
                smoke.append(task)
                smoke_count += 1
        if smoke_count != 1:
            raise ValueError(f"Expected one indexed smoke case for {benchmark}, found {smoke_count}")
    registry = [{"name": name, "version": version, "description": f"AstroAgentBench {name}", "tasks": tasks}
                for name, tasks in sorted(subsets.items())]
    registry.append({"name": "smoke", "version": version, "description": "One oracle integration check per benchmark family", "tasks": smoke})
    (output / "registry.json").write_text(json.dumps(registry, indent=2) + "\n")
    return registry


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--image", required=True)
    args = parser.parse_args()
    export(**vars(args))


if __name__ == "__main__":
    main()
