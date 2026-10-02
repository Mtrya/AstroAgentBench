[English](../../../../../../solvers/revisit_constellation/rgt_apc_gap_constructive/README.md) | 中文

# RGT/APC 基于重访间隔的构造式求解器

<!-- i18n-source-sha256: 4d64cdf10f02c4f6bf27b08189d88307d428d1f2e29b657ae3a0f4d57637e2b6 -->

本求解器面向 `revisit_constellation`，是一个可运行的复现求解器。

它把 Zhang 与 Lee 的重复星下点轨迹（RGT）和可见性剖面星座（APC）设计思路，与 Mercado-Martinez、Soret 和 Jurado-Navas 的新鲜度感知构造式调度模式结合起来，并适配该 benchmark 的公开测试实例与解的契约。

## 引用文献

```bibtex
@article{zhang2018leo,
  title = {LEO Constellation Design Methodology for Observing Multi-Targets},
  author = {Zhang, Chen and Jin, Jin and Kuang, Linling and Yan, Jian},
  journal = {Astrodynamics},
  volume = {2},
  number = {2},
  pages = {121--131},
  year = {2018},
  doi = {10.1007/s42064-017-0015-4}
}

@article{lee2020apc,
  title = {Satellite Constellation Pattern Optimization for Complex Regional Coverage},
  author = {Lee, Hang Woon and Shimizu, Seiichi and Yoshikawa, Shoji and Ho, Koki},
  journal = {Journal of Spacecraft and Rockets},
  volume = {57},
  number = {6},
  pages = {1309--1327},
  year = {2020},
  doi = {10.2514/1.A34657},
  eprint = {1910.00672},
  archivePrefix = {arXiv}
}

@article{mercado2025energyconstructive,
  title = {Scheduling Agile Earth Observation Satellites with Onboard Processing and Real-Time Monitoring},
  author = {Mercado-Martinez, Antonio M. and Soret, Beatriz and Jurado-Navas, Antonio},
  year = {2025},
  eprint = {2506.11556},
  archivePrefix = {arXiv}
}
```

该求解器独立自洽：读取 `assets.json` 与 `mission.json`，写出 benchmark 的解 JSON，不导入也不执行 benchmark、experiment、runtime 或其他求解器的内部实现。

## 方法概述

流程如下：

1. 加载 `revisit_constellation` 的公开测试实例文件。
2. 在测试实例的高度范围内构造确定性的、考虑 J2 的重复星下点轨迹壳层，再把筛选通过的壳层展开为 APC 风格的 RAAN 与相位候选。
3. 对候选目标的可见性剖面采样，并把可见采样点归并为观测机会。
4. 依据对重访间隔时间线的 benchmark 风格边际改进，并辅以确定性的覆盖多样性平局裁决，从候选池中贪心选出最终输出的卫星。
5. 按 Mercado 风格的新鲜度、可分配灵活度与机会成本优先级构建观测动作。
6. 执行求解器本地校验、确定性的插入/删除修复，以及有界的大重访间隔局部搜索。
7. 把局部搜索得到的调度表输出为 `solution.json`，并保留 no-op、FIFO、constructive、repaired 与 local-search 各模式的对比作为调试证据。

最终动作集合只包含 `observation` 动作。卫星状态为任务开始时刻的 GCRF 笛卡尔状态。

## benchmark 适配

该 benchmark 与上述论文在若干要点上不同：

- Zhang 与 Lee 的工作主要在星座/可见性剖面设计层面展开。该 benchmark 对已排定观测的中点计分，因此本求解器把 RGT/APC 可见时间线用作候选设计的证据，再编排具体的观测。
- Lee 的 APC 模型在种子可见性剖面、星座构型向量与覆盖时间线之间使用循环卷积。本求解器用有界相位槽复现了可见性剖面平移的思路，但没有求解 Lee 的 BILP 覆盖满足模型。
- 本求解器把 Mercado 的 AoI 新鲜度适配为 benchmark 的中点重访间隔。目标当前的新鲜度，是它在任务开始、已有观测中点与任务结束之间（含边界）的最大重访间隔。
- 可分配灵活度，指该目标剩余的本地可行观测选项数量。
- 机会成本：选择某个观测会阻塞本地冲突选项，这些选项按质量加权的新鲜度收益即为机会成本。
- benchmark 的硬合法性规则要求满足几何、互不重叠、姿态机动/稳定时间与电池可行性。求解器在本地检查这些内容，权威结果以 benchmark 验证器为准。

