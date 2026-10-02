[English](../../../../../benchmarks/stereo_imaging/README.md) | 中文

# 立体成像 Benchmark
<!-- i18n-source-sha256: 620cacfb56942ac6a81672a574b47657be1a1547669bd26181046b41b9742f53 -->

## 问题

规划光学卫星观测，在一组地面目标上获取同轨立体或跨卫星（有界）立体与三立体成像影像。

本 benchmark 关注物理上合理的观测几何与再指向代价，不建模摄影测量内部过程、云层覆盖、下行链路、存储或星上功耗。

给定一组真实地球观测卫星（其 TLE 已冻结，传感器与敏捷能力参数精简）以及一组带地理参考的地面目标，agent 必须在固定的任务时域内生成一份带时间戳的观测动作调度表，使立体覆盖范围与成像质量最大化。

## 单位约定

所有对外公开的量均使用 SI 单位或度：

| 物理量 | 单位 | 后缀 |
|---|---|---|
| 距离、半径、高度 | 米 | `_m` |
| 面积 | 平方米 | `_m2` |
| 时间、持续时长 | 秒 | `_s` |
| 速度 | 米/秒 | `_mps` |
| 加速度 | 米/秒² | `_mps2` |
| 角度 | 度 | `_deg` |
| 角速度 | 度/秒 | `_deg_per_s` |
| 角加速度 | 度/秒² | `_deg_per_s2` |
| 时间戳 | 带 `Z` 或显式时区偏移的 ISO 8601（不接受无偏移的时间戳） | — |

## 数据集结构

```text
dataset/
├── index.json              # Case inventory and source provenance
├── example_solution.json   # Minimal actions for verifier smoke testing
└── cases/
    └── <split>/
        └── case_NNNN/
            ├── satellites.yaml
            ├── targets.yaml
            └── mission.yaml
```

每个测试实例都是自包含的。验证器读取一个测试实例目录和一个解文件。

## 测试实例文件格式

### `satellites.yaml`

一个 YAML 序列，每个条目定义一颗卫星：

```yaml
- id: str
  norad_catalog_id: int
  tle_line1: str
  tle_line2: str

  pixel_ifov_deg: float          # angular IFOV of one pixel, cross-track direction
  cross_track_pixels: int        # number of cross-track detector pixels
  max_off_nadir_deg: float       # max tilt from nadir; see combined-angle formula in Hard action constraints

  max_slew_velocity_deg_per_s: float
  max_slew_acceleration_deg_per_s2: float
  settling_time_s: float

  min_obs_duration_s: float
  max_obs_duration_s: float
```

验证器依据角传感器模型推导弹幅几何：

```text
cross_track_fov_deg    = cross_track_pixels * pixel_ifov_deg
half_cross_track_fov_deg = 0.5 * cross_track_fov_deg
strip_half_width_m     ≈ slant_range_m * tan(half_cross_track_fov_deg)
```

### `targets.yaml`

一个 YAML 序列，每个条目定义一个地面目标：

```yaml
- id: str
  latitude_deg: float
  longitude_deg: float
  aoi_radius_m: float       # radius of the area of interest around the target center
  elevation_ref_m: float    # reference terrain elevation

  scene_type: urban_structured | vegetated | rugged | open
```

`scene_type` 是一种规划层面的抽象，用来刻画立体匹配的难度与遮挡特性。硬约束的合法性判定不依赖 `scene_type`，但立体质量得分依赖它。

### `mission.yaml`

```yaml
mission:
  horizon_start: ISO8601
  horizon_end: ISO8601

  allow_cross_satellite_stereo: true
  max_stereo_pair_separation_s: 7200

  validity_thresholds:
    min_overlap_fraction: 0.80
    min_convergence_deg: 5.0
    max_convergence_deg: 45.0
    max_pixel_scale_ratio: 1.5
    min_solar_elevation_deg: 10.0
    near_nadir_anchor_max_off_nadir_deg: 10.0

  quality_model:
    pair_weights:
      geometry: 0.50
      overlap: 0.35
      resolution: 0.15
    tri_stereo_bonus_by_scene:
      urban_structured: 0.12
      rugged: 0.10
      vegetated: 0.08
      open: 0.05
```

