"""Exercise pinned source validation and replacement of stale staging files."""

import importlib
from pathlib import Path
import shutil

import pytest


@pytest.mark.parametrize(
    "module_name,filename",
    [
        ("benchmarks.aeossp_standard.generator.sources", "ne_110m_land.geojson"),
        ("benchmarks.revisit_constellation.generator.sources", "world_cities.csv"),
        ("benchmarks.stereo_imaging.generator.sources", "world_cities.csv"),
        ("benchmarks.satnet.generator", "satnet.json"),
        ("benchmarks.spot5.generator", "8.spot"),
    ],
)
def test_generator_rejects_changed_source_bytes(module_name, filename, tmp_path, monkeypatch):
    module = importlib.import_module(module_name)
    source_dir = module.SOURCE_SNAPSHOT_DIR
    original = (source_dir / filename).read_bytes()
    shutil.copyfile(source_dir / "manifest.json", tmp_path / "manifest.json")
    snapshot = tmp_path / filename
    snapshot.write_bytes(original)
    monkeypatch.setattr(module, "SOURCE_SNAPSHOT_DIR", tmp_path)

    assert module._read_source_snapshot(filename) == original
    snapshot.write_bytes(original + b"\n")
    with pytest.raises(ValueError):
        module._read_source_snapshot(filename)


@pytest.mark.parametrize("force", [False, True])
@pytest.mark.parametrize("benchmark", ["aeossp_standard", "revisit_constellation", "stereo_imaging"])
def test_source_staging_replaces_stale_data(benchmark, force, tmp_path):
    module = importlib.import_module(f"benchmarks.{benchmark}.generator.sources")
    if benchmark == "aeossp_standard":
        relative = Path("natural_earth/ne_110m_land.geojson")
        stage = module.download_natural_earth_land
    elif benchmark == "stereo_imaging":
        relative = Path("world_cities/world_cities.csv")
        stage = module.download_world_cities
    else:
        relative = Path("world_cities.csv")
        stage = module.download_sources

    destination = tmp_path / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("stale cached upstream data")
    stage(tmp_path, force_download=force)
    assert destination.read_bytes() == (module.SOURCE_SNAPSHOT_DIR / relative.name).read_bytes()


def test_stereo_preserves_canonical_source_provenance(tmp_path):
    import hashlib
    import json

    from benchmarks.stereo_imaging.generator import run, sources

    staged = sources.fetch_all_sources(tmp_path)
    city_source = staged["world_cities"]
    assert city_source.extra["sha256"] == hashlib.sha256(city_source.paths[0].read_bytes()).hexdigest()
    provenance = json.loads(run._write_provenance(tmp_path, staged, repo_root=tmp_path).read_text())
    benchmark_root = Path(sources.__file__).resolve().parents[1]
    canonical = json.loads((benchmark_root / "dataset/index.json").read_text())
    assert provenance == canonical["source"]["runtime_provenance"]
