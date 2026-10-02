[English](../../../../../../solvers/regional_coverage/celf_submodular/README.md) | 中文

# 区域覆盖 CELF 子模求解器
<!-- i18n-source-sha256: 21b8cbdd796bf33bc0ff3cd30a889647a841ff81703f8978b3924abe403986a6 -->

本求解器在固定的候选条带覆盖模型上实现 CELF/CEF，包含调度修复、局部改进和明确的计算量限制。

它沿用 Leskovec、Krause、Guestrin、Faloutsos、VanBriesen 和 Glance 在《Cost-effective Outbreak Detection in Networks》中描述的 CELF 与 CEF 方法族，并适配到本 benchmark 公开的条带观测测试实例与解契约。

## 引用

```bibtex
@inproceedings{leskovec2007cost,
  title={Cost-effective outbreak detection in networks},
  author={Leskovec, Jure and Krause, Andreas and Guestrin, Carlos and Faloutsos, Christos and VanBriesen, Jeanne and Glance, Natalie},
  booktitle={Proceedings of the 13th ACM SIGKDD International Conference on Knowledge Discovery and Data Mining},
  pages={420--429},
  year={2007},
  doi={10.1145/1281192.1281239}
}

@article{nemhauser1978analysis,
  title={An analysis of approximations for maximizing submodular set functions---I},
  author={Nemhauser, George L. and Wolsey, Laurence A. and Fisher, Marshall L.},
  journal={Mathematical Programming},
  volume={14},
  number={1},
  pages={265--294},
  year={1978},
  doi={10.1007/BF01588971}
}

@article{khuller1999budgeted,
  title={The budgeted maximum coverage problem},
  author={Khuller, Samir and Moss, Anna and Naor, Joseph},
  journal={Information Processing Letters},
  volume={70},
  number={1},
  pages={39--45},
  year={1999},
  doi={10.1016/S0020-0190(99)00031-9}
}
```

本求解器独立自洽。它读取 benchmark 的测试实例文件，写出 benchmark 解 JSON，但不导入或执行 benchmark、实验、运行时基座或其他求解器的内部实现。

## 方法概述

论文将疫情暴发检测建模为在选定传感器或信息源上的单调子模奖励最大化问题：

- 每个元素是一个待选节点
- 每个场景一旦被至少一个选中的元素检测到，就获得奖励
- 贪心选择每次加入边际奖励最高的元素
- CELF 仅在元素到达优先队列队首时才惰性刷新过期的边际增益，从而省去朴素贪心的大部分重算
- CEF 通过同时运行单位代价贪心和收益/代价贪心来处理非均匀代价，然后返回奖励更高的解

本次复现保留这一框架，并将其适配到 `regional_coverage`：

- 元素：一个固定的定时 `strip_observation` 候选动作
- 场景/条目：一个公开覆盖网格采样点索引
- 奖励：固定候选采样集合上的唯一加权采样覆盖
- 单位代价策略：边际加权覆盖
- 收益/代价策略：边际加权覆盖除以配置的代价
- 最终 CEF 策略：在单位代价与收益/代价两种惰性贪心输出中取目标函数值更高者
- 在线证据：CELF 选择完成后，在同一固定候选集上计算的 3.2 节上界

## Benchmark 适配

本 benchmark 与论文有几处重要差异：

- 论文在图上选择抽象传感器；本 benchmark 要求的是定时的卫星动作，并遵循滚转、时长、姿态机动、功耗、占空比和任务时域规则。
- 论文的奖励可以建模检测概率、检测时间或受影响人群；本求解器使用的是面向 benchmark 的公开网格采样点唯一加权覆盖。
- 论文的预算是一种抽象的选择预算；除非配置了显式的求解器选择预算，本求解器将其映射为 `max_actions_total`。
- 非均匀代价是可选的。支持的代价模式有动作数量、成像时间、估计成像能量和简单的滚转转换开销。
- 候选几何由求解器本地计算，并且是近似的：使用公开 TLE（两行根数）、Brahe SGP4 轨道传播、仅滚转的 WGS84 射线求交和覆盖网格采样点。官方区域几何、合法性判定与评分仍由 benchmark 掌握。
- 论文的纯集合选择模型并不包含调度可行性，因此本求解器把调度感知的 CELF 接受检查作为一项 benchmark 适配，并在选择之后单独报告修复情况。
- 在线上界只针对求解器生成的、经 benchmark 适配的有限候选全集计算，不能证明任意连续调度或验证器侧几何意义上的最优性。