## 解格式

agent 提交一个 JSON 文件，其中包含单个测试实例的对象：

**单测试实例：**
```json
{
  "actions": [
    {
      "type": "observation",
      "satellite_id": "sat_pleiades_1a",
      "target_id": "urban_paris_01",
      "start_time": "2026-06-18T10:00:00Z",
      "end_time": "2026-06-18T10:00:08Z",
      "off_nadir_along_deg": 5.0,
      "off_nadir_across_deg": -2.0
    }
  ]
}
```

每个动作用于指定卫星、目标、时间窗口，以及卫星本体坐标系下的视轴指向角。`type` 值不是 `"observation"` 的动作会被验证器忽略。

## 硬动作约束

出现下列任一情况，验证器即判定该解非法：

- `end_time` 未严格晚于 `start_time`
- 观测窗口落在任务时域之外
- 观测时长不在 `[min_obs_duration_s, max_obs_duration_s]` 区间内
- 合成视轴侧摆角超过 `max_off_nadir_deg`。该角度（单位为度）按 $\arctan\sqrt{\tan^2\alpha + \tan^2\beta}$ 计算，其中 $\alpha$ = `off_nadir_along_deg`，$\beta$ = `off_nadir_across_deg`（正切以弧度计算）。这正是验证器由这两个指向角构造视轴射线时所用的、相对天底的几何倾角。
- 视轴射线与地球表面不相交
- 同一卫星上的两次观测在时间上重叠
- 同一卫星上相邻两次观测之间的姿态机动加稳定时间不足
- 引用了未知的 `satellite_id` 或 `target_id`
- 观测未完全落在该目标的某个连续可见区间内（这同时也间接约束了太阳高度角和侧摆角）
- 观测中点时刻目标中心的太阳高度角低于 `min_solar_elevation_deg`

## 验证器输出

验证器返回一份 JSON 报告：

```json
{
  "valid": true,
  "metrics": {
    "valid": true,
    "coverage_ratio": 0.0,
    "normalized_quality": 0.0
  },
  "violations": [],
  "derived_observations": [...],
  "diagnostics": {
    "pair_evaluations": [...],
    "per_target_best_score": {...}
  }
}
```

**`valid`**：是否满足全部硬约束。

**`coverage_ratio`**：至少产出一个有效立体或三立体成像产品的目标所占比例。

**`normalized_quality`**：所有目标上"每个目标最佳立体质量得分"的平均值。

**`derived_observations`**：验证器为每个动作计算的几何量，包括卫星的 ECEF 状态、视轴角、太阳角、太阳方位角、斜距、有效像素尺度以及 `access_interval_id`。

**`diagnostics`**：包含 `pair_evaluations`（每个有效产品的明细，含交会角、B/H 指标、重叠率、像素尺度比、平分线高度与不对称性）和 `per_target_best_score`。

## 立体成像产品定义

### 有效立体对

两次观测 `(i, j)` 满足下列全部条件时，构成一个有效立体对：

1. `target_id` 相同
2. 属于任务允许的立体模式之一：
   - 同星同轨：相同 `satellite_id` 且相同 `access_interval_id`
   - 跨卫星：`satellite_id` 不同，且 `allow_cross_satellite_stereo: true`
3. 两次观测中点的时间间隔 `<= max_stereo_pair_separation_s`
4. AOI 重叠率 `>= min_overlap_fraction`（默认 0.80）
5. 交会角满足 `min_convergence_deg <= gamma <= max_convergence_deg`（默认 5–45 度）
6. 像素尺度比满足 `max(s_i, s_j) / min(s_i, s_j) <= max_pixel_scale_ratio`（默认 1.5）
7. 满足全部动作级硬约束

