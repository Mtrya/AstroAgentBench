[English](../../../../../../solvers/stereo_imaging/time_window_pruned_stereo_milp/README.md) | 中文

# 时间窗口剪枝的立体 MILP 求解器
<!-- i18n-source-sha256: 3ad8d8dc083f22377dadeb1a308acb3d39c3eb0f6d804dde36b14426271e35fc -->

本求解器是 `stereo_imaging` 的可运行复现求解器。

它采用 Junhong Kim、Jaemyung Ahn、Han-Lim Choi 和 Doo-Hyun Cho 在《Task Scheduling of Multiple Agile Satellites with Transition Time and Stereo Imaging Constraints》中描述的任务调度方法，并适配 benchmark 公开的测试实例与解契约。

## 引用

```bibtex
@article{kim2020task,
  title={Task Scheduling of Multiple Agile Satellites with Transition Time and Stereo Imaging Constraints},
  author={Kim, Junhong and Ahn, Jaemyung and Choi, Han-Lim and Cho, Doo-Hyun},
  journal={Journal of Aerospace Information Systems},
  year={2020},
  doi={10.2514/1.I010775}
}
```

本求解器独立自洽。它读取 benchmark 测试实例文件，写出 benchmark 解 JSON，但不会导入或执行 benchmark、experiment、运行时基座或其他求解器的内部实现。

## 方法概述

论文将带立体约束的敏捷对地观测调度分解为候选生成、产品剪枝与 MILP 优化。本复现保留这一结构，并适配到 `stereo_imaging`：

- **候选**：一条落在已找到的可见区间内、且通过任务时域、时长、合成侧摆角、太阳高度角与视线预检的 `(satellite_id, target_id, start_time, end_time, off_nadir_along_deg, off_nadir_across_deg)` 观测。
- **立体对**：同一目标上的两个候选，按交会角、重叠率与像素尺度比阈值评分；扩展后的数据模型可以表示本 benchmark 的同星同轨与跨卫星产品模式。
- **三立体成像集**：同一目标上的三个候选，需有足够的公共重叠率并包含近天底锚点；扩展后的产品元数据使后续阶段能够建模本 benchmark 完整的组成对规则。
- **冲突图**：边用于表示同一卫星上的时间重叠，以及姿态机动加稳定时间不足。
- **覆盖**：只要选中至少一个包含该目标的合法立体对或三立体成像集，该目标即算被覆盖。
- **目标函数**：按字典序先最大化被覆盖的目标数，再最大化每个目标的最佳立体质量。

求解器支持精确与启发式两种优化模式：

- **精确 MILP**：在已安装 OR-Tools 时使用 OR-Tools CP-SAT。
- **确定性贪心启发式**：仅在显式设置 `optimization.backend: greedy` 时启用。

## 面向 benchmark 的适配

本 benchmark 与论文在若干重要方面存在差异：

- 本 benchmark 先按合法性排序，再按覆盖率和归一化质量排序，因此求解器采用“覆盖优先、每目标最佳质量”的选择策略，而不是对重复产品做可加性质量累加。
- 可见区间通过粗时间步长搜索确定，而不是精确的 SGP4 求根；相对于精确轨道传播会出现轻微偏差，这属于预期现象。
- 太阳高度角与视线检查在观测中点采样。
- 重叠率用确定性极坐标网格估计，而不是蒙特卡洛方法；结果可能与验证器相差几个百分点。
- 本 benchmark 现在同时允许同星同轨立体与受任务时域约束的跨卫星立体，求解器也已在产品层中直接枚举这些 benchmark 产品模式。
- 候选生成按卫星分批：每颗卫星在任务时域内只做一次轨道传播，供该卫星的所有目标复用，再按卫星并行以提升速度。
- 产品枚举采用惰性的条带几何构建，并在交会角、像素尺度、锚点与组成对检查上做保守的提前排除，避免为重叠率评估付出不必要的开销。

这意味着本求解器复现了论文的“候选—剪枝—优化”流水线，同时严格遵循 benchmark 公开的合法性契约。

## 求解器契约

```bash
./setup.sh
./solve.sh <case_dir> [config_dir] [solution_dir]
```

