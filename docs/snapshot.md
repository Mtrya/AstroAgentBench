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

Benchmark releases are also versioned on Hugging Face. Preserved run archives, including available solutions, scores, and traces, are published separately through Zenodo; see [Run archives](#run-archives).

## Run archives

Agent run traces are not committed to this repository. They are staged locally from a run tree, scrubbed, checksummed, and deposited as a citable archive record at [10.5281/zenodo.23084446](https://doi.org/10.5281/zenodo.23084446), which covers the main evaluation matrix, the ablations, and the solver-reference studies.

Unlike benchmark releases, the source is an untracked local directory rather than Git objects. Provenance therefore rests on the repository commit plus a per-file SHA-256 inventory, and the stage is reproducible from the source tree rather than from `git archive`.

```bash
uv run --locked python scripts/stage_run_archives.py --source results --output .runtime/run-archive
```

This command performs no upload. It copies the source tree into a temporary directory, applies the redaction rules, refuses to stage inside the source tree, verifies that no credential survives in the staged copy, confirms that the distribution archives reconstruct the payload exactly, builds one compressed archive per experiment family, and atomically installs the result. `run-archive-manifest.json` records the source commit, every redaction rule, per-rule replacement counts, the excluded paths with reasons, and a SHA-256 and byte size for every staged file and every distribution archive. A repeated identical stage succeeds; replacing a stage whose contents differ fails.

Run archives are evidence, so prompts, completions, tool output, logs, and verifier results are retained verbatim. Credentials are removed by pattern, values stored under secret-bearing JSON keys are removed structurally so the surrounding file stays parseable, and local home directories are rewritten. opencode stores its session transcript in a SQLite database alongside the text logs; that database and its write-ahead and shared-memory sidecars duplicate retained content and cannot be scrubbed by pattern, so they are excluded and listed with their reasons in the manifest. Each decision is recorded in the manifest so a reader can audit what was changed and what was deliberately left alone.

`--max-archive-bytes` bounds the size of each published archive. The deposit endpoint accepts one octet-stream request per file, so oversized archives are published as ordered `.part-NNNN` files that concatenate back to the original, with the whole-file SHA-256 retained under `part_of` in the manifest.

## Validation

Installation, existing bounded tests and contract checks, and paper compilation validate this maintained snapshot. They do not rerun agent experiments. The paper retains its available review layout until camera-ready editing is complete.
