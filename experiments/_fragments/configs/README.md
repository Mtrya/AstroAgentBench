# Evaluated system configurations

The main study uses the five systems below. Model identities are part of the experimental configuration; provider credentials and connection settings are supplied by the user.

| Harness profile | Model identity | Manuscript reasoning setting | Configuration example |
|---|---|---|---|
| `claude_code` | `claude-opus-4-6` | high | [Claude Code](claude_code/.claude.example/settings.json) |
| `codex` | `gpt-5.4` | high | [Codex CLI](codex/.codex.example/config.toml) |
| `kimi_cli` | `kimi-for-coding` (reported as Kimi K2.6) | thinking | [Kimi CLI](kimi_cli/.kimi.example/config.toml) |
| `opencode_minimax` | `MiniMax-M2.7` | thinking | [OpenCode / MiniMax](opencode_minimax/opencode.example/opencode.json) |
| `opencode_dpsk` | `deepseek-v4-pro`, with `deepseek-v4-flash` as the small model | max | [OpenCode / DeepSeek](opencode_dpsk/opencode.example/opencode.json) |

The examples retain the available model and harness settings. Fill in the connection placeholders for your provider, and configure the selected harness according to its `assemble` entries in [`main_agentic/harnesses/`](../../main_agentic/harnesses/). Do not publish credentials or account state. Codex obtains its key from the `AR_OPENAI_API_KEY` environment variable. Subscription-authenticated harnesses may also need their native login setup.

Harness package versions are pinned in [`runtimes/base/Dockerfile`](../../../runtimes/base/Dockerfile). The default study matrix uses a two-hour limit, 8 CPUs, 32 GB memory, and 16 GB shared memory; its full settings are in [`matrix.yaml`](../../main_agentic/configs/matrix.yaml).

Provider-side model aliases and deployments can change independently of these files. The preserved reports record the original observations; the examples make the selected configuration inspectable and usable for new runs.
