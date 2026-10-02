[English](../../../README.md) | 中文

# AstroAgentBench
<!-- i18n-source-sha256: 29c8dedba59199e62aaa37610f4023503926a7947540c75282d7691764307a20 -->

AstroAgentBench 在空间任务设计与规划问题上评估完整的 agent 系统和传统求解器。七个彼此独立的 benchmark 家族提供标准测试实例和权威验证器。各系统自行选择模型、工具、记忆与协作方式；[Harbor](https://docs.harborframework.com/) 负责执行评估并收集输出。

| Benchmark | 任务 |
|---|---|
| [AEOSSP](benchmarks/aeossp_standard) | 敏捷地球观测调度 |
| [Regional coverage](benchmarks/regional_coverage) | 区域条带成像调度表 |
| [Relay constellation](benchmarks/relay_constellation) | 中继增强与接触规划 |
| [Revisit constellation](benchmarks/revisit_constellation) | 星座设计与重访调度 |
| [SatNet](benchmarks/satnet) | 地面站跟踪调度表 |
| [SPOT5](benchmarks/spot5) | 照片选取与调度 |
| [Stereo imaging](benchmarks/stereo_imaging) | 立体与三立体成像采集计划 |

## 快速开始

安装 [uv](https://docs.astral.sh/uv/) 以及带 Docker Compose 的 Docker。以下命令均在仓库根目录执行。Python 3.13.11 及 Python 依赖均已锁定版本。

```bash
uv sync --locked --extra evaluation
docker build -t astroagentbench-python:latest runtimes/python
export HARBOR_TELEMETRY=0
```

借助现成的 SPOT5 参考解做一次开销很低的检查，全程不调用模型：

```bash
uv run --locked --extra evaluation python -m experiments.evaluate.prepare spot5 test 8 --output .runtime/tasks/spot5-check --reference-solution benchmarks/spot5/dataset/example_solution.json
uv run --locked --extra evaluation harbor run -p .runtime/tasks/spot5-check -a oracle -n 1 --jobs-dir results --job-name spot5-check
uv run --locked --extra evaluation python -m experiments.evaluate.aggregate results/spot5-check --output results/spot5-check.jsonl
```

准备阶段拒绝覆盖已有的任务目录。换一次运行就要换新的输出目录名和作业名。这项检查覆盖安装、产物传递和评分三个环节，它不是 agent 评估，也不是论文复现。

## 评估系统或求解器

不带 `--reference-solution` 准备任务，然后选择 Harbor 已安装的 agent 适配器，或自行实现 `BaseAgent`。系统写出 `/workspace/solution/solution.json`；Harbor 收集该目录，并在独立容器中完成评估。无需任何仓库专用的模型路由或推理协议。

[评估说明](../../../experiments/evaluate/README.md) 涵盖系统适配器、交互式测试实例查看、一个有真实计算上限的 CELF 求解器示例、配置、结果与局限。传统求解器在 [solvers/](../../../solvers/finished_solvers.json) 下保留各自独立的 `setup.sh` / `solve.sh` 接口，每个求解器的 README 都会说明其方法和计算需求。

## 版本与贡献

`main` 分支随项目持续演进。[`aacl-ijcnlp-2026`](https://github.com/Mtrya/AstroAgentBench/tree/aacl-ijcnlp-2026) 保留了 AACL-IJCNLP 论文所用的五月投稿版本实现。一月份的 AstroReason-Bench 快照保存在 [`acl-submission-2026`](https://github.com/Mtrya/AstroAgentBench/tree/acl-submission-2026) 中。历史研究流程属于各自的快照与历史记录。

贡献可以新增 benchmark，改进验证器或工具，扩展求解器基线，或者评估一套新颖的 agent 系统。请从 [CONTRIBUTING.md](../../../CONTRIBUTING.md) 开始。benchmark 发布件同样会为 Hugging Face 做准备，并附带 Git 提交与校验和作为来源说明，参见[发布暂存](docs/releases.md)。

仓库将 [benchmarks](docs/benchmark_contract.md)、[evaluation](docs/experiment_contract.md)、[solvers](docs/solver_contract.md) 和 [runtimes](docs/runtime_contract.md) 彼此分离。benchmark 验证器定义合法性与原生得分。请在声明的配置下比较系统，不要把互不相干的指标揉进同一个分数里。