APC 的可见性/可见时间线不是最终排定的观测，只是候选机会。输出的 `solution.json` 采用修复后经局部搜索得到的调度表。

## 求解器契约

```bash
./setup.sh
./solve.sh <case_dir> [config_dir] [solution_dir]
```

使用项目环境时，`setup.sh` 不做任何操作。

`solve.sh` 会写出：

- `solution.json`：benchmark 的主要解
- `status.json`：求解器摘要、耗时、本地校验、模式对比，以及论文到 benchmark 的适配说明
- `debug/*`：详细的调试产物

## RGT/APC 轨道库

轨道库搜索整数重复天数/圈数的壳层，要求满足长期项 J2 重复星下点轨迹条件；随后按测试实例初始轨道的高度范围筛选壳层，对解析闭合程度打分，并把筛选通过的壳层展开为确定性的 RAAN 与平近点角相位槽。候选数量由 `orbit_library.max_candidates` 限制，该上限与 benchmark 最终输出卫星数的上限有意分开。

默认搜索模式 `minmax_architecture` 会在候选上限生效之前，把筛选通过的 RGT 壳层、由目标导出的倾角带，以及均衡的 RAAN/平近点角相位槽交错排列。这样既保留了 Lee 式 APC 的可见性剖面平移思路，又避免了早先的行为：一条邻近的基准轨道就可能耗尽整个候选上限。`target_diversified` 与 `legacy_base_first` 可用于与早期枚举方式直接对比。

求解器在 `debug/closure_search.json` 中报告壳层级的解析闭合结果，在 `debug/selected_emitted_closure_audit.json` 中报告选中/输出卫星的数值 J2 闭合审计。解析闭合证据用于壳层构造阶段；数值审计则作为输出卫星的诊断证据上报。

若没有任何 RGT 候选能通过高度范围筛选，求解器会退回到一个规模很小的确定性圆轨道高度网格。该兜底路径会记录在 `status.json` 中；它只是稳健性措施，并不意味着 APC 达到最优。

## 重访间隔感知的卫星选择

候选卫星从更大的候选池中贪心选出。每一轮加入的候选，都是其机会时间线对 benchmark 形式得分改进最大的那个：

- 跨目标取平均的截断最大重访间隔
- 最差目标的截断最大重访间隔，用作诊断性平局裁决
- 原始最大重访间隔
- 超过 12 h 的目标数
- 阈值违反次数

所有间隔计算都含边界并使用观测中点，与 benchmark 的计分约定一致。平均重访间隔仅作为诊断指标上报，不作为有意义的优化目标：相邻观测可以拉低算术平均值，却不会缩短长时间中断。得分相同时，选择器按确定性的多样性判据打破平局：新覆盖的目标、目标覆盖总数、新覆盖的纬度带、相对已选卫星的相位分布，最后是候选 ID。默认实验配置在乐观的已选包络不再改进后，仍会继续选择确定性的支撑卫星，直至达到测试实例的卫星数上限，因为调度器可以利用这些额外平台，在本地硬可行性约束下把包络实现出来。

## 构造式调度与修复

调度器先为每个可见窗口构造一个观测选项，锚定在局部最优的侧摆角/斜距采样点附近，随后按以下准则选择观测：

- 新鲜度：当前目标重访间隔最大者优先
- 灵活度：剩余目标选项较少者优先
- 机会成本：冲突收益损失较小者优先
- 确定性平局裁决：时间戳、卫星 ID、目标 ID 与窗口 ID

求解器本地校验检查未知引用、时长、采样几何、同一卫星上的重叠、所需的姿态机动/稳定时间间隔，以及保守的电池风险。

修复过程是确定性的：先移除本地非法或有风险、且对得分损害最小的观测，再尝试为大重访间隔目标插入可行观测。之后一轮有界的局部搜索会考虑确定性的大重访间隔插入与一对一交换。局部搜索只采纳能改善 benchmark 形式优先级顺序的移动，该顺序为：跨目标平均的截断最大重访间隔、最差目标的截断最大重访间隔、原始最大重访间隔、超过 12 h 的目标数、阈值违反次数。输出的解采用局部搜索模式。no-op、FIFO、未修复的 constructive 与 repaired 模式仅保留用于复现保真度诊断。