调度感知的选择阶段会拒绝那些使当前已选固定候选序列违反动作数量上限、公开条带形状规则、同星半开区间重叠、benchmark 风格的加速-滑行-减速（bang-coast-bang）姿态机动加稳定时间，或保守的电池/占空比风险的候选。修复阶段作为确定性的安全网保留下来，按估计唯一覆盖损失最低、能量开销最高、时长、起始偏移、候选 id 的次序，移除仍然冲突的候选。

## 求解器契约

```bash
./setup.sh
./solve.sh <case_dir> [config_dir] [solution_dir]
```

`setup.sh` 会验证项目环境能否导入 `yaml`。

`solve.sh` 写出以下文件：

- `solution.json`：benchmark 的主解，顶层是由 `strip_observation` 动作组成的 `actions` 数组
- `status.json`：测试实例解析、候选生成、覆盖映射、CELF、修复、复现、输出策略和耗时摘要
- `candidate_debug.json`：根层保存的生成候选抽样及其映射采样覆盖
- `debug/*`：下文描述的详细调试产物

## 配置

求解器从 `<config_dir>/config.yaml` 读取可选配置。

带注释的示例见 [config.example.yaml](../../../../../../solvers/regional_coverage/celf_submodular/config.example.yaml)。

候选生成参数：

- `time_stride_s`：在公开动作网格上的起始时间步长
- `roll_step_deg`：默认的对称滚转网格间距
- `max_candidates_total`：确定性候选数量上限；设为 `null` 可禁用
- `cap_strategy`：`balanced_stride` 在稳定的完整候选网格上均匀采样，`first_n` 则保留用于调试的旧前缀行为
- `duration_values_s`：可选的显式条带时长
- `roll_values_deg`：可选的显式滚转取值
- `debug_candidate_limit`：复制到 `candidate_debug.json` 的候选数量

覆盖映射参数：

- `method`：`indexed` 在公开覆盖采样点上构建稀疏的求解器本地网格；`simple` 扫描全部采样点，保留用于调试和等价性测试
- `spatial_bin_deg`：索引映射器使用的经度/纬度分箱大小
- `worker_count`：串行的整数工作进程数；对于由实验层掌控的重型策略，可设为 `auto`
- `chunk_size`：并行映射时确定性的连续候选分块大小

选择参数：

- `run_unit_cost`：运行 CELF 的单位代价贪心变体
- `run_cost_benefit`：运行 CELF 的收益/代价贪心变体
- `cost_mode`：`action_count`、`imaging_time`、`estimated_energy` 或 `transition_burden`
- `budget`：可选显式选择预算；`null` 表示使用 benchmark 的 `max_actions_total`
- `min_marginal_gain`：接受候选的停止阈值
- `schedule_aware`：只接受能让当前固定候选调度在求解器本地保持可行的候选
- `local_improvement`：在 CELF 之后、确定性修复之前，启用有界的固定候选插入/交换遍历
- `local_improvement_max_passes`：局部改进中允许接受的最大移动次数
- `local_improvement_max_candidate_checks`：每轮局部改进中考察的正收益固定候选数量上限
- `local_improvement_worker_count`：串行的整数工作进程数；确定性并行移动评估可设为 `auto`
- `local_improvement_chunk_size`：局部改进移动评估所用的确定性候选分块大小
- `compute_online_bounds`：为每个启用的 CELF 变体计算 Leskovec 3.2 节固定集上界证据
- `max_bound_order_debug`：调试摘要中保留的上界排序行数上限
- `write_iteration_trace`：写出 `debug/celf_iterations.jsonl`
- `max_iteration_debug`：每个 CELF 变体保留的重算/接受/拒绝行数上限

请根据计算预算在 config.yaml 中选择候选网格规模、局部改进和 worker 数量。有界评测示例只检查集成是否正确。

## 调试产物

求解器写出以下文件：

