[English](../../../../../experiments/evaluate/README.md) | 中文

# 评测
<!-- i18n-source-sha256: bdb917cf65a85a07b87c381bd002023b6ade8061774c114c8aac581abb12dd7a -->

Harbor 0.23.0 负责环境生命周期、并发、超时、重试、已安装或外部的系统适配器以及产物。本目录负责准备标准测试实例、调用权威验证器 CLI、适配独立自洽的求解器 CLI，并汇总原生指标。参见[评测契约](../../docs/experiment_contract.md)。

## agent 系统

准备好一个测试实例，然后运行你选定的 Harbor 适配器：

```bash
uv run --locked --extra evaluation python -m experiments.evaluate.prepare regional_coverage test case_0001 --output .runtime/tasks/regional
uv run --locked --extra evaluation harbor run -p .runtime/tasks/regional -a your_package.agent:YourAgent -n 1 --jobs-dir results --job-name regional-system
```

`your_package.agent:YourAgent` 是你自己安装的实现，不是仓库自带的示例。系统如果在任务容器之外编排，就扩展 Harbor 的 [BaseAgent](https://docs.harborframework.com/core-concepts/agents/custom-agents)；如果系统是容器内的 CLI，则扩展 `BaseInstalledAgent`。系统自己负责执行循环、服务商连接、模型设置、工具、记忆与多智能体协作。它的适配器通过 Harbor 的环境 API 传输文件、执行命令。轨迹是可选的，可以写入适配器日志目录或 `/logs/artifacts`；评分并不要求提供轨迹。

Harbor 还提供[已安装 agent 适配器](https://docs.harborframework.com/core-concepts/agents/pre-integrated-agents)，包括 `claude-code`、`codex`、`gemini-cli` 和 `opencode`。用 `-a` 选择适配器，适用时用 `-m` 指定模型，用 `--agent-kwarg` 传入适配器选项。用适配器支持的版本与配置选项来确定被评测系统的标识。`--install-only` 只检查安装，不运行模型。凭据、服务商支持以及自动生成的模型设置请查阅所选适配器的上游文档；这些设置属于被评测系统的一部分。本仓库的集成不会添加任何生成参数覆盖。Python 接口检查无法证明与真实服务商之间的兼容性。

通用 Python 运行时基座提供科学计算库、bash、curl、git 和 uv。Harbor 适配器自行安装所需的 CLI 依赖；如果系统需要其他工具，可以通过 `prepare --image` 使用自己的镜像。默认运行时基座不捆绑任何特定的运行框架、服务商或领域技能。如果你用隔离的 Buildx 构建器在本地构建运行时基座，请先把它加载进 Docker，并在运行 Harbor 之前执行 `docker buildx use default`，这样 Compose 才能解析到本地基础镜像。

## 独立求解器示例

下面运行真实的 CELF 优化器，并把候选上限刻意压到很小的 32 个。它用于检查集成是否打通，结果可能为零覆盖率；做对比时请使用科学上合适的计算预算。

```bash
uv run --locked --extra evaluation python -m experiments.evaluate.prepare regional_coverage test case_0001 --output .runtime/tasks/regional-solver
uv run --locked --extra evaluation harbor run -p .runtime/tasks/regional-solver -a experiments.evaluate.solver:SolverAgent --agent-kwarg solver_dir=solvers/regional_coverage/celf_submodular --agent-kwarg config_dir=experiments/evaluate/examples/celf -n 1 --jobs-dir results --job-name regional-celf
uv run --locked --extra evaluation python -m experiments.evaluate.aggregate results/regional-celf --output results/regional-celf.jsonl
```

适配器会上传选定的求解器与公开配置，调用求解器自己的 `setup.sh`，再调用 `solve.sh CASE CONFIG SOLUTION`。求解器依赖由求解器自行管理，可能会解析到更新的版本；报告对比结果时，请检查 setup 日志并锁定求解器环境。setup 日志、输入哈希、解、状态以及求解器生成的调试输出都会保留。所用的配置目录中只能包含有意提供给被评测环境的材料。

SPOT5 的查表基线写出的是原生文本格式。准备它的任务时使用 `--solution-filename solution.spot_sol.txt`；其他 benchmark 使用 `solution.json`。查表基线只用来验证链路是否打通，不是优化方法。

## 交互式查看测试实例

如果想手动查看某个测试实例，或者在为它花掉一次 Harbor 试验之前先试跑一个解，可以在系统实际会看到的环境中打开一个 shell：

```bash
uv run --locked --extra evaluation python -m experiments.evaluate.workspace spot5 test 8 --output .runtime/tasks/spot5-inspect
```

该入口脚本准备的任务与 `prepare` 相同，构建的环境镜像也相同，随后把你带入 `/workspace` 下的 `bash`，其中测试实例位于 `case/`，`solution/` 为空。`/workspace/solution` 是绑定挂载，写入其中的内容会保留在宿主机上，之后可以评分：

```bash
uv run --locked --extra evaluation python -m experiments.evaluate.score --tests .runtime/tasks/spot5-inspect/tests --solution .runtime/tasks/spot5-inspect/solution --output .runtime/tasks/spot5-inspect/verifier
```

镜像 tag 带有测试实例的校验和，因此重建的环境始终与准备好的测试实例一致；传入 `--no-build` 可以复用已有镜像。`--cpus`、`--memory-mb`、`--image`、`--network no-network` 和 `--solution-filename` 与 `prepare` 保持一致。`--command` 不打开 shell，而是无交互地运行一条命令，这在脚本中很有用。

容器以宿主机用户的身份运行，所以你留下的文件仍然可编辑；容器外没有 Harbor 试验：不收集产物，不施加 agent 或验证器超时，验证器也不在其中，因为 `prepare` 有意不把验证器放进求解环境。用这种方式查看测试实例，说明不了系统的实际表现。请对结果评分，或者运行一次真正的试验。

## 设置与结果

准备好的任务默认使用 2 个 CPU、4096 MiB 内存、10240 MiB 请求存储、7200 秒系统执行时间和 600 秒验证时间，并允许访问公共网络。Harbor 默认使用 Docker；示例中的 `-n 1` 表示一次只运行一个试验。镜像引用、测试实例与验证器的哈希、源码提交与工作区是否干净、资源上限以及网络策略都会被记录。要做固定条件下的对比，请使用镜像 digest 和干净的源码提交。Docker 不保证 `storage_mb` 会落实为磁盘配额；请确认环境提供方的强制执行能力。

可以使用 `prepare --cpus`、`--memory-mb`、`--timeout`、`--image` 和 `--network no-network`，或者用 Harbor 原生的运行时覆盖选项。`no-network` 模式需要环境提供方支持，可阻止容器内发起外部模型调用；Harbor 会拒绝不受支持的网络策略。构建与 setup 阶段的下载同样取决于本地的网络与代理配置。常规示例不会授予宿主机网络，也不会把仓库挂载进求解容器。

每个 Harbor 原生试验都包含实际配置、任务校验和、系统标识、状态与错误、耗时、日志、收集到的 `artifacts/solution/` 以及 `verifier/` 输出。`report.json` 保留原生指标；`reward.json` 按 benchmark 命名这些指标，并包含合法性。最小化与最大化方向在 `benchmarks/*.yaml` 中声明；Harbor 通用的均值展示并不是跨 benchmark 排名。JSONL 汇总会把非法、缺失、出错和未评分的试验分别保留。分享一次运行时，请把准备好的任务和原生作业目录与汇总一起保留。轨迹与 token 计数是可选的。
