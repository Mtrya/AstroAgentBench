[English](../../../../../../solvers/aeossp_standard/greedy_lns/README.md) | 中文

# AEOSSP 贪心-LNS 求解器
<!-- i18n-source-sha256: 37c9a75949383c31e7531a6f0c7d45f484f4e8552333c4dc64fd3ad70058df84 -->

本求解器是 `aeossp_standard` 的可运行复现求解器。

它采用 Vincent Antuori、Damien Wojtowicz 和 Emmanuel Hebrard 在《Solving the Agile Earth Observation Satellite Scheduling Problem with CP and Local Search》中描述的采集规划方法，并针对 benchmark 公开的测试实例与解契约做了适配。

## 引用

```bibtex
@inproceedings{antuori2025solving,
  title={Solving the Agile Earth Observation Satellite Scheduling Problem with CP and Local Search},
  author={Antuori, Vincent and Wojtowicz, Damien and Hebrard, Emmanuel},
  booktitle={31st International Conference on Principles and Practice of Constraint Programming (CP 2025)},
  series={Leibniz International Proceedings in Informatics},
  volume={340},
  pages={3:1--3:18},
  year={2025},
  doi={10.4230/LIPIcs.CP.2025.3}
}
```

本求解器独立自洽。它读取 benchmark 测试实例文件，写出 benchmark 解 JSON，但不会导入或执行 benchmark、实验、运行时基座或其他求解器的内部实现。

## 方法概述

论文将敏捷对地观测调度分解为采集规划与数据下传规划。本复现保留采集部分，并适配到 `aeossp_standard`：

- **候选**：一次与网格对齐的 `(satellite_id, task_id, start_time, end_time)` 观测；该观测需满足传感器匹配、任务时间窗口、观测几何与初始姿态机动可行性。
- **效用**：默认取成像任务的 `weight / duration`，并用确定性规则打破平局：权重更高、截止时间更早、转移增量更小、候选编号更小者优先。
- **贪心插入**：候选按效用降序处理；只要候选不与已有动作重叠、不违反转移间隔、也不与已排入调度表的成像任务重复，就将其插入对应卫星的调度表。
- **连通分量局部搜索**：求解器根据重叠边与转移边构建同一卫星的依赖图，提取连通分量，然后反复尝试改进当前最优解——先移除某个分量中所有被选中的候选，再针对当前全局选择重新插入。默认采用边际收益贪心排序；对较小的分量还提供可选的有界精确枚举路径。
- **电池保护约束与修复**：局部搜索可选用保护约束，拒绝那些能改进目标函数、却会明显加剧求解器内部电池消耗的移动。最终的有界修复仍会检查调度表是否存在重叠、转移间隔、初始姿态机动、成像任务重复与电池方面的问题，必要时移除效用最低的违规候选。

## 面向 benchmark 的适配

本 benchmark 与论文在若干重要方面存在差异：

- benchmark 排序时先看解是否合法，再依次比较 `WCR`、`CR`、`TAT` 和 `PC`，因此求解器采用加权选择，而不是单纯按采集数量取舍。
- 观测动作必须与公开动作网格严格对齐，时长也必须与每个成像任务的规定时长完全一致。
- 姿态机动可行性采用 benchmark 的标量加速-滑行-减速（bang-coast-bang）加稳定时间语义，而不是论文中与时间无关的转移矩阵。
- 电池约束天然不是成对的，因此没有编码进依赖图。求解器可以在局部搜索中使用求解器内部的电池保护约束，并在贪心插入和局部搜索之后始终执行有界修复。
- 本 benchmark 只涉及观测，数据下传与存储规划不在范围内。

这意味着本求解器复现了论文的贪心构造与连通分量局部搜索思路，同时严格遵循 benchmark 公开的合法性契约。论文中专有的 Tempo 回退方案未集成；当设置 `enable_exact_reinsertion` 时，小分量改用求解器内部的精确枚举，并保持 benchmark 的各项约束：每个成像任务只观测一次、动作互不重叠、满足转移间隔与初始姿态机动要求，且落在固定网格上。

## 求解器契约

```bash
./setup.sh
./solve.sh <case_dir> [config_dir] [solution_dir]
```

在使用项目环境时，`setup.sh` 实际上是一个空操作。

`solve.sh` 会写出：

- `solution.json`：主要的 benchmark 解
- `status.json`：求解器摘要、耗时、复现说明与本地验证详情
- `debug/*`：当 `debug: true` 时可选的调试产物

主要解产物是一个 JSON 对象，其顶层 `actions` 数组由 `observation` 动作组成。

## 流水线

求解器的流水线如下：

1. 加载 `mission.yaml`、`satellites.yaml` 和 `tasks.yaml`。
2. 生成与网格对齐的候选观测，满足传感器匹配、任务时间窗口、观测几何与首个动作的姿态机动可行性。
3. 按效用降序插入候选，构建确定性的贪心调度表。
4. 用基于边际收益重算的首次改进连通分量局部搜索优化调度表。
5. 执行求解器内部的验证与有界修复，清除遗留问题，尤其是电池耗尽风险。

