[English](../../../../../../solvers/aeossp_standard/mwis_conflict_graph/README.md) | 中文

# AEOSSP MWIS 冲突图求解器
<!-- i18n-source-sha256: bc1f2c4267bedde0004691686bbb75e64c587942ac6eac95f816495389eb145d -->

本求解器是 `aeossp_standard` 的可运行复现求解器。

它采用 Duncan Eddy 与 Mykel J. Kochenderfer 在《A Maximum Independent Set Method for Scheduling Earth Observing Satellite Constellations》中描述的方法族，并针对 benchmark 公开的测试实例与解契约做了适配。

## 引用

```bibtex
@article{eddy2021maximum,
  title={A maximum independent set method for scheduling earth-observing satellite constellations},
  author={Eddy, Duncan and Kochenderfer, Mykel J},
  journal={Journal of Spacecraft and Rockets},
  volume={58},
  number={5},
  pages={1416--1429},
  year={2021},
  publisher={American Institute of Aeronautics and Astronautics}
}
```

求解器独立自洽。它读取 benchmark 的测试实例文件并写出 benchmark 解 JSON，但不会导入或执行 benchmark、experiment、运行时基座或其他求解器的内部实现。

## 方法概述

论文将候选成像采集建模为稀疏不可行图中的顶点：

- 每个顶点是一次候选观测
- 每条边表示两次观测不能同时出现在调度表中
- 一个调度表就是一个由互不相邻顶点构成的独立集

本复现保留这一结构，并将其适配到 `aeossp_standard`：

- 顶点：一个与网格对齐的 `(satellite_id, task_id, start_time, end_time)` 观测候选
- 顶点权重：成像任务权重
- 重复成像任务边：任意一对 `task_id` 相同的候选，包括跨卫星的候选
- 同卫星重叠边：两次观测在时间上重叠
- 同卫星转换边：后一次观测在前一次之后没有留下足够的姿态机动加稳定时间

在分量搜索之前，求解器会执行一轮小规模的确定性加权 MWIS 归约，处理孤立顶点和严格加权支配。对于归约后的小分量，求解器用确定性的位掩码动态规划精确搜索。对于归约后的大分量，求解器构造确定性的贪心种子，用有界局部搜索加以改进，再以有界重组精化表现最好的若干当前最优解。

## benchmark 适配

该 benchmark 与论文相比有几处重要差异：

- benchmark 的排序先看解是否合法，再依次看 `WCR`、`CR`、`TAT` 和 `PC`，因此求解器使用加权选择，而不是单纯按采集数量选择。
- 观测动作必须与公开动作网格严格对齐，且时长必须与每个成像任务的精确时长一致。
- 姿态机动可行性采用 benchmark 的标量加速-滑行-减速（bang-coast-bang）加稳定语义，而不是论文中更简单的恒速率模型。
- 电池约束本质上不是两两成对的，因此没有编码为图的边。求解器改为在图选择之后执行求解器内部验证和有界修复。

这意味着该求解器复现了论文的图与搜索方法，同时忠于 benchmark 公开的合法性契约。

## 求解器契约

```bash
./setup.sh
./solve.sh <case_dir> [config_dir] [solution_dir]
```

使用项目环境时，`setup.sh` 实际上是空操作。

`solve.sh` 会写出：

- `solution.json`：benchmark 主解
- `status.json`：求解器摘要、耗时和内部验证详情
- `debug/*`：`debug: true` 时的可选调试产物

主解产物是一个 JSON 对象，其顶层 `actions` 数组由 `observation` 动作组成。

## 搜索与修复

求解器流水线如下：

1. 加载 `mission.yaml`、`satellites.yaml` 和 `tasks.yaml`。
2. 生成与网格对齐的观测候选，需满足传感器匹配、成像任务窗口、观测几何以及首个动作的姿态机动可行性。
3. 根据重复成像任务、重叠和转换冲突构建稀疏冲突图。
4. 求解每个连通分量：
   - 小分量上做精确搜索
   - 较大分量上做确定性贪心种子构造
   - 用插入和加权 2-交换做有界局部改进
   - 较大分量上对当前最优解做有界重组
5. 将选中的候选解码为观测动作。
6. 执行求解器内部验证和有界修复，清除残留的局部问题，尤其是电池耗尽风险。

修复阶段有意保持保守。它让求解器保持独立自洽，减少官方验证器报出的失败，但并不声称电池可行性已由冲突图本身完全证明。

## 配置

求解器可以从以下任一位置读取可选配置：

- `<config_dir>/config.yaml`
- `<config_dir>/config.yml`
- `<config_dir>/config.json`
- `<config_dir>/mwis_conflict_graph.yaml`
- `<config_dir>/mwis_conflict_graph.yml`
- `<config_dir>/mwis_conflict_graph.json`

