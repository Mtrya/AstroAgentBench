[English](../../../../../../solvers/stereo_imaging/cp_local_search_stereo_insertion/README.md) | 中文

# CP/局部搜索立体插入求解器
<!-- i18n-source-sha256: a2123cc4d46ac9e5c8ff87a3a7a1c978c747306396476217ec945a3e2f766806 -->

本求解器是 `stereo_imaging` 的可运行复现求解器。

它遵循 Lemaître 等人在《Selecting and Scheduling Observations of Agile Satellites》中描述的方法族，并针对 benchmark 公开的测试实例与解契约做了适配。Vasquez 与 Hao 的禁忌搜索思想影响了可选的修复/多样化阶段，但本求解器的核心仍是 Lemaitre 的 CP/局部搜索方法。

## 引用

```bibtex
@article{lemaitre2002selecting,
  title = {Selecting and Scheduling Observations of Agile Satellites},
  author = {Lema{\^i}tre, Michel and Verfaillie, G{\'e}rard and Jouhaud, Frank and Lachiver, Jean-Michel and Bataille, Nicolas},
  journal = {Aerospace Science and Technology},
  volume = {6},
  number = {5},
  pages = {367--381},
  year = {2002},
  doi = {10.1016/S1270-9638(02)01173-2}
}
```

修复与多样化思路的相关参考文献：

```bibtex
@article{vasquez2001logic,
  title = {A Logic-Constrained Knapsack Formulation and a Tabu Algorithm for the Daily Photograph Scheduling of an Earth Observation Satellite},
  author = {Vasquez, Michel and Hao, Jin-Kao},
  journal = {Computational Optimization and Applications},
  volume = {20},
  number = {2},
  pages = {137--157},
  year = {2001},
  doi = {10.1023/A:1012300271919}
}
```

本求解器独立自洽。它读取 benchmark 的测试实例文件，写出 benchmark 解 JSON，但不导入或执行 benchmark、experiment、运行时基座或其他求解器的内部实现。

## 方法概述

Lemaître 等人维护每颗卫星各自的可行成像序列，推算各观测最早/最晚的可行位置，并通过插入/移除动作把立体观测当作耦合产品来处理。

本复现保留了这一结构，并将其适配到 `stereo_imaging`：

1. **候选生成**——针对每个卫星–目标组合，发现可见区间，并采样满足几何、太阳高度角、侧摆角和视轴约束的候选观测窗口。
2. **产品库**——从满足交会角、重叠率、像素尺度比与近天底锚点约束的候选中，枚举可行的双立体与三立体成像产品。
3. **贪心种子解**——基于按目标索引的排序产品队列，构造确定性的覆盖优先种子解，避免反复扫描整个产品池。产品以原子方式插入各卫星的序列，三立体成像升级阶段还会在合适的位置尝试换成更高质量的产品。
4. **局部搜索**——通过产品级动作改进种子解：为尚未覆盖的目标插入产品；用更高质量的产品替换已覆盖目标的产品；移除低质量产品，为更优选择腾出容量；以及交换、先移除再修复之类的兜底动作。所有动作都是原子的，失败时回滚。带随机种子的多轮运行配置会确定性地扰动动作顺序，而候选与产品库只构建一次，各轮复用。
5. **修复**——扫描各卫星序列中的重叠与间隙违规，移除价值最低的冲突产品。这一步是保守的防御性措施（受 Vasquez 启发），并非 Lemaitre 方法的核心。

## Benchmark 适配

benchmark 与论文存在若干重要差异：

- **以点状 AOI 产品取代条带。** benchmark 使用固定的候选观测窗口（而非连续时间窗口），所以求解器在可见区间内采样离散的起始时刻，而不去优化窗口边界。
- **三立体成像扩展。** benchmark 增加了三立体成像产品（三次近乎同时的观测）。求解器将其视为三次观测的耦合产品，采用与立体对相同的原子插入/回滚逻辑。
- **采用 benchmark 原生的立体可行性判据。** 交会角、重叠率、像素尺度比与近天底锚点约束完全按 benchmark 验证器求值，而不是套用论文中简化的立体模型。
- **覆盖优先的字典序目标函数。** benchmark 按 `valid > coverage_ratio > normalized_quality` 排序。求解器先优化覆盖，再优化质量，而不是采用论文的线性/非线性加权和。
- **确定性评测。** 仓库要求运行可复现，本求解器改用确定性的平局裁决规则与带种子的随机扰动（经由 `num_runs` 运行框架），而不是无界的随机化运行方式。
- **不涉及存储、能量、天气或下行链路约束。** benchmark 未包含这些内容，求解器也不对其建模。

因此，本求解器在复现论文 CP/局部搜索方法的同时，仍严格遵循 benchmark 公开的合法性契约。

## 求解器契约

```bash
./setup.sh
./solve.sh <case_dir> [config_dir] [solution_dir]
```

