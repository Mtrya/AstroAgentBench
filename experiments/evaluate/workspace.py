"""Open an interactive shell in the environment Harbor builds for one case."""

from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path
import re
import subprocess

from experiments.evaluate.prepare import HERE, prepare, tree_hash

SOLUTION_MOUNT = "/workspace/solution"
IMAGE_PREFIX = "astroagentbench/workspace"


def image_tag(benchmark: str, split: str, case_id: str, environment_sha256: str) -> str:
    """Return a tag that changes whenever the built environment changes.

    The environment digest covers the base image and the case together, so two
    preparations of one case cannot share a tag. Docker repository names are
    lowercase-only and case identifiers such as SatNet's ``W20_2018`` are not,
    so every field is normalized before it reaches the reference.
    """
    fields = [benchmark, split, case_id, environment_sha256[:12]]
    return f"{IMAGE_PREFIX}-" + "-".join(re.sub(r"[^A-Za-z0-9_.-]", "-", f).lower() for f in fields)


def build_command(tag: str, context: Path) -> list[str]:
    return ["docker", "build", "-t", tag, str(context)]


def run_command(
    tag: str,
    solution_dir: Path,
    *,
    cpus: int,
    memory_mb: int,
    network: str,
    command: list[str] | None = None,
) -> list[str]:
    """Build a run command for an interactive shell, or for an explicit command.

    Passing no command allocates a TTY for a shell; passing one runs it headless
    so the entrypoint stays scriptable.
    """
    cmd = ["docker", "run", "--rm"]
    cmd += ["-i", "-t"] if command is None else []
    cmd += ["--cpus", str(cpus), "--memory", f"{memory_mb}m", "--workdir", "/workspace"]
    if network == "no-network":
        cmd += ["--network", "none"]
    # Match the host identity so files left in the solution mount stay editable.
    # That uid has no passwd entry in the runtime. Clearing PS1 makes the image's
    # bashrc return before it installs a default; without that, its \u@\h prompt
    # renders as "I have no name!". Shadowing /etc/passwd would lose system users.
    username = getpass.getuser()
    cmd += ["--user", f"{os.getuid()}:{os.getgid()}", "-e", "HOME=/tmp", "-e", "PS1="]
    cmd += ["-e", f"USER={username}", "-e", f"LOGNAME={username}"]
    cmd += ["-v", f"{solution_dir.resolve()}:{SOLUTION_MOUNT}", tag]
    cmd += command if command is not None else ["bash"]
    return cmd


def workspace(
    benchmark: str,
    split: str,
    case_id: str,
    output: Path,
    *,
    image: str = "astroagentbench-python:latest",
    cpus: int = 2,
    memory_mb: int = 4096,
    network: str = "public",
    solution_filename: str = "solution.json",
    command: str | None = None,
    build: bool = True,
) -> Path:
    task = prepare(
        benchmark,
        split,
        case_id,
        output,
        image=image,
        cpus=cpus,
        memory_mb=memory_mb,
        network=network,
        solution_filename=solution_filename,
    )
    environment_sha256 = tree_hash(task / "environment")
    tag = image_tag(benchmark, split, case_id, environment_sha256)
    if build:
        subprocess.run(build_command(tag, task / "environment"), check=True)
    solution = task / "solution"
    solution.mkdir(exist_ok=True)
    argv = ["bash", "-c", command] if command is not None else None
    completed = subprocess.run(run_command(tag, solution, cpus=cpus, memory_mb=memory_mb, network=network, command=argv))
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)
    print(f"solution: {solution}")
    print(f"score:    python -m experiments.evaluate.score --tests {task / 'tests'} --solution {solution} --output <output>")
    return task


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("benchmark", choices=sorted(p.stem for p in (HERE / "benchmarks").glob("*.yaml")))
    parser.add_argument("split")
    parser.add_argument("case_id")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--image", default="astroagentbench-python:latest")
    parser.add_argument("--cpus", type=int, default=2)
    parser.add_argument("--memory-mb", type=int, default=4096)
    parser.add_argument("--network", choices=["public", "no-network"], default="public")
    parser.add_argument("--solution-filename", default="solution.json")
    parser.add_argument("--command", help="Run this command instead of an interactive shell.")
    parser.add_argument("--no-build", dest="build", action="store_false", help="Reuse the existing environment image.")
    args = vars(parser.parse_args())
    print(workspace(**args))


if __name__ == "__main__":
    main()