[English](../../../../docs/solver_contract.md) | 中文

# 求解器契约
<!-- i18n-source-sha256: 3af9ce83c327ea139429c155a7ea2a3c9dac7cc9b60f8285da7193bdd83a2fc1 -->

本文件定义 `solvers/` 的公开契约。

这份契约为 experiments 提供了一种稳定的方式去调用传统的非 agentic 方法，而不必强行要求每个求解器都采用同一种语言、包管理器或运行时模型。

## 定位

`solvers/` 负责可复用的传统非 agentic 方法。

典型例子包括：

- 启发式求解器
- 基于优化的基线方法
- 可复现的经典流程
- 以 fixture 为支撑的查表式基线方法
- 有文献引用支撑的基线方法

求解器读取 benchmark 的测试实例文件，并产出符合 benchmark 形态的解文件。benchmark 不得依赖求解器。

求解器必须是独立自洽的方法实现。它们不应导入 benchmark 内部的函数、类或模块，也不应调用 benchmark 的验证器或其他 benchmark 可执行程序。如果某个求解器需要前置检查，应当把这些检查实现在求解器自己的代码里。

experiments 负责官方的“求解器对 benchmark”编排流程。它们可以通过 CLI/文件契约运行求解器入口脚本和 benchmark 验证器入口脚本。

## 目录结构

求解器按 benchmark 分组：

```text
solvers/
├── finished_solvers.json
└── <benchmark>/
    └── <solver>/
        ├── README.md
        ├── setup.sh          # required when repro_ci is true
        ├── solve.sh          # required when repro_ci is true
        ├── test.sh           # optional solver-local test entrypoint
        ├── src/              # optional
        ├── tests/            # optional solver-local tests
        └── assets/           # optional
```

已注册求解器的路径由注册表中的字段推导得出，即 `solvers/<benchmark>/<solver>/`。注册表本身并不单独携带 `path` 字段。

## 可运行求解器契约

可运行的求解器暴露两个 shell 入口脚本：

```bash
./setup.sh
./solve.sh <case_dir> [config_dir] [solution_dir]
```

`setup.sh` 用于准备求解器本地的依赖、构建产物或运行时状态。它也可以什么都不做。

`solve.sh` 接收以下参数：

- `case_dir`：必填，benchmark 测试实例目录
- `config_dir`：可选，由 experiments 管理的配置目录
- `solution_dir`：可选，产出解文件的目标目录

experiments 通常应当显式传入这两个可选参数。求解器应把主要解产物写入 `solution_dir`，并在遇到不支持的测试实例或执行失败时以非零状态码退出。

求解器代码可以是 Python、shell、C、C++、Java、Kotlin、Julia、MiniZinc、Rust，或其他任何语言。shell 入口脚本就是边界所在。

求解器入口脚本不得依赖仓库的 Python 工作环境。契约校验在执行 `setup.sh`、`solve.sh` 和 `test.sh` 时，会从继承而来的环境变量中清除所有 Python/工作区相关的痕迹。具体来说，校验器会移除继承的 `VIRTUAL_ENV`、`PYTHONPATH`、`PYTHONHOME`、`PYTHONUSERBASE`、其他继承的 `PYTHON*` 变量，uv 的项目发现配置（如 `UV_PROJECT`、`UV_WORKING_DIR`、`UV_ENV_FILE`、`UV_CONFIG_FILE`），以及 `PATH` 中指向仓库本地的条目。与此同时，校验器保留常规的系统访问能力，包括 `PATH`、locale、临时目录、代理、证书、`HOME`、显式设置的 `SOLVER_*` 值，以及 uv 的包解析配置，如 `UV_INDEX_URL`、`UV_DEFAULT_INDEX`、`UV_EXTRA_INDEX_URL`、各索引的 `UV_INDEX_*` 凭据、`UV_FIND_LINKS`、`UV_KEYRING_PROVIDER`、`UV_CACHE_DIR` 和由运行器管理的 Python 设置。校验器还会设置 `UV_NO_PROJECT=1`、`UV_NO_CONFIG=1` 和 `UV_NO_ENV_FILE=1`，以防 `uv` 的引导命令从求解器目录逐级向上遍历、进而发现仓库工作区。

`uv` 可以作为引导工具使用，例如在 `setup.sh` 里执行 `uv venv` 或 `uv pip install`。但不要在求解器入口脚本中使用 `uv run`，因为它可能在你不注意的情况下直接以仓库项目环境执行。Python 求解器应当创建或复用求解器本地的虚拟环境，在需要时写入 `.solver-env` 文件，并通过 `SOLVER_PYTHON` 或其他由求解器自己掌握的运行时来运行 `solve.sh` / `test.sh`。

## setup 阶段的产物

`setup.sh` 可以创建或更新求解器本地的产物，例如：

