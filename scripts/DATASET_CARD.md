---
license: mit
language:
  - en
tags:
  - aerospace
  - satellite-scheduling
  - astrodynamics
  - benchmark
---

# AstroAgentBench

Versioned benchmark files for evaluating complete agent systems and traditional solvers on space mission design tasks. [GitHub](https://github.com/Mtrya/AstroAgentBench) is the canonical source.

Each immutable release tag contains the corresponding complete benchmark tree under `benchmarks/`: cases, verifiers, generators, source inputs, documentation, and binary assets. `release-manifest.json` records the Git commit, export mapping, byte sizes, and SHA-256 checksums. Required evaluation-package/runtime files are included when the source environment installs them. Git symbolic links are stored as target-text files with their modes in the manifest; external targets are never followed.

Download a release with `hf download OWNER/DATASET --repo-type dataset --revision RELEASE --local-dir benchmark-release`, using the repository and release identifiers from the GitHub release. Follow each benchmark's README and the included dependency lock. Verifiers define validity and native scores; scores across different task families are not interchangeable.

The January release retains its historical AstroReason-Bench identity. Its `src/dataset/` maps to `benchmarks/`, and the original source tree is retained in `legacy/src/`. The manifest records external submodule revisions; their source and historical external services are not bundled or asserted to be available. Use the matching GitHub snapshot for its original execution environment.
