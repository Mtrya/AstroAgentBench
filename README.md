# AstroAgentBench

AstroAgentBench evaluates complete agent systems and traditional solvers on space mission design and planning problems. Seven standalone benchmark families provide canonical cases and authoritative verifiers. Systems choose their own models, tools, memory, and coordination; [Harbor](https://docs.harborframework.com/) runs evaluations and collects their outputs.

| Benchmark | Task |
|---|---|
| [AEOSSP](benchmarks/aeossp_standard) | Agile Earth-observation scheduling |
| [Regional coverage](benchmarks/regional_coverage) | Regional strip-imaging schedules |
| [Relay constellation](benchmarks/relay_constellation) | Relay augmentation and contact planning |
| [Revisit constellation](benchmarks/revisit_constellation) | Constellation design and revisit scheduling |
| [SatNet](benchmarks/satnet) | Ground-station tracking schedules |
| [SPOT5](benchmarks/spot5) | Photograph selection and scheduling |
| [Stereo imaging](benchmarks/stereo_imaging) | Stereo and tri-stereo acquisition plans |

## Quickstart

Install [uv](https://docs.astral.sh/uv/) and Docker with Docker Compose. Run these commands from the repository root. Python 3.13.11 and the Python dependencies are locked.

```bash
uv sync --locked --extra evaluation
docker build -t astroagentbench-python:latest runtimes/python
export HARBOR_TELEMETRY=0
```

Run one inexpensive check using an existing SPOT5 reference solution, with no model calls:

```bash
uv run --locked --extra evaluation python -m experiments.evaluate.prepare spot5 test 8 --output .runtime/tasks/spot5-check --reference-solution benchmarks/spot5/dataset/example_solution.json
uv run --locked --extra evaluation harbor run -p .runtime/tasks/spot5-check -a oracle -n 1 --jobs-dir results --job-name spot5-check
uv run --locked --extra evaluation python -m experiments.evaluate.aggregate results/spot5-check --output results/spot5-check.jsonl
```

Preparation refuses to overwrite an existing task directory. Use a new output/job name for a new run. This check exercises installation, artifact transfer, and scoring; it is not an agent evaluation or a paper reproduction.

## Evaluate a system or solver

Prepare a task without `--reference-solution`, then select a Harbor installed-agent adapter or your own `BaseAgent` implementation. The system writes `/workspace/solution/solution.json`; Harbor collects the directory and evaluates it in a separate container. No repository-specific model router or reasoning protocol is required.

[Evaluation instructions](experiments/evaluate/README.md) cover system adapters, a real bounded CELF solver example, settings, results, and limitations. Traditional solvers retain their standalone `setup.sh` / `solve.sh` interfaces under [solvers/](solvers/finished_solvers.json). Each solver README describes its method and compute requirements.

## Versions and contributions

`main` evolves with the project. [`aacl-ijcnlp-2026`](https://github.com/Mtrya/AstroAgentBench/tree/aacl-ijcnlp-2026) preserves the May submission implementation used for the AACL-IJCNLP paper. The January AstroReason-Bench snapshot currently remains at [`v1`](https://github.com/Mtrya/AstroAgentBench/tree/v1). Historical study workflows belong to their corresponding snapshots and history.

Contributions can add benchmarks, improve verifiers or tooling, extend solver baselines, or evaluate a novel agent system. Start with [CONTRIBUTING.md](CONTRIBUTING.md). Benchmark releases are also prepared for Hugging Face with Git commit and checksum provenance; see [release staging](docs/releases.md).

The repository separates [benchmarks](docs/benchmark_contract.md), [evaluation](docs/experiment_contract.md), [solvers](docs/solver_contract.md), and [runtimes](docs/runtime_contract.md). Benchmark verifiers define validity and native scores. Compare systems under declared settings; do not combine unrelated metrics into a single score.
