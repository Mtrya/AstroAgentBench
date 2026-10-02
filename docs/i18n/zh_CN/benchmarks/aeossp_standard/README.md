[English](../../../../../benchmarks/aeossp_standard/README.md) | 中文

# AEOSSP Standard Benchmark
<!-- i18n-source-sha256: 5042dd5ea46beb5907774f9d362920a65b952f8badc627fa50f84b473d2c680d -->

## 状态

本 benchmark 已实现，是仓库中标准的已完成 AEOSSP benchmark。

它替代了此前公开的 `aeosbench` benchmark 表面层。

## 问题摘要

`aeossp_standard` 是一个面向规划的敏捷地球观测卫星调度 benchmark。

对于每个测试实例，太空规划智能体（space agent）接收：

- 固定的 12 小时规划任务时域
- 由冻结 TLE 及 benchmark 自定义子系统参数所定义的固定真实地球观测卫星星座
- 一组带时间窗口的点成像任务
- 硬观测、电池和姿态机动约束

太空规划智能体必须返回：

- 一个基于事件的 `observation` 动作调度表

本 benchmark 侧重于调度，而非星座设计。求解器不可新增卫星、选取轨道或重新设计编队，也不提交低层姿态指令。

不在范围内：

- 星座设计
- 下行链路与数据交付规划
- 星上存储建模
- 云层覆盖与随机天气
- 详细辐射测量或图像质量评分
- 完整刚体姿态传播

## 数据集布局

规范数据集位于：

```text
dataset/
├── example_solution.json
├── index.json
└── cases/
    └── <split>/
        └── <case_id>/
            ├── mission.yaml
            ├── satellites.yaml
            └── tasks.yaml
```

`dataset/example_solution.json` 是一个与普通提交 schema 相同的真实解对象。`dataset/index.json` 记录测试实例元数据以及通过子集相对路径 `example_smoke_case` 配对的冒烟案例，benchmark 自有的构建契约位于 `benchmarks/aeossp_standard/splits.yaml`。

## 测试实例输入

每个测试实例目录恰好包含三个机器可读文件。

### `mission.yaml`

`mission.yaml` 定义规划任务时域、公共时间网格、传播模型和评分元数据。

重要字段：

- `case_id`
- `horizon_start`
- `horizon_end`
- `action_time_step_s`
- `geometry_sample_step_s`
- `resource_sample_step_s`
- `propagation`
  - `model`
  - `frame_inertial`
  - `frame_fixed`
  - `earth_shape`
- `scoring`
  - `ranking_order`
  - `reported_metrics`

所有时间戳均为 UTC 的 ISO 8601 格式。任务时域必须能被动作步长、几何步长和资源步长整除。

### `satellites.yaml`

`satellites.yaml` 包含该测试实例的固定星座。

每颗卫星条目包括：

- `satellite_id`
- `norad_catalog_id`
- `tle_line1`
- `tle_line2`
- `sensor`
  - `sensor_type`
- `attitude_model`
  - `max_slew_velocity_deg_per_s`
  - `max_slew_acceleration_deg_per_s2`
  - `settling_time_s`
  - `max_off_nadir_deg`
- `resource_model`
  - `battery_capacity_wh`
  - `initial_battery_wh`
  - `idle_power_w`
  - `imaging_power_w`
  - `slew_power_w`
  - `sunlit_charge_power_w`

公共数据集使用 benchmark 自有的可见光和红外传感器模板。

### `tasks.yaml`

`tasks.yaml` 包含任务时域内的成像请求。

每个任务包括：

- `task_id`
- `name`
- `latitude_deg`
- `longitude_deg`
- `altitude_m`
- `release_time`
- `due_time`
- `required_duration_s`
- `required_sensor_type`
- `weight`

冻结任务语义：

- `release_time`、`due_time` 和 `required_duration_s` 必须与公共动作网格对齐
- 任务是二元完成的，不能部分计分
- 目标必须在其时间窗口内被连续观测恰好 `required_duration_s`

## 解契约

有效提交是一个 JSON 对象，包含一个顶层数组：

