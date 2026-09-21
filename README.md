# AstroAgentBench

AstroAgentBench evaluates complete LLM agent systems on seven space mission planning tasks, alongside traditional solver baselines. Each system produces a solution artifact scored by the same standalone, benchmark-owned verifier.

This branch, `aacl-ijcnlp-2026`, maintains the experimental baseline used for the May EMNLP submission and the subsequent AACL-IJCNLP paper. The evolving implementation is on [`main`](https://github.com/Mtrya/AstroAgentBench/tree/main). The original AstroReason-Bench implementation is preserved separately in [`acl-submission-2026`](https://github.com/Mtrya/AstroAgentBench/tree/acl-submission-2026).

## Task families

| Benchmark | Problem |
|---|---|
| [`satnet`](benchmarks/satnet/) | Deep Space Network ground-station antenna scheduling. |
| [`spot5`](benchmarks/spot5/) | SPOT-5 daily photograph selection under camera, memory, and data-flow constraints. |
| [`aeossp_standard`](benchmarks/aeossp_standard/) | Agile Earth-observation scheduling under agility and power limits. |
| [`stereo_imaging`](benchmarks/stereo_imaging/) | Stereo and tri-stereo acquisition planning over ground targets. |
| [`regional_coverage`](benchmarks/regional_coverage/) | Strip-observation planning for polygonal coverage under retargeting and battery constraints. |
| [`revisit_constellation`](benchmarks/revisit_constellation/) | Constellation and observation planning to minimize target revisit gaps. |
| [`relay_constellation`](benchmarks/relay_constellation/) | Relay augmentation and contact planning under service and latency requirements. |

Each benchmark owns its dataset, generator, verifier, and optional visualizer. Its README and verifier define the task and scoring contract.

## Installation and checks

Install Python 3.13 and [uv](https://docs.astral.sh/uv/), then check out this snapshot:

```bash
git clone --branch aacl-ijcnlp-2026 https://github.com/Mtrya/AstroAgentBench.git
cd AstroAgentBench
uv sync --locked
```

The repository lockfile and the agent runtime's pinned packages describe separate environments. Keep both when using this snapshot. Provider availability and new stochastic runs can change results even with the same configuration.

Run the existing local checks without model calls:

```bash
uv run --locked python scripts/validate_benchmark_contract.py
uv run --locked python scripts/validate_solver_contract.py
uv run --locked pytest tests/
```

The solver check prepares solver-local dependencies and runs its declared small cases. Agent evaluations additionally require Docker and credentials for the selected provider.

## Experiments and recorded results

| Study | Entry point and documentation |
|---|---|
| Agent systems | [`experiments/main_agentic/README.md`](experiments/main_agentic/README.md) |
| Traditional solver baselines | [`experiments/main_solver/README.md`](experiments/main_solver/README.md) |
| Verifier exposure | [`experiments/verifier_exposure/README.md`](experiments/verifier_exposure/README.md) |
| Procedure injection | [`experiments/skill_injection/README.md`](experiments/skill_injection/README.md) |
| Temporal robustness | [`experiments/temporal_robustness/README.md`](experiments/temporal_robustness/README.md) |
| Memory accumulation | [`experiments/memory_accumulation/`](experiments/memory_accumulation/) |

[System configuration examples](experiments/_fragments/configs/README.md) retain model identities and inference settings while keeping credentials user-supplied. The shared runtime is defined in [`runtimes/base/Dockerfile`](runtimes/base/Dockerfile).

Preview a single run without starting a model:

```bash
uv run --locked python experiments/main_agentic/run.py --dry-run --benchmark aeossp_standard --harness codex --case case_0001
```

The preview reports any setup inputs still needed. Before executing agent runs, configure the selected harness and build the runtime and opaque verifier helpers as described in the [verifier-helper guide](experiments/_fragments/opaque_verifiers/README.md).

Recorded [main result tables and case studies](experiments/main_agentic/reports/) and the individual study reports are included. Read [the snapshot guide](docs/snapshot.md) for paper and artifact organization.

## Paper

The available manuscript source, bibliography, styles, and required figures are in [`paper/`](paper/README.md). It builds without rerunning experiments. Camera-ready formatting and author metadata are still being finalized.

The original preprint is [AstroReason-Bench, arXiv:2601.11354](https://arxiv.org/abs/2601.11354). Its existing title identifies that earlier version; the updated paper uses AstroAgentBench.

## Repository contracts

Benchmarks, solvers, and runtimes are standalone. Experiments orchestrate their CLI/file interfaces; benchmark verifiers remain authoritative. See the [benchmark](docs/benchmark_contract.md), [solver](docs/solver_contract.md), [experiment](docs/experiment_contract.md), and [runtime](docs/runtime_contract.md) contracts.

Code is provided under the [MIT license](LICENSE). Dataset-specific provenance and terms are recorded in the [dataset card](scripts/DATASET_CARD.md).