- `debug/candidate_summary.json`：候选数量、生效的上限，以及按卫星、按滚转、按时长的直方图
- `debug/coverage_runtime_summary.json`：覆盖映射的执行模型、空间索引规模、采样点检查计数和预筛选缩减比例
- `debug/celf_summary.json`：算法元数据、选中的 id、目标函数值、已覆盖采样点数量、真实的边际重算次数、估计的朴素重算上界、惰性节省量、过期出队、调度不可行跳过、固定集在线上界和 CEF 对比结果
- `debug/celf_iterations.jsonl`：启用后记录重算、接受、非正收益拒绝和不可行跳过事件的有界轨迹
- `debug/selected_candidates.json`：调度修复之前选中的候选
- `debug/feasibility_summary.json`：求解器本地调度检查在修复前后的合法性标志和问题计数
- `debug/repair_log.json`：确定性的移除原因和估计唯一覆盖损失
- `debug/repair_objective_summary.json`：修复前的 CELF 目标函数、修复后的求解器本地目标函数和修复损失
- `debug/repaired_candidates.json`：修复后剩余的候选
- `debug/reproduction_summary.json`：忠实于论文的要素、从论文到 benchmark 的适配、已知保真度限制和选择审计

有用的检查：

- 如果在很小的单元测试中 `estimated_lazy_recomputations_saved` 为零，说明惰性队列没有体现 CELF 的行为。
- 如果 `zero_coverage_count` 等于 `candidate_count`，应检查求解器本地的候选几何、滚转取值、候选上限均衡情况和覆盖网格布点。
- 如果修复移除了大量动作，应检查 `repair_log.json` 和 CELF 的 `infeasible_skip_counts`；瓶颈很可能是求解器本地的调度感知接受条件与残余修复安全网之间的差距。

## 运行方式

直接安装：

```bash
./solvers/regional_coverage/celf_submodular/setup.sh
```

在公开冒烟测试实例上直接求解：

```bash
./solvers/regional_coverage/celf_submodular/solve.sh \
  benchmarks/regional_coverage/dataset/cases/test/case_0001
```

指定配置目录直接求解：

```bash
./solvers/regional_coverage/celf_submodular/solve.sh \
  benchmarks/regional_coverage/dataset/cases/test/case_0001 \
  /path/to/config_dir \
  /tmp/regional_coverage_celf_solution
```

官方评测与结果汇总请使用 [Harbor 求解器工作流](../../../experiments/evaluate/README.md)。

## 合理性基线

论文的理论基线适用于固定的单调子模选择问题，并不直接适用于由验证器评分的卫星调度。请把它们当作算法层面的合理性检查：

- 在小规模固定候选测试中，单位代价贪心应与朴素贪心结果一致
- CELF 的边际重算次数不应多于朴素贪心，并且在队首元素已过期但仍占优的测试实例中应节省重算
- 当配置的代价不同时，收益/代价贪心可能与单位代价贪心结果不同
- 最终 CEF 结果应是已启用的单位代价与收益/代价两个变体中奖励更高的解
- 3.2 节的在线上界不应小于所选固定集的奖励，并应报告用于构成该上界的剩余预算边际收益/代价排序

在 benchmark 运行中，官方验证是合法性的准入门槛，验证器指标是评分依据。固定集在线上界只是针对所生成候选全集的算法证明，不能替代验证器指标。

## 已知限制

- 这里复现的是带固定集在线上界证据的 CELF/CEF 方法族，而非论文中的每一张实验表。
- 在线最优性上界的作用范围仅限于生成的固定候选集和求解器本地的覆盖目标函数，不应被理解为对连续卫星调度问题或官方验证器得分的上界。
- 候选覆盖使用确定性的求解器本地 Brahe SGP4 轨道传播，以及基于公开 TLE 字段的 WGS84 射线求交，不使用 benchmark 验证器的内部实现。
- 调度感知的 CELF 接受条件是在论文方法之上叠加的 benchmark 适配。它能提升输出通过验证器检查的质量，但并不意味着连续调度意义上的最优性。
- 有界局部改进是 CELF 之后的另一项 benchmark 适配。它只使用固定候选和求解器本地调度检查，并把接受的移动与 CELF 惰性重算统计分开报告。
- 选择后的修复仍可能移除 CELF 选中的候选，不过在 `case_0001` 上当前的调度感知质量探测中，修复损失比为 `0.0`。
- 电池与占空比检查是保守的求解器本地近似；官方验证器仍是唯一权威。
- 公开配置有意只保留一套最强的固定候选配置。本地用户可以自行调整 `config.yaml`，但更小的替代配置不会作为质量证据报告。