这里的时间约束是一个时长上限，而不是 UTC 日期边界规则。例如，以 23:59 和 00:01 为中心的两次观测，只要满足 `max_stereo_pair_separation_s` 和其他成对规则，同样可以构成有效产品。

### 有效三立体成像集

三次观测满足下列条件时，构成一个有效三立体成像集：

1. 三次观测的 `target_id` 相同
2. 三个组成对均满足任务级的同星或跨卫星模式规则，以及有界时间约束
3. 公共 AOI 重叠率 `>= min_overlap_fraction`
4. 三个组成对中至少有两个是有效立体对
5. 其中一次观测满足 `boresight_off_nadir_deg <= near_nadir_anchor_max_off_nadir_deg`（近天底锚点）

## 质量模型

### 对质量

对有效立体对：

```
Q_pair = 0.50 * Q_geom + 0.35 * Q_overlap + 0.15 * Q_res
```

其中：

```
Q_overlap = min(1, overlap_fraction / 0.95)
Q_res     = max(0, 1 - (pixel_scale_ratio - 1) / 0.5)
```

`Q_geom` 取决于场景类型所偏好的交会角区间：

| `scene_type` | 偏好区间 |
|---|---|
| `urban_structured` | 8–18 deg |
| `vegetated` | 8–14 deg |
| `rugged` | 10–20 deg |
| `open` | 15–25 deg |

落在区间内部及其边界上时 `Q_geom = 1.0`，区间之外线性下降至 `0.0`。这些是规划用的启发式规则，并非普适的摄影测量结论。

### 三立体成像质量

```
Q_tri = min(1, max(valid_pair_qualities) + beta(scene_type) * R)
```

`R` 是一项有上限的冗余与锚点加成。`beta` 取值来自 `mission.yaml` 中的 `tri_stereo_bonus_by_scene`。

### 单目标得分

每个目标的得分，取覆盖该目标的全部有效立体与三立体成像产品中的最大质量。

## 主要排序

解先按合法性排序，再按覆盖范围排序，最后按质量排序：

1. `valid = true`
2. 最大化 `coverage_ratio`
3. 最大化 `normalized_quality`

## 观测几何模型

验证器采用 SGP4 风格的传播器，从冻结的 TLE 推演卫星轨道。

**可见区间**：目标中心位于 `max_off_nadir_deg` 范围内、且目标处太阳高度角不低于 `min_solar_elevation_deg` 的极大时间窗口。两次观测落在同一个连续可见窗口内时，它们具有相同的 `access_interval_id`。

**有效像素尺度**：

```
effective_pixel_scale_m ≈ slant_range_m * pixel_ifov_deg * (pi / 180)
```

并对离轴投影施加局部正割修正。

**成像足迹**：在局部切平面近似下建模为推扫条带。每个采样点处条带的半宽为 `slant_range_m * tan(radians(half_cross_track_fov_deg))`。

**重叠**：在圆形 AOI 内通过蒙特卡洛采样估计。

## 有意排除在范围之外的内容

- 云层与天气建模
- 下行链路、地面站、接触窗口
- 星上存储与功耗核算
- 时间基线无上界的立体成像产品
- 密集图像匹配的内部实现
- 光束法平差
- 精细的地形遮挡与坡度物理

## 运行工具

### 验证器

```bash
uv run python -m benchmarks.stereo_imaging.verifier.run \
    benchmarks/stereo_imaging/dataset/cases/test/case_0001 \
    path/to/solution.json

# Compact output (valid flag, metrics, violations only):
uv run python -m benchmarks.stereo_imaging.verifier.run \
    benchmarks/stereo_imaging/dataset/cases/test/case_0001 \
    path/to/solution.json \
    --compact
```

解合法时验证器以退出码 `0` 结束，非法时为 `1`。

