[English](../../../../../benchmarks/relay_constellation/README.md) | 中文

# 中继星座 benchmark
<!-- i18n-source-sha256: ec0441ba6e4e94e24b21fa9f118ff01fd35d849998db6523d5fa08b87c705f31 -->

## 状态

本 benchmark 已实现，是仓库中标准的已完成中继网络增强 benchmark。

它替代了此前 `latency_optimization` benchmark 的问题设定。

## 问题摘要

`relay_constellation` 是一个面向中继服务的部分星座设计 benchmark。

每个测试实例都会向太空规划智能体（space agent）提供：

- 固定的 96 小时规划任务时域
- 以笛卡尔初始状态表达的不可变 MEO 骨干星座（backbone）
- 固定的地面通信端点
- 端点对之间有通信需求的窗口
- 该测试实例特有的轨道与通信约束

太空规划智能体必须返回：

- 一组有数量上限的新增中继卫星
- 一份通过激活通信链路来实现连通的任务时域内的接触计划

本 benchmark 关注的是对既有星座的增强，而不是从零重新设计。既有的骨干卫星不可变。预期的增强路线是 LEO 优先：求解器在给定的 MEO 基线之上补充低轨中继卫星，以改善服务、降低延迟。

不在范围内：

- 感知或成像
- 星上功耗或存储建模
- 姿态或天线指向动力学
- 排队与缓冲
- 概率性的链路中断
- 由求解器自行给出的路由结论

## 数据集布局

规范数据集位于：

```text
dataset/
├── example_solution.json
├── index.json
└── cases/
    └── <split>/
        └── <case_id>/
            ├── manifest.json
            ├── network.json
            └── demands.json
```

`dataset/example_solution.json` 是一个真实的解对象，schema 与常规提交完全一致。`dataset/index.json` 记录测试实例元数据，并通过子集相对路径 `example_smoke_case` 给出冒烟测试配对；已提交的子集划分定义位于 `benchmarks/relay_constellation/splits.yaml`。该契约规定了一个包含 5 个测试实例的 `test` 子集，以及一个包含 10 个实例的 `train` 子集，后者沿用 test 的生成控制参数但使用不同的随机种子。

## 测试实例输入

每个测试实例目录恰好包含三个机器可读文件。

### `manifest.json`

`manifest.json` 定义规划任务时域、传播模型、路由步长以及硬性约束。

重要字段：

- `case_id`
- `epoch`
- `horizon_start`
- `horizon_end`
- `routing_step_s`
- `constraints`
  - `max_added_satellites`
  - `min_altitude_m`
  - `max_altitude_m`
  - `max_eccentricity`
  - `min_inclination_deg`
  - `max_inclination_deg`
  - `max_isl_range_m`
  - `max_links_per_satellite`
  - `max_links_per_endpoint`
  - 可选的 `max_ground_range_m`

### `network.json`

`network.json` 包含不可变的骨干星座与地面端点。

生成出的测试实例只发布至少参与一个需求窗口的地面端点；端点 ID 在剪枝后重新编号，以保持紧凑和确定性。

- `backbone_satellites[]`
  - `satellite_id`
  - `x_m`
  - `y_m`
  - `z_m`
  - `vx_m_s`
  - `vy_m_s`
  - `vz_m_s`
- `ground_endpoints[]`
  - `endpoint_id`
  - `latitude_deg`
  - `longitude_deg`
  - `altitude_m`
  - `min_elevation_deg`

所有卫星状态均按测试实例 epoch 时刻的 GCRF 笛卡尔状态解读。

### `demands.json`

`demands.json` 包含有通信需求的窗口。

- `demanded_windows[]`
  - `demand_id`
  - `source_endpoint_id`
  - `destination_endpoint_id`
  - `start_time`
  - `end_time`
  - `weight`

每条记录描述一个端点对的一个需求窗口。

## 解契约

合法提交是一个 JSON 对象，包含两个顶层数组：

- `added_satellites`
- `actions`

### `added_satellites`

每颗新增卫星使用与骨干星座相同的笛卡尔状态约定：

- `satellite_id`
- `x_m`
- `y_m`
- `z_m`
- `vx_m_s`
- `vy_m_s`
- `vz_m_s`

验证器在内部推导轨道属性，并拒绝违反测试实例约束的新增状态。

### `actions`

求解器只提交基于区间的链路激活。支持的动作类型为：

- `ground_link`
- `inter_satellite_link`

共有字段：

- `action_type`
- `start_time`
- `end_time`

`ground_link` 还要求：

- `endpoint_id`
- `satellite_id`

`inter_satellite_link` 还要求：

- `satellite_id_1`
- `satellite_id_2`

求解器不提交端到端路由、延迟声明或需求服务声明。

## 合法性规则

只要违反任何硬约束，验证器就会拒绝该解，包括：

- 测试实例或解的结构格式错误
- 新增卫星 ID 重复或冲突
- 新增卫星数量超出测试实例允许的上限
- 新增轨道超出边界或未被约束
- 引用了未知的端点或卫星
- 不支持的动作类型
- 时长为零、未对齐采样网格或超出任务时域的动作
- 同一条物理链路上的动作相互重叠
- 几何上不可行的地面链路
- 几何上不可行的星间链路
- 在单个采样点上违反 `max_links_per_satellite`
- 在单个采样点上违反 `max_links_per_endpoint`

