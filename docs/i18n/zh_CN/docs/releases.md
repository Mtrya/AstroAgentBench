[English](../../../../docs/releases.md) | 中文

# Benchmark 发布
<!-- i18n-source-sha256: 5af9757f4552ac8bd85dad8fa788b91c82a3367a8ee2c634b1473a03f5cfee4f -->

GitHub 是源码、benchmark 定义、数据集生成器及源输入的权威来源。Hugging Face 在 `kaupane/AstroAgentBench` 分发可运行的 Harbor 任务集，在 `kaupane/AstroAgentBench-Traces` 分发受支持的原生会话。仅包含任务集的新布局从 `v2.0.0` 开始；已有历史 release 和 tag 保持原内容。

发布前，先将发布工具合并到 `main`，再在合并后的 commit 上创建 release tag。GitHub 要求手动触发的工作流已存在于默认分支。先发布 GHCR 运行时基座，再用其 digest 发布 HF 任务集；轨迹数据集单独发布。只有远程 oracle 检查和 Data Studio 检查都通过后，才能关闭发布 issue。

## 运行时基座镜像

创建对应的 GitHub release tag，然后运行 **Publish Python Runtime**，传入该 tag 或其完整 commit SHA，以及相同的版本号。工作流从该 commit 的 `runtimes/python/` 构建镜像，并发布到 `ghcr.io/mtrya/astroagentbench-python`。工作流使用具有 `packages: write` 权限的 `GITHUB_TOKEN`，摘要中会显示不可变的 digest 引用。

新建的 GHCR 包默认是私有的。请在包设置中改为公开，再重新运行匿名拉取检查，然后发布任务集。任务集发布过程也会检查匿名拉取权限和镜像的源码 commit 标签。目前发布的运行时基座支持 Linux amd64。

## Harbor 任务集

安装锁定的仓库依赖及 evaluation extra，然后使用完整 Git commit SHA 或 release tag，以及已发布镜像的 digest 暂存任务集：

```bash
uv sync --locked --extra evaluation
uv run --locked python scripts/upload_benchmark_datasets.py --revision v2.0.0 --version v2.0.0 --image ghcr.io/mtrya/astroagentbench-python@sha256:DIGEST --output .runtime/hf-release
```

暂存过程会把指定 Git revision 克隆到临时检出目录，执行该 revision 的 `experiments.evaluate.taskset` 导出器。测试实例、验证器、任务简报、配置、评分代码和 release card 都来自该检出目录。输出包含 `tasks/`、`registry.json`、`README.md`、`LICENSE` 和 `release-manifest.json`。重复暂存相同内容会成功；已有输出损坏或内容冲突时会失败。早于 Harbor 导出器的 revision 使用其原有的历史发布工具。

注册表条目按 benchmark 和子集选择任务，例如 `regional_coverage-test@v2.0.0`。额外的 `smoke@v2.0.0` 条目选择各任务族索引中的示例测试实例，这七个任务包含 oracle 参考解。每个标准测试实例只存储一次，即使它同时被任务族/子集条目和 `smoke` 选中。默认上限为 8 个 CPU、16384 MiB 内存、7200 秒 agent 超时和 600 秒验证器超时。两种任务环境使用同一镜像 digest。release manifest 记录完整的源码溯源信息和文件 SHA-256 校验和。

从 `main` 运行 **Stage or Publish Benchmark Dataset**，提供 revision、版本号和镜像 digest。默认只暂存为 Actions 产物。选择 `publish` 需要具有数据集写入权限的 `HF_TOKEN`。发布过程确认 Git release tag 指向所选 commit，在 release 分支上创建一个原子 commit，下载并验证其校验和，然后创建不可变的 HF tag。已有 tag 的内容一致时会验证并复用；冲突时会失败。

工作流随后直接从公开 HF tag 加载七个 oracle 任务，并要求每个选中测试实例的结果都合法。这些集成检查通过 Harbor 将资源覆盖为 2 个 CPU 和 4096 MiB 内存，以适配托管运行器；发布的默认值仍为 8 个 CPU 和 16384 MiB。只有检查通过后，工作流才会以原子 commit 将已验证文件更新到 HF 的 `main` 分支，使数据集首页和自动生成的框架命令使用可运行布局。已有 HF tag 永不替换。

本地发布的对应顺序如下：

```bash
uv run --locked python scripts/upload_benchmark_datasets.py --revision v2.0.0 --version v2.0.0 --image ghcr.io/mtrya/astroagentbench-python@sha256:DIGEST --output .runtime/hf-release --publish
uv run --locked --extra evaluation harbor run --repo https://huggingface.co/datasets/kaupane/AstroAgentBench@v2.0.0 --dataset smoke@v2.0.0 --agent oracle -n 1 --jobs-dir results --job-name hf-smoke
uv run --locked --extra evaluation python -m experiments.evaluate.aggregate results/hf-smoke --output results/hf-smoke.jsonl
```

确认预期的七个测试实例状态均为 `valid` 后，在发布命令中同时使用 `--publish --promote` 再执行一次。`--repo URL@VERSION` 中的 Git ref 固定仓库树；`--dataset NAME@VERSION` 则独立选择该树的注册表条目。宣布发布前，请检查 HF 首页及其“Use this dataset”命令。

## 原生会话轨迹

轨迹发布器使用冻结的 [Zenodo v1 记录](https://doi.org/10.5281/zenodo.23084447)，而非可能解析到后续版本的概念 DOI。它固定归档 manifest 的 SHA-256，选择 Claude Code 的 `projects/...jsonl` 和 Codex 的 `rollout-*.jsonl` 会话，并保留实验与运行路径。OpenCode、Kimi CLI、其他不兼容格式及非会话产物仍可通过 Zenodo 获取。所选文件保留归档的 CC BY 4.0 署名信息。

运行 **Stage or Publish Agent Traces**，或在本地暂存：

```bash
uv run --locked python scripts/upload_agent_traces.py --output .runtime/hf-traces
```

该命令下载所需的压缩归档分片，验证校验和，并仅提取选中的会话。下载流程需要 `zstd`。如需复用已有脱敏归档，添加 `--archive DIRECTORY`；该目录必须包含 `run-archive-manifest.json` 和 `run-archive/`，文件内容须与固定的 manifest 一致。原始运行目录不能直接作为归档输入。

暂存过程验证每个选中会话的校验和与 JSONL 结构，然后检查解码文本中的已知凭证模式、含密钥字段及个人主目录路径。加密推理载荷作为不透明数据保留。检查失败会停止发布，只报告文件名和类别，不输出匹配值。请先审查失败原因，再准备修正后的来源；不要原地修改已归档证据。

添加 `--publish`，或选择工作流的发布选项，即可创建公开轨迹数据集，上传一个原子 release，通过 `snapshot_download` 验证，创建 `zenodo-23084447` tag，并更新默认分支。发布后，验证原生格式自动识别，并在 Data Studio 中分别打开一个 Claude Code 和一个 Codex 会话。只有查看器检查通过后，才能在仓库 README 或论文中链接轨迹数据集。仅合并代码变更不能证明发布成功或查看器验收通过。
