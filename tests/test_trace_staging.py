import hashlib
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.error import HTTPError

import pytest
import yaml

from scripts.hf_release import validate_stage
from scripts.upload_agent_traces import TRACE_VERSION, download_file, stage, validate_session

CODEX = 'agent_runs/experiments/main/spot5/codex/test/8/session_logs/sessions/2026/01/01/rollout-example.jsonl'
CLAUDE = 'agent_runs/experiments/main/spot5/claude/test/8/session_logs/projects/workspace/example.jsonl'
OTHER = 'agent_runs/experiments/main/spot5/opencode/test/8/session_logs/history.jsonl'
# A real Fernet envelope encrypting synthetic session reasoning.
CIPHERTEXT = 'gAAAAABq03QOhvqWnlqnI9hTY1z6-n9ticaMyTUSN7Q0G8kwJcdSbABg-8sJeGQh8M_yj9-6w6gsixtz8kJePEBZudjQTsyYtTUFBFCrXC3trgC3t40eu6I='


def archive(tmp_path, *, unsafe=False):
    root = tmp_path / 'archive'
    sessions = {
        CODEX: [{'type': 'session_meta', 'payload': {'cwd': '/workspace'}},
                {'type': 'response_item', 'payload': {'type': 'reasoning', 'encrypted_content': CIPHERTEXT}},
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
    assert result['version'] == TRACE_VERSION
    assert result['archive_manifest_sha256'] == digest
    _, frontmatter, _ = (output / 'README.md').read_text().split('---', 2)
    assert yaml.safe_load(frontmatter)['configs'] == [{
        'config_name': 'default',
        'data_files': [{'split': 'train', 'path': 'sessions/**/*.jsonl'}],
    }]
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


@pytest.mark.parametrize('key', ['token', 'credential', 'accessToken', 'AWS_SECRET_ACCESS_KEY', 'OPENAI_API_KEY', 'provider.refreshToken'])
def test_namespaced_credentials_are_rejected(tmp_path, key):
    session = tmp_path / 'rollout-test.jsonl'
    session.write_text(json.dumps({'type': 'session_meta', 'payload': {key: 'unprefixed-sensitive-value'}}) + '\n')
    with pytest.raises(ValueError, match='secret-bearing field') as error:
        validate_session(session, 'codex')
    assert 'unprefixed-sensitive-value' not in str(error.value)


@pytest.mark.parametrize('kind,item_type', [('codex', 'reasoning'), ('codex', 'message'), ('claude-code', 'reasoning')])
def test_encrypted_field_does_not_hide_plaintext(tmp_path, kind, item_type):
    session = tmp_path / 'session.jsonl'
    session.write_text(json.dumps({'type': 'response_item', 'payload': {'type': item_type, 'encrypted_content': {'token': 'sensitive-value'}}}) + '\n')
    with pytest.raises(ValueError, match='secret-bearing field'):
        validate_session(session, kind)
    session.write_text(json.dumps({'type': 'response_item', 'payload': {'type': item_type, 'encrypted_content': 'sk-' + 'a' * 32}}) + '\n')
    with pytest.raises(ValueError, match='provider credential'):
        validate_session(session, kind)


@pytest.fixture
def archive_server():
    replies, requests = [], []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            status, body, length = replies.pop(0)
            self.send_response(status)
            self.send_header('Content-Length', str(length))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = Thread(target=server.serve_forever)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/archive', replies, requests
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_download_retries_transient_and_truncated_responses(tmp_path, archive_server):
    url, replies, requests = archive_server
    body = b'complete archive shard'
    replies.extend([(503, b'', 0), (200, body[:3], len(body)), (200, body, len(body))])
    target = tmp_path / 'archive'
    digest = hashlib.sha256(body).hexdigest()
    download_file(url, target, digest)
    assert target.read_bytes() == body
    assert len(requests) == 3
    download_file(url, target, digest)
    assert len(requests) == 3


@pytest.mark.parametrize('status,attempts', [(403, 1), (503, 3)])
def test_failed_downloads_are_bounded_and_not_cached(tmp_path, archive_server, status, attempts):
    url, replies, requests = archive_server
    replies.extend([(status, b'', 0)] * attempts)
    target = tmp_path / 'archive'
    with pytest.raises(HTTPError):
        download_file(url, target, '0' * 64)
    assert len(requests) == attempts
    assert not target.exists()


def test_download_checksum_failure_is_not_retried_or_cached(tmp_path, archive_server):
    url, replies, requests = archive_server
    replies.append((200, b'corrupt', 7))
    target = tmp_path / 'archive'
    with pytest.raises(ValueError, match='checksum'):
        download_file(url, target, '0' * 64)
    assert len(requests) == 1
    assert not target.exists()
