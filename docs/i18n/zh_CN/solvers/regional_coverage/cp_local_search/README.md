[English](../../../../../../solvers/regional_coverage/cp_local_search/README.md) | 中文

# Regional Coverage 的 CP 辅助局部搜索求解器

<!-- i18n-source-sha256: a43c25502e62dfa97c86285a2489dc42a23e509fa718db6f9a0b498e0f3cd640 -->

本求解器可运行，是针对 `regional_coverage` 采集规划控制流的 benchmark 适配复现。

它遵循 Valentin Antuori、Damien T. Wojtowicz 和 Emmanuel Hebrard 在 "Solving the Agile Earth Observation Satellite Scheduling Problem with CP and Local Search" 中描述的采集规划方法，并适配到 benchmark 公开的条带覆盖契约。

## 引用

```bibtex
@inproceedings{antuori2025solving,
  title={Solving the Agile Earth Observation Satellite Scheduling Problem with {CP} and Local Search},
  author={Antuori, Valentin and Wojtowicz, Damien T. and Hebrard, Emmanuel},
  booktitle={31st International Conference on Principles and Practice of Constraint Programming (CP 2025)},
  series={Leibniz International Proceedings in Informatics (LIPIcs)},
  volume={340},
  pages={3:1--3:22},
  year={2025},
  publisher={Schloss Dagstuhl -- Leibniz-Zentrum fuer Informatik},
  doi={10.4230/LIPIcs.CP.2025.3}
}
```

本求解器独立自洽。它读取公开的 benchmark 测试实例文件，写出 benchmark 解 JSON，但不导入或执行 benchmark、experiment、运行时基座或其他求解器的内部实现。

## 方法概述

Antuori 等人将 AEOS 调度分解为采集规划与下传规划。采集规划器维护各卫星本地的采集序列，用贪心插入构建初始解，再用局部搜索改进选中的序列邻域。当贪心插入无法安排一次采集时，论文会在一个有界的 TSPTW 型子问题上调用 Tempo。

本复现保留采集规划结构：

- 采集：固定起始的 `strip_observation` 候选，可选地使用保守机会分组以支持区间修复
- 卫星序列：每颗卫星一个条带候选的有序列表
- 转换时间：滚转差值的加速-滑行-减速（bang-coast-bang）姿态机动加上稳定时间
- 贪心插入：选择边际唯一覆盖最优的可行候选与插入位置，并使用确定性平局裁决
- 邻域动作：从有界时间窗或确定性冲突分量中移除选定的卫星本地候选，再以贪心方式重建邻域
- CP 辅助：在局部邻域内运行有界的 OR-Tools CP-SAT 修复，形式可以是固定起始子集修复，也可以是吸附回公开候选的区间/TSPTW 型修复

求解器的目标面向 benchmark，而不是论文原生目标：它在保持公开动作合法的前提下，最大化 `coverage_grid.json` 采样点上的唯一加权覆盖。

## Benchmark 适配

benchmark 与论文有几处重要差异：

- 论文使用固定的可加采集收益；benchmark 按唯一区域覆盖计分，因此候选价值按边际未覆盖采样点权重重新计算。
- 论文使用预先计算的采集机会；benchmark 不提供可见窗口，因此本求解器基于公开测试实例文件生成确定性的固定起始、滚转网格条带候选。
- 论文包含下传与星上存储规划；benchmark 的解契约中没有下传或存储动作。
- benchmark 有硬性的电池与成像占空比约束。本求解器规避已知序列冲突并报告求解器本地校验结果，官方合法性仍由评测运行器与 benchmark 验证器判定。
- 论文用 Tempo 完成基于 CP 的 TSPTW 插入；本求解器使用由 `setup.sh` 准备的求解器本地 OR-Tools CP-SAT 后端。

本求解器在 benchmark 契约下复现论文的采集规划结构，而不是复现每个工业子系统或每张结果表。所选配置采用面向 benchmark 适配的密集优化范围，区间/机会配置则保留为区间式建模的对比路径。

## 求解器契约

```bash
./setup.sh
./solve.sh <case_dir> [config_dir] [solution_dir]
```

`setup.sh` 创建求解器本地的 `.venv/`，从 `requirements.txt` 安装锁定版本的依赖，并写入 `.solver-env`，供直接运行与实验侧运行使用。

`solve.sh` 会写出：

