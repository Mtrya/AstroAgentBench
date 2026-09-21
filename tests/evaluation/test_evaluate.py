from pathlib import Path
import json
import shutil
import subprocess
import sys

import pytest

from experiments.evaluate.prepare import ROOT, prepare, tree_hash
from experiments.evaluate.score import score


BENCHMARKS = json.loads((ROOT / 'benchmarks/finished_benchmarks.json').read_text())['benchmarks']


@pytest.mark.parametrize('benchmark', [entry['name'] for entry in BENCHMARKS])
def test_real_example_through_exported_verifier(tmp_path, benchmark):
    from harbor.models.task.task import Task

    dataset = ROOT / 'benchmarks' / benchmark / 'dataset'
    split, case = json.loads((dataset / 'index.json').read_text())['example_smoke_case'].split('/')
    task = prepare(benchmark, split, case, tmp_path / 'task', cpus=3, memory_mb=3072, timeout=123)
    parsed = Task(task)
    assert parsed.config.environment.cpus == 3
    assert parsed.config.agent.timeout_sec == 123
    assert parsed.config.verifier.environment_mode.value == 'separate'
    assert tree_hash(task / 'environment/case') == tree_hash(dataset / 'cases' / split / case)
    assert sorted(p.name for p in (task / 'environment').iterdir()) == ['Dockerfile', 'case']
    solution = tmp_path / 'solution'
    solution.mkdir()
    shutil.copyfile(dataset / 'example_solution.json', solution / 'solution.json')
    report = score(task / 'tests', solution, tmp_path / 'result')
    assert report['valid'] is True
    assert json.loads((tmp_path / 'result/reward.json').read_text())['valid'] == 1
    assert report['metrics']
    assert (tmp_path / 'result/task-config.json').is_file()


def test_missing_invalid_and_broken_verifier_are_distinct(tmp_path):
    task = prepare('spot5', 'test', '8', tmp_path / 'task')
    solution = tmp_path / 'solution'
    solution.mkdir()
    report = score(task / 'tests', solution, tmp_path / 'missing')
    assert report['status'] == 'missing_solution'
    (solution / 'solution.json').write_text('{"assignments": {"999999": 1}}')
    report = score(task / 'tests', solution, tmp_path / 'invalid')
    assert report['status'] == 'invalid'
    (task / 'tests/benchmarks/spot5/verifier.py').write_text('raise RuntimeError("broken verifier")\n')
    with pytest.raises(ValueError):
        score(task / 'tests', solution, tmp_path / 'broken')
    assert not (tmp_path / 'broken/reward.json').exists()
    assert 'RuntimeError' in (tmp_path / 'broken/verifier.stderr').read_text()


def test_existing_task_cannot_be_overwritten(tmp_path):
    output = prepare('spot5', 'test', '8', tmp_path / 'task')
    with pytest.raises(FileExistsError):
        prepare('spot5', 'test', '8', output)


def test_native_installed_and_external_adapter_interfaces():
    from harbor.agents.factory import AgentFactory
    from harbor.agents.installed.base import BaseInstalledAgent
    from harbor.models.trial.config import AgentConfig
    from experiments.evaluate.solver import SolverAgent

    for name in ('claude-code', 'codex', 'gemini-cli', 'opencode'):
        cls = AgentFactory.get_agent_class_from_config(AgentConfig(name=name))
        assert issubclass(cls, BaseInstalledAgent)
    cls = AgentFactory.get_agent_class_from_config(AgentConfig(import_path='experiments.evaluate.solver:SolverAgent'))
    assert cls is SolverAgent
