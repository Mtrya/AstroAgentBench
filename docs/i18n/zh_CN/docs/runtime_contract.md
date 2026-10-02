[English](../../../../docs/runtime_contract.md) | 中文

# 运行时基座契约
<!-- i18n-source-sha256: cdf92f78921d902a8d1c7bfe1b4ab65f1b15ab6924a91589de0497b708d07f8b -->

`runtimes/` 拥有独立自洽的执行环境。运行时基座不得导入或调用 benchmark、experiment 或 solver 层的代码。评测环节负责准备工作区，并通过 CLI 与文件契约调用上述各层。

`runtimes/python/` 提供默认的 Python 3.13.11 科学计算镜像，其基础镜像以 digest 固定。`requirements.in` 声明依赖项，`requirements.txt` 锁定传递依赖的版本与哈希。使用 `docker build -t astroagentbench-python:latest runtimes/python` 构建。若要主动刷新锁文件，运行 `uv pip compile runtimes/python/requirements.in --generate-hashes -o runtimes/python/requirements.txt`，然后重新构建并校验 benchmark 示例。

镜像中不包含任何必需的 agent 运行框架或 provider 配置。Harbor 适配器自行安装所需的 CLI，或者由研究者提供自定义镜像。`runtime.yaml` 记录镜像名、Dockerfile 与构建上下文，供 CI 自动发现。每个构建上下文都必须留在其所属运行时目录之内。

任务在权威校验时会启用一个全新的运行时实例，因此 agent 安装的软件包以及对文件系统的改动都不会被继承。开展固定环境的评测并对外报告结果时，请使用不可变的镜像 digest。声明的资源与网络配置属于已准备好的任务和 Harbor 作业；它们能否真正生效取决于环境提供方。