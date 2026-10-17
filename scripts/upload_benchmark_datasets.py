#!/usr/bin/env python3
"""Stage a Harbor taskset from an immutable Git revision; publish only with --publish."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.hf_release import finish_stage, publish

ROOT = Path(__file__).resolve().parents[1]


def git(repo: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=repo)


def stage(repo: Path, revision: str, version: str, output: Path, *, image: str, repo_id: str = "kaupane/AstroAgentBench") -> dict:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", version):
        raise ValueError("Version must be a simple release identifier")
    if not re.fullmatch(r"[^\s@]+@sha256:[0-9a-f]{64}", image):
        raise ValueError("Release runtime image must be pinned by sha256 digest")
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        git(repo, "show-ref", "--verify", f"refs/tags/{revision}")
        revision = f"refs/tags/{revision}"
    commit = git(repo, "rev-parse", "--verify", f"{revision}^{{commit}}").decode().strip()
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{output.name}-", dir=output.parent) as temporary:
        source = Path(temporary) / "source"
        destination = Path(temporary) / "payload"
        # A local clone isolates code, profiles, briefs, cases and Git provenance together.
        subprocess.run(["git", "clone", "--quiet", "--shared", "--no-checkout", str(repo.resolve()), str(source)], check=True)
        git(source, "checkout", "--quiet", "--detach", commit)
        if not (source / "experiments/evaluate/taskset.py").is_file():
            raise ValueError("Selected revision predates the Harbor taskset exporter; use its historical release tooling")
        subprocess.run([sys.executable, "-B", "-m", "experiments.evaluate.taskset", "--output", str(destination),
                        "--version", version, "--image", image], cwd=source, check=True)
        shutil.copyfile(source / "LICENSE", destination / "LICENSE")
        card = (source / "scripts/DATASET_CARD.md").read_text()
        # v2.0.0 used a relative license_link that the Hub now rejects. Render it
        # as the immutable dataset-tag URL without changing the frozen Git tag.
        card = card.replace(
            "license_link: README.md#licensing-and-attribution",
            f"license_link: https://huggingface.co/datasets/{repo_id}/blob/{version}/README.md#licensing-and-attribution",
        )
        card = card.replace("{{RELEASE}}", version).replace("{{SOURCE_COMMIT}}", commit).replace("{{DATASET_REPO}}", repo_id)
        (destination / "README.md").write_text(card)
        return finish_stage(destination, output, {"schema_version": 2, "kind": "harbor-taskset", "version": version,
                                                 "source_commit": commit, "runtime_image": image})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", required=True, help="Full Git commit SHA or release tag")
    parser.add_argument("--version", required=True)
    parser.add_argument("--image", required=True, help="Public runtime image pinned by digest")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo-id", default="kaupane/AstroAgentBench")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--promote", action="store_true", help="Also update main after the published smoke checks pass")
    args = parser.parse_args()
    if args.promote and not args.publish:
        parser.error("--promote requires --publish")
    manifest = stage(ROOT, args.revision, args.version, args.output, image=args.image, repo_id=args.repo_id)
    print(json.dumps({"source_commit": manifest["source_commit"], "files": len(manifest["files"]), "staged": str(args.output)}))
    if args.publish:
        release_commit = git(ROOT, "rev-parse", "--verify", f"refs/tags/{args.version}^{{commit}}").decode().strip()
        if release_commit != manifest["source_commit"]:
            raise ValueError("The matching Git release tag does not identify the staged source commit")
        with tempfile.TemporaryDirectory(prefix="anonymous-docker-") as config:
            subprocess.run(["docker", "--config", config, "pull", args.image], check=True)
        image_commit = subprocess.check_output(["docker", "image", "inspect", "--format",
                                               '{{index .Config.Labels "org.opencontainers.image.revision"}}', args.image], text=True).strip()
        if image_commit != release_commit:
            raise ValueError("Runtime image was not built from the selected release commit")
        print(publish(args.output, args.repo_id, promote=args.promote))


if __name__ == "__main__":
    main()
