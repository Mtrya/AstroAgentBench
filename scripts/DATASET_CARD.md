---
license: other
license_name: mixed-source-licenses
license_link: README.md#licensing-and-attribution
language:
  - en
tags:
  - rl-environment
  - harbor
  - aerospace
  - satellite-scheduling
  - astrodynamics
  - benchmark
---

# AstroAgentBench

Harbor tasks for evaluating complete agent systems on space mission design. [GitHub](https://github.com/Mtrya/AstroAgentBench/tree/{{SOURCE_COMMIT}}) is the canonical source for benchmark definitions, generators, and source inputs. This release is `{{RELEASE}}`, generated from Git commit `{{SOURCE_COMMIT}}`.

## Run a taskset

Install Harbor 0.23.0 with Python 3.13 and have Docker available. Run the seven reference checks, one per benchmark family:

```bash
harbor run --repo https://huggingface.co/datasets/{{DATASET_REPO}}@{{RELEASE}} --dataset smoke@{{RELEASE}} --agent oracle -n 1 --jobs-dir results --job-name astroagentbench-smoke
```

`registry.json` lists one dataset per benchmark and split, such as `regional_coverage-test@{{RELEASE}}` and `spot5-single_orbit@{{RELEASE}}`. Select one with `--dataset` and supply your Harbor agent adapter and model. Only the seven tasks in `smoke` include oracle solutions. Native scores have benchmark-specific units and directions; do not combine scores across families.

## Contents and resources

Each directory under `tasks/` contains a task brief, case inputs, environment Dockerfile, and independent verifier. The solving and verifier images share a public runtime pinned by digest. Tasks default to 8 CPUs, 16384 MiB memory, 7200 seconds of agent execution, 600 seconds of verification, public network access, and 10240 MiB requested storage. Docker does not enforce the requested storage as a disk quota. Harbor resource overrides are recorded with each run.

`release-manifest.json` records the Git source, runtime image, byte sizes, and SHA-256 checksums. Dataset versions match the GitHub release tags. Releases from `v2.0.0` use this taskset layout; historical tags retain their original contents. The complete raw source tree remains on GitHub.

## Licensing and attribution

This release combines project code under the root [MIT license](LICENSE) with third-party inputs under their own terms. The MIT license does not replace those source licenses. See the [benchmark READMEs and source manifests at the release commit](https://github.com/Mtrya/AstroAgentBench/tree/{{SOURCE_COMMIT}}/benchmarks) for provenance.

The SPOT5 `.spot` inputs are distributed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), from Zequn Wei and Jin-Kao Hao's [Mendeley Data release, version 1 (2021), DOI 10.17632/2kbzg9nw3b.1](https://data.mendeley.com/datasets/2kbzg9nw3b/1). The bundled source files are unchanged; benchmark case files are derived from them. Retain this attribution and indicate any further modifications when redistributing those data.
