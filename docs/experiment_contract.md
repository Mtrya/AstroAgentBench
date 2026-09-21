# Evaluation Contract

`experiments/evaluate/` integrates standalone benchmark and solver CLI/file contracts with Harbor 0.23.0. Harbor is the evaluation runner. The evaluated agent system is the complete harness, models, tools, memory, and coordination supplied by the researcher.

## Task preparation

`python -m experiments.evaluate.prepare BENCHMARK SPLIT CASE --output DIRECTORY` copies one canonical case and its task brief into a self-contained Harbor task. It records the Git commit/dirty state, case and verifier SHA-256 identities, image reference, solution filename, resource limits, and network policy. Existing output directories are never overwritten.

The solving environment has `/workspace/case/` and an empty `/workspace/solution/`. It does not contain other cases, example solutions, repository history, or authoritative verifier code. `--reference-solution` explicitly adds an Oracle solution for integration checks; omit it for evaluated systems. An independent verifier image contains the original case and unmodified benchmark verifier, plus a small CLI-output adapter.

## Execution and scoring

Use Harbor's native `run -p TASK -a ADAPTER` interface. Installed CLI and external `BaseAgent` adapters use the same task environment and output contract. The repository does not implement a second scheduler, Docker lifecycle, retry loop, model router, or agent reasoning protocol.

The required artifact is `solution/solution.json`, or `solution/solution.spot_sol.txt` when explicitly selected for SPOT5. Additional files in the solution directory are collected. Harbor transfers these artifacts into a fresh verifier environment and runs `tests/test.sh`. The adapter executes the benchmark's public verifier CLI, preserves stdout/stderr and native metrics, and emits Harbor numerical rewards. A missing solution is unsuccessful; malformed verifier output or runtime exceptions remain errors, not successful zero-score runs. Invalid solutions retain the metrics reported by the authority, so consumers must consider validity when comparing scores.

`SolverAgent` calls standalone `setup.sh` and `solve.sh CASE CONFIG SOLUTION`. It imports neither solvers nor benchmarks and leaves their scientific implementations unchanged. Solvers and runtimes never invoke benchmark authorities themselves.

## Results and reproducibility

The native job and prepared task are the durable record. The summary includes task/version, system identity/configuration, limits/access settings, status, timing, validity, metrics, errors, and artifact paths. Full traces and model usage counters are optional. Numerical metrics retain benchmark-specific units and directions; no global scalar is defined. Provider drift and stochasticity mean identical historical values are not a migration or CI requirement.

See [the runnable examples](../experiments/evaluate/README.md) for defaults, overrides, installation-only checks, and practical limits. CI uses real example solutions and a bounded standalone solver rather than a model campaign.
