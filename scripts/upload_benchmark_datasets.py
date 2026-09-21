#!/usr/bin/env python3
"""Stage complete benchmark releases from Git; publish only with --publish."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "release-manifest.json"
# Keep January paths explicit. The original source tree is retained for its imports.
LAYOUTS = {
    "benchmarks": [["benchmarks/", "benchmarks/"]],
    "january": [["src/dataset/", "benchmarks/"], ["src/", "legacy/src/"]],
}


def git(repo: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=repo)


def inventory(directory: Path) -> dict:
    return {p.relative_to(directory).as_posix(): {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size} for p in sorted(directory.rglob("*")) if p.is_file() and p.relative_to(directory).as_posix() != MANIFEST}


def validate_stage(directory: Path) -> dict:
    manifest = json.loads((directory / MANIFEST).read_text())
    actual = inventory(directory)
    # HF-managed attributes are not part of the exported benchmark.
    actual.pop(".gitattributes", None)
    if actual != manifest["files"]:
        raise ValueError(f"Staging content does not match checksums: {directory}")
    return manifest


def stage(repo: Path, revision: str, version: str, output: Path) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", version):
        raise ValueError("Version must be a simple release identifier")
    # A mutable branch name is not a release source. A tag is resolved once to its commit.
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        git(repo, "show-ref", "--verify", f"refs/tags/{revision}")
        revision = f"refs/tags/{revision}"
    commit = git(repo, "rev-parse", "--verify", f"{revision}^{{commit}}").decode().strip()
    entries = []
    for entry in git(repo, "ls-tree", "-rz", commit).split(b"\0"):
        if entry:
            meta, path = entry.split(b"\t", 1)
            mode, kind, oid = meta.decode().split()
            entries.append((mode, kind, oid, path.decode()))
    layout = "benchmarks" if any(p.startswith("benchmarks/") for _, _, _, p in entries) else "january"
    mappings = list(LAYOUTS[layout])
    if any(name == "experiments/evaluate/prepare.py" for _, _, _, name in entries):
        mappings += [["experiments/", "experiments/"], ["runtimes/", "runtimes/"]]
    if not any(p.startswith(mappings[0][0]) for _, _, _, p in entries):
        raise ValueError("Source contains no supported benchmark layout")
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{output.name}-", dir=output.parent) as temporary:
        destination = Path(temporary) / "payload"
        destination.mkdir()
        sources = {}
        modes = {}
        submodules = {}
        for mode, kind, oid, name in entries:
            targets = [target + name[len(source):] for source, target in mappings if name.startswith(source)]
            if name in ("LICENSE", "pyproject.toml", "uv.lock", ".gitmodules"):
                targets.append(name)
            if kind == "commit":
                submodules[name] = oid
                continue
            if targets and mode not in ("100644", "100755", "120000"):
                raise ValueError(f"Unsupported source entry: {name} ({mode})")
            for target in targets:
                file = destination / target
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(git(repo, "cat-file", "blob", oid))
                file.chmod(0o755 if mode == "100755" else 0o644)
                sources[target] = name
                modes[target] = mode
        card = (Path(__file__).with_name("DATASET_CARD.md")).read_text()
        (destination / "README.md").write_text(card + f"\nRelease: `{version}`. Git source: [`{commit}`](https://github.com/Mtrya/AstroAgentBench/tree/{commit}). Source layout: `{layout}`.\n")
        manifest = {"schema_version": 1, "version": version, "source_commit": commit, "layout": layout, "export_mapping": mappings, "source_paths": sources, "git_modes": modes, "external_submodules": submodules, "files": inventory(destination)}
        (destination / MANIFEST).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        validate_stage(destination)
        if output.exists():
            if validate_stage(output) != manifest:
                raise FileExistsError(f"Refusing to replace different staged release: {output}")
        else:
            destination.rename(output)
    return manifest


def publication_action(expected: dict, tagged: dict | None, pending: dict | None) -> str:
    """A released tag is immutable; an interrupted identical commit only needs tagging."""
    if tagged is not None:
        if tagged != expected:
            raise ValueError("Release tag already represents different content")
        return "complete"
    if pending is not None:
        if pending != expected:
            raise ValueError("Release staging branch represents different content")
        return "tag"
    return "commit"


def publish(directory: Path, repo_id: str) -> str:
    from huggingface_hub import CommitOperationAdd, CommitOperationDelete, HfApi, hf_hub_download, snapshot_download
    from huggingface_hub.errors import EntryNotFoundError

    expected = validate_stage(directory)
    release_commit = git(ROOT, "rev-parse", "--verify", f"refs/tags/{expected['version']}^{{commit}}").decode().strip()
    if release_commit != expected["source_commit"]:
        raise ValueError("The matching Git release tag does not identify the staged source commit")
    api = HfApi()
    version = expected["version"]
    branch = f"release-{version}"
    refs = api.list_repo_refs(repo_id, repo_type="dataset")
    tags = {ref.name: ref.target_commit for ref in refs.tags}
    branches = {ref.name: ref.target_commit for ref in refs.branches}

    def remote_manifest(revision: str | None) -> dict | None:
        if revision is None:
            return None
        try:
            path = hf_hub_download(repo_id, MANIFEST, repo_type="dataset", revision=revision)
        except EntryNotFoundError:
            return None
        return json.loads(Path(path).read_text())

    tagged = remote_manifest(tags.get(version))
    if version in tags and tagged is None:
        raise ValueError("Existing release tag has no verifiable manifest")
    pending = remote_manifest(branches.get(branch))
    action = publication_action(expected, tagged, pending)
    if action == "complete":
        commit = tags[version]
    elif action == "tag":
        commit = branches[branch]
    else:
        if branch not in branches:
            base = api.repo_info(repo_id, repo_type="dataset").sha
            api.create_branch(repo_id, branch=branch, repo_type="dataset", revision=base)
        parent = api.repo_info(repo_id, repo_type="dataset", revision=branch).sha
        old_files = set(api.list_repo_files(repo_id, repo_type="dataset", revision=parent))
        names = set(expected["files"]) | {MANIFEST}
        operations = [CommitOperationDelete(path_in_repo=name) for name in sorted(old_files - names - {".gitattributes"})]
        operations += [CommitOperationAdd(path_in_repo=name, path_or_fileobj=directory / name) for name in sorted(names)]
        # One atomic commit: an interrupted blob upload cannot expose a partial release.
        commit = api.create_commit(repo_id, repo_type="dataset", revision=branch, parent_commit=parent, operations=operations, commit_message=f"Benchmark release {version}").oid
    downloaded = Path(snapshot_download(repo_id, repo_type="dataset", revision=commit))
    if validate_stage(downloaded) != expected:
        raise ValueError("Remote release verification failed")
    if action != "complete":
        # Never pass exist_ok: a concurrent tag creation must not be silently accepted.
        api.create_tag(repo_id, tag=version, repo_type="dataset", revision=commit)
    return commit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", required=True, help="Full Git commit SHA or release tag")
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo-id", help="Existing Hugging Face dataset repository")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    manifest = stage(ROOT, args.revision, args.version, args.output)
    print(json.dumps({"source_commit": manifest["source_commit"], "files": len(manifest["files"]), "staged": str(args.output)}))
    if args.publish:
        if not args.repo_id:
            parser.error("--publish requires --repo-id")
        print(publish(args.output, args.repo_id))


if __name__ == "__main__":
    main()