在使用项目环境时，`setup.sh` 实际上等同于空操作。

`solve.sh` 会写出：

- `solution.json`：主要 benchmark 解，其中 `actions` 数组由 `observation` 动作组成
- `status.json`：求解器摘要；按构建/种子/搜索/修复各阶段拆分的耗时；候选与产品库详情；运行策略元数据；以及 `num_runs > 1` 时的多轮汇总统计
- `debug/*`：可选的调试产物，仅在 `debug: true` 时写出

主要解产物是一个 JSON 对象，顶层是 `actions` 数组，由 `observation` 动作组成。

## 搜索与修复

求解流程如下：

1. 加载 `mission.yaml`、`satellites.yaml` 和 `targets.yaml`。
2. 针对每个卫星–目标组合生成候选观测窗口，并按可见几何过滤。
3. 构建由可行双立体与三立体成像产品组成的产品库。
4. 构造确定性的覆盖优先贪心种子解，并执行三立体成像升级。
5. 在限定预算内运行局部搜索，使用插入/替换/移除/交换动作。
6. 执行保守修复，清除序列中残留的冲突。

修复阶段有意保持保守。它使求解器维持独立自洽，并减少官方验证器判定的失败，但并不声称求解器内部的序列模型在所有边界情形下都严格精确。

## 配置

求解器从以下任一位置读取可选配置：

- `<config_dir>/config.yaml`
- `<config_dir>/config.yml`
- `<config_dir>/config.json`
- `<config_dir>/cp_local_search_stereo_insertion.yaml`
- `<config_dir>/cp_local_search_stereo_insertion.yml`
- `<config_dir>/cp_local_search_stereo_insertion.json`

带注释的示例参见 [config.example.yaml](../../../../../../solvers/stereo_imaging/cp_local_search_stereo_insertion/config.example.yaml)。

关键可调项：

- `observation_duration_s`——固定的观测窗口时长
- `candidate_stride_s`——可见区间内的采样步长
- `access_discovery_step_s`——发现可见区间所用的粗步长
- `max_candidates_per_target_per_sat`——每个目标的候选数上限（默认：无上限）
- `seed_only`——直接输出种子解，跳过局部搜索
- `tri_stereo_seed_phase`——在立体对种子解之后启用三立体成像升级
- `pair_weight` / `tri_weight`——种子解排序所用的权重乘子
- `run_profile`——取值为 `smoke`、`benchmark` 或 `profile`
- `max_passes` / `max_moves_per_pass` / `max_time_seconds`——局部搜索预算
- `remove_move_enabled`——启用专门的“先移除再重新插入”动作
- `num_runs`——覆盖运行配置中独立确定性扰动运行的次数
- `random_seed`——多轮随机化所用的基础随机种子
- `parallel_workers`——跨卫星并行生成候选（`null` 表示自动，`0` 表示禁用）
- `debug`——写出详细的调试产物

`num_runs` 会用不同的确定性 RNG 扰动多次运行种子解生成 + 局部搜索 + 修复，并保留最优结果。候选生成与产品构建只执行一次，各轮运行复用。最优/均值/最小值汇总统计与各轮耗时详情写入 `status.json`。

## 运行配置

求解器提供三种显式的运行配置：

| 配置 | 默认运行轮数 | 每轮局部搜索预算 | 适用场景 |
|---|---:|---:|---|
| `smoke` | 1 | 30 s | 确定性验证与面向 CI 的回放 |
| `benchmark` | 5 | 120 s | 以多轮最优/均值指标提供公平的公开证据 |
| `profile` | 10 | 120 s | 更长时间的诊断性剖析 |

默认配置为 `smoke`，以保证单轮行为确定、易于复现。若要产出 benchmark 证据，请使用包含以下内容的配置目录：

```yaml
run_profile: benchmark
```

`benchmark` 配置并非论文中严格 100 次执行的 quality profile，而是针对 benchmark 适配的确定性多轮折中方案。它在保持可复现性的同时，如实报告最优与均值结果。

## 调试产物

当 `debug: true` 时，求解器会写出：

- `debug/candidate_summary.json`
- `debug/product_summary.json`
- `debug/seed_log.json`
- `debug/local_search_log.json`
- `debug/repair_log.json`

这些文件有助于回答以下问题：

- 某个目标为何没有任何候选或产品
- 种子解构建期间哪些产品被接受或拒绝，原因是什么
- 尝试并接受了哪些局部搜索动作
- 修复是否因序列冲突移除了产品
- 各阶段的运行时间构成

## 运行方式

直接安装：

```bash
./solvers/stereo_imaging/cp_local_search_stereo_insertion/setup.sh
```

在公开冒烟测试实例上直接求解：

```bash
./solvers/stereo_imaging/cp_local_search_stereo_insertion/solve.sh \
  benchmarks/stereo_imaging/dataset/cases/test/case_0001
```