## 配置

求解器从以下任一位置读取可选配置：

- `<config_dir>/config.yaml`
- `<config_dir>/config.yml`

完整示例见 [config.example.yaml](../../../../../../solvers/revisit_constellation/rgt_apc_gap_constructive/config.example.yaml)。

配置文件既可以像 [config.example.yaml](../../../../../../solvers/revisit_constellation/rgt_apc_gap_constructive/config.example.yaml) 那样只给出一份直接配置，也可以声明 `active_profile` 与若干具名 `profiles`。使用 profile 时，求解器会把激活的 profile 深度合并进共享配置，并把解析出的设置记录到 `status.json`、`debug/run_profile_summary.json` 和 `debug/parameter_sweep_summary.json`。更宽裕的计算资源包络应放在实验配置中，而不是求解器本地的示例配置里。

主要可调参数：

- `active_profile`
- `profiles.<name>`
- `parameter_sweep.points`
- `orbit_library.max_candidates`
- `orbit_library.search_mode`
- `orbit_library.max_rgt_days`
- `orbit_library.min_revolutions_per_day`
- `orbit_library.max_revolutions_per_day`
- `orbit_library.raan_slot_count`
- `orbit_library.phase_slot_count`
- `orbit_library.max_shells`
- `orbit_library.max_closure_error_m`
- `orbit_library.j2_closure_tolerance_m`
- `orbit_library.j2_refinement_iterations`
- `orbit_library.fallback_altitude_count`
- `visibility.sample_step_sec`
- `visibility.max_windows`
- `visibility.keep_samples_per_window`
- `visibility.worker_count`
- `selection.max_selected_satellites`
- `selection.require_positive_improvement`
- `scheduling.max_actions`
- `scheduling.max_actions_per_target`
- `scheduling.observation_margin_sec`
- `scheduling.transition_gap_sec`
- `scheduling.require_positive_gap_improvement`
- `scheduling.enforce_simple_energy_budget`
- `scheduling.enable_repair`
- `scheduling.repair_max_iterations`
- `scheduling.enable_local_search`
- `scheduling.local_search_max_iterations`
- `scheduling.local_search_options_per_target`
- `scheduling.local_search_removals_per_option`

较小的可见性采样步长会提高机会的保真度，但会增加运行时间。`visibility.worker_count: null` 会自动选择一个有界的、按候选并行的 worker 数量；若要让可见性构造按串行、确定性的方式进行，请设为 `1`。`transition_gap_sec: null` 会在选项冲突检查中使用由测试实例推导出的保守加速-滑行-减速（bang-coast-bang）姿态机动/稳定时间间隔。

## 调试产物

每次运行都会写出：

- `debug/orbit_candidates.json`：生成的候选卫星状态
- `debug/closure_search.json`：已接受/已拒绝的 J2 RGT 壳层诊断
- `debug/selected_emitted_closure_audit.json`：选中/输出卫星的数值 J2 闭合诊断
- `debug/visibility_windows.json`：采样得到的候选目标可见窗口
- `debug/selection_rounds.json`：贪心卫星选择轮次与边际改进
- `debug/target_coverage.json`：调度前目标级的候选覆盖与已选覆盖
- `debug/candidate_coverage.json`：候选级的目标/机会覆盖诊断
- `debug/scheduling_decisions.json`：构造式调度决策、优先级、得分与改进
- `debug/scheduling_rejections.json`：被跳过的选项及求解器本地原因
- `debug/local_validation.json`：最终的本地硬合法性与大重访间隔报告
- `debug/repair_steps.json`：确定性的删除/插入修复日志
- `debug/local_search_moves.json`：已接受与已拒绝的有界局部搜索移动
- `debug/scheduling_summary.json`：选项、动作、拒绝、修复、大重访间隔与模式计数的紧凑汇总
- `debug/baseline_summary.json`：用于跨运行对比的紧凑性能剖析、模式、目标覆盖与大重访间隔证据
- `debug/opportunity_envelope.json`：全部生成、闭合过滤、已选、硬可行与最终调度表的包络指标
- `debug/high_gap_intervals.json`：逐目标的大重访间隔区间与阻塞因素诊断
- `debug/run_profile_summary.json`：激活的 profile、可用 profile，以及解析出的计算关键参数
- `debug/parameter_sweep_summary.json`：可选的扫描点及其解析出的参数
- `debug/mode_comparison.json`：求解器本地 no-op、FIFO、constructive、repaired 与 local-search 的对比指标
- `debug/adaptation_notes.json`：论文概念到 benchmark 机制的映射

