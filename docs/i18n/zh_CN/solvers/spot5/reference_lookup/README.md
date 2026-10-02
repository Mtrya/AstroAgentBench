[English](../../../../../../solvers/spot5/reference_lookup/README.md) | 中文

# SPOT5 参考解查找求解器
<!-- i18n-source-sha256: 8857736909eda020b0a7e7dbce95dc378e9b46be235881646228f47f6ea64e0e -->

本求解器是一个以 fixture 为支撑的 SPOT5 查表式基线。

它通过 SHA-256 哈希识别已知的 SPOT5 实例文件，并把匹配的参考解复制到指定的解目录。该求解器可复现，结果也经过验证器检验；但它不是通用的 SPOT5 求解器，也不对未见过的实例作任何保证。

## 契约

```bash
./setup.sh
./solve.sh <case_dir> [config_dir] [solution_dir]
```

`config_dir` 属于 experiments 层，可以省略。省略时 `solution_dir` 默认为 `solution/`。

对于支持的测试实例，求解器写出以下文件：

- `solution.spot_sol.txt`：SPOT5 的主要求解结果产物
- `status.json`：查找元数据

对于不支持的测试实例，求解器会以非零状态退出；当解目录可用时，它还会写出 `status.json`，内容为 `status: "unsupported_case"`。

## 数据溯源

解 fixture 均复制自 `tests/fixtures/spot5_val_sol/`。这些参考解取自 DCKP-RSOA 仓库，在 SPOT5 benchmark README 中有相关说明。
