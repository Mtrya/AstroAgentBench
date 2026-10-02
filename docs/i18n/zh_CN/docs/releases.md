[English](../../../../docs/releases.md) | 中文

# benchmark 发布
<!-- i18n-source-sha256: b93463b486b77bac2b347a3c080ae6216bfa519c05e46f1c3fa669dd7ead7abd -->

GitHub 是权威来源。Hugging Face 上的单个数据集仓库会收到完整的、带版本号的 benchmark 文件，其中包括代码、内置的生成器输入以及二进制资产。GitHub 上的一个 release 标识，同时也是 HF 上那个不可变 tag 的名称。实验运行归档与论文发布是另外两项彼此独立的操作。

从完整的 Git commit SHA 或 release tag 开始暂存（stage）：

```bash
uv run --locked python scripts/upload_benchmark_datasets.py --revision FULL_COMMIT_SHA --version RELEASE --output .runtime/hf-release
```

该命令不会执行任何上传。它导出的是 Git 对象而非本地工作文件，会校验字节大小和 SHA-256 校验和，然后原子地安装暂存目录。用完全相同的内容重复暂存会成功；若已有的输出存在冲突或已经损坏，则失败。`release-manifest.json` 记录源 commit 和路径映射。发布之前请先检查暂存内容。

release card 同样取自所选 commit 的 `scripts/DATASET_CARD.md`，并在末尾附加发布来源信息。没有该 card 的 1 月版本会改为保留其提交时记录的根目录 README；其中的历史链接与说明描述的是原始的仓库结构。清单会记录使用的是哪一份源文档。

当前版本会导出整个 `benchmarks/` 目录树、根目录的依赖与许可证文件，以及源安装所需的评测包与运行时基座文件。1 月版本则显式地把 `src/dataset/` 映射为 `benchmarks/`，并把原始的 `src/` 目录树保存在 `legacy/src/` 之下，外部子模块的 commit 标识记录在清单中。符号链接会以目标内容的字节形式作为普通文件保留，其 Git 模式同样记录在清单中；导出器从不读取外部目标。这种打包方式既不会让历史上的外部服务变得现代化，也不代表它们现在依然可用。

**Stage or Publish Benchmark Dataset**（暂存或发布 benchmark 数据集）工作流接收一个源 revision 和与之匹配的 release 标识。默认行为只是暂存，并保留一个 Actions artifact。请从当前的实现分支运行它。要执行发布，需要选择 `publish`，并为一个已存在的数据集仓库配置 `HF_TOKEN` 和 `HF_DATASET_REPO_ID`。本地的等效做法是在此基础上追加 `--repo-id OWNER/DATASET --publish`。

发布流程首先校验匹配的 Git release tag 确实指向所暂存的 commit，然后在版本专属的暂存分支上创建一个原子 commit，把它下载回来做校验和验证，最后才创建 release tag。如果上传被中断，或者在创建 tag 之前重新运行，流程会接着处理同一份内容。若已存在匹配的 tag，则校验后直接复用；若版本冲突则失败。已发布的 tag 与数据集的 main 分支都不会被覆盖。远端认证、上传限制和 tag 权限需要在获得授权的发布过程中实际验证；本地暂存测试无法证明这些外部操作可行。