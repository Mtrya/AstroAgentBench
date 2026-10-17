import json

from harbor.models.registry import DatasetSpec
from harbor.models.task.task import Task

from experiments.evaluate.prepare import ROOT
from experiments.evaluate.score import score
from experiments.evaluate.taskset import export


def test_all_canonical_cases_and_seven_oracles(tmp_path):
    output = tmp_path / 'taskset'
    image = 'ghcr.io/mtrya/astroagentbench-python@sha256:' + 'a' * 64
    registry = [DatasetSpec.model_validate(row) for row in export(output, 'v2.0.0', image)]
    expected = {}
    families = json.loads((ROOT / 'benchmarks/finished_benchmarks.json').read_text())['benchmarks']
    for family in families:
        name = family['name']
        index = json.loads((ROOT / 'benchmarks' / name / 'dataset/index.json').read_text())
        for case in index['cases']:
            expected.setdefault(f"{name}-{case['split']}", set()).add(f"tasks/{name}-{case['split']}-{case['case_id']}")
    assert {spec.name: {str(task.path) for task in spec.tasks} for spec in registry if spec.name != 'smoke'} == expected
    smoke = next(spec for spec in registry if spec.name == 'smoke')
    assert len(smoke.tasks) == len(families)
    for path in output.glob('tasks/*'):
        task = Task(path)
        assert task.config.environment.cpus == 8
        assert task.config.environment.memory_mb == 16384
        assert task.config.agent.timeout_sec == 7200
        assert task.config.verifier.timeout_sec == 600
        assert task.config.verifier.environment_mode.value == 'separate'
        assert task.config.metadata['runtime_image'] == image
    for reference in smoke.tasks:
        path = output / reference.path
        report = score(path / 'tests', path / 'solution', tmp_path / 'scores' / reference.name)
        assert report['valid'] is True
    assert {path.parent.relative_to(output).as_posix() for path in output.glob('tasks/*/solution')} == {str(task.path) for task in smoke.tasks}
