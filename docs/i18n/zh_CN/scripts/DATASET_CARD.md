---
license: other
license_name: mixed-source-licenses
license_link: README.md#licensing-and-attribution
language:
  - en
tags:
  - rl-environment
  - harbor
  - aerospace
  - satellite-scheduling
  - astrodynamics
  - benchmark
---

[English](../../../../scripts/DATASET_CARD.md) | 中文

# AstroAgentBench
<!-- i18n-source-sha256: a45c82e4fdcf2ec884be685fbfde2357f815c98a28e919d5cd592260ffac99dd -->

用于在空间任务设计问题上评估完整 agent 系统的 Harbor 任务。[GitHub](https://github.com/Mtrya/AstroAgentBench/tree/{{SOURCE_COMMIT}}) 是 benchmark 定义、数据集生成器和源输入的权威来源。本 release 为 `{{RELEASE}}`，由 Git commit `{{SOURCE_COMMIT}}` 生成。

## 运行任务集

使用 Python 3.13 安装 Harbor 0.23.0，并确保 Docker 可用。运行七个参考解检查，每个 benchmark 任务族各一个：

```bash
harbor run --repo https://huggingface.co/datasets/{{DATASET_REPO}}@{{RELEASE}} --dataset smoke@{{RELEASE}} --agent oracle -n 1 --jobs-dir results --job-name astroagentbench-smoke
```

`registry.json` 按 benchmark 和子集列出数据集，例如 `regional_coverage-test@{{RELEASE}}` 和 `spot5-single_orbit@{{RELEASE}}`。通过 `--dataset` 选择条目，并提供 Harbor agent 适配器及模型。只有 `smoke` 中的七个任务包含 oracle 参考解。原生得分的单位和优化方向由各 benchmark 定义，不应跨任务族合并得分。

## 内容与资源

`tasks/` 下的每个目录包含任务简报、测试实例输入、环境 Dockerfile 和独立验证器。求解环境与验证器环境共享一个通过 digest 固定的公开运行时基座。任务默认使用 8 个 CPU、16384 MiB 内存、7200 秒 agent 执行时间、600 秒验证时间、公共网络访问权限，以及 10240 MiB 请求存储。Docker 不会将请求存储强制执行为磁盘配额。每次运行都会记录 Harbor 的资源覆盖设置。

`release-manifest.json` 记录 Git 来源、运行时基座镜像、字节数和 SHA-256 校验和。数据集版本与 GitHub release tag 一致。从 `v2.0.0` 开始使用任务集布局；历史 tag 保留原内容。完整原始源码树仍在 GitHub 上。

## 许可与署名

本 release 同时包含根目录 [MIT 许可](../../../../LICENSE) 下的项目代码，以及受各自条款约束的第三方输入。MIT 许可不替代这些来源的许可。溯源信息请参阅[发布 commit 中的 benchmark README 和来源 manifest](https://github.com/Mtrya/AstroAgentBench/tree/{{SOURCE_COMMIT}}/benchmarks)。

SPOT5 的 `.spot` 输入按 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 分发，来源为 Zequn Wei 与 Jin-Kao Hao 的 [Mendeley Data 第 1 版数据集（2021），DOI 10.17632/2kbzg9nw3b.1](https://data.mendeley.com/datasets/2kbzg9nw3b/1)。内置源文件未修改，benchmark 测试实例文件由其派生。再分发这些数据时须保留署名，并注明后续修改。