### 生成器

```bash
# Re-generate the canonical dataset from the committed split contract.
uv run python -m benchmarks.stereo_imaging.generator.run \
    benchmarks/stereo_imaging/splits.yaml

# Write the dataset to another directory.
uv run python -m benchmarks.stereo_imaging.generator.run \
    benchmarks/stereo_imaging/splits.yaml \
    --output-dir /tmp/stereo_imaging_dataset

# Stage pinned runtime sources only (operational mode; skips dataset emission):
uv run python -m benchmarks.stereo_imaging.generator.run \
    benchmarks/stereo_imaging/splits.yaml \
    --sources-only

# Restage the pinned world-city snapshot:
uv run python -m benchmarks.stereo_imaging.generator.run \
    benchmarks/stereo_imaging/splits.yaml \
    --force-download
```

规范生成器把测试实例写入 `dataset/cases/test/` 和 `dataset/cases/train/`，随后更新 `dataset/index.json`。运行时数据源暂存到 `dataset/source_data/` 下；CelesTrak 的 TLE 行与世界城市输入都是内置快照（分别来自 `generator/satellite_catalog.py` 和 `sources/world_cities.csv`，后者由 Kaggle 数据集 `juanmah/world-cities` 第 8 版规范化而来），因此规范的重建过程无需访问网络。

`splits.yaml` 携带本 benchmark 自有的构建参数，以及内置真实 TLE 子集所对应的确切 CelesTrak 快照 epoch 标签。它定义了一个 5 实例的 `test` 子集和一个 10 实例的 `train` 子集，后者沿用测试集的生成控制项但使用不同的随机种子。卫星 TLE 行和传感器/敏捷能力配置位于 `generator/satellite_catalog.py`，因此 split 文件只需聚焦于实例数量、任务策略和采样参数。规范任务时域锚定在该缓存快照上；由于本 benchmark 不提供其他缓存 TLE 快照，生成器会拒绝任何其他 epoch。

`sources/world_cities.csv` 中的规范化世界城市快照保留了全部原始行以及被使用的五列。`sources/manifest.json` 记录了数据溯源、规范化过程及其经校验的 SHA-256 哈希。规范的 index 与数据源清单都指明生成器所消费的那份规范化输入。加上既有的 TLE 表与查询表，这使得规范生成完全独立于在线下载。

`--sources-only`、`--download-dir` 和 `--force-download` 用于控制暂存行为：它们始终使用固定（pinned）的输入，并覆盖过期的缓存数据；既不刷新上游数据源，也不改变规范的数据集构建契约。

### 可视化工具

```bash
# Case overview (ground tracks and target scatter map):
uv run python -m benchmarks.stereo_imaging.visualizer.run overview \
    --case-dir benchmarks/stereo_imaging/dataset/cases/test/case_0001

# Evaluated stereo product pages for a submitted solution:
uv run python -m benchmarks.stereo_imaging.visualizer.run products \
    --case-dir benchmarks/stereo_imaging/dataset/cases/test/case_0001 \
    --solution-path path/to/solution.json
```

概览图会渲染少量具有代表性的卫星星下点轨迹，作为弱化的上下文图层，使多卫星测试实例中的目标地理分布依然清晰可读。用 `--max-ground-tracks` 可以增加、减少或隐藏该图层。

products 命令默认把面向人工/视觉语言模型的 PNG 页面写入 `benchmarks/stereo_imaging/visualizer/plots/<case_id>/products/`。用 `--max-products` 和 `--products-per-page` 可以指定渲染多少个已评估的立体/三立体产品。每一行产品包含一幅朝向目标的地球视图、一幅目标局部地面条带重叠图、观测几何，以及简要的产品指标。

### 测试

```bash
uv run pytest tests/benchmarks/test_stereo_imaging_verifier.py tests/benchmarks/test_stereo_imaging_generator.py
```