指定配置目录直接求解：

```bash
./solvers/stereo_imaging/cp_local_search_stereo_insertion/solve.sh \
  benchmarks/stereo_imaging/dataset/cases/test/case_0001 \
  /path/to/config_dir \
  /tmp/stereo_cp_solution
```

官方评测与汇总请使用 [Harbor 求解器工作流](../../../experiments/evaluate/README.md)。

求解器本地测试：

```bash
./solvers/stereo_imaging/cp_local_search_stereo_insertion/test.sh
```

官方评测与汇总请使用 [Harbor 求解器工作流](../../../experiments/evaluate/README.md)。

## 合理性基线

论文报告的是调度成像数量与 quality profile，而不是 benchmark 的 `coverage_ratio` 或 `normalized_quality`。论文中的 profile 只能作为对完成情况的粗略合理性检查，不能当作本 benchmark 的目标指标表。

这里真正重要的是：

- 官方验证通过（`valid=true`、零违规）
- 候选与产品数量合理
- 修复不会让调度表崩塌
- 覆盖与质量在公开测试实例上保持较高水平
- 种子解构建在公开测试实例的规模下不是二次复杂度
- `status.json` 能把构建耗时与搜索耗时区分开

如果种子解看起来已经很好，而局部搜索几乎找不到改进动作，可以检查动作日志，确认插入/替换/移除动作确实被尝试过。目前公开测试实例中，若干实例上出现了幅度不大但确实存在的局部搜索改进；剩余计时的主要开销来自产品构建而非搜索。

## 验证

在重新设计的 benchmark 上，5 个公开测试实例全部通过 benchmark 验证器。以下 `smoke` 配置的耗时于 2026-04-25 在共享开发环境中测得，使用默认配置（`run_profile: smoke`、`num_runs: 1`、`parallel_workers: null`），输出位于 `/tmp/cp_phase7_public`。

| 测试实例 | 合法 | 候选数 | 产品数 | 最终覆盖数 | 覆盖率 | 归一化质量 | LS 接受数 | 种子解 s | 局部搜索 s | 总计 s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| test/case_0001 | true | 7,815 | 32,570 | 142 | 0.979 | 0.958 | 1 | 0.107 | 0.813 | 47.7 |
| test/case_0002 | true | 7,611 | 33,677 | 121 | 0.992 | 0.989 | 1 | 0.104 | 0.646 | 49.7 |
| test/case_0003 | true | 6,687 | 27,959 | 118 | 0.959 | 0.957 | 5 | 0.113 | 1.180 | 65.0 |
| test/case_0004 | true | 5,871 | 21,857 | 124 | 0.944 | 0.924 | 3 | 0.170 | 1.309 | 42.3 |
| test/case_0005 | true | 7,583 | 42,434 | 139 | 0.979 | 0.975 | 7 | 0.127 | 2.038 | 220.9 |

在 `test/case_0001` 上以 `run_profile: benchmark` 运行得到的 benchmark 配置证据为（`num_runs: 5`，构建结果只生成一次并在各轮复用）：一个合法解，内部覆盖/质量最优值 `142 / 141.808042`，内部覆盖/质量均值 `142.0 / 141.620498`，验证器给出的覆盖率 `0.971831`，验证器归一化质量 `0.960582`，总运行时间 `52.2 s`，局部搜索总耗时 `4.34 s`。

**确定性：** 在 `test/case_0001` 上重复执行 `smoke` 运行，两次得到的 `solution.json` 逐字节一致。

**修复：** 在所有公开 `smoke` 测试实例上，保守修复阶段移除的产品数都是 `0`。

**三立体成像：** 三立体成像产品与立体对走同一条产品级原子序列路径生成并编排。公开 `smoke` 运行中，每个测试实例的产品库里都保留着数千个可行的三立体成像产品。

## 已知局限

- 本求解器复现的是论文的方法族，并不声称能复现论文中的每一项运行时间或每一张表格。
- 贪心种子解算法是为本实现设计的、基于产品池的覆盖优先启发式方法，而非 Lemaitre 第 3.1 节所述的顺序式 track-builder。
- 局部搜索确实能改进若干公开测试实例，但与论文中的自适应随机插入/移除流程相比，当前的邻域动作仍较为有限。
- 求解器未实现论文中的自适应接受概率 `p_a`，也未实现完整的随机化运行机制。
- 候选生成可按卫星并行；产品构建、种子解生成与局部搜索仍是单进程 Python。
- 目前产品构建已成为剩余的主要运行时瓶颈，在 `test/case_0005` 上尤为明显。运行策略会显式报告这一点；本求解器忠实于 benchmark 且可复现，但并不声称具备有竞争力的优化性能。
- 求解器内部的产品判定条件按验证器的几何定义设计，但受浮点运算顺序影响，仍可能出现细微偏差。
