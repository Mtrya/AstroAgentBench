# Contributing to AstroAgentBench

Contributions can improve benchmark definitions and verifiers, add standalone solvers or tools, or evaluate complete agent systems. Describe the scientific or usability problem and the behavior your change enables.

Start benchmark work with its README and verifier. Keep benchmark families standalone. Do not modify committed cases casually; use the benchmark-local generator and explain any intended semantic change. Add focused tests that execute the implementation and check validity, metrics, or file contracts. Keep scientific changes separate from packaging changes.

For systems and solvers, follow the [evaluation contract](docs/experiment_contract.md) and [solver contract](docs/solver_contract.md). Use Harbor's native interfaces for execution. Report the system/version, configuration, resource/access settings, validity, native metrics, and available artifacts. Full internal traces are welcome but optional. Historical studies remain available in their snapshot branches.

Run the inexpensive checks before opening a PR:

```bash
uv sync --locked --extra evaluation
uv run --locked --extra evaluation python scripts/validate_benchmark_contract.py
uv run --locked --extra evaluation python scripts/validate_solver_contract.py
uv run --locked --extra evaluation pytest tests/
```

Changes to evaluation or runtime integration should also exercise the Docker reference-solution quickstart and the bounded solver example. Canonical regeneration runs in CI with networking disabled. No paid model campaign or exact historical score reproduction is required for a refactor. Keep public documentation concise and runnable, and include the relevant validation results in your PR.
