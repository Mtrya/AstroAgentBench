from pathlib import Path
import json
import subprocess

import pytest

from scripts.upload_benchmark_datasets import stage, validate_stage, publication_action


def git(repo, *args):
    return subprocess.check_output(['git', *args], cwd=repo, text=True).strip()


@pytest.fixture
def source(tmp_path):
    repo = tmp_path / 'repo'
    repo.mkdir()
    git(repo, 'init', '-q')
    git(repo, 'config', 'user.name', 'Release Test')
    git(repo, 'config', 'user.email', 'test@example.invalid')
    (repo / 'scripts').mkdir()
    (repo / 'scripts/DATASET_CARD.md').write_text('# Committed release card\n')
    (repo / '.python-version').write_text('3.13.11\n')
    (repo / 'benchmarks/example').mkdir(parents=True)
    (repo / 'benchmarks/example/input.bin').write_bytes(bytes(range(256)))
    (repo / 'benchmarks/example/verifier.py').write_text('print("standalone verifier")\n')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'Release fixture')
    return repo


def test_binary_code_and_immutable_source(source, tmp_path):
    revision = git(source, 'rev-parse', 'HEAD')
    (source / 'benchmarks/example/input.bin').write_bytes(b'local work')
    card = git(source, 'show', f'{revision}:scripts/DATASET_CARD.md')
    (source / 'scripts/DATASET_CARD.md').write_text('# Uncommitted card\n')
    output = tmp_path / 'release'
    manifest = stage(source, revision, 'v1', output)
    assert (output / 'benchmarks/example/input.bin').read_bytes() == bytes(range(256))
    assert (output / '.python-version').read_text() == '3.13.11\n'
    assert manifest['files']['benchmarks/example/verifier.py']['bytes'] > 0
    assert (output / 'README.md').read_text().startswith(card + '\n')
    assert manifest['source_paths']['README.md'] == 'scripts/DATASET_CARD.md'
    git(source, 'add', 'scripts/DATASET_CARD.md')
    git(source, 'commit', '-qm', 'Newer release card')
    assert stage(source, revision, 'v1', output) == manifest
    with pytest.raises(subprocess.CalledProcessError):
        stage(source, 'HEAD', 'v1', tmp_path / 'mutable')
    (output / 'benchmarks/example/input.bin').write_bytes(b'corrupt')
    with pytest.raises(ValueError):
        validate_stage(output)
    with pytest.raises(ValueError):
        stage(source, revision, 'v1', output)


def test_interrupted_staging_and_publication_decisions(source, tmp_path):
    # A process killed before atomic rename leaves a temporary directory, not a release.
    (tmp_path / '.release-interrupted').mkdir()
    (tmp_path / '.release-interrupted/partial.bin').write_bytes(b'partial')
    expected = stage(source, git(source, 'rev-parse', 'HEAD'), 'v1', tmp_path / 'release')
    assert publication_action(expected, None, None) == 'commit'
    assert publication_action(expected, None, expected) == 'tag'
    assert publication_action(expected, expected, expected) == 'complete'
    changed = dict(expected, source_commit='f' * 40)
    with pytest.raises(ValueError):
        publication_action(expected, changed, None)
    with pytest.raises(ValueError):
        publication_action(expected, None, changed)


def test_january_mapping_retains_original_code(source, tmp_path):
    git(source, 'rm', '-r', 'benchmarks')
    git(source, 'rm', 'scripts/DATASET_CARD.md')
    (source / 'README.md').write_text('# Historical repository\n')
    (source / 'src/dataset/regional_coverage/cases').mkdir(parents=True)
    (source / 'src/dataset/regional_coverage/cases/grid.bin').write_bytes(b'\x00\xff')
    (source / 'src/engine').mkdir()
    (source / 'src/engine/core.py').write_text('VALUE = 1\n')
    (source / 'src/local-link').symlink_to('/not-present/local-tools')
    git(source, 'add', '.')
    git(source, 'commit', '-qm', 'January layout')
    out = tmp_path / 'january'
    manifest = stage(source, git(source, 'rev-parse', 'HEAD'), 'january', out)
    assert manifest['layout'] == 'january'
    assert manifest['source_paths']['README.md'] == 'README.md'
    assert (out / 'README.md').read_text().startswith((source / 'README.md').read_text())
    assert manifest['git_modes']['legacy/src/local-link'] == '120000'
    assert (out / 'legacy/src/local-link').read_text() == '/not-present/local-tools'
    assert (out / 'benchmarks/regional_coverage/cases/grid.bin').read_bytes() == b'\x00\xff'
    assert (out / 'legacy/src/engine/core.py').is_file()
    assert (out / 'legacy/src/dataset/regional_coverage/cases/grid.bin').is_file()
