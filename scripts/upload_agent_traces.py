#!/usr/bin/env python3
"""Stage supported sessions from the frozen Zenodo archive; publish only with --publish."""

from __future__ import annotations

import argparse
import base64
import binascii
from collections import Counter
import hashlib
from http.client import IncompleteRead
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.hf_release import finish_stage, publish

RECORD = "23084447"
TRACE_VERSION = f"zenodo-{RECORD}.1"
FILES_URL = f"https://zenodo.org/api/records/{RECORD}/files"
SOURCE_DOI = f"https://doi.org/10.5281/zenodo.{RECORD}"
ARCHIVE_MANIFEST = "run-archive-manifest.json"
MANIFEST_SHA256 = "8218490689421043031fc23c7e29ebc4ecb7ba6e80b99bc04696a2ecdf3bff19"
CARD = Path(__file__).with_name("TRACES_DATASET_CARD.md")

# Scan decoded text, not opaque encrypted reasoning payloads. Never print matched values.
SECRET_PATTERNS = {
    "provider credential": re.compile(r"(?<![A-Za-z0-9_-])(?:sk-[A-Za-z0-9_-]{16,}|hf_[A-Za-z0-9]{24,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,}|AIza[0-9A-Za-z_-]{30,})(?![A-Za-z0-9_-])"),
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "personal home path": re.compile(r"/(?:home|Users)/[A-Za-z0-9._-]+"),
}
SECRET_KEYS = re.compile(r"(?:^|[^a-z0-9])(?:api_?key|authorization|auth_?token|access_?token|refresh_?token|client_?secret|secret|password|passwd|private_?key|token|credentials?)(?:$|[^a-z0-9])", re.I)


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def session_format(name: str) -> str | None:
    path = Path(name)
    if path.suffix != ".jsonl":
        return None
    if "/session_logs/sessions/" in name and path.name.startswith("rollout-"):
        return "codex"
    if "/session_logs/projects/" in name:
        return "claude-code"
    return None


def opaque_ciphertext(value) -> bool:
    # The frozen Codex archive uses Fernet envelopes. This recognizes their
    # representation, not their authenticity; archive checksums pin the bytes.
    if not isinstance(value, str):
        return False
    try:
        raw = base64.b64decode(value, altchars=b"-_", validate=True)
    except (binascii.Error, ValueError):
        return False
    return len(raw) >= 73 and raw[0] == 0x80 and (len(raw) - 57) % 16 == 0


