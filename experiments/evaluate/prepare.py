"""Export one canonical case as a self-contained Harbor task."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tomllib

import yaml

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def tree_hash(path: Path) -> str:
    digest = hashlib.sha256()
    for file in sorted(p for p in path.rglob("*") if p.is_file()):
        digest.update(file.relative_to(path).as_posix().encode() + b"\0")
        digest.update(hashlib.sha256(file.read_bytes()).digest())
    return digest.hexdigest()


def prepare(benchmark: str, split: str, case_id: str, output: Path, *, image: str = "astroagentbench-python:latest", cpus: int = 2, memory_mb: int = 4096, timeout: int = 7200, network: str = "public", reference_solution: Path | None = None, solution_filename: str = "solution.json", repo: Path = ROOT) -> Path:
    profile = yaml.safe_load((HERE / "benchmarks" / f"{benchmark}.yaml").read_text())
    case = (repo / "benchmarks" / benchmark / "dataset/cases" / split / case_id).resolve()
    case.relative_to((repo / "benchmarks" / benchmark / "dataset/cases").resolve())
    if not case.is_dir():
        raise FileNotFoundError(case)
    if cpus <= 0 or memory_mb <= 0 or timeout <= 0:
        raise ValueError("Resource and time limits must be positive")
    if solution_filename not in ("solution.json", "solution.spot_sol.txt") or (solution_filename.endswith(".txt") and benchmark != "spot5"):
        raise ValueError("Use solution.json, or solution.spot_sol.txt for SPOT5 native text")
    if not image or any(c.isspace() for c in image):
        raise ValueError("Expected a Docker image reference")
    if network not in ("public", "no-network"):
        raise ValueError("Unsupported network policy")
    output.mkdir(parents=True, exist_ok=False)
    environment, tests = output / "environment", output / "tests"
    for target in (environment, tests):
        shutil.copytree(case, target / "case")
    brief = (HERE / "instructions" / f"{benchmark}.md").read_text().replace("solution.json", f"/workspace/solution/{solution_filename}")
    (output / "instruction.md").write_text(brief)
    (environment / "Dockerfile").write_text(f"FROM {image}\nWORKDIR /workspace\nCOPY case /workspace/case\nRUN mkdir -p /workspace/solution\n")
    # The authority and original case exist only in the fresh verifier image.
    verifier = repo / "benchmarks" / benchmark / "verifier"
    package = tests / "benchmarks" / benchmark
    package.mkdir(parents=True)
    (tests / "benchmarks/__init__.py").touch()
    (package / "__init__.py").touch()
    if verifier.is_dir():
        shutil.copytree(verifier, package / "verifier", ignore=shutil.ignore_patterns("__pycache__"))
        command = ["-m", f"benchmarks.{benchmark}.verifier.run"]
    else:
        shutil.copyfile(verifier.with_suffix(".py"), package / "verifier.py")
        command = [f"benchmarks/{benchmark}/verifier.py"]
    shutil.copyfile(HERE / "score.py", tests / "score.py")
    profile.update(solution_filename=solution_filename, verifier_command=command)
    (tests / "profile.json").write_text(json.dumps(profile, indent=2) + "\n")
    (tests / "test.sh").write_text("#!/bin/bash\nset -euo pipefail\npython /tests/score.py\n")
    (tests / "Dockerfile").write_text(f"FROM {image}\nCOPY . /tests\nWORKDIR /tests\n")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=repo, text=True))
    metadata = dict(benchmark=benchmark, split=split, case_id=case_id, source_commit=commit, source_dirty=dirty, case_sha256=tree_hash(case), verifier_sha256=tree_hash(tests / "benchmarks"), runtime_image=image, solution_filename=solution_filename)
    (output / "task.toml").write_text('\n'.join([
        'schema_version = "1.3"',
        'artifacts = [{source = "/workspace/solution", destination = "solution"}]',
        '[task]', f'name = {json.dumps(f"astroagentbench/{benchmark}-{split}-{case_id}")}',
        '[metadata]', *[f'{key} = {json.dumps(value)}' for key, value in metadata.items()],
        '[environment]', f'cpus = {cpus}', f'memory_mb = {memory_mb}', 'storage_mb = 10240', f'network_mode = {json.dumps(network)}',
        '[agent]', f'timeout_sec = {timeout}',
        '[verifier]', 'environment_mode = "separate"', 'timeout_sec = 600',
        '',
    ]))
    (tests / "task-config.json").write_text(json.dumps(tomllib.loads((output / "task.toml").read_text()), indent=2) + "\n")
    if reference_solution is not None:
        (output / "solution").mkdir()
        shutil.copyfile(reference_solution, output / "solution" / solution_filename)
        (output / "solution/solve.sh").write_text(f"#!/bin/bash\nset -euo pipefail\ncp /solution/{solution_filename} /workspace/solution/{solution_filename}\n")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("benchmark", choices=sorted(p.stem for p in (HERE / "benchmarks").glob("*.yaml")))
    parser.add_argument("split")
    parser.add_argument("case_id")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--image", default="astroagentbench-python:latest")
    parser.add_argument("--cpus", type=int, default=2)
    parser.add_argument("--memory-mb", type=int, default=4096)
    parser.add_argument("--timeout", type=int, default=7200)
    parser.add_argument("--network", choices=["public", "no-network"], default="public")
    parser.add_argument("--reference-solution", type=Path)
    parser.add_argument("--solution-filename", default="solution.json")
    args = vars(parser.parse_args())
    print(prepare(**args))


if __name__ == "__main__":
    main()
