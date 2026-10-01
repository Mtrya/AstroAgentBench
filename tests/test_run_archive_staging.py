from pathlib import Path

import pytest

from scripts.stage_run_archives import (
    MANIFEST,
    PAYLOAD,
    credential_hits,
    open_archive,
    redact,
    stage,
    validate_stage,
)

FAKE_KEY = "sk-" + "a1B2c3D4e5F6g7H8" + "i9J0k1L2m3N4o5P6q"


@pytest.fixture
def source(tmp_path: Path) -> Path:
    root = tmp_path / "results"
    (
        root
        / "agent_runs"
        / "experiments"
        / "main_agentic"
        / "case_0001"
        / "session_logs"
    ).mkdir(parents=True)
    (
        root
        / "agent_runs"
        / "experiments"
        / "main_agentic"
        / "case_0001"
        / "session_logs"
        / "rollout.jsonl"
    ).write_text(
        '{"note": "launch", "cmd": "curl -H \'Authorization: Bearer %s\'"}\n' % FAKE_KEY
    )
    (
        root
        / "agent_runs"
        / "experiments"
        / "main_agentic"
        / "case_0001"
        / "agent_stderr.txt"
    ).write_text("no findings here\n")
    (
        root
        / "agent_runs"
        / "experiments"
        / "main_agentic"
        / "case_0001"
        / "session_logs"
        / "opencode.db"
    ).write_bytes(b"SQLite format 3\x00\x01binary payload")
    (root / "agent_runs" / "experiments" / "skill_injection").mkdir(parents=True)
    (
        root / "agent_runs" / "experiments" / "skill_injection" / "opencode.json"
    ).write_text(
        '{\n  "provider": {\n    "dpsk": {\n      "options": {\n'
        '        "baseURL": "https://api.deepseek.com",\n'
        '        "apiKey": "%s"\n      }\n    }\n  }\n}\n' % FAKE_KEY
    )
    (root / "agent_runs" / "experiments" / "skill_injection" / "notes.txt").write_text(
        "workspace was /home/betelgeuse/project\n"
    )
    return root


def test_redact_removes_credentials_and_local_home_paths():
    text, counts = redact(f"key={FAKE_KEY} home=/home/betelgeuse run\n")
    assert FAKE_KEY not in text
    assert "/home/betelgeuse" not in text
    assert counts == {"openai_compatible_key": 1, "local_home_path": 1}


def test_redact_removes_secret_values_without_matching_token_shapes():
    text, counts = redact('{"password": "correct horse battery staple"}\n')
    assert "correct horse" not in text
    assert text.startswith('{"password": "')
    assert counts == {"secret_bearing_key": 1}


def test_stage_redacts_logs_and_keeps_evidence(source, tmp_path):
    manifest = stage(source, tmp_path / "archive", "c" * 40)
    payload = tmp_path / "archive" / PAYLOAD
    rollout = (
        payload
        / "agent_runs/experiments/main_agentic/case_0001/session_logs/rollout.jsonl"
    ).read_text()
    assert FAKE_KEY not in rollout
    assert "Authorization: Bearer [REDACTED]" in rollout
    assert (
        payload / "agent_runs/experiments/main_agentic/case_0001/agent_stderr.txt"
    ).read_text() == "no findings here\n"
    assert manifest["redaction"]["counts_by_rule"]["openai_compatible_key"] == 2


def test_stage_keeps_secret_bearing_json_parseable(source, tmp_path):
    import json

    stage(source, tmp_path / "archive", "c" * 40)
    config = json.loads(
        (
            tmp_path
            / "archive"
            / PAYLOAD
            / "agent_runs/experiments/skill_injection/opencode.json"
        ).read_text()
    )
    options = config["provider"]["dpsk"]["options"]
    assert options["apiKey"] == "[REDACTED]"
    assert options["baseURL"] == "https://api.deepseek.com"


def test_stage_excludes_binary_session_store_and_records_it(source, tmp_path):
    manifest = stage(source, tmp_path / "archive", "c" * 40)
    excluded = manifest["excluded"]
    assert list(excluded) == [
        "agent_runs/experiments/main_agentic/case_0001/session_logs/opencode.db"
    ]
    assert (
        "sqlite"
        in excluded[
            "agent_runs/experiments/main_agentic/case_0001/session_logs/opencode.db"
        ]["reason"]
    )
    assert (
        excluded[
            "agent_runs/experiments/main_agentic/case_0001/session_logs/opencode.db"
        ]["bytes"]
        > 0
    )
    assert not (
        tmp_path
        / "archive"
        / PAYLOAD
        / "agent_runs/experiments/main_agentic/case_0001/session_logs/opencode.db"
    ).exists()


def test_stage_excludes_binary_payloads_named_by_content(source, tmp_path):
    case = (
        source
        / "agent_runs/experiments/main_agentic/case_0001/session_logs/opencode/tool-output"
    )
    case.mkdir(parents=True)
    (case / "tool_elf").write_bytes(b"\x7fELF\x02\x01\x01" + bytes(64))
    manifest = stage(source, tmp_path / "archive", "c" * 40)
    entry = manifest["excluded"][
        "agent_runs/experiments/main_agentic/case_0001/session_logs/opencode/tool-output/tool_elf"
    ]
    assert "ELF" in entry["reason"]
    assert not (
        tmp_path
        / "archive"
        / PAYLOAD
        / "agent_runs/experiments/main_agentic/case_0001/session_logs/opencode/tool-output/tool_elf"
    ).exists()


