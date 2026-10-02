[English](../../../../../benchmarks/revisit_constellation/README.md) | 中文

# 重访星座 benchmark
<!-- i18n-source-sha256: 7048a155b17aef39d90e095b9463113eb6f4d457ce93fc3a7a257b3e925f7934 -->

## 状态

本 benchmark 已实现，是仓库中标准的已完成重访聚焦星座设计 benchmark。

它替代了此前的 `revisit_optimization` benchmark。

## 问题摘要

设计一个地球观测星座及其运行调度表，使任务时域内的目标重访间隔尽可能小。

对于每个测试实例，太空规划智能体（space agent）会收到一个测试实例，其中描述了：

- 卫星模型
- 目标位置
- 硬任务与轨道约束
- 任务起止时间
- 预期重访间隔阈值

太空规划智能体必须返回：

- 一个星座定义
- 一串已调度的动作

本 benchmark 把两个决策合并进同一项任务：

1. 星座架构设计
2. 任务调度

## 预期的 benchmark 范围

架构设计部分指的是确定卫星在任务起始时刻的初始状态。从高层次看，求解器决定部署多少颗卫星（不超过该测试实例的上限），并指定每颗卫星在 GCRF 坐标系下的初始状态。

调度部分指的是为该星座在整个任务时域内生成一个可行的动作序列。

发射设计、发射成本和部署操作不在范围内。本 benchmark 假设所提出的卫星在任务起始时刻就已经处于各自的初始状态。

## 测试实例输入

每个规范测试实例恰好包含两个机器可读文件：

- `assets.json`
- `mission.json`

### `assets.json`

`assets.json` 包含该测试实例的共享卫星模型和卫星数量上限。

- `satellite_model`
  - `model_name`
  - `sensor`
    - `max_off_nadir_angle_deg`
    - `max_range_m`
    - `obs_discharge_rate_w`
  - `resource_model`
    - `battery_capacity_wh`
    - `initial_battery_wh`
    - `idle_discharge_rate_w`
    - `sunlight_charge_rate_w`
  - `attitude_model`
    - `max_slew_velocity_deg_per_sec`
    - `max_slew_acceleration_deg_per_sec2`
    - `settling_time_sec`
    - `maneuver_discharge_rate_w`
  - `min_altitude_m`
  - `max_altitude_m`
- `max_num_satellites`

### `mission.json`

`mission.json` 包含任务时域以及针对各目标的重访要求：

- `horizon_start`
- `horizon_end`
- `targets[]`
  - `id`
  - `name`
  - `latitude_deg`
  - `longitude_deg`
  - `altitude_m`
  - `expected_revisit_period_hours`（以小时为单位的预期重访周期）
  - `min_elevation_deg`
  - `max_slant_range_m`
  - `min_duration_sec`

本 benchmark 初始设定的任务时域为 `48h`。

## 解契约

一个合法解是包含两个顶层数组的单一 JSON 文档：

- `satellites`
- `actions`

### `satellites`

每个卫星条目描述任务起始时刻由求解器选定的一颗卫星：

- `satellite_id`
- `x_m`
- `y_m`
- `z_m`
- `vx_m_s`
- `vy_m_s`
- `vz_m_s`

所有状态都按 SI 单位的 GCRF 笛卡尔状态来解释。

### `actions`

动作列表给出了所提出星座的任务调度表。
支持的动作类型为：

- `observation`

每个动作包含：

- `action_type`
- `satellite_id`
- `start`
- `end`

观测动作还包含：

- `target_id`

## 合法性规则

一旦违反约束，解应立即判为非法。换句话说，指标只对满足全部硬约束的解才有意义。

出现下列任何情况时，验证器都应拒绝该解：

- 解的结构格式有误
- 卫星数量超过该测试实例允许的上限
- 卫星初始状态违反轨道约束
- 观测几何不可行
- 违反功耗约束
- 动作时序前后不一致
- 动作时序相互重叠
- 引用了不存在的卫星或目标

随着 schema 逐渐明确，还可能加入额外的硬性合法性检查。

## 指标与排序

本 benchmark 有意不再保留原有的映射覆盖分支。
新 benchmark 完全由重访指标驱动。

验证器对合法解报告以下指标：

- `capped_max_revisit_gap_hours`：先对每个目标取最大重访间隔，并以该目标的预期重访周期为下限截断，再对各目标取均值
- `num_satellites`
- `target_gap_summary`：逐目标的明细，包含 `expected_revisit_period_hours`、`max_revisit_gap_hours` 和 `observation_count`

预期的排序逻辑是：

1. 合法解优于非法解。
2. 优先使 `capped_max_revisit_gap_hours` 最小。
3. 在此基础上使 `num_satellites` 最小。

## 重访指标解读

重访表现差只意味着得分低，并不会自动导致解被判为非法。

成功的观测用其中点时刻表示。重访间隔把任务开始和任务结束也作为边界时刻计算在内：

- 零次成功观测：重访间隔就是整个任务时域
- 一次成功观测：间隔为开始到观测、以及观测到结束
- 多次成功观测：间隔在相邻两次观测的中点之间计算，并加上任务两端的边界

## 仿真场景

本节说明验证器所使用的物理模型与资源模型。

### 轨道传播

卫星状态使用 `brahe.NumericalOrbitPropagator` 传播：

- **力学模型**：仅含 J2 项的引力（`brahe` 中的 `spherical_harmonic(2, 0)`）
- **坐标系**：传播用 GCRF/ECI，几何检查用 ECEF
- **时间系统**：UTC
- **EOP**：全零值的静态 EOP 提供器，以保证验证的确定性并适合离线运行

