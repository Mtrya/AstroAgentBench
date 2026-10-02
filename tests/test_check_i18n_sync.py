from __future__ import annotations

import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from scripts.check_i18n_sync import (
    REPO_ROOT,
    TRANSLATION_ROOT,
    SyncProblem,
    check_source,
    format_report,
    inline_code_spans,
    is_excluded,
    mapped_zh_path,
    changed_markdown_paths,
    read_stamp,
    source_for_translation,
    source_sha256,
    tracked_markdown_paths,
)


def _stamp(source_text: str) -> str:
    return f"<!-- i18n-source-sha256: {source_sha256(source_text)} -->"


def _make_repo(root: Path, source_rel: str, source_text: str) -> Path:
    source = root / source_rel
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(source_text, encoding="utf-8")
    return source


def _make_translation(root: Path, source_rel: str, source_text: str, body: str) -> Path:
    zh = root / mapped_zh_path(Path(source_rel))
    zh.parent.mkdir(parents=True, exist_ok=True)
    zh.write_text(f"# 标题\n{_stamp(source_text)}\n\n{body}\n", encoding="utf-8")
    return zh


def test_mapped_zh_path_is_a_pure_mirror() -> None:
    assert mapped_zh_path(Path("README.md")) == TRANSLATION_ROOT / "README.md"
    assert (
        mapped_zh_path(Path("docs/benchmark_contract.md"))
        == TRANSLATION_ROOT / "docs" / "benchmark_contract.md"
    )
    assert (
        mapped_zh_path(Path("benchmarks/satnet/dataset/README.md"))
        == TRANSLATION_ROOT / "benchmarks" / "satnet" / "dataset" / "README.md"
    )
    assert (
        mapped_zh_path(Path("solvers/spot5/reference_lookup/README.md"))
        == TRANSLATION_ROOT / "solvers" / "spot5" / "reference_lookup" / "README.md"
    )


@pytest.mark.parametrize(
    "rel_path",
    [
        "AGENTS.md",
        "CLAUDE.md",
        "CONTRIBUTING.md",
        "scripts/BRAHE_SKILL.md",
        ".github/PULL_REQUEST_TEMPLATE/brahe_skill_sync.md",
        "experiments/evaluate/instructions/stereo_imaging.md",
        "tests/fixtures/sgp4_skyfield/README.md",
        "docs/internal/anything.md",
        "docs/i18n/zh_CN/README.md",
        ".agents/skills/brahe/SKILL.md",
        "vendor/SWE-bench/README.md",
    ],
)
def test_excluded_paths(rel_path: str) -> None:
    assert is_excluded(Path(rel_path))


@pytest.mark.parametrize(
    "rel_path",
    [
        "README.md",
        "docs/benchmark_contract.md",
        "benchmarks/satnet/README.md",
        "benchmarks/satnet/dataset/README.md",
        "scripts/DATASET_CARD.md",
        "experiments/evaluate/README.md",
        "solvers/spot5/reference_lookup/README.md",
    ],
)
def test_in_scope_paths(rel_path: str) -> None:
    assert not is_excluded(Path(rel_path))


def test_vendored_papers_excluded_but_dataset_readme_is_not() -> None:
    assert is_excluded(
        Path("benchmarks/spot5/dataset/Earth_Observation_Satellite_Management.md")
    )
    assert not is_excluded(Path("benchmarks/spot5/dataset/README.md"))


def test_missing_translation_is_reported(tmp_path: Path) -> None:
    _make_repo(tmp_path, "docs/contract.md", "# Contract\n")

    problems = check_source(Path("docs/contract.md"), tmp_path)

    assert [(p.kind, p.source) for p in problems] == [
        ("missing translation", "docs/contract.md")
    ]


def test_fresh_stamped_translation_is_clean(tmp_path: Path) -> None:
    source_text = "# Contract\n\nBody with `field_name`.\n"
    _make_repo(tmp_path, "docs/contract.md", source_text)
    _make_translation(tmp_path, "docs/contract.md", source_text, "正文包含 `field_name`。")

    assert check_source(Path("docs/contract.md"), tmp_path) == []