- `.venv/` 下的 Python 虚拟环境
- 包含简单 `SOLVER_*=` 赋值的 `.solver-env` 文件
- C/C++ 的构建目录与可执行文件
- Rust 的 `target/` 产物以及由 Cargo 管理的依赖
- Java/Kotlin 的 jar 包以及 Gradle/Maven 的产物
- Julia 的 depot 或已实例化的项目环境
- MiniZinc 的模型本地后端或可用性检查

setup 阶段生成的产物应当留在求解器本地；当它们因机器而异或属于可复现的构建产物时，应加入忽略规则。

`.solver-env` 是一种约定，而非 CI 强制的要求。它存在时，应当是一个简单的交接文件，用于传递如下取值：

```text
SOLVER_VENV_DIR=/abs/path/to/.venv
SOLVER_PYTHON=/abs/path/to/.venv/bin/python
```

experiments 的运行器可以读取该文件，并把 `SOLVER_*` 取值传给 `solve.sh`，但求解器在 `setup.sh` 跑完之后仍应当能够被直接运行。

## 求解器本地测试

`test.sh` 是可选的求解器本地测试边界。

它可以运行任意该语言原生的测试命令，包括 `pytest`、`cargo test`、`ctest`、`mvn test`、`gradle test`，或 Julia 的测试运行器。仅供测试使用的依赖应当由求解器本地的测试流程安装，或在求解器所选的环境中已经可用。

顶层 pytest 不得收集求解器本地的测试。仓库范围的 pytest 面向 benchmark 测试和仓库工具测试。求解器测试应当放在求解器目录下，并通过 `test.sh` 触达。

## CI 强制的不变量

`scripts/validate_solver_contract.py` 强制执行全仓库范围的不变量：

- `solvers/finished_solvers.json` 符合文档规定的 schema。
- 每条注册表记录都解析到 `solvers/<benchmark>/<solver>/`。
- 每个已注册的求解器都有 `README.md`。
- `repro_ci: true` 的记录带有可执行的 `setup.sh` 和 `solve.sh`。
- `repro_ci: true` 的记录至少声明了一条测试实例路径。
- 已声明的测试实例路径和非空的 fixture 路径都真实存在。
- 已存在的 `test.sh` 文件是可执行的。
- 顶层 pytest 的作用域不包含求解器本地测试。
- 求解器的运行时代码不会跨 `benchmarks/`、`experiments/`、`runtimes/` 或其他求解器进行导入或执行。
- 求解器入口脚本在不继承仓库 Python 环境状态的情况下也能运行。
- 求解器入口脚本不使用 `uv run` 去发现仓库工作区。
- `repro_ci: true` 的记录会在其声明的测试实例上运行 `setup.sh` 和 `solve.sh`。
- 检测到的求解器本地 `test.sh` 入口脚本会作为求解器契约校验的一部分被运行。

CI 只约束边界与可发现性，并不强制规定语言、包管理器、构建系统或内部源码布局。

## 完成态求解器注册表

`solvers/finished_solvers.json` 是一份面向可复现性与 CI 的注册表，不是 experiments 的证据/报告注册表。

每条记录形如：

```json
{
  "benchmark": "aeossp_standard",
  "solver": "greedy_lns",
  "repro_ci": false,
  "repro_ci_reason": "too_expensive",
  "case_and_fixture_paths": []
}
```

对于 `repro_ci: true`，`case_and_fixture_paths` 中包含若干对象：

```json
{
  "case_path": "benchmarks/spot5/dataset/cases/test/8",
  "fixture_path": "solvers/spot5/reference_lookup/assets/solutions/8.spot_sol.txt"
}
```

当 CI 只需执行 setup/solve、不与固定的输出 fixture 比对时，`fixture_path` 可以是空字符串。

当 `repro_ci` 为 false 时，建议填写 `repro_ci_reason`，但 CI 并不强制要求。常用取值包括：

- `citation_based`
- `too_expensive`
- `requires_external_toolchain`
- `requires_external_data`
- `not_reproducible_yet`

证据类型、验证器命令、结果布局、求解器专属配置和报告元数据都由 experiments 的 profile 负责。不要把 `evidence_type`、`runnable`、求解器路径、验证器命令或冒烟测试标签之类的 experiments 元数据写进 `solvers/finished_solvers.json`。

## 归属边界

求解器可以拥有：

- 可复用的求解器实现
- 求解器本地的依赖与环境文件
- 求解器本地的校验与调试辅助工具
- 方法所需的、由求解器自己维护的资产，并记录其来源说明

求解器不得沦为以下各层的共享依赖层：

- `benchmarks/`
- `experiments/`
- `runtimes/`

求解器在运行时同样不得依赖上述各层。读取文档中描述的测试实例文件是允许的；导入或执行 benchmark、experiment、runtime 或其他求解器的内部实现则不允许。

## 独立自洽原则

求解器代码应当保持独立自洽。如果另一个求解器需要类似的行为，应重复那一小段代码，或者定义一种公开的文件格式，而不是导入另一个求解器的内部实现。

如果日后确实需要共享代码，它也应当保持在本层内部，而不是引入一个全仓库范围的共享抽象——后者会削弱 benchmark 与方法之间的边界。