验证器依据各测试实例的海拔上下限来校验卫星初始状态。初始状态必须构成闭合椭圆轨道（近地点和远地点都落在上下限之内）。

### 可见性计算

观测几何在动作执行期间按 10 秒间隔进行校验：

**目标可见性约束**：
- 高度角高于该目标的最小值（当地 ENU 坐标系）
- 斜距不超过该目标的上限，也不超过传感器的上限
- 侧摆角在传感器的最大侧摆指向限制之内

当前的传感器模型是一个以天底点为中心的指向锥，而不是完整的成像足迹模型。只有当目标的视线与天底方向的夹角始终不超过 `max_off_nadir_angle_deg` 时，该目标才可观测。

所有几何检查都使用传播到采样时刻的瞬时卫星位置。固定 10 秒的采样是在正确性和运行时间之间做的折中，相邻采样点之间的短暂越界可能检测不到。

### 星上资源

资源统计在离散时间点上模拟电池状态：

**功耗模型**：
- 用 `brahe` 的地影计算判定是否处于光照区
- 处于光照区时按 `sunlight_charge_rate_w` 充电
- 放电由以下几项构成：
  - 待机：`idle_discharge_rate_w`
  - 观测：额外加上 `obs_discharge_rate_w`
  - 机动：在姿态机动/稳定窗口期间额外加上 `maneuver_discharge_rate_w`

资源检查在动作边界、机动窗口边界以及 30 秒间隔处进行。电池电量会被截断到容量上限，只有电量跌破零才会使解非法。

### 姿态与机动窗口

在相邻两次观测之间，验证器按 bang-coast-bang（加速-滑行-减速）机动轮廓计算所需的姿态机动时间：

- 最大姿态机动速度和加速度限值取自 `attitude_model`
- 姿态机动完成后再加上稳定时间
- 机动窗口不得与任何其他动作重叠
- 姿态机动角度按观测中点时刻的目标向量计算

验证器并不检查观测过程本身的三轴指向，只检查几何条件是否允许获取目标，以及相邻目标之间是否有足够的时间完成姿态机动。

## 验证器输出

验证器返回一个 JSON 对象，其中包含：

- `is_valid`
- `metrics`
- `errors`
- `warnings`

命令行入口：

```bash
uv run python -m benchmarks.revisit_constellation.verifier.run <case_dir> <solution.json>
```

## 可视化工具的使用

可选的可视化工具会输出面向人阅读的 PNG 图。

渲染某个测试实例的目标分布总览图：

```bash
uv run python -m benchmarks.revisit_constellation.visualizer.run overview \
  --case-dir benchmarks/revisit_constellation/dataset/cases/test/case_0001
```

渲染与解相关、逐目标的动作快照：

```bash
uv run python -m benchmarks.revisit_constellation.visualizer.run solution \
  --case-dir benchmarks/revisit_constellation/dataset/cases/test/case_0001 \
  --solution-path benchmarks/revisit_constellation/dataset/example_solution.json
```

`overview` 命令输出 `overview.png`。`solution` 命令为每个渲染出来的被观测目标输出一页 PNG，每一页展示数量有限的若干观测快照，图中包含与目标相关的卫星星下点轨迹，并高亮当前正在观测的那颗卫星。

## 规范的 benchmark 结构

仓库结构如下：

```text
benchmarks/revisit_constellation/
├── dataset/
│   ├── README.md
│   ├── index.json
│   ├── example_solution.json
│   └── cases/
│       └── <split>/<case_id>/{assets.json,mission.json}
├── splits.yaml
├── generator/
│   ├── __init__.py
│   ├── build.py
│   ├── sources.py
│   └── run.py
├── verifier/
│   ├── __init__.py
│   ├── models.py
│   ├── io.py
│   ├── engine.py
│   └── run.py
└── README.md
```

配套的测试侧产物位于：

```text
tests/fixtures/
tests/benchmarks/
```

## 规范数据集

已提交的数据集位于 `dataset/cases/<split>/` 下，数据集级别的元数据记录在 `dataset/index.json` 中。规范的子集划分策略由本 benchmark 自己规定：

- `train`：10 个公开生成的开发用测试实例，即 `case_0001` 到 `case_0010`。
- `test`：5 个留出用于评测的测试实例，即 `case_0001` 到 `case_0005`。

各子集的随机种子和测试实例生成参数声明在 `splits.yaml` 中；train 与 test 两个子集使用互不相交的种子和目标选取偏移量。
目标从有文档说明的世界城市数据源中抽取，以人口规模的对数值为主要信号，以地理分布作为次要的平衡项。已提交的 train 和 test 测试实例共用这一策略，包括相同的最小目标间隔设定，同时保留逐测试实例的确定性种子。

规范生成器的入口脚本为：

```bash
uv run python -m benchmarks.revisit_constellation.generator.run \
  benchmarks/revisit_constellation/splits.yaml
```

规范生成使用 `sources/world_cities.csv` 中经过规范化的世界城市快照，其中保留了全部原始行，只取其中被实际使用的五列。`sources/manifest.json` 记录了上游数据溯源信息、规范化过程，以及在入库前校验过的 SHA-256 哈希。整个过程不需要网络访问。`--download-dir` 和 `--force-download` 只是把固定版本的数据重新入库，而不会去下载更新的 Kaggle 版本；测试实例的构建参数仍由 `splits.yaml` 定义。