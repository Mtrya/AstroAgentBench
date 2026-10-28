English | [中文](docs/i18n/zh_CN/README.md)

<h1 align="center">
<picture>
<source media="(prefers-color-scheme: dark)" srcset="docs/assets/identity/logo-dark.svg">
<img src="docs/assets/identity/logo.svg" alt="AstroAgentBench" width="800">
</picture>
</h1>

**AstroAgentBench is an open benchmark suite for space mission planning, where coding agents and traditional solvers tackle concrete planning problems.** It provides mission cases, independent verifiers, reference solvers, and tools for running evaluations.

[![Paper](https://img.shields.io/badge/arXiv-2601.11354-b31b1b.svg)](https://arxiv.org/abs/2601.11354)
[![Dataset](https://img.shields.io/badge/%F0%9F%A4%97_Hugging_Face-Taskset-yellow)](https://huggingface.co/datasets/kaupane/AstroAgentBench)
[![Run archive](https://zenodo.org/badge/DOI/10.5281/zenodo.23084447.svg)](https://doi.org/10.5281/zenodo.23084447)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

![Two satellites execute a precomputed Earth-observation schedule: one observes A, turns, then observes C; the other observes B during its limited window, then D. A coding agent computes the complete plan before execution.](docs/assets/mission-planning.png)

*An illustrative Earth-observation mission: the coding agent computes a complete schedule, and the constellation executes it. Geometry and timing are schematic.*

[Read the paper](https://arxiv.org/abs/2601.11354) · [Get the taskset](https://huggingface.co/datasets/kaupane/AstroAgentBench) · [Browse agent traces](https://huggingface.co/datasets/kaupane/AstroAgentBench-Traces) · [Full run archive](https://doi.org/10.5281/zenodo.23084447) · [Cite](#citation)

## Explore the missions

Seven benchmark families explore four kinds of planning decisions. Each provides standalone case files and an independent verifier.

<table>
<tr>
<td width="50%"><img src="docs/assets/mission-tour-observe.png" alt="Choose Earth-observation targets, viewing positions, and times."><br><a href="benchmarks/aeossp_standard/README.md">AEOSSP</a> · <a href="benchmarks/spot5/README.md">SPOT-5</a> · <a href="benchmarks/regional_coverage/README.md">Regional Coverage</a> · <a href="benchmarks/stereo_imaging/README.md">Stereo Imaging</a></td>
<td width="50%"><img src="docs/assets/mission-tour-contacts.png" alt="Allocate ground antenna time between competing spacecraft requests."><br><a href="benchmarks/satnet/README.md">SatNet</a></td>
</tr>
<tr>
<td width="50%"><img src="docs/assets/mission-tour-revisit.png" alt="Arrange satellites and observations to revisit targets frequently."><br><a href="benchmarks/revisit_constellation/README.md">Revisit Constellation</a></td>
<td width="50%"><img src="docs/assets/mission-tour-relay.png" alt="Add relays to a fixed backbone and plan contact links."><br><a href="benchmarks/relay_constellation/README.md">Relay Constellation</a></td>
</tr>
</table>

*Illustrative missions: geometry, spacecraft sizes, and timing are schematic.*

## How coding agents participate

![Mission data, objectives, and constraints go to a coding agent, which inspects, codes, runs, and revises locally before submitting a complete plan. An independent verifier checks validity and measures mission value.](docs/assets/agent-workflow.png)

Tasks are [packaged for Harbor](https://huggingface.co/datasets/kaupane/AstroAgentBench): a coding agent works with mission data and constraints, develops its solution through code, and submits a complete plan for [independent verification](experiments/evaluate/README.md). The verifier checks feasibility and measures mission value, providing an outcome that can support both evaluation and reinforcement learning.

## What we’ve learned so far

Coding agents can construct feasible mission plans, but feasibility is only the beginning. Our initial evaluation found substantial differences in mission value across systems and tasks, with some results approaching or exceeding specialized solver references and others leaving considerable room for improvement.

![Initial paper evaluation: five agent systems' mean normalized scores across seven mission families, compared with the best solver reference selected per case and averaged. Valid submissions range from 23 to 35 out of 35 per system.](docs/assets/initial-results.png)

Each point is the mean normalized score over five held-out cases, with missing or invalid submissions scored zero. Compare systems within each family. The [paper](https://arxiv.org/html/2601.11354v3#S4) provides native metrics, confidence intervals, and analysis.

> **Different evaluation protocols:** these are the initial paper results, where agents could use verifier feedback during solving. Current Harbor tasks keep the verifier separate and run it after submission. Use the [frozen paper snapshot](https://github.com/Mtrya/AstroAgentBench/tree/aacl-ijcnlp-2026) and its recorded settings for reproduction.

- **A valid plan can still accomplish little.** Two systems produced valid submissions on all 35 cases, yet their mission scores varied substantially across families.
- **The comparison depends on the mission.** Some agent means exceeded the solver references; Regional Coverage and Stereo Imaging retained larger gaps. Some Stereo runs were also affected by ambiguity in the documented cross-track sign convention, so these outcomes do not isolate planning capability alone.

**[Inspect the results](https://arxiv.org/html/2601.11354v3#S4) · [Browse agent traces](https://huggingface.co/datasets/kaupane/AstroAgentBench-Traces) · [Run your own agent](experiments/evaluate/README.md#agent-systems)**

The trace dataset offers browsable Claude Code and Codex sessions; the [Zenodo archive](https://doi.org/10.5281/zenodo.23084447) includes the other systems and full run artifacts.

<details>
<summary>Full numerical results and evaluation settings</summary>

The paper evaluates each system on **35 held-out cases: five per family**, with a two-hour budget per run on 8 AMD Ryzen 7 9700X cores and 32 GB RAM. Each cell below is the mean normalized score across that family’s five cases; higher is better, with missing or invalid submissions scored zero. “Valid” counts submissions accepted by the verifier.

| Agent system / reference | Valid | AEOSSP | Regional | Relay | Revisit | SatNet | SPOT-5 | Stereo |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Claude Code + Claude Opus 4.6 | 26/35 | 58.45 | 21.22 | 12.25 | 76.50 | 60.36 | 43.96 | 19.16 |
| Codex CLI + GPT-5.4 | 35/35 | 72.91 | 72.08 | 64.91 | 69.58 | 69.45 | 61.92 | 68.91 |
| Kimi CLI + Kimi K2.6 | 35/35 | 72.03 | 73.15 | 57.77 | 73.36 | 66.14 | 61.92 | 0.25 |
| OpenCode + MiniMax M2.7 | 23/35 | 36.44 | 17.73 | 0.00 | 0.00 | 37.54 | 37.47 | 0.00 |
| OpenCode + DeepSeek V4 Pro | 34/35 | 71.44 | 35.79 | 35.67 | 70.95 | 60.23 | 60.91 | 13.00 |
| Best solver reference | — | 75.95 | 86.44 | 61.79 | 70.98 | 61.59 | 60.92 | 96.05 |
| Second solver reference | — | 71.65 | 76.26 | 58.20 | 63.33 | 55.95 | — | 92.00 |

Solver references are selected separately for each case and then averaged within each family; they are quality anchors, not certified optima. SPOT-5 has one reference. Scores use family-specific rules and should be compared within columns. Values are from Table 3 of the paper and are also available as [machine-readable data](docs/assets/initial-results/data.json).

</details>

## News

- **October 2026:** [Runnable Harbor tasksets and browsable native agent traces](https://github.com/Mtrya/AstroAgentBench/releases/tag/v2.0.0) are available on Hugging Face.
- **October 2026:** The [AACL-IJCNLP 2026 paper](https://arxiv.org/abs/2601.11354v3) is available, with the five-system evaluation and a [Zenodo run archive](https://doi.org/10.5281/zenodo.23084447).

## Resources

| I want to… | Start here |
|---|---|
| Understand the benchmark and findings | [Paper](https://arxiv.org/abs/2601.11354) |
| Run released tasks | [Hugging Face taskset](https://huggingface.co/datasets/kaupane/AstroAgentBench) and [evaluation instructions](experiments/evaluate/README.md) |
| Inspect how agents solved tasks | [Browsable Claude Code and Codex sessions](https://huggingface.co/datasets/kaupane/AstroAgentBench-Traces) |
| Examine the full archived runs | [Zenodo archive, v1](https://doi.org/10.5281/zenodo.23084447), including other systems and run artifacts |
| Reproduce the paper | [Paper snapshot and instructions](https://github.com/Mtrya/AstroAgentBench/tree/aacl-ijcnlp-2026) |

## Citation

If you use AstroAgentBench, please cite our AACL-IJCNLP 2026 paper:

```bibtex
@inproceedings{wang2026astroagentbench,
  title = {{AstroAgentBench}: Evaluating Agentic Planning on Space Mission Planning Tasks},
  author = {Wang, Weiyi and Chen, Xinchi and Gong, Jingjing and Huang, Xuanjing and Qiu, Xipeng},
  booktitle = {Proceedings of AACL-IJCNLP 2026},
  year = {2026},
  eprint = {2601.11354},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2601.11354}
}
```

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

The summary in `results/spot5-check.jsonl` should report `"status": "valid"` and `"valid": true`.

Preparation refuses to overwrite an existing task directory. Use a new output/job name for a new run. This check exercises installation, artifact transfer, and scoring; it is not an agent evaluation or a paper reproduction.

## Evaluate a system or solver

Prepare a task without `--reference-solution`, then select a Harbor installed-agent adapter or your own `BaseAgent` implementation. The system writes `/workspace/solution/solution.json`; Harbor collects the directory and evaluates it in a separate container. No repository-specific model router or reasoning protocol is required.

[Evaluation instructions](experiments/evaluate/README.md) cover system adapters, interactive case inspection, a real bounded CELF solver example, settings, results, and limitations. Traditional solvers retain their standalone `setup.sh` / `solve.sh` interfaces under [solvers/](solvers/finished_solvers.json). Each solver README describes its method and compute requirements.

## Versions and contributions

`main` evolves with the project. [`aacl-ijcnlp-2026`](https://github.com/Mtrya/AstroAgentBench/tree/aacl-ijcnlp-2026) preserves the May submission implementation used for the AACL-IJCNLP paper. The January AstroReason-Bench snapshot is preserved in [`acl-submission-2026`](https://github.com/Mtrya/AstroAgentBench/tree/acl-submission-2026). Historical study workflows belong to their corresponding snapshots and history.

Contributions can add benchmarks, improve verifiers or tooling, extend solver baselines, or evaluate a novel agent system. Start with [CONTRIBUTING.md](CONTRIBUTING.md). Benchmark releases are also prepared for Hugging Face with Git commit and checksum provenance; see [release staging](docs/releases.md).

The repository separates [benchmarks](docs/benchmark_contract.md), [evaluation](docs/experiment_contract.md), [solvers](docs/solver_contract.md), and [runtimes](docs/runtime_contract.md). Benchmark verifiers define validity and native scores. Compare systems under declared settings; do not combine unrelated metrics into a single score.
