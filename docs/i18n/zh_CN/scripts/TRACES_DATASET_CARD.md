---
license: cc-by-4.0
language:
  - en
tags:
  - aerospace
  - agent-traces
configs:
  - config_name: default
    data_files:
      - split: train
        path: "sessions/**/*.jsonl"
---

[English](../../../../scripts/TRACES_DATASET_CARD.md) | 中文

# AstroAgentBench 轨迹
<!-- i18n-source-sha256: f7d534e4f67afa4f15a5820c2d7c59cbef6b1d1e57caded6ef288bee63440cba -->

来自 [AstroAgentBench agent 运行归档 v1](https://doi.org/10.5281/zenodo.23084447) 的原生会话，包括 {{CODEX_COUNT}} 个 Codex rollout 文件和 {{CLAUDE_COUNT}} 个 Claude Code 会话文件。在 Hugging Face Data Studio 中打开会话，可以查看其时间线、工具调用和结果。

这是 HF 原生轨迹查看器支持的子集，并非完整实验语料。OpenCode、Kimi CLI、其他会话格式及非会话运行产物仍在 Zenodo 归档中。没有任何会话经过格式转换。`sessions/` 下保留了实验、运行、系统及测试实例的目录结构。

JSONL 文件从冻结的脱敏归档逐字节复制。归档准备过程中已移除凭证并重写个人主目录路径。发布时验证固定的归档 manifest、每个选中文件的 SHA-256、JSONL 结构，以及已知明文凭证和主目录路径模式。不透明的加密推理载荷原样保留，不参与明文扫描。`release-manifest.json` 记录来源、选取数量和发布文件的校验和；`{{TRACE_VERSION}}` 标识这一不可变的选取结果。

## 署名

来源：Wang, Weiyi；Chen, Xinchi；Gong, Jingjing；Huang, Xuanjing；Qiu, Xipeng。*AstroAgentBench agent run archive*，v1（2026），[DOI 10.5281/zenodo.23084447](https://doi.org/10.5281/zenodo.23084447)。按 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 分发。本次分发选取受支持的会话，并添加数据集说明卡和 release manifest；所选会话内容保持不变。