修复阶段有意保持保守。它维持求解器的独立自洽，并减少官方验证器的失败，但不宣称贪心/LNS 核心已完全证明电池可行性。状态产物会报告修复前后的动作与目标函数影响，以及电池失败次数。

## 配置

求解器从以下位置读取可选配置：

- `<config_dir>/config.yaml`
- `<config_dir>/config.yml`
- `<config_dir>/config.json`
- `<config_dir>/greedy_lns.yaml`
- `<config_dir>/greedy_lns.yml`
- `<config_dir>/greedy_lns.json`

带注释的示例参见 [config.example.yaml](../../../../../../solvers/aeossp_standard/greedy_lns/config.example.yaml)。

主要配置项：

- `candidate_stride_multiplier`
- `max_candidates`
- `max_candidates_per_task`
- `minimize_transition_increment`
- `max_local_search_iterations`
- `max_local_search_time_s`
- `restart_count`
- `local_search_workers`
- `random_seed`
- `stochastic_ordering`
- `enable_exact_reinsertion`
- `max_exact_component_size`
- `exact_subproblem_timeout_s`
- `enable_battery_guardrails`
- `battery_guard_min_wh`
- `max_repair_iterations`
- `debug`

`max_local_search_time_s` 只限制局部搜索循环，不限制候选生成或本地验证。若达到时间预算，求解器返回目前找到的最优解，并仍会执行本地验证与修复。当 `local_search_workers > 1` 时，各次重启以确定性的进程池批次运行；每个连通分量下降过程仍保持串行。
在每次重启内部，任何重新插入工作开始之前，都会先用安全的目标函数上界剪除不可能改进成像任务权重的分量。这不改变首次改进策略，因为这类分量本来就不可能被接受为改进移动。

## 调试产物

当 `debug: true` 时，求解器写出：

- `debug/candidate_summary.json`
- `debug/candidates.json`
- `debug/insertion_stats.json`
- `debug/local_search_stats.json`
- `debug/component_summary.json`
- `debug/validation_summary.json`
- `debug/repair_log.json`
- `debug/repaired_candidates.json`

这些产物有助于回答以下问题：

- 某个成像任务为何没有候选
- 贪心插入了多少候选，其余候选为何被跳过
- 每颗卫星的依赖图有多稠密
- 哪些局部搜索移动被接受或拒绝
- 搜索是否因时间预算而停止
- 某个候选为何在本地修复中被移除
- 本地合法性在修复前后如何变化

## 运行方式

直接初始化：

```bash
./solvers/aeossp_standard/greedy_lns/setup.sh
```

在公开冒烟测试实例上直接求解：

```bash
./solvers/aeossp_standard/greedy_lns/solve.sh \
  benchmarks/aeossp_standard/dataset/cases/test/case_0001
```

带配置目录直接求解：

```bash
./solvers/aeossp_standard/greedy_lns/solve.sh \
  benchmarks/aeossp_standard/dataset/cases/test/case_0001 \
  /path/to/config_dir \
  /tmp/aeossp_greedy_lns_solution
```

官方评测与汇总请使用 [Harbor 求解器工作流](../../../experiments/evaluate/README.md)。

求解器本地测试：

```bash
./solvers/aeossp_standard/greedy_lns/test.sh
```

官方评测与汇总请使用 [Harbor 求解器工作流](../../../experiments/evaluate/README.md)。

## 合理性基线

论文报告的是相对上界的收益差距，而不是 benchmark 的 `WCR`、`CR`、`TAT` 或 `PC`。仅做采集的 Greedy/LS-tempo 在作者生成的算例上平均差距约为 0.115。对本 benchmark 而言，最接近的合理性检查是：求解器能否产出合法解，且候选数量与加权完成率是否合理。

这里关注的是：

- 官方验证通过
- 候选数量合理
- 修复不会使调度表崩溃
- 公开测试实例上的加权完成率保持在合理水平

如果原始贪心/局部搜索的选择看起来很强，但修复移除了大量动作，应先检查本地电池模型、转移间隔逻辑与候选生成，再调整搜索参数。

## 已知局限

- 本求解器复现的是论文的采集规划方法，并不声称复现论文中的每个运行时间或每张表格。
- 求解器不包含论文中专有的 Tempo CP-SAT TSPTW 后端。其可选的精确重插入路径是针对小连通分量的有界等效实现，且适配了 benchmark。
- 电池可行性由可选的求解器内部保护约束与有界修复处理，而不是完整编码进贪心/LNS 核心。
- 候选生成无法中断，且在局部搜索获得时间预算之前仍可能消耗可观的运行时间。
- 本求解器省略了数据下传与存储调度，因为 benchmark 只涉及观测。