def test_stale_translation_is_reported(tmp_path: Path) -> None:
    _make_repo(tmp_path, "docs/contract.md", "# Contract\n\nOriginal.\n")
    _make_translation(tmp_path, "docs/contract.md", "# Contract\n\nOriginal.\n", "旧译文。")

    _make_repo(tmp_path, "docs/contract.md", "# Contract\n\nRewritten body.\n")

    problems = check_source(Path("docs/contract.md"), tmp_path)
    assert [p.kind for p in problems] == ["stale"]


def test_missing_stamp_is_reported_separately_from_staleness(tmp_path: Path) -> None:
    source_text = "# Contract\n\nBody.\n"
    _make_repo(tmp_path, "docs/contract.md", source_text)
    zh = tmp_path / mapped_zh_path(Path("docs/contract.md"))
    zh.parent.mkdir(parents=True)
    zh.write_text("# 标题\n\n正文。\n", encoding="utf-8")

    problems = check_source(Path("docs/contract.md"), tmp_path)
    assert [p.kind for p in problems] == ["unstamped"]


def test_dropped_code_span_is_reported(tmp_path: Path) -> None:
    source_text = "# Contract\n\nRun `python -m benchmarks.x.run` for `field_name`.\n"
    _make_repo(tmp_path, "docs/contract.md", source_text)
    _make_translation(
        tmp_path,
        "docs/contract.md",
        source_text,
        "运行 `python -m benchmarks.x.run` 即可获得 `field_name`。",
    )
    # A translator silently localising one identifier while leaving the other intact.
    zh = tmp_path / mapped_zh_path(Path("docs/contract.md"))
    zh.write_text(zh.read_text(encoding="utf-8").replace("`field_name`", "字段名"), encoding="utf-8")

    problems = check_source(Path("docs/contract.md"), tmp_path)
    assert [p.kind for p in problems] == ["missing code span"]
    assert "`field_name`" in problems[0].detail


def test_translation_may_add_code_spans(tmp_path: Path) -> None:
    source_text = "# Contract\n\nUses `field_name`.\n"
    _make_repo(tmp_path, "docs/contract.md", source_text)
    _make_translation(
        tmp_path,
        "docs/contract.md",
        source_text,
        "使用 `field_name`，参见 `extra_reference`。",
    )

    assert check_source(Path("docs/contract.md"), tmp_path) == []


def test_fenced_code_blocks_are_not_inline_spans() -> None:
    text = "Intro `inline_span`.\n\n```python\nvalue = `not_a_span`\n```\n\nTail.\n"
    assert inline_code_spans(text) == Counter({"inline_span": 1})


def test_fence_matching_follows_commonmark() -> None:
    """A shorter or differently-characterised fence must not close the block."""
    text = (
        "Before `kept`.\n\n"
        "````text\n"
        "```\n"
        "inner = `swallowed`\n"
        "````\n\n"
        "After `also_kept`.\n"
    )

    assert inline_code_spans(text) == Counter({"kept": 1, "also_kept": 1})


def test_tilde_fence_does_not_close_a_backtick_block() -> None:
    text = "A `x`.\n\n```text\n~~~\nstill code\n```\n\nB `y`.\n"

    assert inline_code_spans(text) == Counter({"x": 1, "y": 1})


def test_repeated_identifier_must_appear_as_often_in_the_translation(tmp_path: Path) -> None:
    source_text = "# Contract\n\nUse `field` before and after `field`.\n"
    _make_repo(tmp_path, "docs/contract.md", source_text)
    _make_translation(
        tmp_path,
        "docs/contract.md",
        source_text,
        "在 `field` 之前使用，并在 `field` 之后再次使用。",
    )

    assert check_source(Path("docs/contract.md"), tmp_path) == []

    # Dropping only the second occurrence must still be caught.
    zh = tmp_path / mapped_zh_path(Path("docs/contract.md"))
    zh.write_text(
        zh.read_text(encoding="utf-8").replace("，并在 `field` 之后再次使用", ""),
        encoding="utf-8",
    )

    problems = check_source(Path("docs/contract.md"), tmp_path)
    assert [p.kind for p in problems] == ["missing code span"]
    assert "`field`" in problems[0].detail


