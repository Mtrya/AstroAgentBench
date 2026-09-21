# AstroReason-Bench

Official implementation of **AstroReason-Bench: Evaluating Unified Agentic Planning across Heterogeneous Space Planning Problems**.

AstroReason-Bench is a comprehensive benchmark for evaluating agentic planning in astronautics mission design and planning. It integrates multiple scheduling regimes under a unified agent-oriented interface with strict physical constraints.

## Overview

Five distinct planning challenges enforcing orbital mechanics, power budgets, data storage, and slew kinematics:

1. **SatNet** - Deep Space Network resource allocation
2. **Revisit Optimization** - Minimize time gaps for continuous target monitoring
3. **Regional Coverage** - Maximize area coverage using strip-imaging satellites
4. **Stereo Imaging** - Schedule synchronized observation pairs for 3D reconstruction
5. **Latency Optimization** - Manage LEO constellation for integrated sensing and communications

## Historical snapshot

The `acl-submission-2026` branch maintains the January ACL submission implementation under its original **AstroReason-Bench** name. See the [original arXiv paper (v1, January 16, 2026)](https://arxiv.org/abs/2601.11354v1). The historical baseline is [`52e4f54`](https://github.com/Mtrya/AstroAgentBench/commit/52e4f5410c4a984e2ba148883086743251bbf423): its code, datasets, dependency lockfile, and SatNet revision are identical to the January 9 initial commit; subsequent historical changes only updated the README and license. This maintained branch adds installation and validation repairs, without asserting an exact submission tag.

For the evolving AstroAgentBench implementation, use [`main`](https://github.com/Mtrya/AstroAgentBench/tree/main). The later submission snapshot is [`aacl-ijcnlp-2026`](https://github.com/Mtrya/AstroAgentBench/tree/aacl-ijcnlp-2026).

The four orbital benchmarks require the historical Astrox service at `http://astrox.cn:8765` for propagation, access, and lighting computations. SatNet planning and scoring use the pinned local submodule. Agent runs additionally need Claude Code and a supported model/provider account. The Python lockfile does not pin the hosted service or Claude Code, and model availability may change.

## Installation

### Prerequisites

- **Python 3.12.12** (the tested interpreter, selected by `.python-version`)
- **[Claude Code](https://claude.com/claude-code)** (for agent runs; not required for local tests)
- **[uv](https://docs.astral.sh/uv/)** (required - manages environments and builds sandboxes)
- **bubblewrap** (optional, enables filesystem isolation):
  ```bash
  # Debian/Ubuntu
  sudo apt install bubblewrap

  # Arch Linux
  sudo pacman -S bubblewrap

  # Fedora
  sudo dnf install bubblewrap
  ```

### Setup

```bash
# Clone the repository with submodules
git clone --branch acl-submission-2026 --recurse-submodules https://github.com/Mtrya/AstroAgentBench.git
cd AstroAgentBench

# If you already cloned without submodules, initialize them:
# git submodule update --init --recursive

# Create virtual environment and install dependencies
uv sync --locked --all-groups

# Activate the environment (required for all subsequent commands)
source .venv/bin/activate  # bash/zsh
# or: source .venv/bin/activate.fish  # fish

# Build sandbox environments (required before running benchmarks)
bash src/benchmark/build_sandbox.sh
bash src/satnet_agent/build_sandbox.sh
```

The builders export the existing `uv.lock` and install hash-checked dependencies for the same Python interpreter into each sandbox. They refresh the bundled source copies from `src/`. Activate the project environment before running benchmarks so their MCP servers use that interpreter. The SatNet gitlink is fixed at `3e78e56eca1fcd4001c55e7491e6e3eb542e350a`; use the root environment rather than installing the submodule’s separate legacy training dependencies.

Claude Code must be available on `PATH`; filesystem isolation also expects its native installation under your `~/.local`. The runners create a per-run home and resolve that location for the current user. `--bwrap` needs working bubblewrap/user namespaces; `--memory-limit` and `--cpu-quota` additionally need a working user systemd session.

### API Keys

```bash
export ANTHROPIC_API_KEY="..."      # Claude
export DEEPSEEK_API_KEY="..."       # DeepSeek
export DASHSCOPE_API_KEY="..."      # Qwen
```

## How to Run

### Running For Novel Benchmarks

Evaluate agentic LLM systems on benchmarks:

```bash
# Single case evaluation
python src/benchmark/run_benchmark.py \
  --benchmark revisit-optimization \
  --case case_0001 \
  --model anthropic::claude-sonnet-4-5-20250929

# All cases in benchmark
python src/benchmark/run_benchmark.py \
  --benchmark stereo-imaging \
  --all \
  --model anthropic::claude-sonnet-4-5-20250929

# Interactive mode (for close inspection and observation)
python src/benchmark/run_benchmark.py \
  --benchmark regional-coverage \
  --case case_0001 \
  --model anthropic::claude-sonnet-4-5-20250929 \
  --interactive

# File system isolation and resource limits
python src/benchmark/run_benchmark.py \
  --benchmark latency-optimization \
  --case case_0001 \
  --bwrap \
  --cpu-quota 800% \
  --memory-limit 16G \
  --model deepseek::deepseek-chat
```

**Available benchmarks:** `revisit-optimization`, `stereo-imaging`, `latency-optimization`, `regional-coverage`

### Running SatNet (DSN Scheduling) Benchmark

SatNet uses a separate runner:

```bash
# Run SatNet Week 40
python src/satnet_agent/run_benchmark.py \
  --week 40 \
  --model anthropic::claude-sonnet-4-5-20250929

# Run all weeks
python src/satnet_agent/run_benchmark.py \
  --all \
  --model anthropic::claude-sonnet-4-5-20250929

# Interactive mode
python src/satnet_agent/run_benchmark.py \
  --week 40 \
  --model anthropic::claude-sonnet-4-5-20250929 \
  --interactive

# File isolation and resource limits
python src/satnet_agent/run_benchmark.py \
  --week 40 \
  --model anthropic::claude-sonnet-4-5-20250929 \
  --bwrap \
  --memory-limit 16G \
  --cpu-quota 800%
```

**Available weeks:** 10, 20, 30, 40, 50

### Local validation

After installation, run the bounded local checks:

```bash
bash scripts/check_snapshot.sh
```

This builds both sandboxes with locked dependencies, checks the CLI entrypoints, and runs the local SatNet scenario/MCP/state/scorer tests plus service-independent orbital checks. It does not call models or the Astrox service. Branch CI runs the same command. The remaining orbital integration tests require the live service; run individual test cases deliberately rather than treating unrestricted `pytest` as an offline check.

### Historical evaluation commands

These commands launch paid model runs and require the external services described above. They preserve the historical configuration; exact numerical results are not guaranteed.

```bash
# Run all benchmarks with Claude Sonnet 4.5
for benchmark in revisit-optimization stereo-imaging latency-optimization regional-coverage; do
  python src/benchmark/run_benchmark.py \
  --benchmark $benchmark \
  --bwrap --memory-limit 16G --cpu-quota 800% \
  --all \
  --model anthropic::claude-sonnet-4-5-20250929 \
  --timeout 7200
done

# Run SatNet weeks
python src/satnet_agent/run_benchmark.py \
--bwrap --memory-limit 16G --cpu-quota 800% \
--all \
--model anthropic::claude-sonnet-4-5-20250929 \
--timeout 7200
```

## Dataset Structure

Each benchmark case includes:

```
src/dataset/<benchmark>/cases/<case_id>/
├── mission_brief.md      # Natural language task description
├── manifest.json         # Case metadata and configuration
├── requirements.yaml     # Mission-specific requirements
├── satellites.yaml       # Satellite constellation definition
├── stations.yaml         # Ground station locations
├── targets.yaml          # Observation targets
└── initial_plan.json     # Empty/template plan
```

## Architecture

Four-layer design:

1. **Physics Layer** - SGP4 propagation, slew kinematics, resource modeling (stateless)
2. **Scenario Layer** - State management, action registry, persistence (stateful)
3. **Interface Layer** - MCP tools + Python API
4. **Cognitive Layer** - LLM agent (ReAct loop via Claude Code)

Agents use MCP tools for exploration and Python scripts for bulk optimization.

## Citation

If you use AstroReason-Bench in your research, please cite:

```bibtex
@article{wang2026astroreason,
      title={AstroReason-Bench: Evaluating Unified Agentic Planning across Heterogeneous Space Planning Problems}, 
      author={Weiyi Wang and Xinchi Chen and Jingjing Gong and Xuanjing Huang and Xipeng Qiu},
      year={2026},
      eprint={2601.11354},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2601.11354v1},
}
```

## References

This benchmark integrates the SatNet scheduling problem:

```bibtex
@inproceedings{goh2021satnet,
  title={SatNet: A benchmark for satellite scheduling optimization},
  author={Goh, Edwin and Venkataram, Hamsa Shwetha and Balaji, Bharathan and Wilson, Brian D and Johnston, Mark D},
  booktitle={AAAI-22 Workshop on Machine Learning for Operations Research (ML4OR)},
  year={2021}
}
```

## Data Sources

Benchmark datasets are derived from the following sources:

- **TLE orbital data**: [CelesTrak](https://celestrak.org/)
- **City locations**: [World cities database](https://www.kaggle.com/datasets/juanmah/world-cities) (CC BY 4.0)
- **Ground stations**: [Ground Station Dataset](https://www.kaggle.com/datasets/pratiksharm/ground-station-dataset) (MIT License)

**Note:** Satellite parameters other than orbital elements (e.g., power budgets, data storage, slew rates) are fictional or represent typical values for benchmark purposes.

Datasets are also available on [Hugging Face](https://huggingface.co/datasets/kaupane/astro-reason).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
