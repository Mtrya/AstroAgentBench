"""Atomic, immutable Hugging Face dataset releases shared by tasksets and traces."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

MANIFEST = "release-manifest.json"


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


def finish_stage(destination: Path, output: Path, metadata: dict) -> dict:
    manifest = {**metadata, "files": inventory(destination)}
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


def needs_promotion(directory: Path, expected: dict) -> bool:
    manifest = directory / MANIFEST
    if not manifest.exists() or json.loads(manifest.read_text()) != expected:
        return True
    actual = inventory(directory)
    actual.pop(".gitattributes", None)
    return actual != expected["files"]


def publish(directory: Path, repo_id: str, *, promote: bool = False) -> str:
    from huggingface_hub import CommitOperationAdd, CommitOperationDelete, HfApi, hf_hub_download, snapshot_download
    from huggingface_hub.errors import EntryNotFoundError

    expected = validate_stage(directory)
    api = HfApi()
    api.create_repo(repo_id, repo_type="dataset", private=False, exist_ok=True)
    if api.repo_info(repo_id, repo_type="dataset").private:
        raise ValueError("The release dataset must be public")
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
    if promote:
        # Promotion changes only main; immutable release tags keep their original trees.
        parent = api.repo_info(repo_id, repo_type="dataset", revision="main").sha
        current = Path(snapshot_download(repo_id, repo_type="dataset", revision=parent))
        if needs_promotion(current, expected):
            old_files = set(api.list_repo_files(repo_id, repo_type="dataset", revision=parent))
            names = set(expected["files"]) | {MANIFEST}
            operations = [CommitOperationDelete(path_in_repo=name) for name in sorted(old_files - names - {".gitattributes"})]
            operations += [CommitOperationAdd(path_in_repo=name, path_or_fileobj=directory / name) for name in sorted(names)]
            parent = api.create_commit(repo_id, repo_type="dataset", revision="main", parent_commit=parent,
                                       operations=operations, commit_message=f"Promote release {version}").oid
        if validate_stage(Path(snapshot_download(repo_id, repo_type="dataset", revision=parent))) != expected:
            raise ValueError("Default-branch verification failed")
    return commit
