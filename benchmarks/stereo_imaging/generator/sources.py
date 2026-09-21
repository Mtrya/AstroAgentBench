"""Stage benchmark-owned source snapshots for stereo_imaging."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import satellite_catalog
from .normalize import parse_tle_text

CELESTRAK_EARTH_RESOURCES_URL = (
    "https://celestrak.org/NORAD/elements/gp.php?GROUP=resource&FORMAT=tle"
)
CELESTRAK_SNAPSHOT_EPOCH_UTC = "2026-04-24T00:00:00Z"
CELESTRAK_RAW_NAME = "earth_resources_raw.tle"
CELESTRAK_CSV_NAME = "earth_resources.csv"

WORLD_CITIES_DATASET = "juanmah/world-cities"
WORLD_CITIES_FILENAME = "world_cities.csv"


SOURCE_SNAPSHOT_DIR = Path(__file__).resolve().parent.parent / "sources"


def _read_source_snapshot(filename: str) -> bytes:
    manifest = json.loads((SOURCE_SNAPSHOT_DIR / "manifest.json").read_text(encoding="utf-8"))
    if manifest["schema_version"] != 1:
        raise ValueError("Unsupported source snapshot manifest version")
    payload = (SOURCE_SNAPSHOT_DIR / filename).read_bytes()
    if hashlib.sha256(payload).hexdigest() != manifest["files"][filename]["sha256"]:
        raise ValueError(f"Source snapshot checksum mismatch: {filename}")
    return payload


def _sha256_file(path: Path, *, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class SourceFetchResult:
    """Paths and metadata returned by individual fetch steps."""

    kind: str
    paths: list[Path]
    extra: dict[str, Any]


def download_celestrak(dest_dir: Path, *, force_download: bool) -> SourceFetchResult:
    """Write normalized CelesTrak-format TLE CSV from the vendored satellite catalog."""
    del force_download  # Kept for API parity with `download_world_cities`; TLEs are always vendored.

    cele_dir = dest_dir / "celestrak"
    raw_path = cele_dir / CELESTRAK_RAW_NAME
    csv_path = cele_dir / CELESTRAK_CSV_NAME
    cele_dir.mkdir(parents=True, exist_ok=True)

    rows = list(satellite_catalog.CACHED_CELESTRAK_ROWS)
    lines: list[str] = []
    for row in rows:
        lines.extend([row["name"], row["tle_line1"], row["tle_line2"]])
    raw_text = "\n".join(lines) + "\n"
    records = parse_tle_text(raw_text)
    if len(records) != len(rows):
        raise RuntimeError(
            f"Vendored TLE snapshot parse mismatch: expected {len(rows)} satellites, got {len(records)}"
        )
    raw_bytes = raw_text.encode("utf-8")
    raw_path.write_bytes(raw_bytes)

    csv_buf = io.StringIO()
    writer = csv.DictWriter(
        csv_buf,
        fieldnames=["name", "norad_catalog_id", "tle_line1", "tle_line2", "epoch_iso"],
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    csv_bytes = csv_buf.getvalue().encode("utf-8")
    csv_path.write_bytes(csv_bytes)
    csv_sha256 = hashlib.sha256(csv_bytes).hexdigest()

    return SourceFetchResult(
        "celestrak",
        [raw_path, csv_path],
        {
            "url": CELESTRAK_EARTH_RESOURCES_URL,
            "snapshot_epoch_utc": CELESTRAK_SNAPSHOT_EPOCH_UTC,
            "record_count": len(rows),
            "sha256": csv_sha256,
            "vendored_snapshot": True,
        },
    )


def download_world_cities(dest_dir: Path, *, force_download: bool) -> SourceFetchResult:
    """Stage the pinned normalized world-city input, replacing stale cache data."""
    del force_download
    payload = _read_source_snapshot(WORLD_CITIES_FILENAME)
    manifest = json.loads((SOURCE_SNAPSHOT_DIR / "manifest.json").read_text(encoding="utf-8"))
    final_csv = dest_dir / "world_cities" / WORLD_CITIES_FILENAME
    final_csv.parent.mkdir(parents=True, exist_ok=True)
    final_csv.write_bytes(payload)
    return SourceFetchResult(
        "world_cities",
        [final_csv],
        {
            "kaggle_dataset": WORLD_CITIES_DATASET,
            "sha256": _sha256_file(final_csv),
            "upstream_sha256": manifest["origin"]["input_sha256"],
            "vendored_snapshot": True,
        },
    )


def fetch_all_sources(
    dest_dir: Path,
    *,
    force_download: bool = False,
) -> dict[str, SourceFetchResult]:
    """Stage the pinned source inputs needed by the lookup-table-based generator."""
    return {
        "celestrak": download_celestrak(dest_dir, force_download=force_download),
        "world_cities": download_world_cities(dest_dir, force_download=force_download),
    }