- `actions`

每个动作格式为：

```json
{
  "type": "observation",
  "satellite_id": "sat_001",
  "task_id": "task_0001",
  "start_time": "2025-07-17T04:12:00Z",
  "end_time": "2025-07-17T04:12:20Z"
}
```

支持的动作类型：

- `observation`

求解器不提交：

- 可见性声明
- 功耗声明
- 姿态机动区间
- 姿态轨迹
- 完成声明

这些都由验证器确定。

## 有效性规则

如果任何硬约束被违反，验证器将拒绝该解，包括：

- 测试实例或解结构格式错误
- 测试实例内重复的任务或卫星标识符
- 解中引用了未知的卫星或任务
- 不支持的动作类型
- 零时长、偏离网格或超出任务时域的动作
- 超出任务窗口的动作
- 动作时长与 `required_duration_s` 不匹配
- 传感器类型不匹配
- 几何非法的观测
- 同一卫星的观测重叠
- 姿态机动加稳定间隙不足
- 电池耗尽至零以下

任何硬违规都会使整个解非法。非法解返回：

- `valid = false`
- 归零指标：
  - `CR = 0`
  - `WCR = 0`
  - `TAT = null`
  - `PC = 0`

## 几何、姿态与功耗语义

轨道传播和观测几何由验证器计算。

传播模型：

- 基于测试实例 TLE 的 Brahe `SGPPropagator`
- GCRF 惯性坐标系
- ITRF 地固坐标系
- WGS84 地球模型
- 静态零值 EOP 提供器，用于确定性离线验证

观测几何：

- 在公共几何网格点和动作边界上检查可见性
- 目标必须在动作区间内保持连续可见
- 所需侧摆角必须始终处于 `attitude_model.max_off_nadir_deg` 范围内

姿态机动模型：

- 求解器仅调度观测区间
- 验证器从几何中导出名义指向策略
- 姿态机动窗口在较晚的观测之前立即预留
- 姿态机动可行性使用标量加速-滑行-减速（bang-coast-bang）模型，参数包括：
  - `max_slew_velocity_deg_per_s`
  - `max_slew_acceleration_deg_per_s2`
  - `settling_time_s`
- 公共解可视化工具渲染的示意图侧摆曲线：
  - 在观测期间跟踪瞬时侧摆角
  - 在预留姿态机动窗口期间使用相同的标量 bang-coast-bang 姿态机动形状
  - 在连续观测之间保持前一次观测的终端指向
  - 在第一次预留姿态机动之前保持对地指向

功耗模型：

- 电池在整个任务时域上通过显式积分段进行模拟
- 总电力负载为：
  - `idle_power_w`
  - 观测期间加上 `imaging_power_w`
  - 姿态机动窗口期间加上 `slew_power_w`
- 卫星处于光照区时应用太阳能充电
- `PC` 仅报告总电力消耗，不扣除太阳能充电

## 指标与排序

验证器报告：

- `CR`
- `WCR`
- `TAT`
- `PC`

指标含义：

- `CR`：已完成任务的比例
- `WCR`：已完成权重的比例
- `TAT`：已完成任务的平均 `(completion_time - release_time)`，若无任何任务完成则为 `null`
- `PC`：整个任务时域内的总耗电瓦时数

任务完成语义：

- 如果至少有一次有效观测满足任务，则该任务完成
- 重复的有效观测不会获得额外加分
- 最早的有效完成时间决定 `TAT`

预期排序优先级：

1. 合法解优于非法解
2. 最大化 `WCR`
3. 最大化 `CR`
4. 最小化 `TAT`
5. 最小化 `PC`

## 公共入口点

数据集生成器：

```bash
uv run python -m benchmarks.aeossp_standard.generator.run \
  benchmarks/aeossp_standard/splits.yaml
```

对于更大的子集族或 CI 重新生成，可以传入 `--jobs N` 以并行生成互相独立的测试实例，同时保持测试实例种子和索引顺序的确定性。

验证器：

