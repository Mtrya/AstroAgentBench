# Evaluation

Harbor 0.23.0 owns environment lifecycle, concurrency, timeouts, retries, installed or external system adapters, and artifacts. This directory prepares canonical cases, invokes authoritative verifier CLIs, adapts standalone solver CLIs, and summarizes native metrics. See the [evaluation contract](../../docs/experiment_contract.md).

## Agent systems

Prepare a case and run your chosen Harbor adapter:

```bash
uv run --locked --extra evaluation python -m experiments.evaluate.prepare regional_coverage test case_0001 --output .runtime/tasks/regional
uv run --locked --extra evaluation harbor run -p .runtime/tasks/regional -a your_package.agent:YourAgent -n 1 --jobs-dir results --job-name regional-system
```

`your_package.agent:YourAgent` is your installed implementation, not a bundled example. Extend Harbor's [BaseAgent](https://docs.harborframework.com/core-concepts/agents/custom-agents) for systems orchestrated outside the task container, or `BaseInstalledAgent` for a CLI inside it. The system owns its execution loop, provider connections, model settings, tools, memory, and multi-agent coordination. Its adapter transfers files and executes commands through Harbor's environment API. Optional traces can be written to the adapter log directory or `/logs/artifacts`; a trace is not required for scoring.

Harbor also supplies [installed-agent adapters](https://docs.harborframework.com/core-concepts/agents/pre-integrated-agents), including `claude-code`, `codex`, `gemini-cli`, and `opencode`. Select one with `-a`, its model with `-m` when applicable, and adapter options with `--agent-kwarg`. Use the adapter's supported version/config options to identify the evaluated system. `--install-only` checks installation without running a model. Check the selected adapter's upstream documentation for credentials, provider support, and any generated model settings; those settings are part of the evaluated system. Our integration adds no generation overrides. Python interface checks do not establish live provider compatibility.

The general Python runtime supplies scientific libraries, bash, curl, git, and uv. Harbor adapters install their own CLI prerequisites; a system requiring other tools can use its own image via `prepare --image`. No specific harness, provider, or domain skill is bundled into the default runtime.

## Standalone solver example

This runs the real CELF optimizer with a deliberately small 32-candidate cap. It checks integration and can yield zero coverage; use a scientifically appropriate compute budget for comparisons.

```bash
uv run --locked --extra evaluation python -m experiments.evaluate.prepare regional_coverage test case_0001 --output .runtime/tasks/regional-solver
uv run --locked --extra evaluation harbor run -p .runtime/tasks/regional-solver -a experiments.evaluate.solver:SolverAgent --agent-kwarg solver_dir=solvers/regional_coverage/celf_submodular --agent-kwarg config_dir=experiments/evaluate/examples/celf -n 1 --jobs-dir results --job-name regional-celf
uv run --locked --extra evaluation python -m experiments.evaluate.aggregate results/regional-celf --output results/regional-celf.jsonl
```

The adapter uploads the selected solver and public configuration, calls its own `setup.sh`, then `solve.sh CASE CONFIG SOLUTION`. Solver dependencies remain solver-owned and may resolve newer versions; inspect the setup logs and lock a solver environment when reporting a comparison. Setup logs, input hashes, solution, status, and solver-produced debug outputs are retained. Only use a config directory containing material intended for the evaluated environment.

SPOT5's lookup baseline writes native text. Prepare its task with `--solution-filename solution.spot_sol.txt`; other benchmarks use `solution.json`. Lookup baselines validate plumbing and are not optimization methods.

## Settings and results

Prepared tasks default to 2 CPUs, 4096 MiB memory, 10240 MiB requested storage, 7200 seconds of system execution, 600 seconds of verification, and public network access. Harbor defaults to Docker; `-n 1` in the examples runs one trial at a time. Image references, case/verifier hashes, source commit and dirty state, limits, and network policy are recorded. Use an image digest and a clean source commit for a fixed comparison. Docker does not promise a disk quota from `storage_mb`; check the provider's enforcement capabilities.

Use `prepare --cpus`, `--memory-mb`, `--timeout`, `--image`, and `--network no-network` or Harbor's native runtime overrides. No-network requires provider support and prevents external model calls from inside the container; Harbor rejects unsupported policies. Build/setup downloads also depend on your local network and proxy configuration. The normal examples do not grant host networking or mount the repository into the solving container.

Each native Harbor trial contains its actual config, task checksum, system identity, status/error, timing, logs, collected `artifacts/solution/`, and `verifier/` outputs. `report.json` retains native metrics; `reward.json` names them by benchmark and includes validity. Minimize/maximize directions are declared in `benchmarks/*.yaml`; Harbor's generic mean display is not a cross-benchmark ranking. The JSONL summary retains invalid, missing, errored, and unscored trials separately. Keep the prepared task and native job directory with the summary when sharing a run. Traces and token counts are optional.