- `solution.json`：包含 `strip_observation` 动作的主要 benchmark 解
- `status.json`：求解器摘要、耗时、复现说明、本地校验和 CP 指标
- `debug/candidate_summary.json`
- `debug/candidates.json`
- `debug/greedy_summary.json`
- `debug/local_search_summary.json`
- 启用机会分组时写出 `debug/opportunities.json`
- `debug/selected_candidates.json`
- 可选的 `debug/insertion_attempts.jsonl`
- 可选的 `debug/moves.jsonl`

主要求解产物是一个 JSON 对象，其顶层是 `actions` 数组。每个动作包含：

- `type: strip_observation`
- `satellite_id`
- `start_time`
- `duration_s`
- `roll_deg`

## 搜索流程

求解流程如下：

1. 加载 `manifest.json`、`satellites.yaml`、`regions.geojson` 和 `coverage_grid.json`。
2. 利用公开动作网格、合法滚转区间和固定确定性滚转采样，生成网格对齐的条带候选。
3. 用求解器本地的条带段几何为候选覆盖计分，该几何与公开验证器的仅滚转 WGS84 条带模型对齐。
4. 构建空的卫星本地序列状态。
5. 以边际唯一覆盖计分执行确定性贪心插入。
6. 构建有界的卫星-时间邻域，或同卫星冲突分量邻域。
7. 针对当前已覆盖采样点集合，用贪心插入重建每个邻域。
8. 若启用 CP，则对没有改进的局部邻域调用有界的 OR-Tools CP-SAT 修复。
9. 将选定的候选序列输出为 `strip_observation` 动作。
10. 写出调试摘要和状态元数据。

默认行为确定且有界。重启与随机化邻域行为需在配置中显式开启，并记录到 `status.json`。

## CP 后端

`cp_backend: ortools_cp_sat` 是受支持的后端。

它是在小型 TSPTW 型邻域上构建的求解器本地 CP-SAT 模型。提供两种修复模式：

- `fixed_start_subset`：沿用复现对比配置中的原固定起始修复。
- `interval_tsptw`：为每个选中的机会给出有界起始区间，并在输出解之前把选中成员吸附回具体的公开 `strip_observation` 候选。

两种模式遵循相同的公开解契约：

- 输入：保留的当前最优解候选，加上一个有界的邻域候选池
- 可行性：针对已选候选与邻域外锚点的卫星本地转换冲突约束
- 目标：在尚未被保留候选覆盖的采样点上最大化边际唯一覆盖
- 目标键：合法性优先，其次是覆盖权重、更低的能量估计、更低的姿态机动负担、更少的动作数
- 限制：`cp_max_calls`、`cp_max_candidates`、`cp_max_conflicts` 和 `cp_time_limit_s`

该后端不是 Tempo，也不声称具有 Tempo 的性能。它保留了论文的控制流：先尝试贪心序列修复，当邻域值得投入时再调用有界的 CP 修复。OR-Tools 只安装到 `setup.sh` 创建的求解器本地 `.venv/` 中，不需要系统级依赖。

CP 指标记录在 `status.json` 和 `debug/local_search_summary.json` 中：

- `calls`
- `successful_calls`
- `call_success_rate`
- `improving_solutions`
- `improving_success_rate`
- 跳过调用的计数器
- 模型构建与求解耗时
- 求解器状态计数、分支、冲突、模型规模、超时停止和冲突上限停止

## 配置

求解器从以下位置读取可选配置：

- `<config_dir>/config.yaml`
- `<config_dir>/config.yml`
- `<config_dir>/config.json`

带注释的示例见 [config.example.yaml](../../../../../../solvers/regional_coverage/cp_local_search/config.example.yaml)。

关键参数：

- `candidate_stride_s`
- `roll_samples_per_side`
- `max_candidates_per_satellite`
- `candidate_workers`
- `include_zero_coverage_candidates`
- `max_zero_coverage_candidates_per_satellite`
- `greedy_policy`
- `greedy_max_iterations`
- `greedy_wall_time_limit_s`
- `local_search_enabled`
- `local_search_neighborhood_mode`
- `local_search_max_iterations`
- `local_search_component_gap_s`
- `local_search_time_padding_s`
- `local_search_max_component_size`
- `local_search_component_subwindow_s`
- `local_search_include_sample_competition`
- `local_search_max_neighborhoods_per_iteration`
- `local_search_max_neighborhood_candidates`
- `opportunity_grouping_enabled`
- `opportunity_max_time_gap_s`
- `opportunity_min_coverage_jaccard`
- `cp_enabled`
- `cp_backend`
- `cp_repair_mode`
- `cp_interval_start_window_s`
- `cp_max_calls`
- `cp_max_candidates`
- `cp_max_conflicts`
- `cp_time_limit_s`
- `cp_min_improvement_weight_m2`
- `write_insertion_attempts`
- `write_local_search_moves`
- `search_restart_count`
- `search_run_seeds`
- `greedy_random_choice_probability`
- `local_search_randomize_neighborhood_order`

