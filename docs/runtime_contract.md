# Runtime Contract

`runtimes/` owns standalone execution environments. A runtime must not import or invoke benchmark, experiment, or solver code. Evaluation prepares workspaces and invokes those layers through CLI/file contracts.

`runtimes/python/` provides the default Python 3.13.11 science image, with its base pinned by digest. `requirements.in` declares its dependencies; `requirements.txt` pins transitive versions and hashes. Build it with `docker build -t astroagentbench-python:latest runtimes/python`. To refresh the lock deliberately, run `uv pip compile runtimes/python/requirements.in --generate-hashes -o runtimes/python/requirements.txt`, then rebuild and validate benchmark examples.

The image contains no mandatory agent harness or provider settings. Harbor adapters install their own CLIs, or researchers provide a custom image. `runtime.yaml` records the image name, Dockerfile, and build context for CI discovery. Each build context must remain inside its runtime directory.

The task uses a fresh runtime instance for authoritative verification, so agent-installed packages and filesystem mutations are not inherited. Use an immutable image digest for reported fixed-environment evaluations. Declared resource and network settings belong to the prepared task and Harbor job; enforcement depends on the environment provider.
