"""Warn when an English source document changed without its zh_CN translation.

This is a soft, per-change warning, not a repository-state gate. It is meant to
run on ``pull_request`` over the set of Markdown files that pull request actually
touched, and it reports translations that are missing, stale, or that dropped a
code identifier from the source.

Deliberately not enforced here:

* the exclusion list is documentation, not a checked invariant
* the ``_TERMS.md`` glossary is not linted

Both decisions are recorded in the design issue. The previous revision of this
script counted H1/H2 headings, which let a full repository rename through
unnoticed and then stayed permanently red on the one file that had drifted.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

TRANSLATION_ROOT = Path("docs") / "i18n" / "zh_CN"

#: Directories whose Markdown is never translated, as a path prefix.
#:
#: Two distinct kinds of input are excluded, and the distinction matters.
#:
#: ``experiments/evaluate/instructions/`` holds prompts handed to *space agents*
#: under evaluation. Translating them changes what those agents are told, which
#: moves benchmark scores and breaks reproducibility against published results.
#:
#: ``AGENTS.md`` and ``CLAUDE.md`` guide *coding agents* developing this
#: repository. Translating them does not affect any score, but it would create a
#: second, drifting source of truth for repository policy.
#:
#: ``benchmarks/<name>/dataset/*.md`` holds vendored upstream papers, which are
#: third-party copyrighted text.
EXCLUDED_PREFIXES = (
    Path("experiments") / "evaluate" / "instructions",
    Path("tests") / "fixtures",
    Path("docs") / "internal",
    Path("docs") / "i18n",
    # Vendored third-party trees: the bundled brahe skill ships several hundred
    # upstream documents that are not ours to translate.
    Path(".agents"),
    Path(".claude"),
    Path("vendor"),
)

#: Individual files that are never translated.
EXCLUDED_FILES = (
    Path("AGENTS.md"),
    Path("CLAUDE.md"),
    Path("CONTRIBUTING.md"),
    # Agent-facing skill source, not reader documentation: generate_brahe_skill.py
    # consumes it to build the vendored .agents/skills/brahe/ tree.
    Path("scripts") / "BRAHE_SKILL.md",
    # Body of the pull request that brahe-skill-sync.yml opens automatically.
    Path(".github") / "PULL_REQUEST_TEMPLATE" / "brahe_skill_sync.md",
)


def _is_vendored_dataset_paper(rel_path: Path) -> bool:
    """Report whether a path is a vendored upstream paper inside a dataset directory.

    Only files sitting directly in ``benchmarks/<name>/dataset/`` qualify. The
    dataset ``README.md`` is repository-authored documentation and stays in scope,
    so this cannot be expressed as a blanket ``benchmarks/*/dataset/*.md`` glob.
    """
    parts = rel_path.parts
    return (
        len(parts) == 4
        and parts[0] == "benchmarks"
        and parts[2] == "dataset"
        and parts[3] != "README.md"
    )

STAMP_PATTERN = re.compile(r"<!--\s*i18n-source-sha256:\s*([0-9a-f]{64})\s*-->")

#: An opening or closing code fence, per CommonMark: up to three spaces of
#: indentation, then three or more backticks or three or more tildes.
FENCE_PATTERN = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")

#: Inline code spans. The opening run of backticks is captured and matched by
#: backreference, so CommonMark's multi-backtick delimiters -- ``` ``a`b`` ```
#: -- are recognised as a single span rather than silently skipped.
INLINE_CODE_PATTERN = re.compile(r"(?<!`)(`+)(?!`)([^\n]+?)\1(?!`)")

GIT_LOCATION_VARS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_COMMON_DIR",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
)


def git_env() -> dict[str, str]:
    """Keep git pointed at this checkout rather than one inherited from the caller."""
    return {key: value for key, value in os.environ.items() if key not in GIT_LOCATION_VARS}


def is_excluded(rel_path: Path) -> bool:
    """Report whether a repository-relative path is outside the translation scope."""
    if rel_path in EXCLUDED_FILES:
        return True
    if any(rel_path == prefix or prefix in rel_path.parents for prefix in EXCLUDED_PREFIXES):
        return True
    return _is_vendored_dataset_paper(rel_path)


def mapped_zh_path(rel_path: Path) -> Path:
    """Mirror an English source into the zh_CN tree.

    The mapping is a pure mirror: ``docs/benchmark_contract.md`` becomes
    ``docs/i18n/zh_CN/docs/benchmark_contract.md`` and ``README.md`` becomes
    ``docs/i18n/zh_CN/README.md``. The previous revision carried special cases for
    the root README, ``docs/`` and ``scripts/`` that each returned exactly this
    value, so they were dead branches.
    """
    return TRANSLATION_ROOT / rel_path


def normalize_newlines(text: str) -> str:
    """Collapse CRLF and CR to LF.

    A checkout on Windows with ``core.autocrlf`` rewrites Markdown line endings on
    disk while git stores LF. That is a local checkout artefact, not a change to
    the committed document, so the stamp must not react to it.
    """
    return text.replace("\r\n", "\n").replace("\r", "\n")


def source_sha256(text: str) -> str:
    """Hash the source document with line endings normalised.

    The stamp answers "did the committed English content change?". Hashing raw
    bytes instead would make the same commit hash differently on a CRLF
    checkout, so every contributor on Windows would see a false "stale" report
    for a document that had not changed. The translate-docs skill stamps with
    the matching normalisation; the two must not drift apart.
    """
    return hashlib.sha256(normalize_newlines(text).encode("utf-8")).hexdigest()


def read_stamp(text: str) -> str | None:
    match = STAMP_PATTERN.search(text)
    return match.group(1) if match else None


def _strip_fenced_blocks(text: str) -> str:
    """Remove fenced code blocks, following CommonMark fence-matching rules.

    A block opened with backticks closes only on a run of backticks of at least
    the opening length, and vice versa for tildes. Matching on "any fence line"
    would end a block early on an unrelated fence character and then scan the
    remaining code as prose, inventing code spans that are not really there.
    """
    kept: list[str] = []
    open_char: str | None = None
    open_len = 0

    for line in text.splitlines():
        match = FENCE_PATTERN.match(line)
        if open_char is None:
            if match is not None:
                open_char = match.group(1)[0]
                open_len = len(match.group(1))
            else:
                kept.append(line)
            continue

        if match is not None:
            marker, rest = match.group(1), match.group(2)
            if marker[0] == open_char and len(marker) >= open_len and not rest.strip():
                open_char = None
                open_len = 0
        # Lines inside an open block are dropped.

    return "\n".join(kept)


def inline_code_spans(text: str) -> Counter[str]:
    """Return inline code span occurrences, ignoring fenced code blocks.

    Counts rather than a set: if a source repeats an identifier twice and the
    translation keeps it once, that is a dropped occurrence worth reporting, and
    set difference would hide it.
    """
    return Counter(m.group(2) for m in INLINE_CODE_PATTERN.finditer(_strip_fenced_blocks(text)))


@dataclass(frozen=True)
class SyncProblem:
    source: str
    kind: str
    detail: str

    def render(self) -> str:
        return f"| `{self.source}` | {self.kind} | {self.detail} |"


def check_source(rel_path: Path, repo_root: Path = REPO_ROOT) -> list[SyncProblem]:
    """Check one English source against its translation."""
    if is_excluded(rel_path):
        return []

    source_file = repo_root / rel_path
    zh_file = repo_root / mapped_zh_path(rel_path)

    if not source_file.is_file():
        # A pull request that deletes a source but leaves the mirror behind
        # orphans the translation, whose [English] link then points at nothing.
        if zh_file.is_file():
            return [
                SyncProblem(
                    rel_path.as_posix(),
                    "orphaned translation",
                    f"source is gone but `{mapped_zh_path(rel_path).as_posix()}` still exists",
                )
            ]
        return []

    source_text = source_file.read_text(encoding="utf-8")

    if not zh_file.is_file():
        return [
            SyncProblem(
                rel_path.as_posix(),
                "missing translation",
                "no file at "
                f"`{mapped_zh_path(rel_path).as_posix()}`",
            )
        ]

    zh_text = zh_file.read_text(encoding="utf-8")
    problems: list[SyncProblem] = []

    stamp = read_stamp(zh_text)
    expected = source_sha256(source_text)
    if stamp is None:
        problems.append(
            SyncProblem(
                rel_path.as_posix(),
                "unstamped",
                "translation carries no `i18n-source-sha256` comment",
            )
        )
    elif stamp != expected:
        problems.append(
            SyncProblem(
                rel_path.as_posix(),
                "stale",
                f"stamped `{stamp[:12]}…`, source now hashes to `{expected[:12]}…`",
            )
        )

    dropped = inline_code_spans(source_text) - inline_code_spans(zh_text)
    if dropped:
        shown = sorted(dropped.items())[:5]
        listed = ", ".join(
            f"`{span}`" if count == 1 else f"`{span}` ×{count}" for span, count in shown
        )
        more = "" if len(dropped) <= 5 else f" (+{len(dropped) - 5} more)"
        problems.append(
            SyncProblem(
                rel_path.as_posix(),
                "missing code span",
                f"{sum(dropped.values())} occurrence(s) absent from the translation: "
                f"{listed}{more}",
            )
        )

    return problems


def tracked_markdown_paths(repo_root: Path = REPO_ROOT) -> list[Path]:
    """List every tracked Markdown document, excluding vendored and private trees.

    Discovery is git-tracked rather than a filesystem walk. A walk reaches into
    ``.venv/``, ``.runtime/`` and ``.local-preservation/``, which hold vendored
    or generated Markdown that is not part of the repository.
    """
    result = subprocess.run(
        ["git", "ls-files", "-z", "*.md"],
        cwd=repo_root,
        capture_output=True,
        text=False,
        check=True,
        env=git_env(),
    )
    output = result.stdout.decode("utf-8")
    paths = [Path(item) for item in output.split("\x00") if item]
    return sorted((p for p in paths if not is_excluded(p)), key=lambda p: p.as_posix())


def source_for_translation(rel_path: Path) -> Path | None:
    """Return the English source a translation belongs to, if the path is one."""
    translation_root = TRANSLATION_ROOT.as_posix()
    posix = rel_path.as_posix()
    if not posix.startswith(translation_root + "/"):
        return None
    relative = Path(posix[len(translation_root) + 1 :])
    # The _TERMS.md glossary lives under the translation root without being a
    # translation of any English source. It has no source to map back to;
    # without this, editing it produces a phantom "orphaned translation" for
    # a source that never was. Only that file is exempt — any other name maps
    # normally, so an underscore-prefixed source added later is still checked.
    if relative.name == "_TERMS.md":
        return None
    return relative


def changed_markdown_paths(
    repo_root: Path = REPO_ROOT,
    base_ref: str | None = None,
) -> list[Path]:
    """List in-scope Markdown sources affected by the change against ``base_ref``.

    Defaults to the upstream merge base of the current branch, which is what a
    ``pull_request`` event should inspect.

    Both sides of the pair are collected. A changed English source is checked
    because it may have invalidated its translation, and a changed translation is
    checked because editing one can drop a code identifier without any English
    edit to trigger a staleness comparison.
    """
    if base_ref is None:
        base_ref = _default_base_ref(repo_root)

    if base_ref is None:
        result = subprocess.run(
            ["git", "diff", "--name-only", "-z", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=False,
            check=True,
            env=git_env(),
        )
    else:
        result = subprocess.run(
            ["git", "diff", "--name-only", "-z", f"{base_ref}...HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=False,
            check=True,
            env=git_env(),
        )

    output = result.stdout.decode("utf-8")
    changed = [Path(item) for item in output.split("\x00") if item]

    sources: set[Path] = set()
    for path in changed:
        if path.suffix != ".md":
            continue
        # Map a changed translation back to its source before applying the
        # exclusion list: docs/i18n/ is itself excluded as a source tree, so the
        # check has to happen in this order or every translation is dropped.
        mirrored = source_for_translation(path)
        candidate = mirrored if mirrored is not None else path
        if is_excluded(candidate):
            continue
        sources.add(candidate)

    return sorted(sources, key=lambda p: p.as_posix())


def _default_base_ref(repo_root: Path) -> str | None:
    """Resolve the upstream merge base, or None outside a branch checkout."""
    result = subprocess.run(
        ["git", "merge-base", "HEAD", "@{upstream}"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        env=git_env(),
    )
    if result.returncode != 0:
        return None
    base = result.stdout.strip()
    return base or None


def format_report(problems: list[SyncProblem]) -> str:
    lines = [
        "### zh_CN translations need attention",
        "",
        "These English documents changed in this pull request without their Chinese "
        "translation being brought along. Nothing here blocks the merge; it is a "
        "reminder.",
        "",
        "| English source | Problem | Detail |",
        "|---|---|---|",
    ]
    lines.extend(problem.render() for problem in problems)
    lines.extend(
        [
            "",
            "To refresh one, run the `translate-docs` skill and re-stamp the source "
            "hash. If a translation is intentionally out of date, say so in the pull "
            "request description.",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Warn about zh_CN translations that fell behind their English source."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root path",
    )
    parser.add_argument(
        "--base-ref",
        default=None,
        help="Git ref to diff against. Defaults to the upstream merge base.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Check every in-scope document instead of only changed ones.",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()

    if args.all:
        sources = tracked_markdown_paths(repo_root)
    else:
        sources = changed_markdown_paths(repo_root, args.base_ref)

    problems: list[SyncProblem] = []
    for rel_path in sources:
        problems.extend(check_source(rel_path, repo_root))

    if args.format == "json":
        import json

        print(
            json.dumps(
                [
                    {"source": p.source, "kind": p.kind, "detail": p.detail}
                    for p in problems
                ],
                indent=2,
                ensure_ascii=False,
            )
        )
    elif problems:
        print(format_report(problems))
    else:
        print("No in-scope document changed without its translation.")

    return 0


if __name__ == "__main__":
    sys.exit(main())