这些产物用于回答：

- 调度之前是否已有候选覆盖
- 哪些卫星改善了重访时间线
- 某个目标为何仍然存在大重访间隔或未被观测
- 修复或局部搜索是否改变了构造式解
- FIFO/no-op 与 constructive、repaired、local-search 模式相比表现如何
- 哪些论文成分被复现，哪些属于 benchmark 适配

## 运行方式

直接执行安装：

```bash
./solvers/revisit_constellation/rgt_apc_gap_constructive/setup.sh
```

在公开冒烟测试实例（smoke test）上直接求解：

```bash
./solvers/revisit_constellation/rgt_apc_gap_constructive/solve.sh \
  benchmarks/revisit_constellation/dataset/cases/test/case_0001
```

带配置目录直接求解：

```bash
./solvers/revisit_constellation/rgt_apc_gap_constructive/solve.sh \
  benchmarks/revisit_constellation/dataset/cases/test/case_0001 \
  /path/to/config_dir \
  /tmp/revisit_rgt_apc_solution
```

官方评测与结果汇总请使用 [Harbor 求解器工作流](../../../experiments/evaluate/README.md)。

## 合理性基线

文献报告的是覆盖与 AoI 风格的调度行为，而不是这些公开测试实例上的 benchmark `capped_max_revisit_gap_hours`。应把论文当作方法参考，而不是数值目标表。

此处关注的是：

- benchmark 验证通过
- 所选卫星数量符合测试实例上限
- 在 benchmark 验证之前，本地校验无问题
- constructive/repaired 模式在主要指标（截断最大值指标）上优于 no-op
- 修复不会使调度表崩溃
- 大重访间隔目标与未观测目标能在调试摘要中看到

在最近一次记录的冒烟测试运行（`test/case_0001`）中，benchmark 验证器通过：18 颗卫星、147 个观测动作、无硬合法性违规，`capped_max_revisit_gap_hours = 9.345108695652174`。全部生成包络、闭合过滤包络与已选包络均为 `8.876086956521739 h`，而本地硬可行结果与最终调度表为 `9.345108695652174 h`。因此剩余的冒烟测试损失来自调度与硬可行性限制，而不是已选包络限制。

同一次冒烟测试运行中，`max_revisit_gap_hours = 11.966666666666667`，超过 12 h 的目标数为 0，另有 12 个目标超过各自更严格的 8 h 预期重访周期。该求解器仍是有效的适配复现基线，而不是已求解到最优的 benchmark 结果。

## 已知局限

- 这是针对该 benchmark 适配的方法族忠实复现，并不复现 Zhang、Lee 或 Mercado 论文中的每一张表或精确优化模型。
- Lee 的 APC/BILP 覆盖满足模型并未精确求解；RGT/APC 仅用作确定性候选生成与可见性剖面证据。
- 求解器在构造阶段使用解析 J2 壳层闭合，并对选中/输出卫星报告数值 J2 审计。在最近一次冒烟测试运行中，所选卫星的数值闭合残差仍有数百千米，因此该数值审计应视为如实反映现状的诊断，而不是其在 benchmark 传播器下闭合的证明。
- 求解器只使用圆形轨道的 J2-RGT 候选或兜底的圆形候选，可能错过得分更优的非对称非 RGT 设计或椭圆轨道设计。
- 可见窗口是采样得到的，因此极短的机会可能被漏掉或只能近似。
- 电池可行性由求解器本地以保守方式校验和修复，最终仍以 benchmark 验证器为准。
- 完整公开测试实例的运行比聚焦的冒烟测试实例更慢，因为运行时间主要花在可见性采样上。公开测试实例的耗时与合法性证据应放在实验配置和结果中，而不是求解器注册表里。