def test_stage_keeps_text_logs_that_contain_stray_nul_bytes(source, tmp_path):
    stderr = source / "agent_runs/experiments/main_agentic/case_0001/agent_stderr.txt"
    stderr.write_bytes(
        b"Performing one time database migration\n\x00\x01binary noise\n"
    )
    archive = tmp_path / "archive"
    manifest = stage(source, archive, "c" * 40)
    retained = (
        archive
        / PAYLOAD
        / "agent_runs/experiments/main_agentic/case_0001/agent_stderr.txt"
    )
    assert "Performing one time database migration" in retained.read_text(
        errors="replace"
    )
    assert "agent_stderr.txt" not in manifest["excluded"]


def test_staged_tree_carries_no_credentials(source, tmp_path):
    archive = tmp_path / "archive"
    stage(source, archive, "c" * 40)
    for path in (archive / PAYLOAD).rglob("*"):
        if path.is_file():
            assert credential_hits(path) is None


def test_stage_refuses_to_write_inside_source(source):
    with pytest.raises(ValueError, match="inside the source tree"):
        stage(source, source / "nested", "c" * 40)


def test_stage_emits_auditable_manifest(source, tmp_path):
    manifest = stage(source, tmp_path / "archive", "c" * 40)
    rule_ids = {rule["id"] for rule in manifest["redaction"]["rules"]}
    assert {
        "openai_compatible_key",
        "secret_bearing_key",
        "local_home_path",
    } <= rule_ids
    decisions = {
        item["topic"]: item["decision"] for item in manifest["redaction"]["decisions"]
    }
    assert decisions["email addresses"] == "not redacted"
    assert manifest["source"] == {"path": "results", "commit": "c" * 40}
    assert {a["name"] for a in manifest["archives"]} == {
        "archives/agent_runs__experiments__main_agentic.tar.zst",
        "archives/agent_runs__experiments__skill_injection.tar.zst",
    }
    written = (tmp_path / "archive" / MANIFEST).read_text()
    assert "not redacted" in written


def test_stage_is_idempotent_for_identical_input(source, tmp_path):
    first = stage(source, tmp_path / "one", "c" * 40)
    second = stage(source, tmp_path / "two", "c" * 40)
    assert first["files"] == second["files"]
    assert first["archives"] == second["archives"]


def test_stage_never_modifies_the_source_tree(source, tmp_path):
    before = {
        p.relative_to(source).as_posix(): p.read_bytes()
        for p in source.rglob("*")
        if p.is_file()
    }
    stage(source, tmp_path / "archive", "c" * 40)
    after = {
        p.relative_to(source).as_posix(): p.read_bytes()
        for p in source.rglob("*")
        if p.is_file()
    }
    assert before == after


def test_validate_stage_accepts_untouched_and_rejects_tampered(source, tmp_path):
    archive = tmp_path / "archive"
    stage(source, archive, "c" * 40)
    assert validate_stage(archive)["source"]["commit"] == "c" * 40
    target = (
        archive
        / PAYLOAD
        / "agent_runs/experiments/main_agentic/case_0001/agent_stderr.txt"
    )
    target.write_text("edited after staging\n")
    with pytest.raises(ValueError, match="does not match checksums"):
        validate_stage(archive)


def test_stage_archives_files_that_sit_above_the_shard_depth(source, tmp_path):
    loose = source / "main_solver"
    loose.mkdir()
    (loose / "summary.csv").write_text("family,score\naeossp,1.0\n")
    manifest = stage(source, tmp_path / "archive", "c" * 40)
    root = [
        a for a in manifest["archives"] if a["name"].endswith("payload-root.tar.zst")
    ]
    assert len(root) == 1
    assert root[0]["source"] == "."
    assert root[0]["root"] == "payload-root"


def test_every_payload_file_appears_in_exactly_one_archive(source, tmp_path):
    archive = tmp_path / "archive"
    manifest = stage(source, archive, "c" * 40)
    payload = archive / PAYLOAD
    present = {
        p.relative_to(payload).as_posix() for p in payload.rglob("*") if p.is_file()
    }
    covered = set()
    for entry in manifest["archives"]:
        with open_archive(archive / entry["name"]) as handle:
            for member in handle:
                if member.isfile():
                    tail = "/".join(member.name.split("/")[1:])
                    covered.add(
                        tail if entry["source"] == "." else f"{entry['source']}/{tail}"
                    )
    assert covered == present


def test_stage_splits_oversized_archives_into_ordered_parts(source, tmp_path):
    manifest = stage(source, tmp_path / "archive", "c" * 40, 3, 64)
    parts = [a for a in manifest["archives"] if "part_of" in a]
    assert parts
    for part in parts:
        assert part["bytes"] <= 64
        assert part["part_of"]["bytes"] > 64
        assert 1 <= part["part"] <= part["of"]
    regrouped = {}
    for part in parts:
        regrouped.setdefault(part["part_of"]["name"], []).append(part)
    for name, group in regrouped.items():
        group.sort(key=lambda p: p["part"])
        assert [p["part"] for p in group] == list(range(1, len(group) + 1))


def test_split_parts_reassemble_into_the_original_archive(source, tmp_path):
    archive = tmp_path / "archive"
    unsplit = stage(source, archive, "c" * 40)
    whole = next(a for a in unsplit["archives"] if a["bytes"] > 0)
    rebuilt = stage(
        source, tmp_path / "split", "c" * 40, 3, max(1, whole["bytes"] // 3)
    )
    original = (archive / whole["name"]).read_bytes()
    joined = b""
    for entry in sorted(
        (
            a
            for a in rebuilt["archives"]
            if a.get("part_of", {}).get("name") == whole["name"]
        ),
        key=lambda a: a["part"],
    ):
        joined += (archive.parent / "split" / entry["name"]).read_bytes()
    assert joined == original
