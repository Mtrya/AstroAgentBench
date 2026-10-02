[English](../../../../docs/benchmark_contract.md) | 中文

# Benchmark 契约
<!-- i18n-source-sha256: 65a1a05a944dd331ff1f95d2cc3afc74be4a1f4bc59d8579be25115b39e1fdaa -->

本文档规定了本仓库在 benchmark 布局、公共入口脚本以及 CI 强制执行方面的契约。

该契约只对列入 `benchmarks/finished_benchmarks.json` 的 benchmark 强制执行。仍在开发中的 benchmark 由仓库惯例约束，暂不纳入严格的 CI 检查。

## 已完成 benchmark 的元数据

`benchmarks/finished_benchmarks.json` 是判定 benchmark 是否已完成的唯一事实来源。

每个已完成 benchmark 的条目记录：

- benchmark 名称
- 是否应在专用 CI 中运行数据集生成器的可复现性检查
- 哪些数据集路径属于生成器拥有的规范输出

只有在公共 README、数据集布局、生成器、验证器和测试都可以视为稳定之后，才应把某个 benchmark 提升为已完成状态。

## benchmark 的必备结构

每个已完成的 benchmark 必须位于 `benchmarks/<name>/` 下，并包含：

- `README.md`
- `dataset/`
- `splits.yaml`
- 生成器入口脚本：`generator.py` 或 `generator/run.py`
- 验证器入口脚本：`verifier.py` 或 `verifier/run.py`

可选：

- `visualizer.py` 或 `visualizer/run.py`
- `dataset/index.json`
- `dataset/README.md`
- `sources/`，存放紧凑的、由 benchmark 自有的生成器输入快照及其来源说明

已完成的 benchmark 不允许存在其他被 git 追踪的顶层条目。

## 入口脚本的调用方式

入口脚本的调用方式与文件布局对应：

- **顶层脚本**（`generator.py`、`verifier.py`、`visualizer.py`）：在仓库根目录下直接调用，写作 `python benchmarks/<name>/<entrypoint>.py ...`。
- **包入口脚本**（`generator/run.py`、`verifier/run.py`、`visualizer/run.py`）：在仓库根目录下以模块方式调用，写作 `python -m benchmarks.<name>.<entrypoint_pkg>.run ...`。

不要让同一个入口脚本同时支持这两种调用方式。（这是公共契约的一部分，但契约校验器目前只挑选第一个匹配的入口脚本，两者同时存在时也不会报错。）也不要用引导 hack（`sys.path` 手术、伪造运行时包之类）来强行让嵌套的 `run.py` 能作为直接路径脚本运行。

可视化工具是供人和 VLM 使用的可选检查工具。它们应当输出图表、图片或视频，而不是机器可读的旁路产物。benchmark 提供可视化工具时，为保持一致性，优先使用具名的输入参数：

```bash
python -m benchmarks.<name>.visualizer.run <command> --case-dir <case_dir>
python -m benchmarks.<name>.visualizer.run <command> --case-dir <case_dir> --solution-path <solution_path>
```

## 数据集契约

已完成 benchmark 的规范数据集布局为：

```text
dataset/
├── example_solution.json  # required, one minimal runnable example (same schema as a real solution)
├── cases/
│   └── <split>/
│       └── <case_id>/
├── index.json      # optional
└── README.md       # optional
```

规则：

- `dataset/cases/` 是必需的。
- 已完成 benchmark 的规范提交布局为 `dataset/cases/<split>/<case_id>/`。
- 子集名称是 benchmark 自有的路径段，通过 `splits.yaml` 校验。
- 测试实例标识符由各 benchmark 自行定义。CI 不强制要求 `case_####` 这样的命名格式。
- 数据集根目录必须包含 `example_solution.json`、`example_solution.yaml` 或 `example_solution.yml` 之一，这样 CI 才能自动针对真实的 benchmark 测试实例运行公共验证器。该文件必须包含**单个**解对象，其 schema 与按测试实例组织的普通解文件相同（而不是从测试实例 ID 到解的映射）。
- `index.json` 是可选的。如果存在，它属于 benchmark 元数据，而不是判定完成状态的第二事实来源。它可以包含可选的 `example_smoke_case`（字符串）：一个相对测试实例路径，例如 `test/case_0001`，在 `dataset/cases/` 下解析，用于验证器冒烟测试。省略该字段时，CI 使用 `dataset/cases/<split>/` 下按字典序排在第一的测试实例目录。
- 生成器不得写入 `dataset/README.md`。
- 允许存在其他被追踪的数据集文件，前提是它们属于 benchmark 自有的公共产物，并在 benchmark README 中有文档说明。
- `dataset/source_data/` 可以用作下载/缓存目录，但必须保持 git 忽略状态，且不得要求在运行生成器之前就已存在。

