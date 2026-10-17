import hashlib
import json
from pathlib import Path

import pytest

from scripts.hf_release import validate_stage
from scripts.upload_agent_traces import stage, validate_session

CODEX = 'agent_runs/experiments/main/spot5/codex/test/8/session_logs/sessions/2026/01/01/rollout-example.jsonl'
CLAUDE = 'agent_runs/experiments/main/spot5/claude/test/8/session_logs/projects/workspace/example.jsonl'
OTHER = 'agent_runs/experiments/main/spot5/opencode/test/8/session_logs/history.jsonl'


def archive(tmp_path, *, unsafe=False):
    root = tmp_path / 'archive'
    sessions = {
        CODEX: [{'type': 'session_meta', 'payload': {'cwd': '/workspace'}},
                {'type': 'response_item', 'payload': {'type': 'reasoning', 'encrypted_content': 'sk-' + 'a' * 32}},
                {'type': 'response_item', 'payload': {'type': 'message', 'content': '/home/person/file' if unsafe else '/home/[REDACTED_USER]/file'}}],
        CLAUDE: [{'type': 'user', 'message': {'role': 'user', 'content': 'Solve the case'}},
                 {'type': 'assistant', 'message': {'role': 'assistant', 'content': []}}],
        OTHER: [{'text': 'Unsupported history'}],
    }
    files = {}
    for name, rows in sessions.items():
        path = root / 'run-archive' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = ''.join(json.dumps(row) + '\n' for row in rows).encode()
        path.write_bytes(payload)
        files[name] = {'sha256': hashlib.sha256(payload).hexdigest(), 'bytes': len(payload)}
    manifest = root / 'run-archive-manifest.json'
    manifest.write_text(json.dumps({'files': files, 'source': {'commit': 'a' * 40}}))
    return root, hashlib.sha256(manifest.read_bytes()).hexdigest()


def test_selection_preserves_session_bytes_and_provenance(tmp_path):
    root, digest = archive(tmp_path)
    output = tmp_path / 'release'
    result = stage(root, output, manifest_sha256=digest)
    assert result['sessions'] == {'codex': 1, 'claude-code': 1}
    assert result['archive_manifest_sha256'] == digest
    for name in (CODEX, CLAUDE):
        assert (output / 'sessions' / name).read_bytes() == (root / 'run-archive' / name).read_bytes()
    assert not (output / 'sessions' / OTHER).exists()
    assert stage(root, output, manifest_sha256=digest) == result
    assert validate_stage(output) == result
    (root / 'run-archive' / CODEX).write_text('{}\n')
    with pytest.raises(ValueError, match='differs'):
        stage(root, tmp_path / 'corrupt', manifest_sha256=digest)
    with pytest.raises(ValueError, match='manifest'):
        stage(root, tmp_path / 'wrong-source', manifest_sha256='0' * 64)


def test_unsafe_archive_is_not_installed(tmp_path):
    root, digest = archive(tmp_path, unsafe=True)
    output = tmp_path / 'release'
    with pytest.raises(ValueError, match='personal home path'):
        stage(root, output, manifest_sha256=digest)
    assert not output.exists()


def test_plaintext_credentials_and_malformed_sessions_fail(tmp_path):
    session = tmp_path / 'rollout-test.jsonl'
    session.write_text(json.dumps({'type': 'session_meta', 'payload': {'text': 'hf_' + 'a' * 34}}) + '\n')
    with pytest.raises(ValueError, match='provider credential'):
        validate_session(session, 'codex')
    session.write_text('{broken\n')
    with pytest.raises(json.JSONDecodeError):
        validate_session(session, 'codex')
    session.write_text(json.dumps({'type': 'session_meta', 'payload': {}}) + '\n')
    with pytest.raises(ValueError, match='Incomplete'):
        validate_session(session, 'codex')
