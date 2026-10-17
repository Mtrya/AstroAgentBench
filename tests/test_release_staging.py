from pathlib import Path
import json
import shutil
import subprocess
import tomllib

import pytest

from experiments.evaluate.prepare import ROOT
from scripts.hf_release import finish_stage, needs_promotion, validate_stage, publication_action
from scripts.upload_benchmark_datasets import stage

IMAGE = 'ghcr.io/mtrya/astroagentbench-python@sha256:' + 'a' * 64


def git(repo, *args):
    return subprocess.check_output(['git', *args], cwd=repo, text=True).strip()


@pytest.fixture
def source(tmp_path):
    repo = tmp_path / 'repo'
    repo.mkdir()
    git(repo, 'init', '-q')
    git(repo, 'config', 'user.name', 'Release Test')
    git(repo, 'config', 'user.email', 'test@example.invalid')
    shutil.copytree(ROOT / 'experiments/evaluate', repo / 'experiments/evaluate', ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copyfile(ROOT / 'experiments/__init__.py', repo / 'experiments/__init__.py')
    shutil.copytree(ROOT / 'benchmarks/spot5', repo / 'benchmarks/spot5')
    (repo / 'benchmarks/finished_benchmarks.json').write_text(json.dumps({'benchmarks': [{'name': 'spot5'}]}))
    (repo / 'scripts').mkdir()
    shutil.copyfile(ROOT / 'scripts/DATASET_CARD.md', repo / 'scripts/DATASET_CARD.md')
    shutil.copyfile(ROOT / 'LICENSE', repo / 'LICENSE')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'Canonical SPOT5 and real task exporter')
    return repo


def test_taskset_uses_committed_code_and_data(source, tmp_path):
    revision = git(source, 'rev-parse', 'HEAD')
    brief = source / 'experiments/evaluate/instructions/spot5.md'
    committed_brief = brief.read_text()
    score = source / 'experiments/evaluate/score.py'
    committed_score = score.read_bytes()
    brief.write_text('Uncommitted brief')
    score.write_text('raise RuntimeError("Uncommitted adapter")\n')
    (source / 'benchmarks/spot5/dataset/cases/single_orbit/8/untracked.bin').write_bytes(b'local')
    out = tmp_path / 'release'
    manifest = stage(source, revision, 'v2.0.0', out, image=IMAGE)
    task = out / 'tasks/spot5-single_orbit-8'
    assert (task / 'instruction.md').read_text() == committed_brief.replace('solution.json', '/workspace/solution/solution.json')
    assert (task / 'tests/score.py').read_bytes() == committed_score
    assert not (task / 'environment/case/untracked.bin').exists()
    config = tomllib.loads((task / 'task.toml').read_text())
    assert config['metadata']['source_commit'] == revision
    assert config['metadata']['source_dirty'] is False
    assert config['metadata']['runtime_image'] == IMAGE
    assert {p.name for p in out.iterdir()} == {'README.md', 'LICENSE', 'tasks', 'registry.json', 'release-manifest.json'}
    assert manifest['kind'] == 'harbor-taskset'
    git(source, 'add', '.')
    git(source, 'commit', '-qm', 'Newer source')
    assert stage(source, revision, 'v2.0.0', out, image=IMAGE) == manifest
    with pytest.raises(subprocess.CalledProcessError):
        stage(source, 'HEAD', 'v2.0.0', tmp_path / 'mutable', image=IMAGE)
    (task / 'tests/score.py').write_bytes(b'corrupt')
    with pytest.raises(ValueError):
        validate_stage(out)
    with pytest.raises(ValueError):
        stage(source, revision, 'v2.0.0', out, image=IMAGE)


def test_release_conflicts_and_digest_requirement(source, tmp_path):
    revision = git(source, 'rev-parse', 'HEAD')
    with pytest.raises(ValueError, match='digest'):
        stage(source, revision, 'v2.0.0', tmp_path / 'mutable-image', image='python:latest')
    expected = stage(source, revision, 'v2.0.0', tmp_path / 'release', image=IMAGE)
    assert publication_action(expected, None, None) == 'commit'
    assert publication_action(expected, None, expected) == 'tag'
    assert publication_action(expected, expected, expected) == 'complete'
    changed = dict(expected, source_commit='f' * 40)
    with pytest.raises(ValueError):
        publication_action(expected, changed, None)
    with pytest.raises(ValueError):
        publication_action(expected, None, changed)


@pytest.mark.parametrize('directory', [False, True])
def test_case_symlinks_cannot_export_host_files(source, tmp_path, directory):
    outside = tmp_path / 'host'
    outside.mkdir()
    (outside / 'private.txt').write_text('host-only contents')
    link = source / 'benchmarks/spot5/dataset/cases/single_orbit/8/host-link'
    link.symlink_to(outside if directory else outside / 'private.txt')
    git(source, 'add', '.')
    git(source, 'commit', '-qm', 'Case with an external link')
    output = tmp_path / 'release'
    with pytest.raises(subprocess.CalledProcessError):
        stage(source, git(source, 'rev-parse', 'HEAD'), 'v2.0.0', output, image=IMAGE)
    assert not output.exists()


def test_case_root_symlink_cannot_escape_checkout(source, tmp_path):
    cases = source / 'benchmarks/spot5/dataset/cases'
    outside = tmp_path / 'external-cases'
    cases.rename(outside)
    cases.symlink_to(outside)
    git(source, 'add', '.')
    git(source, 'commit', '-qm', 'External case root')
    output = tmp_path / 'release'
    with pytest.raises(subprocess.CalledProcessError):
        stage(source, git(source, 'rev-parse', 'HEAD'), 'v2.0.0', output, image=IMAGE)
    assert not output.exists()


def test_promotion_checks_files_even_when_manifest_matches(tmp_path):
    payload = tmp_path / 'payload'
    payload.mkdir()
    (payload / 'task.txt').write_text('canonical task')
    expected = finish_stage(payload, tmp_path / 'release', {'version': 'v2.0.0'})
    current = tmp_path / 'main'
    shutil.copytree(tmp_path / 'release', current)
    (current / '.gitattributes').write_text('HF-managed attributes')
    assert not needs_promotion(current, expected)
    (current / 'task.txt').write_text('changed')
    assert needs_promotion(current, expected)
    (current / 'task.txt').write_text('canonical task')
    (current / 'extra.txt').write_text('extra')
    assert needs_promotion(current, expected)
    (current / 'extra.txt').unlink()
    (current / 'task.txt').unlink()
    assert needs_promotion(current, expected)
    (current / 'release-manifest.json').unlink()
    assert needs_promotion(current, expected)