## 单位约定（推荐，非 CI 强制）

benchmark 数据集应一致地编码物理单位：

- 线性量：米（键名后缀为 `_m`；当某个键是无量纲时，需在 README 中说明）。
- 面积量：平方米。
- 时间长度：秒（后缀为 `_s` 或 `_sec`，具体以该 benchmark 的文档为准）。
- 速度量：米每秒（后缀为 `_m_s` 或同等含义的、已文档化的命名）。
- 角度量：度（后缀 `_deg`）或弧度（后缀 `_rad`），二者择一。
- 时间戳：带 `Z` 或显式 UTC 偏移的 ISO 8601 格式。

有助于提高清晰度时，优先采用 SI 风格的键名和取值；但如果小时这类非 SI 时间单位本就是该问题惯用的表述，并且已在 benchmark README 中写清楚，benchmark 也可以使用非 SI 时间单位。

## 生成器契约

已完成 benchmark 的生成器必须满足以下条件：

- 已完成的 benchmark 必须提交 benchmark 本地的 `splits.yaml`。
- **顶层** `generator.py`：可运行方式为 `python benchmarks/<name>/generator.py ...`。
- **嵌套** `generator/run.py`：可运行方式为 `python -m benchmarks.<name>.generator.run ...`。
- 复现规范数据集时必须显式给出 YAML 路径：
  - `python benchmarks/<name>/generator.py benchmarks/<name>/splits.yaml`
  - `python -m benchmarks.<name>.generator.run benchmarks/<name>/splits.yaml`
- 缺少必需的 YAML 路径时，运行必须失败并输出用法信息。已完成的 benchmark 不再保留无参数的规范生成路径。
- 提交的 `splits.yaml` 是 benchmark 自有的公共配置，不是占位符。它应当足够清晰地呈现预期的数据集构建参数，让读者不必从 Python 代码里反推生成器的默认值。
- 数据集构建参数应放在 YAML 中。纯粹的操作性控制项（如 `--help`），以及在确有理由时保留的 benchmark 特定运行时开关（如强制刷新或强制下载行为），可以作为可选 CLI 参数保留。
- 已完成 benchmark 的规范生成必须使用 benchmark 自有的输入快照。它必须能在没有网络访问、也没有现成的 `dataset/source_data/` 缓存的情况下运行。请保留规范化的源数据快照以及一份 `sources/manifest.json`，其中记录上游来源、规范化说明和文件 SHA-256 哈希；在使用这些文件之前先校验哈希。生成器包中已有的固定版本目录和查找表仍然算作合规的源数据快照。
- `dataset/source_data/` 下的运行时暂存内容保持不被追踪。替换过期的暂存缓存时，应当恢复已固定版本的输入，而不是去下载新的上游版本。明确属于维护性质的导入可以使用单独的源目录或归档，但必须记录各自不同的来源说明。

测试实例规范应当由参数（种子、缩放规则、采样等）算法推导得出，而不是来自手工维护的逐实例元组列表。不建议硬编码精心挑选的列表（如 `base_specs` 或 `BASE_SPECS`）；可参考 `stereo_imaging` 生成器的做法（例如由种子驱动的采样）。

### `splits.yaml` 的结构

已完成的 benchmark 必须提交一份带顶层 `splits:` 映射的 `splits.yaml`。支持两种共用结构：

**子集参数**，用于按子集构建测试实例的算法型生成器：

```yaml
splits:
  easy:
    seed: 42
    case_count: 5
    max_satellites: 3
  hard:
    seed: 142
    case_count: 5
    max_satellites: 12
```

**子集分配**，用于把已有测试实例 ID 划入各子集的固定测试实例型 benchmark：

```yaml
splits:
  test:
    - case_001
    - case_002
  train:
    - case_003
    - case_004
```

规则：

- 只有单个子集的 YAML 也是合法的。
- 每个 benchmark 的 `splits:` 映射只使用一种结构，不要把分配列表和参数映射混在一起。
- benchmark 自有的子集字段仍由各 benchmark 自行定义，但须放在共用的外层 `splits:` 结构之内。
- 不易看懂的 benchmark 自有字段应加文档说明。当行内 YAML 注释有助于解释参数含义或它对数据集构建的影响时，优先写行内注释。