```bash
uv run python -m benchmarks.aeossp_standard.verifier.run \
  benchmarks/aeossp_standard/dataset/cases/test/case_0001 \
  benchmarks/aeossp_standard/dataset/example_solution.json
```

测试实例可视化工具：

```bash
uv run python -m benchmarks.aeossp_standard.visualizer.run case \
  --case-dir benchmarks/aeossp_standard/dataset/cases/test/case_0001
```

解可视化工具：

```bash
uv run python -m benchmarks.aeossp_standard.visualizer.run solution \
  --case-dir benchmarks/aeossp_standard/dataset/cases/test/case_0001 \
  --solution-path benchmarks/aeossp_standard/dataset/example_solution.json
```

可视化产物解读：

- 测试实例的 `access_off_nadir_curves.png` 仅反映几何：
  - 它展示有代表性的可见性与侧摆角需求曲线
  - 它并不是名义姿态策略图
- 解的 `attitude_curves.png` 虽是示意图，但与验证器一致：
  - 它由验证器所依据的观测区间与姿态机动窗口导出
  - 它采用 benchmark 的标量 bang-coast-bang 姿态机动轮廓，而非线性角度插值

规范生成器需要提交仓库中的 `splits.yaml` 路径，并在 `dataset/cases/` 和 `dataset/index.json` 下复现 benchmark 自有的数据集产物。

## 生成器与规范数据集

生成器依据 benchmark 自有规则构建测试实例，而不是依靠手写的测试实例清单。

当前子集划分：

- `test_easy` 是压力较低的评测子集
- `test` 是主要的中等难度评测子集
- `test_horizon_2022` 沿用同等的中等难度控制参数，并使用内置的 2022 年历史 TLE 缓存，使任务时域落在 2022 年 4 月
- `test_hard` 是压力更高的评测子集；它采用更多卫星、更多任务、更长时长、更紧时间窗口和更低的城市目标占比，以保证规范生成在单核 CI 运行器上仍有界
- `train` 与 `test` 的控制参数一致，共 `10` 个测试实例

当前规范中等难度族：

- 5 个规范测试实例
- 每个测试实例 20 至 28 颗卫星
- 每个测试实例 1600 至 2000 个任务
- 可见光与红外任务需求混合
- 城市与陆地背景目标来源混合
- 任务窗口依据真实可见机会导出

完整的规范子集族共包含 30 个生成的测试实例。它被设计为在单个 CPU 核上即可从容地重新生成，`--jobs N` 仅作为本地可选的加速手段。

公共源数据工作流：

- 内置的 CelesTrak 地球资源 TLE 快照（`generator/cached_tles.py` 与 `generator/cached_tles_2022.py`）
- GeoNames 城市数据
- Natural Earth 陆地多边形

规范生成只使用随仓库分发的输入：生成器内部已归一化的 GeoNames 城市快照和 TLE 星表，以及 `sources/` 中精简后的 Natural Earth 陆地几何。源数据清单记录了数据溯源、归一化过程和 SHA-256 校验和，并在暂存前完成校验。干净环境下重新生成无需网络访问。

操作标志 `--download-dir`、`--output-dir` 和 `--force-download` 控制暂存目录与输出目录的位置。重新暂存总是还原已固定的输入，即使本地存在过期缓存也是如此；它从不刷新上游数据。`splits.yaml` 仍然是任务时序、卫星筛选、子系统模板和任务采样的构建契约。

## 测试与 Fixtures

验证器由以下聚焦的 fixture 驱动测试锁定：

- `tests/fixtures/aeossp_standard/`
- `tests/benchmarks/test_aeossp_standard_verifier.py`

这些 fixtures 覆盖：

- 精确的合法解评分
- 零完成语义
- 重复观测无额外加分语义
- 传感器不匹配
- 可见性导致的非法
- 重叠导致的非法
- 姿态机动间隙导致的非法
- 电池导致的非法

## 谱系

`aeossp_standard` 参考了标准 AEOSSP 表述以及此前的 benchmark 工作（如 AEOS-Bench），但它并不是任何单一遗留 benchmark 或仿真器栈的复现。