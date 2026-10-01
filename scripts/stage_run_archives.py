#!/usr/bin/env python3
"""Stage a redacted public archive of agent run traces.

Run archives are produced locally and are not part of any Git commit, so provenance is
anchored on the repository commit plus a per-file checksum inventory rather than on Git
objects. Staging never writes inside the source tree: files are copied and scrubbed into a
temporary directory that is installed atomically, and the source is left untouched.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "run-archive-manifest.json"
PAYLOAD = "run-archive"
README = "ARCHIVE_README.md"
SCHEMA = "astroagentbench-run-archive/1"

REDACTED = "[REDACTED]"
REDACTED_USER = "[REDACTED_USER]"

# Credential shapes. Anything matching these is removed regardless of which provider issued it.
CREDENTIAL_RULES = [
    ("openai_compatible_key", re.compile(r"sk-[A-Za-z0-9_-]{16,}")),
    ("github_fine_grained_token", re.compile(r"github_pat_[A-Za-z0-9_]{20,}")),
    ("github_token", re.compile(r"ghp_[A-Za-z0-9]{20,}")),
    ("aws_access_key_id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("google_api_key", re.compile(r"AIza[0-9A-Za-z_-]{30,}")),
    (
        "private_key_block",
        re.compile(
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"
        ),
    ),
]

# Values stored under a secret-bearing key are removed even when the value is not a known
# token shape. The key name is matched rather than the surrounding text, so the surrounding
# formatting of the file is preserved.
SECRET_KEYS = (
    "apiKey|api_key|apikey|authorization|auth_token|access_token|refresh_token|"
    "accessToken|refreshToken|client_secret|clientSecret|secret|password|passwd|private_key|privateKey"
)
SECRET_VALUE_RULE = (
    "secret_bearing_key",
    re.compile(r'("(?:' + SECRET_KEYS + r')"\s*:\s*)"(?:[^"\\]|\\.)*"', re.IGNORECASE),
    r'\1"[REDACTED]"',
)

HOME_PATH_RULE = (
    "local_home_path",
    re.compile(r"/home/[A-Za-z0-9._-]+"),
    "/home/" + REDACTED_USER,
)

TEXT_RULES = [(name, pattern, REDACTED) for name, pattern in CREDENTIAL_RULES] + [
    SECRET_VALUE_RULE,
    HOME_PATH_RULE,
]

# opencode keeps its session transcript in a SQLite store, alongside its write-ahead and
# shared-memory sidecars, that duplicates the retained text logs. Those are named rather
# than sniffed so the exclusion is explicit in the manifest.
EXCLUDED_SUFFIXES = {
    ".db": "opencode sqlite session store duplicating retained text logs",
    ".db-wal": "opencode sqlite write-ahead log belonging to an excluded session store",
    ".db-shm": "opencode sqlite shared-memory sidecar belonging to an excluded session store",
    ".node": "vendored native addon binary",
}
# A file is only dropped for its content when it *starts* as a binary format. Agent logs such
# as agent_stderr.txt begin as text and can contain stray NUL bytes later; those stay.
BINARY_MAGIC = [
    (b"\x7fELF", "ELF executable image"),
    (b"SQLite format 3\x00", "SQLite database"),
    (b"MZ", "Windows executable image"),
    (b"\x1f\x8b", "gzip stream"),
    (b"\x28\xb5\x2f\xfd", "zstd stream"),
    (b"\x89PNG", "PNG image"),
    (b"PK\x03\x04", "zip archive"),
    (b"\xff\xd8\xff", "JPEG image"),
    (b"\x00\x00\x01\x00", "Windows icon"),
]
SNIFF_BYTES = 4096
# results/agent_runs/experiments/<family> and results/main_solver/<group> are the
# independently useful units, so that is the level each archive is built from.
DEFAULT_SHARD_DEPTH = 3
SCAN_CHUNK = 1 << 20
SCAN_OVERLAP = 1 << 16

DECISIONS = [
    {
        "topic": "email addresses",
        "decision": "not redacted",
        "rationale": (
            "Every address present in the tree is a synthetic placeholder emitted by an agent or "
            "a test fixture, or an author address of vendored third-party code. No author or "
            "personal address appears in the source runs."
        ),
    },
    {
        "topic": "model prompts, completions, and tool output",
        "decision": "retained verbatim",
        "rationale": "These are the evidence the published analysis is built from.",
    },
]


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def inventory(directory: Path) -> dict:
    return {
        p.relative_to(directory).as_posix(): {
            "sha256": checksum(p),
            "bytes": p.stat().st_size,
        }
        for p in sorted(directory.rglob("*"))
        if p.is_file() and p.relative_to(directory).as_posix() != MANIFEST
    }


def redact(text: str) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {}
    for name, pattern, replacement in TEXT_RULES:
        text, hits = pattern.subn(replacement, text)
        if hits:
            counts[name] = counts.get(name, 0) + hits
    return text, counts


def binary_reason(path: Path) -> str | None:
    with path.open("rb") as handle:
        head = handle.read(SNIFF_BYTES)
    for magic, description in BINARY_MAGIC:
        if head.startswith(magic):
            return description
    return None


def is_binary(path: Path) -> bool:
    return binary_reason(path) is not None


def scrub(source: Path, destination: Path) -> dict[str, int]:
    payload = source.read_bytes()
    prefix = b"\xef\xbb\xbf" if payload.startswith(b"\xef\xbb\xbf") else b""
    text, counts = redact(payload[len(prefix) :].decode("utf-8", errors="replace"))
    destination.write_bytes(prefix + text.encode("utf-8"))
    return counts


def credential_hits(path: Path) -> str | None:
    """Return the first credential rule that matches, scanning in bounded memory."""
    carry = ""
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        while True:
            chunk = handle.read(SCAN_CHUNK)
            if not chunk:
                break
            window = carry + chunk
            for name, pattern in CREDENTIAL_RULES:
                if pattern.search(window):
                    return name
            carry = window[-SCAN_OVERLAP:]
    return None


def verify_clean(directory: Path) -> None:
    """Fail loudly rather than staging an archive that still carries a credential."""
    offenders = []
    for path in sorted(directory.rglob("*")):
        if path.is_file() and not is_binary(path):
            rule = credential_hits(path)
            if rule:
                offenders.append(f"{path.relative_to(directory).as_posix()}: {rule}")
    if offenders:
        listing = "\n  ".join(offenders[:20])
        raise ValueError(f"Staged archive still contains credentials:\n  {listing}")


def deterministic(info: tarfile.TarInfo) -> tarfile.TarInfo:
    """Drop timestamps and ownership so identical content yields identical archives."""
    info.mtime = 0
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    info.mode = 0o755 if info.isdir() else 0o644
    return info


def write_archive(destination: Path, build) -> None:
    """Write a tar (optionally zstd-compressed) from a callback that populates it."""
    zstd = shutil.which("zstd")
    tar = destination.with_name(destination.name.removesuffix(".tar.zst") + ".tar")
    with tarfile.open(tar, "w") as handle:
        build(handle)
    if zstd:
        subprocess.run(
            [zstd, "-12", "-T0", "-q", "-f", str(tar), "-o", str(destination)],
            check=True,
        )
        tar.unlink()
    else:
        with tarfile.open(destination, "w:gz") as compressed:
            with tar.open("r") as plain:
                while True:
                    block = plain.read(1 << 20)
                    if not block:
                        break
                    compressed.addfile(_plain_info(tar), plain)
            tar.unlink()


def _plain_info(tar: Path) -> tarfile.TarInfo:
    info = tarfile.TarInfo(tar.name)
    info.size = tar.stat().st_size
    return info


def shard_directories(payload: Path, depth: int) -> list[Path]:
    """Directories exactly ``depth`` levels below the payload, which become the archives."""
    found = [
        p
        for p in sorted(payload.rglob("*"))
        if p.is_dir() and len(p.relative_to(payload).parts) == depth
    ]
    if not found:
        raise ValueError(f"No directory at shard depth {depth} below {payload}")
    return found


def residual_files(payload: Path, depth: int) -> list[Path]:
    """Payload files that sit above the shard depth and would otherwise be lost."""
    return [
        p
        for p in sorted(payload.rglob("*"))
        if p.is_file() and len(p.relative_to(payload).parts) < depth
    ]


def split_archive(path: Path, limit: int) -> list[Path]:
    """Cut one archive into byte-sized parts.

    Zenodo's deposit endpoint accepts a single octet-stream PUT per file and resets the
    connection for larger bodies, so large archives are published as ordered parts.
    """
    parts: list[Path] = []
    with path.open("rb") as source:
        index = 1
        while True:
            chunk = source.read(limit)
            if not chunk:
                break
            part = path.with_name(f"{path.name}.part-{index:04d}")
            part.write_bytes(chunk)
            parts.append(part)
            index += 1
    path.unlink()
    return parts


def build_archives(payload: Path, archive_dir: Path, depth: int) -> list[dict]:
    """One archive per shard directory, plus one for any file the shards do not reach."""
    groups = [
        (d, d.relative_to(payload).as_posix(), d.name)
        for d in shard_directories(payload, depth)
    ]
    loose = residual_files(payload, depth)
    if loose:
        groups.append((loose, ".", "payload-root"))

    built: list[dict] = []
    for group, source, root in groups:
        name = root if source == "." else source.replace("/", "__")
        destination = archive_dir / f"{name}.tar.zst"
        if group is loose:
            write_archive(
                destination,
                lambda h, files=loose: [
                    h.add(
                        f,
                        arcname=f"payload-root/{f.relative_to(payload).as_posix()}",
                        filter=deterministic,
                    )
                    for f in files
                ],
            )
        else:
            write_archive(
                destination,
                lambda h, d=group: h.add(d, arcname=d.name, filter=deterministic),
            )
        built.append(
            {
                "name": f"archives/{destination.name}",
                "source": source,
                "root": root,
                "sha256": checksum(destination),
                "bytes": destination.stat().st_size,
            }
        )
    return built


def apply_part_limit(entries: list[dict], archive_dir: Path, limit: int) -> list[dict]:
    """Replace any oversized archive with ordered parts, keeping the whole-file digest."""
    bounded: list[dict] = []
    for entry in entries:
        path = archive_dir / Path(entry["name"]).name
        if entry["bytes"] <= limit:
            bounded.append(entry)
            continue
        whole = {k: entry[k] for k in ("name", "sha256", "bytes")}
        parts = split_archive(path, limit)
        for index, part in enumerate(parts, 1):
            bounded.append(
                {
                    "name": f"archives/{part.name}",
                    "source": entry["source"],
                    "root": entry["root"],
                    "sha256": checksum(part),
                    "bytes": part.stat().st_size,
                    "part_of": whole,
                    "part": index,
                    "of": len(parts),
                }
            )
    return bounded


@contextlib.contextmanager
def open_archive(path: Path):
    """Open a distribution archive. tarfile only reads zstd on newer interpreters."""
    if path.name.endswith(".tar.zst") and shutil.which("zstd"):
        process = subprocess.Popen(["zstd", "-dcq", str(path)], stdout=subprocess.PIPE)
        try:
            with tarfile.open(fileobj=process.stdout, mode="r|") as handle:
                yield handle
        finally:
            process.stdout.close()
            process.wait()
    else:
        with tarfile.open(path, "r:*") as handle:
            yield handle


def verify_coverage(payload: Path, archives: list[dict], archive_dir: Path) -> None:
    """The distribution archives must reconstruct the payload exactly."""
    covered: set[str] = set()
    for entry in archives:
        path = archive_dir / Path(entry["name"]).name
        with open_archive(path) as handle:
            for member in handle:
                if not member.isfile():
                    continue
                parts = member.name.split("/")
                if parts[0] != entry["root"]:
                    raise ValueError(
                        f"Unexpected archive layout in {path.name}: {member.name}"
                    )
                tail = "/".join(parts[1:])
                covered.add(
                    tail if entry["source"] == "." else f"{entry['source']}/{tail}"
                )
    present = {
        p.relative_to(payload).as_posix() for p in payload.rglob("*") if p.is_file()
    }
    if covered != present:
        missing = sorted(present - covered)
        raise ValueError(
            f"Distribution archives do not cover the staged payload; "
            f"{len(missing)} files missing, e.g. {missing[:5]}"
        )


def build_archive_readme(
    commit: str, excluded: dict, counts: dict, archives: list[dict]
) -> str:
    rules = "\n".join(
        f"- `{name}` — `{pattern.pattern}`" for name, pattern, _ in TEXT_RULES
    )
    decisions = "\n".join(
        f"- **{item['topic']}**: {item['decision']}. {item['rationale']}"
        for item in DECISIONS
    )
    excluded_bytes = sum(item["bytes"] for item in excluded.values())
    reasons = sorted({item["reason"] for item in excluded.values()})
    excluded_note = (
        "\n".join(f"- {reason}" for reason in reasons)
        + f"\n\n{len(excluded)} files totalling {excluded_bytes / 1e9:.2f} GB were excluded; see "
        f"`excluded` in `{MANIFEST}` for every path with its reason and size."
        if excluded
        else "No files were excluded from this archive."
    )
    split = [a for a in archives if "part_of" in a]
    if split:
        groups = sorted({a["part_of"]["name"] for a in split})
        split_note = (
            "\n\nSome archives exceed the deposit endpoint's single-request size limit and are "
            "published as ordered `.part-NNNN` files. Concatenate them in numeric order to "
            "rebuild the original archive, then verify it against the SHA-256 recorded under "
            f"`part_of` in `{MANIFEST}`:\n\n"
            "```bash\n"
            "cat run_agent.tar.zst.part-* > run_agent.tar.zst\n"
            "```\n\n"
            f"Split archives: {', '.join(f'`{g}`' for g in groups)}."
        )
    else:
        split_note = ""
    return f"""# AstroAgentBench Run Archive

