[English](../../../../../benchmarks/regional_coverage/README.md) | 中文

# 区域覆盖 Benchmark
<!-- i18n-source-sha256: 75d279355eda113e2f5ef76db53ac3b41b2dae3dc18301a12bd1b1452a12d411 -->

## 问题

对多边形目标区域规划条带观测，在固定的规划任务时域内最大化区域唯一覆盖率。

本 benchmark 建模的是一个紧凑的类 SAR 区域成像问题：

- 真实卫星，配有冻结的 TLE
- 条带几何由验证器掌握，由定时的仅滚转动作推导得到
- 同一颗卫星的再指向限制
- 带光照区充电的电池可行性
- benchmark 自有的细网格覆盖评分

本 benchmark 有意**不**对存储、下行链路、地面站、云层或 SAR 图像形成过程建模。

## 单位约定

所有对外公开的量都使用 SI 单位或度：

| 物理量 | 单位 | 后缀 |
|---|---|---|
| 距离、高度 | 米 | `_m` |
| 面积 | 平方米 | `_m2` |
| 时间、时长 | 秒 | `_s` |
| 角度 | 度 | `_deg` |
| 角速度 | 度/秒 | `_deg_per_s` |
| 角加速度 | 度/秒² | `_deg_per_s2` |
| 能量 | 瓦时 | `_wh` |
| 功率 | 瓦 | `_w` |
| 时间戳 | 带 `Z` 或显式时区偏移的 ISO 8601 | — |

## 数据集结构

```text
dataset/
├── index.json
├── example_solution.json
└── cases/
    └── <split>/
        └── case_0001/
            ├── manifest.json
            ├── satellites.yaml
            ├── regions.geojson
            └── coverage_grid.json
```

当前规范发布包含 5 个测试实例。每个测试实例都是自包含的。验证器读取一个测试实例目录和一份对应的解文件。

数据集级的 `example_solution.json` 是一个可直接运行的冒烟示例，不是基线解。

`dataset/index.json` 中包含子集相对路径 `example_smoke_case`，目前指向 `test/case_0001`。benchmark 自有的构建契约位于 `benchmarks/regional_coverage/splits.yaml`。

## 规范测试实例族

生成器目前产出：

- 5 个规范测试实例
- 72 小时的任务时域
- 每个测试实例 6 至 12 颗卫星
- 当前发布中每个测试实例 2 至 3 个区域
- 每个测试实例 1 或 2 个卫星类别
- 每个测试实例约 5,000 至 20,000 个加权覆盖采样点

当前公开的测试实例使用一组温和的双类别族：

- `sar_narrow`
- `sar_wide`

这些只是 benchmark 层面的抽象，并不意味着本 benchmark 复现了某个具体的在轨任务。

## 测试实例文件格式

### `manifest.json`

测试实例级的元数据与验证器配置：

```json
{
  "case_id": "case_0001",
  "benchmark": "regional_coverage",
  "spec_version": "v1",
  "seed": 20270415,
  "horizon_start": "2025-07-17T00:00:00Z",
  "horizon_end": "2025-07-20T00:00:00Z",
  "time_step_s": 10,
  "coverage_sample_step_s": 5,
  "earth_model": {
    "shape": "wgs84"
  },
  "grid_parameters": {
    "sample_spacing_m": 5000.0
  },
  "scoring": {
    "primary_metric": "coverage_ratio",
    "revisit_bonus_alpha": 0.0,
    "max_actions_total": 64
  }
}
```

`time_step_s` 是对外公开的动作网格。`coverage_sample_step_s` 是验证器在计算条带几何和当前功耗积分网格时使用的采样步长。

### `satellites.yaml`

一个 YAML 序列。每个卫星条目定义：

```yaml
- satellite_id: sat_iceye-x2
  tle_line1: str
  tle_line2: str
  tle_epoch: ISO8601

  sensor:
    min_edge_off_nadir_deg: float
    max_edge_off_nadir_deg: float
    cross_track_fov_deg: float
    min_strip_duration_s: float
    max_strip_duration_s: float

  agility:
    max_roll_rate_deg_per_s: float
    max_roll_acceleration_deg_per_s2: float
    settling_time_s: float

  power:
    battery_capacity_wh: float
    initial_battery_wh: float
    idle_power_w: float
    imaging_power_w: float
    slew_power_w: float
    sunlit_charge_power_w: float
    imaging_duty_limit_s_per_orbit: float | null
```

验证器使用：

- TLE 结合 Brahe 的 SGP4 传播
- GCRF 作为惯性坐标系
- ITRF 作为地固坐标系
- WGS84 用于地球表面求交与大地坐标转换

### `regions.geojson`

RFC 7946 GeoJSON 格式的、便于人工阅读的区域定义。

