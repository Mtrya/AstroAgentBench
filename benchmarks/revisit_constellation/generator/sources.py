"""Stage the pinned world-city input for canonical generation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


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


def download_sources(destination_dir: Path, *, force_download: bool = False) -> Path:
    """Stage verified benchmark-owned data, replacing any stale local cache."""
    del force_download  # Restaging never refreshes the canonical source from the network.
    payload = _read_source_snapshot(WORLD_CITIES_FILENAME)
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / WORLD_CITIES_FILENAME
    destination.write_bytes(payload)
    return destination
