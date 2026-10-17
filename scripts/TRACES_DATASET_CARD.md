---
license: cc-by-4.0
language:
  - en
tags:
  - aerospace
  - agent-traces
---

# AstroAgentBench Traces

Native sessions from the [AstroAgentBench agent run archive, version v1](https://doi.org/10.5281/zenodo.23084447): {{CODEX_COUNT}} Codex rollout files and {{CLAUDE_COUNT}} Claude Code session files. Open a session in Hugging Face Data Studio to inspect its timeline, tool calls, and results.

This is the subset supported by HF's native trace viewer, not the complete experimental corpus. OpenCode, Kimi CLI, other session formats, and non-session run artifacts remain in the Zenodo archive. No sessions have been converted. Experiment, run, system, and case directory structure is preserved under `sessions/`.

The JSONL files are copied byte-for-byte from the frozen redacted archive. Credentials and personal home paths were scrubbed during archive preparation. Publication verifies the pinned archive manifest, every selected file's SHA-256, JSONL structure, and known plaintext credential/home-path patterns. Opaque encrypted reasoning payloads are retained and excluded from plaintext scanning. `release-manifest.json` records source provenance, selection counts, and the published file checksums; `zenodo-23084447` identifies this immutable selection.

## Attribution

Source: Wang, Weiyi; Chen, Xinchi; Gong, Jingjing; Huang, Xuanjing; and Qiu, Xipeng. *AstroAgentBench agent run archive*, v1 (2026), [DOI 10.5281/zenodo.23084447](https://doi.org/10.5281/zenodo.23084447). Distributed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). This distribution selects supported sessions and adds a dataset card and release manifest; the selected session contents are unchanged.
