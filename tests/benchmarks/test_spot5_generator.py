import json
import sys
import subprocess
import zipfile
from pathlib import Path

import pytest

import benchmarks.spot5.generator as generator_module
from benchmarks.spot5.generator import (
    build_case_dataset,
    build_local_directory_provenance,
    collect_spot_files,
    extract_zip_tree,
)


PROJECT_ROOT = Path(__file__).parent.parent.parent
SMALL_SPOT = "8\n0\n"
MULTI_SPOT = "1502\n0\n"


def test_build_case_dataset_from_local_source_dir(tmp_path):
    source_dir = tmp_path / "raw"
    source_dir.mkdir()

    (source_dir / "8.spot").write_text(SMALL_SPOT)
    (source_dir / "1502.spot").write_text(MULTI_SPOT)

    output_dir = tmp_path / "output"
    build_case_dataset(
        spot_files=collect_spot_files(source_dir),
        output_dir=output_dir,
        provenance=build_local_directory_provenance(source_dir),
        split_assignments={
            "single_orbit": ["8"],
            "multi_orbit": ["1502"],
            "test": ["8"],
        },
        example_smoke_case="single_orbit/8",
    )

    index_path = output_dir / "index.json"
    assert index_path.exists()

    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert index["benchmark"] == "spot5"
    assert index["example_smoke_case"] == "single_orbit/8"
    assert any(item["path"] == "cases/single_orbit/8" for item in index["cases"])
    assert any(item["path"] == "cases/multi_orbit/1502" for item in index["cases"])
    assert any(item["path"] == "cases/test/8" for item in index["cases"])
    assert index["source"]["kind"] == "local_directory"

    assert not (output_dir / "example_solution.json").exists()
    assert (output_dir / "cases" / "single_orbit" / "8" / "8.spot").read_text() == SMALL_SPOT
    assert (output_dir / "cases" / "multi_orbit" / "1502" / "1502.spot").read_text() == MULTI_SPOT
    assert (output_dir / "cases" / "test" / "8" / "8.spot").read_text() == SMALL_SPOT


def test_default_cli_rebuilds_published_instances_from_local_snapshot(tmp_path):
    benchmark_root = PROJECT_ROOT / "benchmarks" / "spot5"
    output_dir = tmp_path / "dataset"
    subprocess.run(
        [sys.executable, str(benchmark_root / "generator.py"),
         str(benchmark_root / "splits.yaml"), "--output-dir", str(output_dir)],
        check=True,
    )
    expected_index = json.loads((benchmark_root / "dataset/index.json").read_text())
    actual_index = json.loads((output_dir / "index.json").read_text())
    assert actual_index == expected_index
    for case in expected_index["cases"]:
        relative = Path(case["path"]) / case["instance_file"]
        assert (output_dir / relative).read_bytes() == (benchmark_root / "dataset" / relative).read_bytes()


def test_extract_zip_tree_extracts_nested_zip_contents(tmp_path):
    inner_zip = tmp_path / "inner.zip"
    with zipfile.ZipFile(inner_zip, "w") as archive:
        archive.writestr("8.spot", "8\n0\n")

    outer_zip = tmp_path / "outer.zip"
    with zipfile.ZipFile(outer_zip, "w") as archive:
        archive.write(inner_zip, arcname="wrapper/spot5.zip")

    extract_dir = tmp_path / "extracted"
    extract_zip_tree(outer_zip, extract_dir)

    extracted_spot = extract_dir / "wrapper" / "spot5" / "8.spot"
    assert extracted_spot.exists()
    assert extracted_spot.read_text() == "8\n0\n"


def test_main_requires_splits_yaml(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["generator.py"])

    with pytest.raises(SystemExit) as exc_info:
        generator_module.main()

    captured = capsys.readouterr()
    assert exc_info.value.code == 2
    assert "usage:" in captured.err.lower()


def test_main_builds_dataset_from_local_nested_zip(monkeypatch, tmp_path):
    inner_zip = tmp_path / "inner.zip"
    with zipfile.ZipFile(inner_zip, "w") as archive:
        archive.writestr("SPOT5 benchmarks/8.spot", SMALL_SPOT)

    outer_zip = tmp_path / "outer.zip"
    with zipfile.ZipFile(outer_zip, "w") as archive:
        archive.write(
            inner_zip,
            arcname="Benckmark inctances of the (SPOT5) daily photograph scheduling problem/SPOT5 benchmarks.zip",
        )

    splits_path = tmp_path / "splits.yaml"
    splits_path.write_text(
        "example_smoke_case: single_orbit/8\n"
        "splits:\n"
        "  single_orbit:\n"
        "    - 8\n",
        encoding="utf-8",
    )

    output_dir = tmp_path / "output"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "generator.py",
            str(splits_path),
            "--zip-path",
            str(outer_zip),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert generator_module.main() == 0
    assert (output_dir / "cases" / "single_orbit" / "8" / "8.spot").read_text() == SMALL_SPOT
    index = json.loads((output_dir / "index.json").read_text(encoding="utf-8"))
    assert index["example_smoke_case"] == "single_orbit/8"
    assert not (output_dir / "example_solution.json").exists()
