[English](../../../../../../solvers/revisit_constellation/j2_rgt_set_cover/README.md) | 中文

# J2 RGT 集合覆盖求解器
<!-- i18n-source-sha256: 9b48bcad9aee5aa295386c56606c3ada5f77c2a8db8a4309011bd3b6786ad593 -->

本求解器为 `revisit_constellation` 实现了一套带认证环节、考虑 J2 摄动的重复地面轨迹（repeat-ground-track，RGT）集合覆盖方法。它先构建重复地面轨迹轨道模板，把模板展开为面向特定 RAAN 的候选，在全局排行榜上对候选排序；针对排名靠前的候选，用与最终调度相同的 J2 精细模型对候选-目标配对做数值校验；只选取已确认的指派，最后输出符合 benchmark 格式的观测调度表。

本求解器独立自洽，直接读取 benchmark 的测试实例文件，不导入 benchmark、experiment、运行时基座或其他求解器的内部实现。

## 契约

```bash
./setup.sh
./solve.sh <case_dir> [config_dir] [solution_dir]
```

求解器写出以下文件：

- `solution.json`：卫星，以及经过求解器本地验证的观测动作
- `status.json`：闭合搜索、解析覆盖、数值认证、选择、计时和计算量等摘要
- `debug/closure_search.json`：被接受与被拒绝的 J2 RGT 模板记录
- `debug/coverage_summary.json`：面向特定 RAAN 的候选、解析可见性证据，以及解析得到的候选-目标断言
- `debug/certification_summary.json`：候选排行榜、经过数值校验的候选-目标记录，以及拒绝原因
- `debug/selection_summary.json`：被选中的已确认指派、卫星总成本、未覆盖目标，以及预算阻塞项
- `debug/solution_summary.json`：卫星、最终输出的已选指派动作、目标间隔、本地验证，以及重试历史

配置目录通过独立自洽的 `solve.sh` 契约传入。求解器会把 `active_profile`、`compute_envelope` 和 worker 数量记录到 `status.json.compute_profile` 中；官方 benchmark 验证由评测运行器负责。

## 轨道模板与候选

求解器首先构造闭合的 RGT 模板。每个模板固定以下参数：

- `repeat_days`
- `revolutions`
- `inclination_deg`
- 修正后的 `semi_major_axis_m`
- 修正后的初始 `mean_anomaly_deg`
- `eccentricity`
- `argument_of_perigee_deg`
- `repeat_period_sec`

模板的 `raan_deg` 取 `0.0`，仅作为闭合评分所用的标准参考朝向，不参与覆盖决策。

一个覆盖候选是展开后的元组，包含：

- 上述全部模板字段
- 一个具体的 `raan_deg`

RAAN 之所以是候选的组成部分，是因为在任务起始时刻，它使重复地面轨迹相对地球经度发生旋转，从而改变哪些目标值得覆盖。

## J2 RGT 构造

对于每个配置好的整数重复模板 `(revolutions, repeat_days)` 和倾角，求解器用 J2 长期项重复地面轨迹方程解出半长轴，再用求解器本地的 Brouwer-Lyddane 风格 J2 解析传播器，低成本搜索邻近的高度与平近点角修正。

构造器记录 `repeat_days` 个恒星日后的解析闭合。测试会在更大的种子集合上把解析构造器与 Brahe 数值 J2 传播做对比；测试通过后，求解器在搜索路径中直接信任解析构造器。

这不是开普勒式的整数比种子。模板只有在具备 Brouwer-Lyddane J2 闭合证据后才会被接受。

## 覆盖、认证与选择

每个被接受的模板都会在确定性的 RAAN 网格上展开。求解器对每个候选在一个重复周期内采样，并在求解器本地检查与 benchmark 兼容的可见性几何：

- 目标高度角高于 `min_elevation_deg`
- 斜距同时不超过目标和传感器的最大距离
- 侧摆角位于传感器的锥形范围内
- 分组后的可见性证据必须满足目标的 `min_duration_sec`

