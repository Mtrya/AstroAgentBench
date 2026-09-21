# AACL-IJCNLP snapshot

The `aacl-ijcnlp-2026` branch maintains the experimental baseline developed for the May EMNLP submission and used for the AACL-IJCNLP paper. Its public name is AstroAgentBench. Maintenance preserves the benchmark cases, scoring rules, experiment architecture, and pinned environments.

## Environments

The repository environment is resolved by `uv.lock`; install it with `uv sync --locked`. The agent execution environment has separate package pins in [`runtimes/base/Dockerfile`](../runtimes/base/Dockerfile). Traditional solvers prepare their own dependencies through their documented `setup.sh` entrypoints. These are distinct environments and should not be replaced with one another.

The [configuration examples](../experiments/_fragments/configs/README.md) record model identities while leaving authentication to the user. Model aliases, hosted deployments, and stochastic execution can change over time. A new run is not expected to reproduce every historical numerical value.

## Included materials

- [`benchmarks/`](../benchmarks/) contains the canonical cases, generators, and authoritative verifiers.
- [`experiments/`](../experiments/) contains the study runners, configurations, prompts, analysis tools, and preserved reports.
- [Main comparison and ablation tables](../experiments/main_agentic/reports/) retain the reported fields and values; the other study directories include their own reports and case studies.
- [`solvers/`](../solvers/) contains the traditional baselines.
- [`paper/`](../paper/README.md) contains the available manuscript source and its required build assets. Building the paper does not run experiments.

Benchmark releases will also be versioned on Hugging Face. Preserved run archives, including available solutions, scores, and traces, will be linked through Zenodo when the paper release is published.

## Validation

Installation, existing bounded tests and contract checks, and paper compilation validate this maintained snapshot. They do not rerun agent experiments. The paper retains its available review layout until camera-ready editing is complete.
