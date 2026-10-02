[English](../../../../../../solvers/relay_constellation/umcf_srr_contact_plan/README.md) | 中文

# UMCF/SRR 接触计划求解器
<!-- i18n-source-sha256: dba1f4cc559168c666412931170d8baaa4c1b7086f705b110ab47c3c1a48f81e -->

面向 `relay_constellation` 的可运行复现求解器，基于不可拆分多商品流（UMCF）与顺序随机舍入（SRR）。

本求解器沿用 Grislain 等人与 Lamothe 等人提出的方法族，并按 benchmark 公开的测试实例与解契约做了适配。它只读取 benchmark 的测试实例文件并写出 benchmark 解 JSON，不导入 benchmark、experiment、runtime 或其他求解器的内部实现。

## 引用

```bibtex
@inproceedings{grislain2022rethinking,
  title={Rethinking {LEO} Constellations Routing with the Unsplittable Multi-Commodity Flows Problem},
  author={Grislain, Paul and Pelissier, Nicolas and Lamothe, Fran{\c{c}}ois and Hotescu, Oana and Lacan, J{\'e}r{\^o}me and Lochin, Emmanuel and Radzik, Jos{\'e}},
  booktitle={2022 11th Advanced Satellite Multimedia Systems Conference and 17th Signal Processing for Space Communications Workshop (ASMS/SPSC)},
  pages={1--8},
  year={2022},
  organization={IEEE},
  doi={10.1109/ASMS/SPSC55670.2022.9914743}
}

@article{lamothe2023dynamic,
  title={Dynamic unsplittable flows with path-change penalties: New formulations and solution schemes for large instances},
  author={Lamothe, Fran{\c{c}}ois and Rachelson, Emmanuel and Ha{\"i}t, Alain and Baudoin, C{\'e}dric and Dup{\'e}, Jean-Baptiste},
  journal={Computers \& Operations Research},
  volume={152},
  pages={106154},
  year={2023},
  publisher={Elsevier},
  doi={10.1016/j.cor.2023.106154}
}
```

## 方法概要

Grislain 等人用 UMCF 路由把每个需求分配到一条不可拆分的路径上，同时考虑拥塞；Lamothe 等人把 UMCF 扩展到动态图，引入路径变更惩罚与 SRR 启发式。

本 benchmark 适配把 UMCF/SRR 用作求解器本地的接触规划 oracle：

- 在测试实例约束内生成确定性的候选轨道库
- 按边际路由服务潜力贪心挑选候选中继
- 在路由网格上对骨干星座与选中的中继做轨道外推
- 为每个采样点构建一张动态通信图
- 为每个活跃需求枚举一个有限的 k 最短路径集
- 用 SciPy HiGHS 求解路径受限的 LP 松弛
- 用 SRR 对 LP 的分数路径值做随机舍入，同时跟踪边容量与节点容量
- 把舍入后的路径转换为验证器可接受的区间链路动作

最终的路由、分配、合法性检查与指标都由 benchmark 验证器负责。求解器只提交 `added_satellites` 与基于区间的 `actions`。

## Benchmark 适配

相对论文的主要适配如下：

- 论文在固定星座上做路由。`relay_constellation` 要求的是带数量上限的中继增强，因此本求解器额外加入了一层面向 benchmark 的候选生成与候选选择。
- 论文可以输出路由或路由选择结果。本 benchmark 只接受链路激活，所以 UMCF/SRR 的路径要转换成链路激活区间，再由验证器独立重新路由。
- 验证器采用单位容量、边不相交的路由模型。求解器的 LP 与 SRR oracle 同样使用单位边容量，以匹配这一分配模型。
- benchmark 对每个采样点的端点与卫星设有节点度上限。求解器把这些上限建模为 LP/SRR 中的节点容量，并把事后修复保留为合法性兜底。
- Lamothe 的动态模型在路径序列或时间块上做优化。本求解器对每个路由采样点只求解一个 LP，并把路径变更偏好实现为每个采样点上的舍入概率加成。

## 求解器契约

```bash
./setup.sh
./solve.sh <case_dir> [config_dir] [solution_dir]
```

`setup.sh` 会检查项目提供的基础依赖，并为 SciPy HiGHS 创建求解器本地的 `.venv`。求解器专属依赖有意不纳入顶层项目环境。

`solve.sh` 会写出：

- `solution.json`：benchmark 的主要解文件
- `status.json`：求解器摘要、耗时、所选 profile，以及计算资源包络的披露
- `debug/*`：求解器本地的诊断信息

## 正式启用的配置

独立运行（standalone）的配置记录在 config.example.yaml 中。

正式启用的公开 profile 是 `reproduction`：

- 生成 64 颗候选卫星
- 确定性的 SRR
- 每个采样点求解一次 LP
- 由 SciPy HiGHS 实现的路径受限 LP 松弛
- 每个商品取 k=4 条最短简单路径
- 跳数模式下的 LP 路径开销 epsilon 为 `1.0e-4`
- 不限制首跳入站与末跳出站卫星的选择
- 在按步长抽选的样本上执行贪心边际候选选择
- 求解器超时 300 秒