中间地面端点不能作为路由服务中的合法中转节点。所选路由中只有需求源端点和需求目的端点可以作为地面端点出现。

## 路由、服务与延迟

在需求窗口内的每个验证器采样时刻，如果存在一条从源端点到目的端点的物理可行多跳路径——经由骨干星座以及求解器新增的卫星、且只使用当前处于激活状态的调度链路——该需求即视为被服务。

路由与资源分配由验证器负责：

- 它根据校验通过的动作构建活跃通信图
- 它在边容量为 1 的前提下分配路由
- 它以确定性方式选定路由

单个采样点内部的排序意图为：

1. 最大化被服务需求的总权重
2. 最小化被服务需求的总延迟
3. 以确定性方式打破其余平局

延迟只对被服务的需求采样点计算：

```text
latency_ms = 1000 * total_path_length_m / c
```

未被服务的时间会拉低服务比例，但不会带来合成的或无穷大的延迟。

## 指标与排序

验证器报告：

- `service_fraction`
- `worst_demand_service_fraction`
- `mean_latency_ms`
- `latency_p95_ms`
- `num_added_satellites`
- `num_demanded_windows`
- `num_backbone_satellites`
- `per_demand`
  - `requested_sample_count`
  - `served_sample_count`
  - `service_fraction`
  - `mean_latency_ms`
  - `latency_p95_ms`

预期的排序顺序为：

1. 合法解优于非法解
2. 最大化 `service_fraction`
3. 最大化 `worst_demand_service_fraction`
4. 最小化 `num_added_satellites`
5. 最小化 `mean_latency_ms`
6. 最小化 `latency_p95_ms`

## 验证器输出格式

验证器 CLI 打印的 JSON 对象具有如下顶层结构：

```json
{
  "valid": true,
  "metrics": {
    "service_fraction": 0.0,
    "worst_demand_service_fraction": 0.0,
    "mean_latency_ms": 0.0,
    "latency_p95_ms": 0.0,
    "num_added_satellites": 0,
    "num_demanded_windows": 0,
    "num_backbone_satellites": 0,
    "per_demand": {}
  },
  "violations": [],
  "diagnostics": {}
}
```

- `valid`：所有硬约束均满足时为 `true`，否则为 `false`
- `metrics`：指标与排序一节中记录的评分值
- `violations`：描述硬约束失败情况的、人类可读的字符串列表
- `diagnostics`：用于调试或分析的额外确定性信息

## 传播与链路模型

验证器使用一套固定版本的天体力学软件栈：

- `brahe.NumericalOrbitPropagator`
- 仅含 J2 的引力模型
- 惯性状态使用 GCRF
- 几何检查使用 ITRF/ECEF
- 取零值的静态 EOP 提供器，以保证离线校验的确定性

链路可行性判定：

- 地面链路：
  - 端点仰角高于 `min_elevation_deg`
  - 可选的斜距上限，由 `max_ground_range_m` 给出
- 星间链路：
  - 欧氏距离不超过 `max_isl_range_m`
  - 视线不被地球遮挡

验证器把几何与拓扑分开处理：

- 先校验动作的几何可行性，并记录每个采样点上的边距离
- 再据此构建时序图，并从这些已校验的边计算服务与延迟

## 公共入口点

数据集生成器：

```bash
uv run python -m benchmarks.relay_constellation.generator.run \
  benchmarks/relay_constellation/splits.yaml
```

可选的数据集输出目录覆盖：

```bash
uv run python -m benchmarks.relay_constellation.generator.run \
  benchmarks/relay_constellation/splits.yaml \
  --output-dir /tmp/relay_constellation_dataset
```

验证器：

```bash
uv run python -m benchmarks.relay_constellation.verifier.run \
  benchmarks/relay_constellation/dataset/cases/test/case_0005 \
  benchmarks/relay_constellation/dataset/example_solution.json
```

可视化工具：

```bash
uv run python -m benchmarks.relay_constellation.visualizer.run overview \
  --case-dir benchmarks/relay_constellation/dataset/cases/test/case_0001
```

该命令会为骨干星座输出 `ground_tracks.png`，并为仅考虑几何、不限制链路并发数且不含新增卫星的骨干连通性输出 `baseline_connectivity.png`。

```bash
uv run python -m benchmarks.relay_constellation.visualizer.run solution \
  --case-dir benchmarks/relay_constellation/dataset/cases/test/case_0005 \
  --solution-path benchmarks/relay_constellation/dataset/example_solution.json
```

该命令会为骨干星座加新增卫星输出 `ground_tracks.png`，并为验证器依据所提交动作推导出的连通性输出 `scheduled_connectivity.png`。它还会在 `demand_windows/` 下为每个需求窗口输出一张详细图，图中带路由配色标注以及实际服务所经过的路由节点。

## 测试

运行聚焦于本中继 benchmark 的测试：

```bash
uv run pytest tests/benchmarks/test_relay_constellation_generator.py \
  tests/benchmarks/test_relay_constellation_verifier.py \
  tests/benchmarks/test_relay_constellation_visualizer.py
```