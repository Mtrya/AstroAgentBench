# Benchmark Releases

GitHub is canonical. Hugging Face receives complete versioned benchmark files, including code, vendored generator inputs, and binary assets, in one dataset repository. A GitHub release identifier also names the immutable HF tag. Experimental run archives and paper publication are separate operations.

Stage from a full Git commit SHA or release tag:

```bash
uv run --locked python scripts/upload_benchmark_datasets.py --revision FULL_COMMIT_SHA --version RELEASE --output .runtime/hf-release
```

This command performs no upload. It exports Git objects rather than local working files, verifies byte sizes and SHA-256 checksums, and atomically installs the staged directory. A repeated identical stage succeeds; conflicting or corrupt existing output fails. `release-manifest.json` records the source commit and path mapping. Review the stage before publication.

Current releases export the entire `benchmarks/` tree, root dependency/license files, and the evaluation package/runtime files needed by the source installation. January releases explicitly map `src/dataset/` to `benchmarks/` and preserve the original `src/` tree under `legacy/src/`, with external submodule commit identities in the manifest. Symbolic links retain their target bytes as ordinary files and their Git modes in the manifest; the exporter never reads external targets. This packaging does not modernize or establish availability of historical external services.

The **Stage or Publish Benchmark Dataset** workflow takes a source revision and matching release identifier. Its default only stages and retains an Actions artifact. Run it from the current implementation branch. Publication requires selecting `publish` and configuring `HF_TOKEN` and `HF_DATASET_REPO_ID` for an existing dataset repository. The local equivalent adds `--repo-id OWNER/DATASET --publish`.

Publication first verifies that the matching Git release tag identifies the staged commit, then creates one atomic commit on a version-specific staging branch, downloads it for checksum verification, then creates the release tag. Rerunning after an interrupted upload or before tag creation resumes the same content. A matching existing tag is verified and reused; a conflicting version fails. Neither a published tag nor the dataset's main branch is overwritten. Remote authentication, upload limits, and tag permissions require validation during an authorized publication; local staging tests do not establish those external operations.
