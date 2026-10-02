---
license: other
license_name: mixed-source-licenses
license_link: README.md#licensing-and-attribution
language:
  - en
tags:
  - aerospace
  - satellite-scheduling
  - astrodynamics
  - benchmark
---

[English](../../../../scripts/DATASET_CARD.md) | 中文

# AstroAgentBench
<!-- i18n-source-sha256: 9a018759aa0d51783a0f7ac4797ee5b23ab9a4a221f4e4a90901fb9f1f2f05cd -->

本数据集仓库提供带版本号的 benchmark 文件，用于在空间任务设计问题上评估完整的 agent 系统与传统求解器。[GitHub](https://github.com/Mtrya/AstroAgentBench) 是权威来源。

每个不可变 release tag 都包含 `benchmarks/` 下对应的完整 benchmark 目录树：测试实例、验证器、数据集生成器、源输入数据、文档以及二进制资产。`release-manifest.json` 记录 Git commit、导出映射、字节大小和 SHA-256 校验和。评测包/运行时基座所需的文件会随源环境一并包含在内。Git 符号链接以文本文件形式存储，文件内容即链接目标，其模式记录在清单中；外部目标一律不跟随。

使用 `hf download OWNER/DATASET --repo-type dataset --revision RELEASE --local-dir benchmark-release` 下载 release，其中的仓库标识符与 release 标识符取自 GitHub release。请遵循各 benchmark 的 README 和随附的依赖锁文件。验证器定义合法性与原生得分，不同任务家族之间的得分不可互换。

1 月版本保留了 AstroReason-Bench 这一历史名称。它的 `src/dataset/` 映射到 `benchmarks/`，原始源码树保留在 `legacy/src/` 下。清单记录了外部子模块的 revision；这些子模块的源码和历史外部服务不会随包提供，也不保证仍然可用。如需还原其原始执行环境，请使用与之匹配的 GitHub 快照。

## 许可与署名

本 release 同时包含根目录 [MIT 许可证](../../../../LICENSE) 下的项目代码与材料，以及按各自条款提供的第三方输入。MIT 许可证并不替代这些来源许可证；数据溯源信息见各 benchmark 的 README 与 `sources/manifest.json`。

SPOT5 的 `.spot` 输入依据 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 分发，来自 Zequn Wei 与 Jin-Kao Hao 的 [Mendeley Data 发布（第 1 版，2021 年），DOI 10.17632/2kbzg9nw3b.1](https://data.mendeley.com/datasets/2kbzg9nw3b/1)。内置的源文件保持原样，benchmark 测试实例文件均由它们派生而来。再分发这些数据时，请保留本署名，并注明所做的任何进一步修改。