`greedy_wall_time_limit_s` 只约束贪心插入。`cp_time_limit_s` 只约束每次 CP-SAT 修复调用。候选生成、解写出与本地校验仍会在求解器退出前完成。

## 调试产物

调试摘要用于解释求解器行为与得分差异：

- `candidate_summary.json`：候选数量、正覆盖数量、零覆盖数量、每颗卫星的数量以及最大候选权重
- `candidates.json`：前 `candidate_debug_limit` 条候选记录
- `opportunities.json`：机会分组、成员数量、公开候选映射，以及 `opportunity_grouping_enabled` 为 true 时被省略的分组数量
- `greedy_summary.json`：被接受的候选 ID、边际覆盖总量、插入尝试、可行性拒绝以及确定性平局裁决顺序
- `local_search_summary.json`：生成的邻域、被接受的邻域动作、目标函数增量、当前最优解的演进和 CP 指标
- `selected_candidates.json`：按解中顺序排列的最终选中候选记录，启用机会分组时还包括来源机会 ID
- `insertion_attempts.jsonl`：可选的贪心插入尝试详情
- `moves.jsonl`：可选的局部搜索动作详情，包括 CP 修复记录
- `status.json`：合并后的运行摘要、执行模式、配置、序列模型、校验摘要和复现说明

实用的初步检查：

- 若 `positive_coverage_candidate_count` 为零，检查候选步长和滚转采样。
- 若 CP 调用次数为零，检查 `cp_enabled`、规模限制和邻域生成。
- 若 CP 调用成功但没有带来改进，说明对采样的邻域而言，贪心序列在局部已经足够强。
- 若官方覆盖率低于求解器本地覆盖率，检查条带几何和候选转换。

## 运行方式

直接安装：

```bash
./solvers/regional_coverage/cp_local_search/setup.sh
```

在公开冒烟测试实例上直接求解：

```bash
./solvers/regional_coverage/cp_local_search/solve.sh \
  benchmarks/regional_coverage/dataset/cases/test/case_0001
```

指定配置目录直接求解：

```bash
./solvers/regional_coverage/cp_local_search/solve.sh \
  benchmarks/regional_coverage/dataset/cases/test/case_0001 \
  /path/to/config_dir \
  /tmp/regional_coverage_cp_local_search_solution
```

官方评测与汇总请使用 [Harbor 求解器工作流](../../../experiments/evaluate/README.md)。

## 范围

已实现并适配的部分包括：独立自洽的测试实例解析、确定性候选生成、与验证器一致的唯一覆盖计分、卫星本地序列、贪心插入、有界局部搜索邻域、冲突分量邻域、保守机会分组、重启/多起点机制、可选的 OR-Tools CP-SAT 邻域修复、结构化耗时统计以及官方评测。

benchmark 适配是明确的：本求解器不是 Tempo 本身，也不复现下传或存储规划。在公开的 regional-coverage 契约内，所选方法提供密集的候选集合、进程并行的候选生成、经过验证的全实例实验输出，以及相对贪心可观察到的局部搜索/CP 改进。

## 已知局限

- 本求解器复现的是 Antuori 采集规划方法族，而不是完整的采集/下传/存储一体化规划器。
- Tempo 不能作为项目依赖使用；公开后端采用 OR-Tools CP-SAT，用于有界的固定起始或区间/TSPTW 型邻域。
- 候选生成使用确定性的时间与滚转网格，因此网格点之间更细的机会会被有意忽略。
- 机会分组是保守的，并会吸附回公开的固定候选；它主要用于把区间式建模与固定起始修复进行对比。
- 区间修复模式在模型内部允许有界的起始灵活性，但输出的仍是具体的公开动作，而不是连续的工业级可见窗口调度表。
- 电池和占空比约束没有在搜索目标中全局优化。官方合法性仍由 benchmark 验证器通过 experiments 检查。
- 局部搜索有意保持有界且确定。它不是 ALNS，也不是大范围元启发式扫描。
- 服务器端复现可以把 `candidate_workers` 提高到 `16`；请根据可用内存选择合适的 worker 数量。
