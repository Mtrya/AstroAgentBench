[English](../../../../../../benchmarks/spot5/dataset/README.md) | 中文

# SPOT-5 数据集布局
<!-- i18n-source-sha256: a08e05d63c7a18f2e294a2826bd25eff9e49ff590c136c3438f2ef7c377ed9d9 -->

规范 SPOT-5 数据集以测试实例为单位存放在 `cases/` 下。

每个测试实例目录中恰好包含一个原始实例文件：

```text
dataset/
├── index.json
├── example_solution.json
└── cases/
    └── <split>/
        └── <case_id>/
            └── <case_id>.spot
```

示例：

- `cases/single_orbit/8/8.spot`
- `cases/multi_orbit/1502/1502.spot`
- `cases/test/1021/1021.spot`

`index.json` 记录 benchmark 名称、上游来源、已发布的按子集划分的测试实例列表，以及 `example_smoke_case`，后者用于在 CI 中把示例解与某个测试实例配对（参见 `docs/benchmark_contract.md`）。

`example_solution.json` 是一份可运行的解（schema 与真实提交的解相同），用于验证器冒烟测试。它不是基线。

提交到仓库的子集划分记录在 [splits.yaml](../../../../../../benchmarks/spot5/splits.yaml) 中。它完整定义了 `single_orbit` 和 `multi_orbit` 两个实例族，另有两个存在重叠的子集：以种子 `42` 抽样、含 5 个测试实例的 `test` 子集，以及以种子 `163` 抽样、含 10 个测试实例的 `train` 子集。

要重新生成该布局，请运行：

```bash
uv run python benchmarks/spot5/generator.py benchmarks/spot5/splits.yaml
```

默认路径读取内置的 [sources/](../../../../../../benchmarks/spot5/sources) 快照，每个已发布实例各对应一个未经改动的 `.spot` 输入文件。[sources/manifest.json](../../../../../../benchmarks/spot5/sources/manifest.json) 记录原始的 Mendeley 数据溯源、所做的规范化处理，以及每个文件的 SHA-256 哈希，以上信息在生成前会全部校验。标准生成路径无需网络访问。

如果改用本地 `.spot` 原始文件目录重新生成，请运行：

```bash
uv run python benchmarks/spot5/generator.py benchmarks/spot5/splits.yaml --source-dir /path/to/raw-spot-files
```
