[English](../../../../../benchmarks/spot5/README.md) | 中文

# SPOT-5 卫星拍摄调度 Benchmark
<!-- i18n-source-sha256: 09f14fff70cd4cb72d007190790da50ae713b32eed0282020743fdc1f5019b0b -->

这是地球观测卫星调度领域的一个经典约束优化问题，源头是 ROADEF 2003 挑战赛以及法国航天局（CNES）的日常运行。

## 问题概述

SPOT-5 卫星（2002–2015 年在轨运行）搭载三台成像仪器：两台 HRG（高分辨率几何）相机和一台 HRS（高分辨率立体）相机。每日调度问题要求在满足以下约束的同时选择照片，以最大化总利润：

- **相机约束**：单幅图像使用一台相机（HRG 前、中或后）；立体图像需要前后两台 HRG 相机同时工作
- **非重叠约束**：受镜面姿态机动时间限制，两张照片不能相互冲突
- **数据流约束**：瞬时遥测带宽限制会禁止某些组合
- **存储容量约束**：星载记录容量限制所选图像的总数（仅多轨道实例）

这可以归结为一个带有复杂逻辑约束的析取约束背包问题（DCKP）。

## 历史背景与来源

| 年份 | 事件 |
|------|-------|
| 2002 | CNES 发射 SPOT-5 卫星 |
| 2003 | ROADEF 2003 挑战赛发布原始遥测数据（多文件格式，含轨道参数） |
| 2001–2003 | Vasquez 与 Hao 将物理约束抽象为冲突图（VCSP 形式化） |
| 2021 | Wei 与 Hao 进一步简化，并在 Mendeley Data 上以 DCKP 格式发布了 21 个 benchmark 实例 |

