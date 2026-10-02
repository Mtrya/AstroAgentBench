[English](../../../../../../solvers/relay_constellation/mclp_teg_contact_plan/README.md) | 中文

# MCLP+TEG 接触计划求解器
<!-- i18n-source-sha256: e2c9e5c9a6905195122ebd096b00730a347dd65520ffe720f8035da344dac9ca -->

这是 `relay_constellation` 的确定性复现求解器，把 Rogers 风格的最大覆盖选址问题（MCLP）候选筛选层与 Gerard 风格的时间扩展图（TEG）接触调度器组合在一起。

求解器遵循仓库的求解器契约：

```bash
./setup.sh
./solve.sh <case_dir> <config_dir> <solution_dir>
```

它读取 benchmark 测试实例文件，写出 `solution.json`、`status.json` 和求解器本地的调试产物。它不导入 benchmark 的 Python 模块，也不调用 benchmark 的验证器。

## 推荐配置

求解器配置与计算限制参见 `config.example.yaml`。

不传配置直接运行时，会使用内置的小型冒烟配置，且仅用于本地契约校验。冒烟测试的输出不应作为该求解器的复现结果上报。

## 方法

### 候选筛选

Rogers 层的适配方式如下：

- 在测试实例给定的高度、倾角、偏心率和 RAAN 边界内，生成由可行轨道槽位构成的确定性有限候选库。
- 把 benchmark 的 `max_added_satellites` 取值视为基数上限约束。
- 按边际需求窗口服务潜力为候选打分：只要当前激活的星座能通过地面链路和星间链路连通源端点与目的端点，该需求采样点即视为被覆盖。
- 用带索引的确定性贪心 MCLP 打分筛选候选。候选集合很小时仍可走小型 PuLP/CBC MILP 路径，但公开测试实例使用贪心筛选。

experiments 负责的复现配置在当前公开测试实例上会生成大约 300 个候选。

### 接触调度

Gerard 层的适配方式如下：

- 在 benchmark 的路由网格上构建时间扩展的链路可行性。
- 使用两级链路缓存：MCLP 筛选依赖地面可见性以及与骨干星座相连的星间链路；最终调度会为骨干星座与选中的候选重建精确缓存。
- 所报告的配置采用路由感知的逐采样点调度：在满足 `max_links_per_satellite` 和 `max_links_per_endpoint` 的前提下，贪心地选出完整的端到端路径。
- 把连续被选中的采样点压缩成验证器兼容的区间动作。

小规模测试实例仍可使用有界的逐采样点调度器 MILP，但公开测试实例采用可扩展的路由感知方案。

## 论文到 benchmark 的适配

| 论文概念 | benchmark 适配 |
|---|---|
| Rogers 的目标覆盖奖励 | 面向端点对的需求窗口服务潜力奖励 |
| Rogers 的精确固定基数约束 | benchmark 的基数上界 `<= max_added_satellites` |
| Rogers 的全候选集 MILP | 确定性的贪心 MCLP，仅小规模测试实例使用有界 MILP |
| Gerard 的 TEG 链路激活 | `ground_link` 与 `inter_satellite_link` 区间动作 |
| Gerard 的全时域 MILP | 有界的逐采样点 MILP，配路由感知回退 |
| Gerard 的路由表与转发 | 不提交；路由与分配由 benchmark 验证器负责 |
| 光学重新指向延迟 | 不建模，因为 benchmark 未对指向延迟建模 |

## 配置字段

experiments 运行器会把配置目录传给 `solve.sh`。求解器优先读取 `config.yaml`，本地临时使用时回退到 `config.json`。

重要配置项：

| 配置项 | 用途 |
|---|---|
| `mclp_mode` | `auto`、`greedy`、`milp` 或 `none` 候选筛选模式。 |
| `scheduler_mode` | `auto`、`greedy`、`route_aware` 或 `milp` 接触调度模式。 |
| `parallel_mode` | `auto`、`parallel` 或 `sequential` 进程执行模式。 |
| `max_parallel_workers` | 进程池工作进程数上限。 |
| `time_budget_s` | 记录在 `status.json` 中的逐测试实例预算，仅供参考。 |
| `orbit_grid` | 候选库密度。 |
| `mclp_milp_config` | 小规模实例的 MCLP MILP 边界。 |
| `milp_config` | 小规模实例调度器 MILP 的边界与回退选择。 |

## 输出

`solution.json` 包含提交给 benchmark 的 `added_satellites` 与 `actions`。

`status.json` 记录计算资源包络、候选数量、选中的候选、调度器模式、各阶段耗时拆分、并行执行模型、缓存诊断信息和回退原因。

`debug/` 下是生成候选、链路缓存、MCLP 打分、选中轨道与调度器行为的摘要。

## 局限性

- 求解器复现的是方法族，而不是论文中的每一张表格或每一条任务假设。
- 公开测试实例规模过大，无法采用精确的全候选集 Rogers MILP 与 Gerard 全时域 MILP 这两条求解路径。
- 路由感知调度器是面向 benchmark 适配的可扩展回退方案，而不是完整的时间容量 MILP。
- 路由与延迟评分由 benchmark 验证器负责，因此求解器只提交链路激活，不提交路由。
- 更大规模的候选网格仍会带来沉重的轨道传播开销；所报告的配置代表了当前实际可行的最强计算范围。