`setup.sh` 会在 `.venv/` 下创建求解器本地、与仓库隔离的虚拟环境（该目录已加入 git 忽略规则），从 `requirements.txt` 安装求解器依赖，并检查其中能否导入 `brahe`、`numpy`、`yaml` 和 `skyfield`。如果想复用已经准备好的求解器专属环境，可以用 `SOLVER_VENV_DIR=/path/to/env` 覆盖该位置。setup 完成后，`.solver-env` 会记录直接求解与 experiment 运行器所用的 `SOLVER_VENV_DIR` 和 `SOLVER_PYTHON` 绝对路径。

### 后端安装

默认的 `thorough` 模式使用 `optimization.backend: ortools`，这要求求解器本地环境中安装 OR-Tools：

```bash
./setup.sh
# or
SOLVER_VENV_DIR=/path/to/stereo-milp-env ./setup.sh
```

`requirements.txt` 包含求解器运行所需的核心依赖。`setup.sh` 随后会尝试在求解器本地环境中安装 `ortools>=9.11`。它来自 PyPI，不会装入仓库工作区。精确求解使用 `backend: ortools`，在 OR-Tools 不可用时直接明确报错，而不会静默切换到贪心模式。只有刻意做冒烟测试或诊断运行时，才应使用 `backend: greedy`。

## 运行模式

求解器通过 `runtime.mode` 提供两个有文档记录的运行预设：

- `thorough`：面向 benchmark 的更密集预设，用于公开测试实例评测。未提供配置时，它是隐含的默认值。
- `fast`：更轻量的启发式预设，适合快速扫描以及运行时间的前后对比。

求解器先应用预设，用户指定的参数随后覆盖它。`thorough` 使用 OR-Tools 精确模式，在 OR-Tools 不可用时直接失败。`fast` 显式设置 `optimization.backend: greedy`。

`solve.sh` 会写出：

- `solution.json`：主要的 benchmark 解
- `status.json`：求解器摘要、耗时、复现说明与后端细节
- `debug/*`：当 `debug: true` 时可选的调试产物

主要解产物是一个 JSON 对象，其顶层 `actions` 数组由 `observation` 动作组成。

## 流水线

求解器的流水线如下：

1. 加载 `mission.yaml`、`satellites.yaml` 和 `targets.yaml`。
2. 构建按卫星分批的状态序列，并用粗时间步长搜索为每个目标找出可见区间。
3. 在每个可见区间内采样起始时间与指向角，生成候选观测，并用缓存的中点状态执行廉价的局部预检。
4. 枚举立体对与三立体成像集；在安全的前提下先做廉价的排除筛选，再计算重叠几何。
5. 可选地用 Kim 风格的时间窗口聚类上限对候选做剪枝。
6. 构建抽象 MILP，其中包含观测、立体对、三立体成像与覆盖变量，并由冲突约束将它们关联起来。
7. 用 OR-Tools 或显式指定的确定性贪心启发式求解，采用覆盖优先与每目标最佳质量的语义。
8. 执行求解器本地的保守修复，消除残余的转移或互斥违规，然后重新计算 benchmark 形态的覆盖率与质量指标。

修复阶段有意保持保守。它维持求解器的独立自洽，减少官方验证器判失败的情况，但并不声称所有几何近似都是精确的。

## 配置

求解器从以下位置读取可选配置：

- `<config_dir>/config.yaml`
- `<config_dir>/config.yml`
- `<config_dir>/config.json`
- `<config_dir>/time_window_pruned_stereo_milp.yaml`
- `<config_dir>/time_window_pruned_stereo_milp.yml`
- `<config_dir>/time_window_pruned_stereo_milp.json`

带注释的示例见 [config.example.yaml](../../../../../../solvers/stereo_imaging/time_window_pruned_stereo_milp/config.example.yaml)。

关键参数：

- `runtime.mode`
- `time_step_s`
- `sample_stride_s`
- `max_candidates_per_interval`
- `parallel_candidate_generation`
- `steering_along_samples`
- `steering_across_samples`
- `steering_grid_spread_deg`
- `use_target_centered_steering`
- `strip_sample_step_s`
- `overlap_grid_angles`
- `overlap_grid_radii`
- `pruning.enabled`
- `optimization.backend`
- `optimization.time_limit_s`
- `debug`

