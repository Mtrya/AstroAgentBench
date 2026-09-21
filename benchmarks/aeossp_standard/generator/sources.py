"""Source acquisition helpers for the aeossp_standard generator."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from . import cached_tles, cached_tles_2022


CELESTRAK_EARTH_RESOURCES_URL = (
    "https://celestrak.org/NORAD/elements/gp.php?GROUP=resource&FORMAT=tle"
)
CELESTRAK_SNAPSHOT_EPOCH_UTC = "2026-04-14T00:00:00Z"
CELESTRAK_2022_SNAPSHOT_EPOCH_UTC = "2022-04-14T00:00:00Z"
CELESTRAK_CSV_NAME = "earth_resources.csv"
LEGACY_CELESTRAK_RAW_NAME = "earth_resources_raw.tle"

_CELESTRAK_SNAPSHOT_ROWS = {
    CELESTRAK_SNAPSHOT_EPOCH_UTC: cached_tles.CACHED_CELESTRAK_ROWS,
    CELESTRAK_2022_SNAPSHOT_EPOCH_UTC: cached_tles_2022.CACHED_CELESTRAK_ROWS,
}

WORLD_CITIES_URL = "https://download.geonames.org/export/dump/cities15000.zip"
WORLD_CITIES_FILENAME = "world_cities.csv"
WORLD_CITIES_SNAPSHOT_NAME = "world_cities_snapshot.csv"

NATURAL_EARTH_LAND_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_land.geojson"
)
NATURAL_EARTH_LAND_FILENAME = "ne_110m_land.geojson"

_GENERATOR_DIR = Path(__file__).resolve().parent
VENDORED_WORLD_CITIES_PATH = _GENERATOR_DIR / WORLD_CITIES_SNAPSHOT_NAME


SOURCE_SNAPSHOT_DIR = Path(__file__).resolve().parent.parent / "sources"


def _read_source_snapshot(filename: str) -> bytes:
    manifest = json.loads((SOURCE_SNAPSHOT_DIR / "manifest.json").read_text(encoding="utf-8"))
    if manifest["schema_version"] != 1:
        raise ValueError("Unsupported source snapshot manifest version")
    payload = (SOURCE_SNAPSHOT_DIR / filename).read_bytes()
    if hashlib.sha256(payload).hexdigest() != manifest["files"][filename]["sha256"]:
        raise ValueError(f"Source snapshot checksum mismatch: {filename}")
    return payload


@dataclass(frozen=True)
class SourceFetchResult:
    kind: str
    paths: list[Path]
    extra: dict[str, object]


def _sha256_file(path: Path, *, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def supported_celestrak_snapshot_epochs() -> tuple[str, ...]:
    return tuple(_CELESTRAK_SNAPSHOT_ROWS)


def celestrak_csv_path(dest_dir: Path, snapshot_epoch_utc: str) -> Path:
    if snapshot_epoch_utc == CELESTRAK_SNAPSHOT_EPOCH_UTC:
        return dest_dir / "celestrak" / CELESTRAK_CSV_NAME
    label = snapshot_epoch_utc.replace(":", "").replace("-", "")
    return dest_dir / "celestrak" / label / CELESTRAK_CSV_NAME


def get_celestrak(
    dest_dir: Path,
    *,
    snapshot_epoch_utc: str = CELESTRAK_SNAPSHOT_EPOCH_UTC,
) -> SourceFetchResult:
    try:
        rows = list(_CELESTRAK_SNAPSHOT_ROWS[snapshot_epoch_utc])
    except KeyError as exc:
        supported = ", ".join(supported_celestrak_snapshot_epochs())
        raise ValueError(
            f"Unsupported aeossp_standard CelesTrak snapshot epoch {snapshot_epoch_utc!r}; "
            f"supported epochs: {supported}"
        ) from exc

    csv_path = celestrak_csv_path(dest_dir, snapshot_epoch_utc)
    legacy_raw_path = dest_dir / "celestrak" / LEGACY_CELESTRAK_RAW_NAME
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    if legacy_raw_path.exists():
        legacy_raw_path.unlink()
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "name",
                "norad_catalog_id",
                "tle_line1",
                "tle_line2",
                "epoch_iso",
                "inclination_deg",
                "eccentricity",
                "mean_motion_rev_per_day",
                "altitude_m",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    csv_bytes = csv_path.read_bytes()
    return SourceFetchResult(
        "celestrak",
        [csv_path],
        {
            "url": CELESTRAK_EARTH_RESOURCES_URL,
            "snapshot_epoch_utc": snapshot_epoch_utc,
            "record_count": len(rows),
            "sha256": hashlib.sha256(csv_bytes).hexdigest(),
            "vendored_snapshot": True,
        },
    )


def download_world_cities(dest_dir: Path, *, force_download: bool) -> SourceFetchResult:
    del force_download  # Vendored snapshot is always used for reproducibility.

    if not VENDORED_WORLD_CITIES_PATH.is_file():
        raise FileNotFoundError(
            f"Vendored world-cities snapshot is missing: {VENDORED_WORLD_CITIES_PATH}"
        )

    cities_dir = dest_dir / "world_cities"
    final_csv = cities_dir / WORLD_CITIES_FILENAME
    cities_dir.mkdir(parents=True, exist_ok=True)
    final_csv.write_bytes(VENDORED_WORLD_CITIES_PATH.read_bytes())
    return SourceFetchResult(
        "world_cities",
        [final_csv],
        {
            "url": WORLD_CITIES_URL,
            "sha256": _sha256_file(final_csv),
            "vendored_snapshot": True,
        },
    )


def download_natural_earth_land(dest_dir: Path, *, force_download: bool) -> SourceFetchResult:
    del force_download  # Canonical generation always stages the pinned source.
    payload = _read_source_snapshot(NATURAL_EARTH_LAND_FILENAME)
    geojson_path = dest_dir / "natural_earth" / NATURAL_EARTH_LAND_FILENAME
    geojson_path.parent.mkdir(parents=True, exist_ok=True)
    geojson_path.write_bytes(payload)
    return SourceFetchResult(
        "natural_earth_land",
        [geojson_path],
        {
            "url": NATURAL_EARTH_LAND_URL,
            "sha256": _sha256_file(geojson_path),
            "vendored_snapshot": True,
        },
    )


def fetch_all_sources(
    dest_dir: Path,
    *,
    force_download: bool = False,
    celestrak_snapshot_epochs_utc: list[str] | tuple[str, ...] | None = None,
) -> dict[str, SourceFetchResult]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    celestrak_epochs = tuple(celestrak_snapshot_epochs_utc or (CELESTRAK_SNAPSHOT_EPOCH_UTC,))
    celestrak_results = [
        get_celestrak(
            dest_dir,
            snapshot_epoch_utc=snapshot_epoch_utc,
        )
        for snapshot_epoch_utc in dict.fromkeys(celestrak_epochs)
    ]
    celestrak_result = celestrak_results[0]
    if len(celestrak_results) > 1:
        celestrak_result = SourceFetchResult(
            "celestrak",
            [path for result in celestrak_results for path in result.paths],
            {
                "snapshots": {
                    str(result.extra["snapshot_epoch_utc"]): result.extra
                    for result in celestrak_results
                },
                "vendored_snapshot": True,
            },
        )
    return {
        "celestrak": celestrak_result,
        "world_cities": download_world_cities(dest_dir, force_download=force_download),
        "natural_earth_land": download_natural_earth_land(dest_dir, force_download=force_download),
    }
