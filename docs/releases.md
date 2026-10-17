# Benchmark Releases

GitHub is canonical for source code, benchmark definitions, generators, and source inputs. Hugging Face distributes runnable Harbor tasksets in `kaupane/AstroAgentBench` and supported native sessions in `kaupane/AstroAgentBench-Traces`. The taskset-only layout starts at `v2.0.0`; existing historical releases and tags keep their original contents.

Merge the release tooling into `main` before publishing, then create the release tag on the merged commit. GitHub requires manually dispatched workflows to exist on the default branch. Publish the GHCR runtime first, then the HF taskset using its digest, and publish the trace dataset separately. Close the publication issue only after the remote oracle checks and Data Studio checks pass.

## Runtime image

Create the matching GitHub release tag, then run **Publish Python Runtime** with that tag or its full commit SHA and the same version. It builds `runtimes/python/` from that commit and publishes `ghcr.io/mtrya/astroagentbench-python`. The workflow uses `GITHUB_TOKEN` with `packages: write`; its summary reports the immutable digest reference.

A newly created GHCR package defaults to private. Set its visibility to public in the package settings, then rerun the anonymous-pull check before publishing the taskset. Taskset publication also checks anonymous pull access and the image's source-commit label. The published runtime currently supports Linux amd64.

## Harbor taskset

Install the locked repository dependencies with the evaluation extra. Stage from a full Git commit SHA or release tag and the published runtime digest:

```bash
uv sync --locked --extra evaluation
uv run --locked python scripts/upload_benchmark_datasets.py --revision v2.0.0 --version v2.0.0 --image ghcr.io/mtrya/astroagentbench-python@sha256:DIGEST --output .runtime/hf-release
```

Staging clones the selected Git revision into a temporary checkout and runs that revision's `experiments.evaluate.taskset` exporter. Cases, verifiers, task briefs, profiles, scoring code, and the release card all come from that checkout. The output contains `tasks/`, `registry.json`, `README.md`, `LICENSE`, and `release-manifest.json`. A repeated identical stage succeeds; corrupt or conflicting existing output fails. Revisions predating the Harbor exporter use their original historical release tooling.

Registry entries select one benchmark and split, for example `regional_coverage-test@v2.0.0`. The additional `smoke@v2.0.0` entry selects each family's indexed example case; those seven tasks include oracle solutions. Every canonical case is stored once, even when selected by both a family/split entry and `smoke`. Default limits are 8 CPUs, 16384 MiB memory, a 7200-second agent timeout, and a 600-second verifier timeout. Both task environments use the same image digest. Full source provenance and file SHA-256 checksums are recorded in the release manifest.

Run **Stage or Publish Benchmark Dataset** from `main`, supplying the revision, version, and image digest. The default only stages an Actions artifact. Selecting `publish` requires `HF_TOKEN` with write access to the dataset. Publication verifies that the Git release tag identifies the selected commit, makes one atomic commit on a release branch, downloads it for checksum verification, and creates an immutable HF tag. A matching existing tag is verified and reused; a conflicting tag fails.

The workflow then loads the seven oracle tasks directly from the public HF tag and requires valid results for every selected case. These integration checks use Harbor overrides of 2 CPUs and 4096 MiB to fit the hosted runner; the released defaults remain 8 CPUs and 16384 MiB. Only after the checks pass does it atomically promote the verified files to HF's `main` branch, so the landing page and generated framework commands see the runnable layout. Existing HF tags are never replaced.

The corresponding local publication sequence is:

```bash
uv run --locked python scripts/upload_benchmark_datasets.py --revision v2.0.0 --version v2.0.0 --image ghcr.io/mtrya/astroagentbench-python@sha256:DIGEST --output .runtime/hf-release --publish
uv run --locked --extra evaluation harbor run --repo https://huggingface.co/datasets/kaupane/AstroAgentBench@v2.0.0 --dataset smoke@v2.0.0 --agent oracle -n 1 --jobs-dir results --job-name hf-smoke
uv run --locked --extra evaluation python -m experiments.evaluate.aggregate results/hf-smoke --output results/hf-smoke.jsonl
```

Confirm that all seven expected cases have status `valid`, then repeat the publisher command with `--publish --promote`. The Git ref in `--repo URL@VERSION` pins the repository tree; `--dataset NAME@VERSION` separately selects an entry in that tree's registry. Check the HF landing page and its “Use this dataset” command before announcing the release.

## Native session traces

The trace publisher uses the frozen [Zenodo v1 record](https://doi.org/10.5281/zenodo.23084447), rather than the concept DOI that can resolve to future versions. It pins the archive manifest's SHA-256 and selects Claude Code `projects/...jsonl` and Codex `rollout-*.jsonl` sessions, preserving experiment/run paths. OpenCode, Kimi CLI, other incompatible formats, and non-session artifacts remain available through Zenodo. The selected files retain the archive's CC BY 4.0 attribution.

Run **Stage or Publish Agent Traces**, or stage locally:

```bash
uv run --locked python scripts/upload_agent_traces.py --output .runtime/hf-traces
```

This downloads the relevant compressed archive shards, verifies their checksums, and extracts only selected sessions. The download path requires `zstd`. To reuse an existing redacted archive, add `--archive DIRECTORY`; that directory must contain `run-archive-manifest.json` and `run-archive/` with files matching the pinned manifest. Raw run directories are not accepted as an archive.

Staging verifies every selected session's checksum and JSONL structure, then screens decoded text for known credential patterns, secret-bearing fields, and personal home paths. Encrypted reasoning payloads are retained as opaque data. A screening failure stops publication and names the file and category without printing the matched value. Review such failures before preparing a corrected source; do not modify the archived evidence in place.

Add `--publish`, or select the workflow's publication option, to create the public traces dataset, upload one atomic release, verify it through `snapshot_download`, tag it `zenodo-23084447`, and update its default branch. After publication, verify native format auto-detection and open both a Claude Code and a Codex session in Data Studio. Linking the traces dataset from the repository README or paper waits for that viewer check. A merged code change alone does not establish publication or viewer acceptance.