`time_limit_s` 只限制 MILP 或贪心求解这一步，不限制候选生成、产品枚举或本地校验。若达到时间预算，求解器返回目前找到的最优解，并仍会执行修复。

`status.json` 还包含一个 `profiling` 段，记录候选生成、产品枚举以及求解与模型构建各阶段的计数器；这样无需临时加日志，就能对比运行时间调优的效果。

## 调试产物

当 `debug: true` 时，求解器会写出：

- `debug/candidate_summary.json`
- `debug/product_summary.json`
- `debug/pruning_summary.json`
- `debug/repair_log.json`

`status.json` 是 Phase 4 工作的主要计时产物：

- `timing_seconds`：保存各阶段的粗粒度墙钟总耗时
- `profiling.runtime_mode`：记录实际运行的是哪个预设
- `profiling.candidate_generation`：报告分批状态、可见区间搜索、采样与太阳检查的计数
- `profiling.product_enumeration`：报告中点几何、条带几何与重叠率评估的计数
- `profiling.solve`：报告冲突图、模型构建与后端细节

这些信息可用于回答以下问题：

- 某个目标为何没有候选
- 找到了多少个合法立体对与三立体成像集
- 剪枝是否移除了可用的候选
- 某个候选为何在修复中被移除
- 最终选择了哪个后端

## 运行方式

直接安装：

```bash
./solvers/stereo_imaging/time_window_pruned_stereo_milp/setup.sh
```

在公开冒烟测试实例上直接求解：

```bash
./solvers/stereo_imaging/time_window_pruned_stereo_milp/solve.sh \
  benchmarks/stereo_imaging/dataset/cases/test/case_0001
```

指定配置目录直接求解：

```bash
./solvers/stereo_imaging/time_window_pruned_stereo_milp/solve.sh \
  benchmarks/stereo_imaging/dataset/cases/test/case_0001 \
  /path/to/config_dir \
  /tmp/stereo_milp_solution
```

官方评测与汇总请使用 [Harbor 求解器工作流](../../../experiments/evaluate/README.md)。

求解器本地测试：

```bash
./solvers/stereo_imaging/time_window_pruned_stereo_milp/test.sh
```

官方评测与汇总请使用 [Harbor 求解器工作流](../../../experiments/evaluate/README.md)。

## 合理性基线

论文报告的是 MILP 目标函数值与覆盖比例，这些数值来自论文自己生成的实例，而不是本 benchmark 的覆盖率或归一化质量得分。论文的覆盖比例只能作为对完成行为的粗略合理性检查，不应视为本 benchmark 的目标指标表。

这里关注的是：

- 官方验证通过
- 候选数量合理
- 修复不会使调度表崩溃
- 公开测试实例上的覆盖率保持在合理水平

如果原始立体对/三立体成像选择看起来很强，但修复移除了大量观测，应先检查本地冲突模型、转移间隔逻辑与候选生成，再调整搜索参数。

## 已知局限

- 本求解器复现的是论文的“候选—剪枝—优化”流水线，并不声称复现论文中每次运行的耗时或每张表格。
- 可见区间通过粗时间步长搜索确定，而不是精确的 SGP4 求根；相对于精确轨道传播会出现轻微偏差，这属于预期现象。
- 太阳高度角与视线检查在观测中点采样。
- 重叠率用确定性极坐标网格估计，而不是蒙特卡洛方法；结果可能与验证器相差几个百分点。
- OR-Tools MILP 使用一条次级确定性平局裁决，在覆盖率与每目标最佳质量固定之后，移除冗余的可行观测。
- 如果某个目标不存在合法的立体对或三立体成像集（例如只有一颗卫星能观测到它，或姿态机动时间超过相邻可见区间之间的间隔），该目标将保持未被覆盖。
- 精确 MILP 需要求解器本地的 `ortools`；除非显式选择 `optimization.backend: greedy`，否则缺少 OR-Tools 会被报告为错误。