这一解析过程并非最终的覆盖真值，它产生的是候选-目标断言：候选 X 可能覆盖目标 Y。这些记录只是候选的证据，而非步骤 2 的主要控制结构。

步骤 1 构建全局候选排行榜。排行榜的一条记录是一个候选，带有具体的卫星数量，以及它断言可覆盖的目标集合。优先级在以下几项之间权衡：

- 加权目标数：被更少候选断言覆盖的目标权重更高
- 绝对目标数
- 稀有目标数
- 每颗卫星的价值
- 解析重访间隔、几何裕度、闭合误差，以及确定性的候选 ID 平局裁决规则

步骤 2 按顺序读取排行榜，对排名靠前的候选做候选-目标配对的数值校验：

```yaml
strategy:
  one_day_first: true
  deepen_max_candidates_to_check: 96
rgt_search:
  max_repeat_days: 1
certification:
  max_candidates_to_check: 48
  worker_count: 8
  max_selection_retries: 8
```

默认策略只检查单日重复轨迹候选。它先从更密的 RAAN 网格中取前 48 个候选；只有当第一轮过后仍留下重访间隔偏大或未覆盖的目标时，才会在同一单日网格上用 96 个候选重跑。这样算力就能集中在一日候选上，而不必花在代价更高的两日变体上。

几何与采样默认值继承自 `scheduling`，除非在 `certification` 中被覆盖。只有某条已确认的候选-目标记录中经过精细化的观测机会满足目标重访周期时，该目标才可能被选中。

选择环节把确定性的候选变体视为集合覆盖条目。一个变体就是一个面向特定 RAAN 的候选，带有一个具体的卫星数量；它可以覆盖在该卫星数量下通过数值确认的全部目标记录。选择器对候选变体执行精确的位集分支定界搜索：在卫星预算约束下最大化已确认目标的覆盖数量，剪掉剩余乐观目标增益无法超过当前最优解的状态，最后再应用确定性的平局裁决规则。对于在某个候选上被断言覆盖的目标，所需卫星数量的起点由下式给出：

```text
required_satellites = ceil(candidate_repeat_period_hours / target_revisit_hours)
```

确定性目标函数是：先尽可能多地覆盖已确认目标，再依次最小化卫星数量、已确认覆盖的截断平均间隔、已确认覆盖的最差间隔、所选候选数量，以及变体 ID 的字典序。如果在卫星预算内无法实现全部已确认覆盖，求解器会输出最优的合法部分解，并报告未覆盖的目标。

## 实现与调度

每个被选中的特定 RAAN 候选都按星下点轨迹相位等间隔展开成具体卫星。解析 J2 仍是架构搜索所用的模型，但最终实现使用与 benchmark 验证器相同的 Brahe 数值 J2 力学模型，用于观测机会精细化、姿态机动矢量和求解器本地的采样可见性检查。

最终调度器只处理已指派的目标。对于被指派到某条选中的已确认候选记录的目标，调度器在该目标的观测机会时间线上填充动作，直到满足该目标的重访阈值，并用确定性的间隔剖面规则打破平局。对于只是可见或未被覆盖的目标，它不会安排机会性观测。插入动作之前会检查同卫星重叠以及姿态机动/稳定时间间隔。

如果由于跨目标动作冲突，最终输出无法满足某个被选中的认证条目，求解器会把失败的认证条目或候选变体加入黑名单，重新运行认证选择，并最多重试 `certification.max_selection_retries` 次。如果重试次数耗尽，则输出本地最优的合法部分解，并在 debug/status 产物中报告尚未解决的目标。

求解器本地的验证器会检查 benchmark 形式的引用、时间信息、轨道边界、采样可见性、同卫星重叠、保守的姿态机动间隔，以及按不充电假设评估的保守电池风险。

## 验证

```bash
./test.sh
```