**注意：** 验证器只读取每个 Polygon 的第一个线性环（`coordinates[0]`）。内环（孔洞）目前被忽略。

每个 feature 包含：

```json
{
  "type": "Feature",
  "properties": {
    "region_id": "region_001",
    "weight": 1.0,
    "min_required_coverage_ratio": 0.25
  },
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[lon, lat], ...]]
  }
}
```

`min_required_coverage_ratio` 是可选的。

### `coverage_grid.json`

由 benchmark 掌握的、供机器读取的评分支撑数据。

当前的规范 schema 是加权采样点：

```json
{
  "grid_version": 1,
  "sample_spacing_m": 5000.0,
  "regions": [
    {
      "region_id": "region_001",
      "total_weight_m2": 123456789.0,
      "samples": [
        {
          "sample_id": "region_001_s000001",
          "longitude_deg": 90.0,
          "latitude_deg": 1.0,
          "weight_m2": 25000000.0
        }
      ]
    }
  ]
}
```

每个采样点恰好归属于一个区域，默认情况下只贡献一次唯一覆盖权重。

## 解格式

对外公开的解是单个 JSON 对象：

```json
{
  "actions": [
    {
      "type": "strip_observation",
      "satellite_id": "sat_iceye-x2",
      "start_time": "2025-07-17T03:31:00Z",
      "duration_s": 20,
      "roll_deg": 20.0
    }
  ]
}
```

公开定义的动作类型只有一种：`"strip_observation"`。

验证器会忽略未知的动作类型，但 benchmark 的使用者应当只提交 `strip_observation` 动作。

解中不得包含：

- 用户自行编写的条带多边形
- 用户自行编写的条带中心线
- 用户自行声称的覆盖情况
- 预计算的可见窗口标识符

## 条带与姿态模型

本 benchmark 使用一个通用的角度条带传感器，配合仅滚转的指向模型。

对于一个动作：

- `roll_deg` 是带中心侧摆角的带符号取值
- `cross_track_fov_deg` 是完整的跨轨角视场

定义：

```text
r = abs(roll_deg)
f = cross_track_fov_deg
theta_inner_deg = r - 0.5 * f
theta_outer_deg = r + 0.5 * f
```

只有满足以下条件时，该动作在传感器意义上才是有效的：

```text
theta_inner_deg >= min_edge_off_nadir_deg
theta_outer_deg <= max_edge_off_nadir_deg
```

验证器在这些边界处施加了 `1e-6` 度的数值容差。

验证器推导条带几何的方式是：在动作时间区间内传播卫星位置，把中心射线、内侧边缘射线和外侧边缘射线与 WGS84 椭球求交，再把这些边缘交点沿时间扫掠成条带区段。

因此，地面幅宽是由轨道几何和姿态推导出来的。benchmark 不使用预先存储的固定幅宽。

## 硬性合法性规则

出现以下任一情况时，验证器都会判定该解非法：

- `satellite_id` 未知
- `start_time` 落在测试实例任务时域之外
- `duration_s <= 0`
- `duration_s` 不是 `time_step_s` 的整数倍
- `start_time` 未对齐到 `time_step_s` 网格
- `duration_s` 超出该卫星传感器的能力范围
- `theta_inner_deg` 或 `theta_outer_deg` 违反了传感器的侧摆角范围
- 条带射线未能与地球相交
- 同一颗卫星上的两个条带观测在时间上重叠
- 同一颗卫星的两次观测之间的间隔小于所需的姿态机动时间加上稳定时间
- 电池状态低于零
- 在 `imaging_duty_limit_s_per_orbit` 存在的情况下超出该限制
- 在区域级 `min_required_coverage_ratio` 存在的情况下未达到该要求

本 benchmark **不**对外暴露预计算的可见窗口。条带的可达性完全由验证器掌握。

## 姿态机动模型

同一颗卫星的再指向采用仓库中的加速-滑行-减速（bang-coast-bang）/梯形最短机动时间模型。

对于同一颗卫星上前后相继的两个动作：

```text
d = abs(current.roll_deg - previous.roll_deg)
omega = max_roll_rate_deg_per_s
alpha = max_roll_acceleration_deg_per_s2
d_tri = omega^2 / alpha

if d <= d_tri:
    t_slew = 2 * sqrt(d / alpha)
else:
    t_slew = d / omega + omega / alpha

t_required_gap = t_slew + settling_time_s
```

本 benchmark 依据指令给定的滚转增量来度量机动，而不是依据被动的星下点轨迹漂移。

## 功耗模型

本 benchmark 对每颗卫星使用单一的电池荷电状态，充电在光照区与地影区之间二元切换，负载按分段恒定处理。

发电：

- 处于光照区时为 `sunlit_charge_power_w`
- 处于地影区时为 `0`

负载：

- `idle_power_w` 持续存在
- 成像期间叠加 `imaging_power_w`
- 在必需的再指向窗口内叠加 `slew_power_w`