规模更大、面向质量的 128 候选随机设置仅用于校准。它在 `case_0001` 和 `case_0002` 上通过了验证，但峰值 RSS 约为 3.6 至 3.8 GiB；在计入运行框架开销后，它在 `case_0002` 上超出了实际可行的全矩阵预算。它不是正式启用的 profile。

与正式启用的 profile 对应的直接运行示例见 [config.example.yaml](../../../../../../solvers/relay_constellation/umcf_srr_contact_plan/config.example.yaml)。

## 流水线

1. 加载 `manifest.json`、`network.json` 与 `demands.json`。
2. 生成确定性的候选中继库。
3. 在路由网格上用 Brahe 对骨干卫星与候选卫星做轨道外推。
4. 构建包含全部候选的采样图。
5. 用确定性的贪心边际可达性代理指标选择候选。
6. 只用选中的候选重建采样图。
7. 根据活跃需求构建每个采样点的 UMCF 实例。
8. 求解路径受限的 LP 松弛并运行 SRR。
9. 过滤、修复、压缩并输出区间动作。

## 依赖与后端选择

- Python 3.13
- 用 Brahe 做轨道外推，与验证器仅含 J2 的确定性模型保持一致
- 用 NumPy 做向量化几何计算
- 用 PyYAML 解析配置
- 通过求解器本地 setup 使用 SciPy HiGHS 做 LP 松弛
- 不依赖外部图论库

## 调试产物

求解器会把调试产物写入 `<solution_dir>/debug/`，包括：

- `compute_envelope.json`
- `scale_diagnostics.json`
- `selected_candidates.json`
- `routed_potential_summary.json`
- `umcf_instances.json`
- `lp_summary.json`
- `srr_summary.json`
- `rounded_paths.json`
- `active_link_summary.json`
- `action_summary.json`
- `oracle_drift_diagnostics.json`
- `reproduction_summary.json`

这些产物会披露候选规模、图规模、LP 规模与状态、SRR 决策、修复带来的影响、oracle 与验证器之间的偏差风险，以及论文组件映射。

## 运行方式

直接运行 setup：

```bash
./solvers/relay_constellation/umcf_srr_contact_plan/setup.sh
```

在公开测试实例上直接求解：

```bash
./solvers/relay_constellation/umcf_srr_contact_plan/solve.sh \
  benchmarks/relay_constellation/dataset/cases/test/case_0001
```

官方评测与结果聚合请使用 [Harbor 求解器工作流](../../../experiments/evaluate/README.md)。

## 复现差距汇总

- **UMCF 商品与容量**：已适配（ADAPTED）。商品来自 benchmark 的需求窗口；边容量为单位容量，与验证器的分配一致。
- **每个商品一条路径的不可拆分约束**：已实现（IMPLEMENTED）。SRR 为每个商品在每个采样点至多分配一条路径。
- **分数流的 LP 松弛**：已适配（ADAPTED）。SciPy HiGHS 在每个采样点的 k 最短路径集上求解一个有限的路径受限 LP。
- **SRR 顺序舍入控制流**：已实现（IMPLEMENTED）。商品按权重递减的顺序处理，每固定一条路径后就更新容量。
- **基于 LP 解的随机舍入**：已实现（IMPLEMENTED）。LP 的分数路径值决定 SRR 概率；确定性模式选择概率最高的可行路径。
- **节点度上限建模**：已适配（ADAPTED）。benchmark 的节点度上限作为节点容量进入 LP/SRR，并在修复阶段再次检查。
- **k 最短路径限制**：已实现（IMPLEMENTED）。正式启用的 profile 按跳数和距离取 k=4 条最短简单路径。
- **动态路径变更惩罚**：已适配（ADAPTED）。求解器在每个采样点上为前一路径施加概率加成，而不是采用 Lamothe 的块级目标项。
- **k 近邻首跳/末跳限制**：部分实现（PARTIAL）。该选项通过 `first_last_hop_k` 提供，但正式启用的 profile 未加限制，因为校准没有把它认定为最强设置。
- **路径序列、弧-路径与弧-节点 MILP 模型**：未实现（MISSING）。求解器没有实现这些模型。
- **列生成与定价**：未实现（MISSING）。LP 限定在已生成的有限路径集上。
- **舍入期间的 LP 重求解**：未实现（MISSING）。求解器只在每个采样点的 SRR 之前求解一次 LP。
- **候选轨道库与贪心边际选择**：已实现，属于 benchmark 适配，而非论文组件。
- **节点度上限修复与区间压缩**：已实现，属于 benchmark 适配。

## 已知局限

- 本求解器是 UMCF/SRR 方法族经 benchmark 适配后的复现，并不复现论文中的每一个表格、仿真假设或动态模型。
- 候选选择使用可达性代理指标，不会为每次候选边际评估都求解 UMCF。
- 由于求解器不提交路由，验证器的路由结果可能与求解器本地的 SRR oracle 不同。
- 完整的动态路径序列优化、列生成与 LP 重求解仍不在正式启用的 profile 范围内。
- 就当前实际可行的范围而言，正式启用的 profile 是面向全矩阵运行的最强配置。规模更大的质量校准只是证据，并非对外默认配置。