当前数据集（即 `.spot` 文件）是托管在 [Mendeley Data](https://data.mendeley.com/datasets/2kbzg9nw3b/1) 上的 DCKP 抽象，采用 **CC BY 4.0** 许可。之所以能采用这一宽松许可，是因为抽象过程生成了一个与 CNES 专有原始遥测数据相分离的派生数据集。

在本仓库中，每个已发布实例都作为独立的 benchmark 测试实例存放：

```text
benchmarks/spot5/dataset/cases/<split>/<case_id>/<case_id>.spot
```

## 实例文件格式（.spot）

### 整体结构

```
<total_variables>
<variable_spec_lines...>
<total_constraints>
<constraint_spec_lines...>
[<capacity>]  # Optional, only for multi-orbit instances
```

### 变量规格

每个变量代表一个拍照请求：

```
<var_id> <profit> <domain_size> {<value_id> <recorder_consumption>}* <domain_size> [extra_fields...]
```

- **var_id**：变量标识符（从 0 开始索引）
- **profit**：选中该变量后获得的权重/利润（待最大化的目标）
- **domain_size**：可能的相机分配数量（SPOT-5 始终为 3）
- **value_id**、**recorder_consumption**：定义允许取值的配对
  - 取值 `1`：HRG 前相机
  - 取值 `2`：HRG 中相机
  - 取值 `3`：HRG 后相机
  - 取值 `13`：HRG 前 + 后相机
- **extra_fields**：含义不明，忽略

14 个单轨道实例：所有 `recorder_consumption = 0`
7 个多轨道实例：`recorder_consumption` 表示内存占用量

示例：

1. 单轨道，domain_size = 3

```11.spot, line 3
1 1 3 1 0 2 0 3 0
```

1 -> var_id（第二个变量）
1 -> profit（选中后获得 1 点利润）
3 -> domain_size：3 种可能的相机分配（即 1、2、3）
1 0 -> value_id 1, recorder_consumption 0
2 0 -> value_id 2, recorder_consumption 0
3 0 -> value_id 3, recorder_consumption 0

2. 多轨道，domain_size = 3

```1504.spot, line 40
38 2 3 1 451.1500000000069 2 451.1500000000069 3 451.1500000000069 213302 1
```

38 -> var_id（第 39 个变量）
2 -> profit（选中后获得 2 点利润）
3 -> domain_size：3 种可能的相机分配（即 1、2、3）
1 451.1500000000069 -> value_id 1, recorder_consumption 451.1500000000069
2 451.1500000000069 -> value_id 2, recorder_consumption 451.1500000000069
3 451.1500000000069 -> value_id 3, recorder_consumption 451.1500000000069
213302 1 -> extra_field, 忽略

3. 多轨道，domain_size = 1

```1506.spot, line 127
125 2000 1 13 1804.5999999999822 136703 1
```

125 -> var_id（第 126 个变量）
2000 -> profit（选中后获得两千点利润）
1 -> domain_size：1 种可能的相机分配（即 13）
13 1804.5999999999822 -> value_id 13, recorder_consumption 1804.5999999999822
136703 1 -> extra_field, 忽略

### 约束规格

```
<arity> <var_id_1> ... <var_id_arity> {<forbidden_tuple>}*
```

- **arity**：变量数量（2 表示二元，3 表示三元）
- **var_id_***：该约束涉及的变量
- **forbidden_tuple**：禁止的取值组合（以空格分隔）

**二元约束**编码析取冲突：两张照片不能同时被选中。禁止元组是一对取值（例如 `1 1 2 2 3 3` 表示"不能同时使用相机 1、不能同时使用相机 2、不能同时使用相机 3"）。

**三元约束**编码数据流限制或复杂的干扰模式。禁止元组是三个取值的组合。

示例：

1. 二元

```11.spot, line 370
2 242 240 13 3 13 1
```

2 -> arity（二元）
242 -> var_id_1
240 -> var_id_2
13 3 -> forbidden_tuple 1
13 1 -> forbidden_tuple 2

禁止把取值 13 分配给变量 242 **且**同时把取值 3 分配给变量 240；也禁止把取值 13 分配给变量 242 **且**同时把取值 1 分配给变量 240。

2. 三元

```11.spot, line 369
3 124 81 72 13 2 13
```

3 -> arity（三元）
124 -> var_id_1
81 -> var_id_2
72 -> var_id_3
13 2 13 -> forbidden_tuple 1

禁止把取值 13 分配给变量 124 **且**同时把取值 2 分配给变量 81 **且**同时把取值 13 分配给变量 72。


### 容量行（仅多轨道）

对于实例 `1401, 1403, 1405, 1502, 1504, 1506, 1021`，文件以一个数字结尾，该数字表示存储容量约束。**注意**：验证器会忽略文件中的这个数字，真实容量始终为 **200**。

## 解文件格式（.spot_sol.txt）

```
profit = <P>, weight = <W>
number of candidate photographs = <N>
number of selected photographs = <S>
<assignment_0>
<assignment_1>
...
<assignment_n-1>
```

- **P**：总利润（所选照片的权重之和）
- **W**：内存总占用量（仅多轨道实例，参见权重计算）
- **N**：候选照片（变量）的总数
- **S**：所选照片数量（assignment ≠ 0）
- **assignments**：每个变量一个，取值来自 `{0, 1, 2, 3, 13}`

## 约束类型验证

只要满足全部约束，解就是合法的：

### 二元约束
对于每个带禁止元组 `F` 的二元约束 `C(i, j)`：
- 若 `assignment[i] ≠ 0` **且** `assignment[j] ≠ 0`，则配对 `(assignment[i], assignment[j])` **不得**出现在 `F` 中
- 若其中任一为 0，则该约束满足

### 三元约束
对于每个带禁止元组 `F` 的三元约束 `C(i, j, k)`：
- 若三个 assignment 均 ≠ 0，则该三元组 **不得**出现在 `F` 中
- 若其中任一为 0，则该约束满足

### 存储容量约束（仅多轨道）
```
total_weight ≤ 200
```

其中 `total_weight` 按下文的权重计算方式得出。

## 得分计算

### 利润
```python
profit = sum(variables[i].profit for i in range(n) if assignment[i] != 0)
```

### 权重（内存占用）

**单轨道实例**（8, 54, 404, 408, 412, 5, 11, 28, 29, 42, 503, 505, 507, 509）：
- 所有内存占用量均为 0
- `weight = 0`

**多轨道实例**（1401, 1403, 1405, 1502, 1504, 1506, 1021）：

对于每个带域值的变量，原始的 `recorder_consumption` 需要归一化：
```python
# Example from 1021.spot line:
# 0 1000 1 2 451.1500000000069 42510 1
# Value 1 has recorder_consumption = 451.1500000000069

# Build a dict mapping each value_id to its normalized weight
weight_per_value = {
    value_id: round(recorder_consumption / 451)
    for value_id, recorder_consumption in variable.domain_items
}

total_weight = sum(
    weight_per_value[assignment[i]]
    for i in range(n) if assignment[i] != 0
)
```

约束：`total_weight ≤ 200`

## 实例分类

### 合计 21 个实例

| 类别 | 实例 | 变量数 | 约束数 | 容量 |
|----------|-----------|-----------|-------------|----------|
| 小型（单轨道） | 8, 54, 404, 408, 412 | 8–78 | 7–52 | 0 |
| 中型（单轨道） | 5, 11, 28, 29, 42 | 306–309 | 4308–6273 | 0 |
| 大型（单轨道） | 503, 505, 507, 509 | 315 | 3983–8122 | 0 |
| 多轨道 | 1401, 1403, 1405, 1502, 1504, 1506 | 163–855 | 可变 | 200 |
| 多轨道（最大） | 1021 | 1,057 | 20,730 | 200 |

**14 个实例无存储约束**（capacity = 0）
**7 个实例有存储约束**（capacity = 200）

## 已提交子集

已完成 benchmark 在
`benchmarks/spot5/splits.yaml` 中保留了四个已提交子集：

- `single_orbit`：所有数字 ID `< 1000` 的已发布实例
- `multi_orbit`：所有数字 ID `> 1000` 的已发布实例
- `test`：以种子 `42` 抽取的 5 个测试实例，与上述子集重叠
- `train`：以种子 `163` 抽取的 10 个测试实例，与上述子集重叠

重叠是有意为之。例如，测试实例 `8` 同时出现在
`single_orbit`、`test` 和 `train` 中。数据集级冒烟示例与
`single_orbit/8` 配对。

## 已知解与验证

参考解位于 `tests/fixtures/spot5_val_sol/`，取自 [DCKP_RSOA 仓库](https://github.com/Zequn-Wei/DCKP_RSOA)。

验证结果（使用 `verifier.py`）：

- **14 个解**：声称的利润/权重与计算得到的利润/权重完全一致
- **7 个解**：分配合法，但头部报告值存在细微差异

**头部不匹配**（分配本身是正确的）：

| 实例 | 声称利润 | 计算利润 | 差异 | 权重状态 |
|----------|----------------|-----------------|------|---------------|
| 11       | 22,117         | 22,119          | +2   | ✓ (0) |
| 408      | 3,078          | 3,080           | +2   | ✓ (0) |
| 509      | 19,115         | 19,117          | +2   | ✓ (0) |
| 1403     | 172,141        | 172,143         | +2   | ✓ (0) |
| 1506     | 164,239        | 164,241         | +2   | ✓ (0) |
| 1021     | 169,240        | 169,243         | +3   | 声称 200，实际 198 |
| 1405     | 170,175        | 170,179         | +4   | 声称 200，实际 198 |

验证器把这些测试实例判为**合法解**；差异似乎出在 DCKP-RSOA 算法对利润/权重的上报逻辑上，而非解的质量本身。

## 验证器使用

```bash
# Verify a .spot_sol.txt solution
uv run python benchmarks/spot5/verifier.py \
    benchmarks/spot5/dataset/cases/single_orbit/8 \
    tests/fixtures/spot5_val_sol/8.spot_sol.txt

# Verify a JSON solution (same schema as example_solution.json)
uv run python benchmarks/spot5/verifier.py \
    benchmarks/spot5/dataset/cases/single_orbit/8 \
    benchmarks/spot5/dataset/example_solution.json
```

验证器会检查：
1. 所有 assignment 都取自有效域
2. 所有二元约束都被满足
3. 所有三元约束都被满足
4. 存储容量约束被满足（在适用的情况下）
5. 利润与权重的计算结果与 assignment 一致（头部声称值不匹配时只告警，不判为非法解）
6. 选中数量与头部一致

## 文件位置

- **测试实例目录**：`benchmarks/spot5/dataset/cases/<split>/<case_id>/`
- **实例文件**：`benchmarks/spot5/dataset/cases/<split>/<case_id>/<case_id>.spot`
- **数据集清单**：`benchmarks/spot5/dataset/index.json`
- **数据集级参考**：`benchmarks/spot5/dataset/*.md`（额外纳入版本管理的参考文献文件）
- **解文件**：`tests/fixtures/spot5_val_sol/*.spot_sol.txt`
- **验证器**：`benchmarks/spot5/verifier.py`
- **生成器**：`uv run python benchmarks/spot5/generator.py benchmarks/spot5/splits.yaml`

随仓库分发的 `sources/` 目录为每个不同的已发布实例保留一份未经修改的 `.spot` 输入，并对重叠子集做了去重。其清单记录了原始数据溯源信息以及每个文件的 SHA-256 哈希，生成前会逐一校验。标准重新生成流程不需要访问网络。维护场景下仍可显式使用 `--source-dir` 和 `--zip-path` 导入，它们各自带有独立的数据溯源信息。

## 许可与归属

**数据许可**：CC BY 4.0（知识共享署名 4.0 国际）
**来源**：Mendeley Data，DOI: 10.17632/2kbzg9nw3b.1
**归属**：
- 原始问题：CNES（法国航天局）与 ONERA
- 问题抽象：Vasquez 与 Hao（2001），Wei 与 Hao（2021）
- 参考解：DCKP-RSOA 算法（Wei 与 Hao，2021）

**商业使用**：CC BY 4.0 允许商业使用。数据集并非病毒式许可；Mendeley Data 上的发布属于宽松许可，这一点不同于采用 GPL 的参考解程序。

## 参考文献

1. Bensana E, Lemaitre M, Verfaillie G. "Earth observation satellite management." Constraints, 1999.
2. Verfaillie G, Lemaitre M, Schiex T. "Russian Doll Search for Solving Constraint Optimization Problems." AAAI-96, 1996.
3. Agnès J-C, Bataille N, Blumstein D, et al. "Exact and Approximate Methods for the Daily Management of an Earth Observation Satellite." ESA Workshop 1995.
4. Vasquez M, Hao JK. "A Logic-Constrained Knapsack Formulation and a Tabu Search Algorithm for the Daily Photograph Scheduling of an Earth Observation Satellite." 2001.
5. Wei Z, Hao JK. "A Threshold Search Based Memetic Algorithm for the Disjunctively Constrained Knapsack Problem." Applied Soft Computing, 2021.