Redacted agent run traces for the AstroAgentBench evaluation.

- Source tree: `results/` at repository commit `{commit}`
- Integrity: `{MANIFEST}` records a SHA-256 and byte size for every file under `{PAYLOAD}/`,
  plus a SHA-256 for each distribution archive
- Layout: `{PAYLOAD}/` preserves the original relative paths of the run tree

## Distribution archives

`{PAYLOAD}/` is also provided as one compressed archive per top-level experiment family, so a
reviewer can download only the runs they need. Each archive holds a single top-level directory
named after its family. `{MANIFEST}` lists each archive with its checksum.
{split_note}

## Redaction

Run archives are production evidence, so prompts, completions, tool output, logs, and verifier
results are retained verbatim. The following were removed:

{rules}

Local home directories were additionally rewritten to `/home/{REDACTED_USER}`.

Redactions applied to this archive, by rule:

```
{json.dumps(counts, indent=2, sort_keys=True)}
```

Total replacements: {sum(counts.values())}.

Explicit decisions recorded for audit:

{decisions}

## Exclusions

{excluded_note}
"""


def validate_stage(directory: Path) -> dict:
    manifest = json.loads((directory / MANIFEST).read_text())
    actual = inventory(directory / PAYLOAD)
    if actual != manifest["files"]:
        raise ValueError(f"Staged archive does not match checksums: {directory}")
    return manifest


def stage(
    source: Path,
    output: Path,
    commit: str,
    shard_depth: int = DEFAULT_SHARD_DEPTH,
    max_archive_bytes: int | None = None,
) -> dict:
    source = source.resolve()
    output = output.resolve()
    if not source.is_dir():
        raise ValueError(f"Source directory does not exist: {source}")
    if output == source or source in output.parents:
        raise ValueError("Refusing to stage inside the source tree")

    excluded: dict[str, str] = {}
    counts: dict[str, int] = {}
    per_file: dict[str, dict] = {}

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{output.name}-", dir=output.parent
    ) as temporary:
        built = Path(temporary) / "stage"
        payload = built / PAYLOAD
        payload.mkdir(parents=True)
        for path in sorted(source.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(source).as_posix()
            destination = payload / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix in EXCLUDED_SUFFIXES:
                excluded[relative] = {
                    "reason": EXCLUDED_SUFFIXES[path.suffix],
                    "bytes": path.stat().st_size,
                }
                continue
            sniffed = binary_reason(path)
            if sniffed:
                excluded[relative] = {
                    "reason": f"binary content: {sniffed}",
                    "bytes": path.stat().st_size,
                }
                continue
            file_counts = scrub(path, destination)
            if file_counts:
                per_file[relative] = file_counts
            for name, hits in file_counts.items():
                counts[name] = counts.get(name, 0) + hits

        verify_clean(payload)

        archive_dir = built / "archives"
        archive_dir.mkdir()
        archives = build_archives(payload, archive_dir, shard_depth)
        verify_coverage(payload, archives, archive_dir)
        if max_archive_bytes:
            archives = apply_part_limit(archives, archive_dir, max_archive_bytes)

        manifest = {
            "schema": SCHEMA,
            "source": {"path": source.name, "commit": commit},
            "generated_by": "scripts/stage_run_archives.py",
            "redaction": {
                "rules": [
                    {"id": name, "pattern": pattern.pattern, "replacement": replacement}
                    for name, pattern, replacement in TEXT_RULES
                ],
                "decisions": DECISIONS,
                "counts_by_rule": counts,
                "counts_by_file": per_file,
            },
            "excluded": excluded,
            "files": inventory(payload),
            "archives": archives,
        }
        (built / MANIFEST).write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        )
        (built / README).write_text(
            build_archive_readme(commit, excluded, counts, archives)
        )

        if output.exists():
            if validate_stage(output) != manifest:
                raise FileExistsError(
                    f"Refusing to replace different staged archive: {output}"
                )
            shutil.rmtree(output)
        built.rename(output)

    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "results")
    parser.add_argument(
        "--output", type=Path, default=ROOT / ".runtime" / "run-archive"
    )
    parser.add_argument("--commit", default=git("rev-parse", "HEAD").decode().strip())
    parser.add_argument("--shard-depth", type=int, default=DEFAULT_SHARD_DEPTH)
    parser.add_argument(
        "--max-archive-bytes",
        type=int,
        default=None,
        help="Split distribution archives larger than this many bytes into ordered parts.",
    )
    args = parser.parse_args()

    manifest = stage(
        args.source, args.output, args.commit, args.shard_depth, args.max_archive_bytes
    )
    redaction = manifest["redaction"]
    print(f"Staged {len(manifest['files'])} files to {args.output}")
    print(f"Excluded {len(manifest['excluded'])} files")
    print(
        f"Applied {sum(redaction['counts_by_rule'].values())} redactions in {len(redaction['counts_by_file'])} files"
    )
    for name, hits in sorted(redaction["counts_by_rule"].items()):
        print(f"  {name}: {hits}")
    for archive in manifest["archives"]:
        print(f"  {archive['name']}: {archive['bytes'] / 1e9:.2f} GB")


if __name__ == "__main__":
    main()
