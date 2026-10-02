# SPOT-5 Dataset Layout

The canonical SPOT-5 dataset is stored case by case under `cases/`.

Each case directory contains exactly one raw instance file:

```text
dataset/
├── index.json
├── example_solution.json
└── cases/
    └── <split>/
        └── <case_id>/
            └── <case_id>.spot
```

Examples:

- `cases/single_orbit/8/8.spot`
- `cases/multi_orbit/1502/1502.spot`
- `cases/test/1021/1021.spot`

`index.json` records the benchmark name, upstream provenance, the list of
published split-aware case placements, and `example_smoke_case` for pairing the
example solution with a case in CI (see `docs/benchmark_contract.md`).

`example_solution.json` is one runnable solution (same schema as a real submission) for verifier smoke tests. It is not a baseline.

The committed split assignment is recorded in [splits.yaml](../splits.yaml).
It defines the full `single_orbit` and `multi_orbit` families plus an overlapping 5-case `test` split sampled with seed `42` and an overlapping 10-case `train` split sampled with seed `163`.

To regenerate this layout, run:

```bash
uv run python benchmarks/spot5/generator.py benchmarks/spot5/splits.yaml
```

The default route reads the bundled [sources/](../sources) snapshot, one
unchanged `.spot` input per distinct published instance.
[sources/manifest.json](../sources/manifest.json) records the original Mendeley
provenance, the normalization applied, and the SHA-256 hash of each file, all
checked before generation. Canonical generation needs no network access.

To regenerate from a local directory of raw `.spot` files instead, run:

```bash
uv run python benchmarks/spot5/generator.py benchmarks/spot5/splits.yaml --source-dir /path/to/raw-spot-files
```
