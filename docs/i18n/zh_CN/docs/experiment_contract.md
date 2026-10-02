[English](../../../../docs/experiment_contract.md) | 中文

# 评测契约
<!-- i18n-source-sha256: bd6c18bf2b7d40dc82fedf5393952ec5d2bd5423cd0ecc2bc17617db264e4f71 -->

`experiments/evaluate/` 把独立自洽的 benchmark 与求解器的 CLI 和文件契约接入 Harbor 0.23.0。Harbor 是评测执行器。被评测的智能体系统，指研究者提供的完整组合：运行框架、模型、工具、记忆与协作机制。

## 任务准备

`python -m experiments.evaluate.prepare BENCHMARK SPLIT CASE --output DIRECTORY` 会把一个标准测试实例及其任务简报复制成一个自包含的 Harbor 任务。它记录 Git 提交号与工作区是否干净、测试实例与验证器的 SHA-256 标识、镜像引用、解文件名、资源上限以及网络策略。已有的输出目录绝不会被覆盖。

求解环境中包含 `/workspace/case/` 和一个空的 `/workspace/solution/`。其中没有其他测试实例、示例解、仓库历史或权威验证器代码。`--reference-solution` 会显式加入一份 Oracle 解供集成检查使用；评测被评测系统时应当省略该参数。另有一个独立的验证器镜像，内含原始测试实例和未经修改的 benchmark 验证器，外加一个很薄的 CLI 输出适配器。

## 执行与评分

使用 Harbor 原生的 `run -p TASK -a ADAPTER` 接口。已安装的 CLI 与外部 `BaseAgent` 适配器共用同一套任务环境和输出契约。仓库不实现第二套调度器、Docker 生命周期管理、重试循环、模型路由或 agent 推理协议。

`python -m experiments.evaluate.workspace BENCHMARK SPLIT CASE --output DIRECTORY` 是唯一的例外，它是排查辅助工具，而非评测路径。它准备同样的任务，随后构建该任务专属的环境上下文并在其中打开 shell，供手动调试。镜像 tag 由环境摘要派生，因此 workspace 绝不会运行基于其他基座或其他测试实例构建出来的镜像。它不收集任何产物，不施加 agent 或验证器超时，也不运行验证器和评分适配器，其产出不计入所报告的成绩。若要给它产出的结果打分，请显式使用 `python -m experiments.evaluate.score`，并把该结果作为一次人工检查来报告，而不是系统评测。

必需的产物是 `solution/solution.json`；只有在明确为 SPOT5 选用其他格式时，才使用 `solution/solution.spot_sol.txt`。解目录下的其他文件也会被一并收集。Harbor 会把这些产物转移到一个全新的验证器环境中，并运行 `tests/test.sh`。适配器执行 benchmark 公开的验证器 CLI，保留 stdout/stderr 与原生指标，并输出 Harbor 的数值奖励。缺失解即判定为失败；验证器输出格式错误或运行时异常仍计为错误，而不是成功的零分运行。非法解会保留权威方所报告的指标，因此比较得分时必须把合法性一并考虑进去。

`SolverAgent` 调用独立自洽的 `setup.sh` 和 `solve.sh CASE CONFIG SOLUTION`。它既不导入求解器，也不导入 benchmark，二者的科学实现原样保留。求解器与运行时基座自身从不调用 benchmark 的权威实现。

## 结果与可复现性

原生作业和准备好的任务共同构成持久记录。摘要包含任务与版本、系统标识与配置、上限与访问设置、状态、耗时、合法性、指标、错误以及产物路径。完整轨迹和模型用量计数是可选的。数值指标保留各 benchmark 各自的单位和方向，不定义全局标量。服务商侧的漂移与随机性意味着历史数值完全一致并不是迁移或 CI 层面的要求。

关于默认值、覆盖方式、仅安装检查以及实际限制，请参阅[可运行示例](../../../../experiments/evaluate/README.md)。CI 使用真实的示例解和一个有界的独立求解器，而不是模型的大规模运行。