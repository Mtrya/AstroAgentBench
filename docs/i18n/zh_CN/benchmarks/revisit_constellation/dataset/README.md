[English](../../../../../../benchmarks/revisit_constellation/dataset/README.md) | 中文

# 重访星座数据集
<!-- i18n-source-sha256: 797896e5e99d81e1e42b18dc35cc0d65441aac2da24a07a8df56af864b0af178 -->

本目录包含 `revisit_constellation` benchmark 已提交的规范数据集。

## 布局

- `index.json`
- `example_solution.json`
- `cases/<split>/<case_id>/assets.json`
- `cases/<split>/<case_id>/mission.json`

每个测试实例目录仅包含验证器使用的两个规范的机器可读文件。`index.json` 记录带数据子集信息的测试实例路径，并给出 `example_smoke_case`，用于把 `example_solution.json` 与某个已提交的测试实例配对。`example_solution.json` 是单个最小可运行解（与真实提交的 schema 相同），供验证器冒烟测试使用；这些文件不是基线。

已提交的子集划分策略由本 benchmark 自己规定：

- `cases/train/case_0001` 到 `cases/train/case_0010` 是公开的开发用测试实例。
- `cases/test/case_0001` 到 `cases/test/case_0005` 是留出用于评测的测试实例。

train 和 test 测试实例由互不相交的子集种子与目标选取偏移量生成，这些参数在 [splits.yaml](../../../../../../benchmarks/revisit_constellation/splits.yaml) 中声明。目标选取以对数尺度的城市人口作为主要采样信号，以地理分布作为次要平衡项，两个子集共用同一策略。

## 规范生成

重建该数据集应使用以下命令：

```bash
uv run python -m benchmarks.revisit_constellation.generator.run \
  benchmarks/revisit_constellation/splits.yaml
```

数据集生成器默认将内置的 world-cities 快照（`../sources/world_cities.csv`，由有文档说明的 Kaggle 数据集第 8 版规范化得到）暂存到 `dataset/source_data/` 下，随后在无网络访问的情况下重建规范测试实例。已提交的数据集结构契约记录在 [splits.yaml](../../../../../../benchmarks/revisit_constellation/splits.yaml) 中；`--download-dir` 这类暂存操作控制项仍属于 CLI 选项。

源数据集：

- 世界城市：`juanmah/world-cities` 第 8 版（内置为 `../sources/world_cities.csv`）