带注释的示例见 [config.example.yaml](../../../../../../solvers/aeossp_standard/mwis_conflict_graph/config.example.yaml)。

关键可调项：

- `candidate_stride_multiplier`
- `max_candidates`
- `max_candidates_per_task`
- `candidate_workers`
- `graph_workers`
- `backend`
- `selection_policy`
- `max_exact_component_size`
- `max_local_passes`
- `population_size`
- `recombination_rounds`
- `total_time_budget_s`
- `time_limit_s`
- `max_repair_iterations`
- `enable_incremental_repair`
- `debug`

`total_time_budget_s` 是公平运行的主要运行时长控制项。候选生成和图构建在选择开始前就已计入，剩余预算会传给 MWIS 精化阶段。`time_limit_s` 作为只限制精化阶段的上限保持向后兼容；两者都设置时，以较早的截止时间为准。若预算耗尽，求解器返回目前找到的最优解，并且仍会执行内部验证和修复。

对于困难的测试实例，可在总预算内通过 `max_local_passes`、`population_size` 和 `recombination_rounds` 调整精化强度。`graph_workers` 可以启用按卫星划分的图构建 worker，同时保持边集合的确定性。`status.json` 会报告图构建的执行模型、生效的选择预算、截止时间来源、选择是否在总预算耗尽之后才开始、所选 backend、归约次数、归约耗时，以及各分量的简明停止原因。

`backend` 默认为 `internal_reduction`，即求解器内部基于归约的 Python 路径。`fallback_python` 显式选择同一套确定性的纯 Python 回退机制。`redumis` 可作为可选的 backend 请求被接受，但仓库不附带外部 ReduMIS 二进制；在安装并集成之前，求解器会报告其不可用，并回退到 `fallback_python`。

修复默认在首次全量检查之后，采用增量式的受影响卫星验证。设置 `enable_incremental_repair: false` 可强制重复全量验证，以便对比。修复状态会报告对目标函数的影响、按原因分类的移除数量、各轮验证耗时、增量与全量验证次数以及回退次数。

## 调试产物

当 `debug: true` 时，求解器会写出：

- `debug/candidate_summary.json`
- `debug/graph_summary.json`
- `debug/solver_summary.json`
- `debug/component_search.json`
- `debug/repair_log.json`
- `debug/candidates.json`
- `debug/selected_candidates.json`
- `debug/repaired_candidates.json`

这些产物有助于回答：

- 某个成像任务为何没有候选
- 冲突图有多密集
- 当前最优解来自哪条搜索路径
- 时间预算是否中止了精化
- 每个分量报告了哪个停止原因
- 在安全的 MWIS 归约下每个分量缩小了多少
- 修复消耗了多少目标函数收益和验证时间
- 某个候选为何在内部修复中被移除

## 运行方式

直接安装：

```bash
./solvers/aeossp_standard/mwis_conflict_graph/setup.sh
```

在公开冒烟测试实例上直接求解：

```bash
./solvers/aeossp_standard/mwis_conflict_graph/solve.sh \
  benchmarks/aeossp_standard/dataset/cases/test/case_0001
```

带配置目录直接求解：

```bash
./solvers/aeossp_standard/mwis_conflict_graph/solve.sh \
  benchmarks/aeossp_standard/dataset/cases/test/case_0001 \
  /path/to/config_dir \
  /tmp/aeossp_mwis_solution
```

官方评测与汇总请使用 [Harbor 求解器工作流](../../../experiments/evaluate/README.md)。

求解器内部测试：

```bash
./solvers/aeossp_standard/mwis_conflict_graph/test.sh
```

官方评测与汇总请使用 [Harbor 求解器工作流](../../../experiments/evaluate/README.md)。

## 合理性基线

论文报告的是已调度采集次数，而不是 benchmark 的 `WCR`、`CR`、`TAT` 或 `PC`。论文中的采集比例只能作为对完成情况的粗略合理性参考，而不是本 benchmark 的目标指标表。

这里真正重要的是：

- 官方验证通过
- 候选数量合理
- 修复不会导致调度表大幅缩水
- 公开测试实例上的加权完成率仍然很高

如果图的原始选择结果表现很好，但修复却移除了大量动作，应先检查本地的电池模型、转换间隔逻辑和候选生成，再调整搜索策略。

## 已知局限

- 本求解器复现的是论文的方法族，并不声称能复现论文中的每一项运行时间或每一张表格。
- 求解器实现了内部基于归约的 backend 接口，但未附带外部 ReduMIS backend。
- 电池可行性交由求解器内部验证和修复处理，而不是完整编码为图冲突。
- 在服务器上做多测试实例的整体调参，可能比在开发用笔记本上更实际。
