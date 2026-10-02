[English](../../../../../../benchmarks/satnet/dataset/README.md) | 中文

# SatNet 数据集布局
<!-- i18n-source-sha256: d3ddb3fdf05d99a0e940656574158305e273c123da07e3c3899e7040fe04fa6b -->

规范的 SatNet 数据集按测试实例组织，每个实例对应一周/一年。

## 结构

```text
dataset/
├── README.md
├── index.json
├── mission_color_map.json
├── example_solution.json
└── cases/
    └── test/
        └── W10_2018/
            ├── problem.json
            ├── maintenance.csv
            └── metadata.json
```

## 规范测试实例

每个测试实例目录包含验证一个 SatNet 实例所需的全部内容：

- `problem.json`：恰好对应一个 `(week, year)` 实例的请求列表
- `maintenance.csv`：已按同一实例筛选的维护窗口
- `metadata.json`：每个测试实例的轻量摘要元数据

共享的、对验证器并不关键的 benchmark 元数据保留在数据集层级：

- `index.json`：数据集清单和数据集级数据溯源
- `example_solution.json`：数据集层级的一个可运行解（schema 与真实提交相同），供验证器冒烟测试使用；它不是基线
- `mission_color_map.json`：沿用上游 SatNet 发布版的任务显示元数据

## 数据溯源

规范测试实例由 [sources/satnet.json](../../../../../../benchmarks/satnet/sources/satnet.json) 中的内置快照生成，该快照汇集了已发布的上游 SatNet 数据：

- 仓库：`https://github.com/edwinytgoh/satnet`
- 源文件：`data/problems.json`、`data/maintenance.csv`、
  `data/mission_color_map.json`

[sources/manifest.json](../../../../../../benchmarks/satnet/sources/manifest.json) 记录了所应用的归一化处理、作为数据溯源而非实时下载选择依据的历史上游 ref，以及生成前校验的 SHA-256 哈希。标准生成流程读取该快照，无需网络访问。

随仓库提交的子集划分记录在 [splits.yaml](../../../../../../benchmarks/satnet/splits.yaml) 中，目前将全部五个已发布测试实例放入 `test` 子集，并把 `dataset/example_solution.json` 与 `test/W10_2018` 配对。

使用 [generator.py](../../../../../../benchmarks/satnet/generator.py) 可从内置快照重新生成这一布局：

```bash
uv run python benchmarks/satnet/generator.py benchmarks/satnet/splits.yaml
```

若改为从上游 `data/` 目录的本地副本重新生成，请加上 `--source-dir /path/to/upstream-data`。这条路径会跳过内置快照及其哈希校验，因此它只是维护用的输入，而非标准生成路径。