def screen(value, location: str, kind: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "encrypted_content" and kind == "codex" and value.get("type") in {"reasoning", "compaction"} and opaque_ciphertext(item):
                continue
            normalized_key = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", key)
            if SECRET_KEYS.search(normalized_key) and isinstance(item, str) and item and item != "[REDACTED]":
                raise ValueError(f"Review secret-bearing field in {location}: {key}")
            screen(item, location, kind)
    elif isinstance(value, list):
        for item in value:
            screen(item, location, kind)
    elif isinstance(value, str):
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(value):
                raise ValueError(f"Review {label} in {location}")


def validate_session(path: Path, kind: str) -> None:
    types = set()
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            types.add(row["type"])
            screen(row, f"{path.name}:{number}", kind)
    required = {"session_meta", "response_item"} if kind == "codex" else {"user", "assistant"}
    if not required <= types:
        raise ValueError(f"Incomplete {kind} session: {path.name}")


def read_manifest(archive: Path, expected_sha256: str) -> dict:
    path = archive / ARCHIVE_MANIFEST
    if checksum(path) != expected_sha256:
        raise ValueError("Archive manifest does not match the pinned Zenodo version")
    return json.loads(path.read_text())


def download_file(url: str, destination: Path, expected_sha256: str) -> None:
    if destination.exists():
        if checksum(destination) != expected_sha256:
            raise ValueError(f"Corrupt cached archive file: {destination.name}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
        downloaded = Path(temporary) / "download"
        for attempt in range(3):
            try:
                with urllib.request.urlopen(url, timeout=60) as response, downloaded.open("wb") as handle:
                    shutil.copyfileobj(response, handle)
                    length = response.headers.get("Content-Length")
                    if length is not None and handle.tell() < int(length):
                        raise IncompleteRead(b"", int(length) - handle.tell())
                break
            except (urllib.error.URLError, TimeoutError, IncompleteRead) as error:
                if isinstance(error, urllib.error.HTTPError) and error.code not in {408, 429, 500, 502, 503, 504}:
                    raise
                if attempt == 2:
                    raise
                print(f"Retrying archive download ({attempt + 2}/3): {destination.name}", file=sys.stderr)
                time.sleep(2 ** attempt)
        if checksum(downloaded) != expected_sha256:
            raise ValueError(f"Downloaded archive checksum mismatch: {destination.name}")
        downloaded.rename(destination)


def download_archive(cache: Path) -> Path:
    download_file(f"{FILES_URL}/{ARCHIVE_MANIFEST}/content", cache / ARCHIVE_MANIFEST, MANIFEST_SHA256)
    manifest = read_manifest(cache, MANIFEST_SHA256)
    selected = {name for name in manifest["files"] if session_format(name)}
    groups = {}
    for entry in manifest["archives"]:
        if any(name.startswith(entry["source"] + "/") for name in selected):
            whole = entry.get("part_of", entry)
            groups.setdefault(whole["name"], []).append(entry)
    for entries in groups.values():
        entry = entries[0]
        whole = entry.get("part_of", entry)
        for part in entries:
            download_file(f"{FILES_URL}/{Path(part['name']).name}/content", cache / part["name"], part["sha256"])
        archive = cache / whole["name"]
        if "part_of" in entry:
            with archive.open("wb") as target:
                for part in sorted(entries, key=lambda item: item["part"]):
                    with (cache / part["name"]).open("rb") as source:
                        shutil.copyfileobj(source, target)
        if checksum(archive) != whole["sha256"]:
            raise ValueError(f"Reassembled archive checksum mismatch: {archive.name}")
        # Extract only exact manifest entries; never extract links or unrelated archive paths.
        process = subprocess.Popen(["zstd", "-dcq", str(archive)], stdout=subprocess.PIPE)
        try:
            with tarfile.open(fileobj=process.stdout, mode="r|") as bundle:
                for member in bundle:
                    root, _, tail = member.name.partition("/")
                    name = f"{entry['source']}/{tail}"
                    if root != entry["root"] or not member.isfile() or name not in selected:
                        continue
                    target = cache / "run-archive" / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with bundle.extractfile(member) as source, target.open("wb") as destination:
                        shutil.copyfileobj(source, destination)
        finally:
            process.stdout.close()
            returncode = process.wait()
        if returncode:
            raise subprocess.CalledProcessError(returncode, process.args)
    return cache


def stage(archive: Path, output: Path, *, manifest_sha256: str = MANIFEST_SHA256) -> dict:
    manifest = read_manifest(archive, manifest_sha256)
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    counts = Counter()
    with tempfile.TemporaryDirectory(prefix=f".{output.name}-", dir=output.parent) as temporary:
        destination = Path(temporary) / "payload"
        destination.mkdir()
        for name, expected in sorted(manifest["files"].items()):
            kind = session_format(name)
            if kind is None:
                continue
            source = archive / "run-archive" / name
            if source.stat().st_size != expected["bytes"] or checksum(source) != expected["sha256"]:
                raise ValueError(f"Session differs from the frozen archive: {name}")
            validate_session(source, kind)
            target = destination / "sessions" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            counts[kind] += 1
        if not counts:
            raise ValueError("Archive contains no supported sessions")
        card = CARD.read_text().replace("{{CODEX_COUNT}}", str(counts["codex"]))
        card = card.replace("{{CLAUDE_COUNT}}", str(counts["claude-code"]))
        card = card.replace("{{TRACE_VERSION}}", TRACE_VERSION)
        (destination / "README.md").write_text(card)
        return finish_stage(destination, output, {"schema_version": 2, "kind": "agent-traces", "version": TRACE_VERSION,
                                                 "source_doi": SOURCE_DOI, "source_commit": manifest["source"]["commit"],
                                                 "archive_manifest_sha256": manifest_sha256, "sessions": dict(counts)})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="Existing redacted archive directory containing its manifest and run-archive/")
    parser.add_argument("--cache", type=Path, default=Path(".runtime/zenodo-traces"), help="Download cache when --archive is omitted")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo-id", default="kaupane/AstroAgentBench-Traces")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    archive = args.archive if args.archive is not None else download_archive(args.cache)
    manifest = stage(archive, args.output)
    print(json.dumps({"source_doi": SOURCE_DOI, "sessions": manifest["sessions"], "staged": str(args.output)}))
    if args.publish:
        print(publish(args.output, args.repo_id, promote=True))


if __name__ == "__main__":
    main()