## 验证器契约

已完成 benchmark 的验证器必须满足以下条件：

- **顶层** `verifier.py`：可运行方式为 `python benchmarks/<name>/verifier.py ...`。
- **嵌套** `verifier/run.py`：可运行方式为 `python -m benchmarks.<name>.verifier.run ...`。
- 公共 CLI 接受两个位置参数：
  - `case_dir`
  - `solution_path`
- 任何额外的 CLI 选项都必须是可选的。
- 验证器必须能按文档所述方式运行，并且必须能够加载规范测试实例而不崩溃。

数据集层面的 `example_solution.json` 或 `example_solution.yaml` 是已完成 benchmark 做验证器冒烟测试的首选约定。它保存一个最小可运行解，其 schema 与真实提交一致。当冒烟测试实例不是 `dataset/cases/<split>/` 下字典序第一的目录时，用 `index.json` 中的 `example_smoke_case` 与测试实例目录配对；该字段的值是相对路径，例如 `test/case_0001`。这些只是可运行的示例，不是基线。

### 参考系（建议，非 CI 强制）

参考系的选择因 benchmark 而异。对于使用地心参考系的验证器：

- **地固系（ECEF）**：在精度要求较高时，优先使用 ITRF 之类有明确定义的实现。
- **惯性系（ECI）**：在适用时，优先使用 GCRF 之类的标准天球参考系。
- 在同一个验证器内部保持使用同一套天体力学工具栈，避免坐标系混用带来的不一致。
- 如果地球定向参数（EOP）之类因素会影响解，请在 benchmark README 中写明处理策略。

以上都是建议而非严格的 CI 要求：有些 benchmark 出于清晰的考虑会使用简化的参考系。

## 强制执行的 CI 检查

对于已完成的 benchmark，CI 强制检查：

- benchmark 是否出现在 `benchmarks/finished_benchmarks.json` 中
- 必需的顶层文件和目录是否存在
- `dataset/cases/<split>/<case_id>/` 下的规范测试实例布局
- benchmark 本地 `splits.yaml` 是否存在且结构合法
- 数据集根目录是否存在用于验证器冒烟测试的示例解
- 是否没有被追踪的 `dataset/source_data/`
- 是否没有被追踪的编辑器备份产物（例如以 `~` 结尾的文件）
- benchmark 的生成器/验证器/可视化工具代码中是否存在 `sys.path` hack
- benchmark 的生成器/验证器/可视化工具代码中是否存在 `from benchmarks.` 导入
- 每种入口脚本形态（直接脚本还是 `python -m`）下，生成器 `--help`、生成器无参数时失败，以及验证器冒烟测试是否通过
- 仓库测试是否通过
- 对标记了 `"repro_ci": true` 的 benchmark，通过 `scripts/check_finished_benchmark_repro.py` 执行可复现性检查

GitHub Actions 中运行：

- PR/push CI（`ci.yml`）：测试加契约校验
- PR/push 可复现性检查（`benchmark-repro.yml`）：针对标记了 `"repro_ci": true` 的 benchmark 执行生成器可复现性检查
- 数据集暂存与发布（`sync-datasets.yml`）：手动触发；默认只暂存产物，只有显式选择 `publish` 时才上传到 Hugging Face。发布 GitHub release 并不会触发它。参见 [Benchmark Releases](releases.md)。

可复现性工作流只比较 `generated_paths` 中由生成器拥有的数据集输出，因为已完成的 benchmark 可能还保留着有文档说明的手写数据产物，例如数据集层面的说明。此外，它会用该 benchmark 已被追踪、且位于 `generated_paths` 之外的数据集文件来补齐每个暂存副本，并要求重新生成之后这些文件依然存在且逐字节一致。生成器只拥有它声明的那些路径：既不能删除，也不能重写其余人工维护的文件。

## 已写入文档但尚未完全自动化的部分

以下内容属于公共契约的一部分，即使 CI 目前还没有完全强制执行：

- benchmark 的公共代码和公共产物不得引用仅限内部使用的指导材料，例如 `AGENTS.md`、`CLAUDE.md`、`GEMINI.md` 或 `docs/internal/`
- 公共验证器/生成器/可视化工具代码应避免路径 hack 之类脆弱的引导做法
- 面向 benchmark 的公共数据和注释，应避免会泄露 benchmark 身份的措辞，比如明确告诉 space agent 它正身处验证 harness 之中
- 本仓库始终不保存任何解题结果；示例解只用于验证器冒烟测试，不作为基线