def test_excluded_source_is_never_checked(tmp_path: Path) -> None:
    _make_repo(tmp_path, "AGENTS.md", "# Agents\n")

    assert check_source(Path("AGENTS.md"), tmp_path) == []


def test_deleted_source_is_skipped(tmp_path: Path) -> None:
    assert check_source(Path("docs/does_not_exist.md"), tmp_path) == []


def test_stamp_survives_a_crlf_checkout(tmp_path: Path) -> None:
    """A CRLF working copy is a core.autocrlf artefact, not a content change."""
    source_text = "# Contract\n\nBody with `field_name`.\n"
    _make_repo(tmp_path, "docs/contract.md", source_text)
    _make_translation(tmp_path, "docs/contract.md", source_text, "正文包含 `field_name`。")
    assert check_source(Path("docs/contract.md"), tmp_path) == []

    source = tmp_path / "docs/contract.md"
    source.write_bytes(source.read_bytes().replace(b"\n", b"\r\n"))

    assert check_source(Path("docs/contract.md"), tmp_path) == []


def test_documented_stamping_command_matches_the_checker(tmp_path: Path) -> None:
    """The command the skill tells contributors to run must produce a valid stamp."""
    import subprocess
    import sys as _sys

    source = tmp_path / "docs/contract.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("# Contract\n\nBody.\n", encoding="utf-8")

    command = (
        "import hashlib,pathlib,sys;"
        "t=pathlib.Path(sys.argv[1]).read_text(encoding='utf-8');"
        "print(hashlib.sha256(t.replace('\\r\\n','\\n').replace('\\r','\\n').encode()).hexdigest())"
    )
    stamped = subprocess.run(
        [_sys.executable, "-c", command, str(source)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    assert stamped == source_sha256(source.read_text(encoding="utf-8"))


def test_read_stamp_requires_a_full_sha256() -> None:
    assert read_stamp("<!-- i18n-source-sha256: " + "a" * 64 + " -->") == "a" * 64
    assert read_stamp("<!-- i18n-source-sha256: abc -->") is None
    assert read_stamp("no comment here") is None


def test_format_report_names_the_offending_files() -> None:
    problems = [SyncProblem(source="docs/contract.md", kind="stale", detail="hash changed")]

    report = format_report(problems)

    assert "`docs/contract.md`" in report
    assert "stale" in report
    assert "blocks the merge" in report


def test_tracked_markdown_discovery_skips_vendored_trees() -> None:
    sources = tracked_markdown_paths(REPO_ROOT)

    assert Path("README.md") in sources
    assert Path("docs/benchmark_contract.md") in sources
    assert not any(source.parts[0] == ".agents" for source in sources)
    assert not any(Path("AGENTS.md") == source for source in sources)


def test_every_translation_links_back_to_a_real_english_source() -> None:
    """The language switch is the only route back to the English document.

    Link depth differs per destination directory, and a wrong depth silently
    resolves to a non-existent path rather than failing loudly.
    """
    link_pattern = re.compile(r"\[English\]\(([^)]+)\)")

    translations = [
        path
        for path in (REPO_ROOT / TRANSLATION_ROOT).rglob("*.md")
        if path.name != "_TERMS.md"
    ]
    assert translations, "expected a non-empty zh_CN tree"

    for translation in translations:
        match = link_pattern.search(translation.read_text(encoding="utf-8"))
        assert match, f"{translation} has no [English](...) switch"
        target = (translation.parent / match.group(1)).resolve()
        assert target.is_file(), f"{translation} links to missing {match.group(1)}"


def test_relative_links_inside_translations_resolve() -> None:
    """A translation sits deeper than its source, so its relative links can miss.

    Links are expected to resolve either to a translated document in the mirror
    tree or to the English original. What must never happen is a link that points
    at neither, which renders as a dead anchor on GitHub.
    """
    link_pattern = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
    fenced_pattern = re.compile(r"```.*?```", re.DOTALL)

    translations = [
        path
        for path in (REPO_ROOT / TRANSLATION_ROOT).rglob("*.md")
        if path.name != "_TERMS.md"
    ]

    broken: list[str] = []
    for translation in translations:
        text = fenced_pattern.sub("", translation.read_text(encoding="utf-8"))
        for match in link_pattern.finditer(text):
            link = match.group(1)
            if link.startswith(("http://", "https://", "#", "mailto:")):
                continue
            target = (translation.parent / link.split("#")[0]).resolve()
            if not target.exists():
                broken.append(f"{translation.relative_to(REPO_ROOT)} -> {link}")

    assert not broken, "unresolvable relative links in translations:\n" + "\n".join(broken)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def test_source_for_translation_maps_back_to_the_english_source() -> None:
    assert (
        source_for_translation(Path("docs/i18n/zh_CN/docs/releases.md"))
        == Path("docs/releases.md")
    )
    assert (
        source_for_translation(Path("docs/i18n/zh_CN/README.md")) == Path("README.md")
    )
    assert source_for_translation(Path("docs/releases.md")) is None


def test_changed_translation_is_inspected_even_though_i18n_is_excluded(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """docs/i18n/ is excluded as a source tree, so mapping must happen first.

    A pull request that edits only a translation must still be validated, or a
    dropped code identifier goes unnoticed.
    """
    repo = tmp_path_factory.mktemp("repo")
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")

    for rel in (
        "docs/releases.md",
        "docs/i18n/zh_CN/docs/releases.md",
        "experiments/evaluate/instructions/spot5.md",
    ):
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# doc\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    _git(repo, "checkout", "-q", "-b", "feature")

    (repo / "docs/i18n/zh_CN/docs/releases.md").write_text("# changed\n", encoding="utf-8")
    (repo / "experiments/evaluate/instructions/spot5.md").write_text("# prompt\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "edit translation and agent prompt")

    changed = changed_markdown_paths(repo, "main")

    assert changed == [Path("docs/releases.md")]


def test_repo_translation_tree_covers_every_in_scope_tier_one_document() -> None:
    tier_one = [
        Path("README.md"),
        Path("docs/benchmark_contract.md"),
        Path("docs/solver_contract.md"),
        Path("docs/experiment_contract.md"),
        Path("docs/runtime_contract.md"),
        Path("docs/releases.md"),
        Path("benchmarks/aeossp_standard/README.md"),
        Path("benchmarks/regional_coverage/README.md"),
        Path("benchmarks/relay_constellation/README.md"),
        Path("benchmarks/revisit_constellation/README.md"),
        Path("benchmarks/satnet/README.md"),
        Path("benchmarks/spot5/README.md"),
        Path("benchmarks/stereo_imaging/README.md"),
    ]

    for rel_path in tier_one:
        assert (REPO_ROOT / mapped_zh_path(rel_path)).is_file(), rel_path


def test_no_translation_exists_for_an_excluded_document() -> None:
    translated = {
        path.relative_to(REPO_ROOT / TRANSLATION_ROOT).as_posix()
        for path in (REPO_ROOT / TRANSLATION_ROOT).rglob("*.md")
    }

    for rel_path in translated:
        assert not is_excluded(Path(rel_path)), rel_path


def test_worktree_is_insulated_from_inherited_git_environment(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_i18n_sync.py", "--all", "--format", "json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
        env={
            "PATH": "/usr/bin:/bin",
            "HOME": str(tmp_path),
            "GIT_DIR": str(tmp_path / "nonexistent.git"),
            "GIT_WORK_TREE": str(tmp_path),
            "GIT_COMMON_DIR": str(tmp_path / "nope.common"),
            "GIT_INDEX_FILE": str(tmp_path / "nope.index"),
        },
    )

    assert '"source"' in result.stdout