当前的实现规则：

- 在验证器掌握、供规范测试实例使用的 5 秒网格上做确定性定步长积分
- 光照状态在每个区间的中点处判定

离散更新：

```text
E_next = E_curr + (P_charge_w - P_load_w) * delta_t_s / 3600
```

能量会被截断到上限 `E_max`，但负值**不会**被钳位到零。只要电池状态在任何时刻变为负值，该解即为非法。

## 覆盖评分

覆盖评分在 `coverage_grid.json` 中 benchmark 自有的细网格上进行，而不是在精确的多边形并集上进行。

对于每个权重为 `w_i`、被覆盖计数为 `c_i` 的采样点 `i`：

```text
u_i = 1 if c_i >= 1 else 0
```

按区域统计的覆盖率：

```text
coverage_ratio_r = sum_i(w_i * u_i) / sum_i(w_i)
```

全局覆盖率：

```text
coverage_ratio =
    sum_r(region_weight_r * coverage_ratio_r) / sum_r(region_weight_r)
```

默认的重访处理方式：

- 首次覆盖获得全部分数
- 重复覆盖不获得额外分数
- `revisit_bonus_alpha` 在 schema 中存在，但在规范发布中取值为 `0.0`

## 验证器输出

验证器返回一份 JSON 报告，其顶层结构如下：

```json
{
  "valid": true,
  "metrics": {
    "coverage_ratio": 0.0,
    "weighted_coverage_ratio": 0.0,
    "num_actions": 0,
    "min_battery_wh": 0.0,
    "region_coverages": {}
  },
  "violations": [],
  "diagnostics": {}
}
```

重要的指标字段：

- `coverage_ratio`
- `weighted_coverage_ratio`——所有区域中已覆盖网格面积权重之和除以网格面积权重之和
- `num_actions`——统计每一个解析出的 `strip_observation` 动作，包括因违反调度约束而被拒绝的动作
- `min_battery_wh`
- `region_coverages`——按区域给出的覆盖诊断细节，其中包含原始的已覆盖面积等效权重

主要的排序优先级为：

1. `valid = true`
2. 最大化 `coverage_ratio`
3. 最大化 `weighted_coverage_ratio`
4. 最小化 `num_actions`
5. 最大化 `min_battery_wh`

## 有意排除在范围外的内容

- 存储
- 下行链路与地面站
- 云层覆盖与日照门控
- 辐射定标与 SAR 图像形成
- 热控子模型
- 反作用轮动量卸载
- 求解器侧的可见窗口

## 运行工具

### 验证器

```bash
uv run python benchmarks/regional_coverage/verifier.py \
    benchmarks/regional_coverage/dataset/cases/test/case_0001 \
    benchmarks/regional_coverage/dataset/example_solution.json
```

合法时验证器以退出码 `0` 结束，非法时为 `1`。

### 生成器

```bash
# Rebuild the canonical dataset in-place from the committed split contract.
uv run python -m benchmarks.regional_coverage.generator.run \
    benchmarks/regional_coverage/splits.yaml

# Write the dataset to another directory.
uv run python -m benchmarks.regional_coverage.generator.run \
    benchmarks/regional_coverage/splits.yaml \
    --output-dir /tmp/regional_coverage_dataset
```

仓库中提交的 `splits.yaml` 为内置的真实 TLE 子集标注了一个受精确支持的 CelesTrak 快照 epoch 标签。它定义了 5 个测试实例的 `test` 子集，以及 10 个测试实例的 `train` 子集，后者沿用测试子集的生成控制项但使用不同的随机种子。由于本 benchmark 不随包分发其他缓存的 TLE 快照，生成器会拒绝任何其他 epoch。

运行规范生成器会就地重写 `benchmarks/regional_coverage/dataset/`，其中包括：

- `dataset/cases/test/`
- `dataset/cases/train/`
- `dataset/index.json`

### 可视化工具

可视化工具用于检查 benchmark 以及编写 fixture。

```bash
# 2D case overview PNG.
uv run python -m benchmarks.regional_coverage.visualizer.run overview \
    --case-dir benchmarks/regional_coverage/dataset/cases/test/case_0001

# Solution inspection bundle with 3D strip geometry HTML and region-scale PNGs.
uv run python -m benchmarks.regional_coverage.visualizer.run inspect \
    --case-dir benchmarks/regional_coverage/dataset/cases/test/case_0001 \
    --solution-path path/to/solution.json
```

概览图会渲染少量具有代表性的卫星星下点轨迹，作为弱化的上下文图层，这样在多卫星的测试实例中区域几何依然清晰可读。使用 `--max-ground-tracks` 可以增加、减少或隐藏该图层。生成的可视化产物写在 `benchmarks/regional_coverage/visualizer/plots/` 下。