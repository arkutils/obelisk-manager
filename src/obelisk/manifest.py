from __future__ import annotations

from collections import Counter
from operator import attrgetter
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from obelisk.json_utils import save_as_json


if TYPE_CHECKING:
    from pathlib import Path


MANIFEST_FILENAME = '_manifest.json'


class ManifestFile(BaseModel):
    version: str | None = None
    format: str | None = None
    files: dict[str, RawManifestEntry]


class RawManifestEntry(BaseModel):
    version: str | None = None
    hash: str | None = None
    format: str | None = None
    mod: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class ManifestEntry(BaseModel):
    filename: str
    version: str | None = None
    hash: str | None = None
    format: str | None = None
    mod: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


def parse_manifest(path: Path) -> list[ManifestEntry]:
    """Load a manifest from the given path.

    Input JSON shape (example):
      {
        "format": "4",
        "files": {
          "file1.json": {"version": "1.0", "format": "2", "mod": {...}},
          "file2.json": {"version": "2.0"}
        }
      }
    """
    data = path.read_text(encoding='utf-8')
    full_manifest = ManifestFile.model_validate_json(data, strict=True)

    # Propagate top-level format to entries where missing
    global_format = full_manifest.format
    entries: list[ManifestEntry] = []
    for filename, entry in full_manifest.files.items():
        new_entry = ManifestEntry.model_validate(
            {
                **entry.model_dump(),
                'filename': filename,
                'format': entry.format or global_format,
            },
            strict=True,
        )
        entries.append(new_entry)

    # Sort entries by filename for consistency
    entries.sort(key=attrgetter('filename'))

    return entries


def write_manifest(path: Path, entries: list[ManifestEntry]) -> None:
    """Write a manifest to the specified path."""

    # First, look for the most common format among entries
    format_counts: Counter[str] = Counter(entry.format for entry in entries if entry.format)
    most_common: list[tuple[str, int]] = format_counts.most_common(1)
    global_format = most_common[0][0] if most_common else None

    # Build the output file
    file_data = ManifestFile(
        format=global_format,
        files={},
    )
    for entry in entries:
        raw_entry = RawManifestEntry(
            version=entry.version,
            hash=entry.hash,
            mod=entry.mod,
            metadata=entry.metadata,
        )
        if entry.format != global_format:
            raw_entry.format = entry.format
        file_data.files[entry.filename] = raw_entry

    # Get the raw data
    data = file_data.model_dump(exclude_none=True)

    # Write to file using our slightly customised JSON serialiser
    save_as_json(path, data)


def manifest_match(a: list[ManifestEntry], b: list[ManifestEntry]) -> bool:
    """
    Check if two manifests match exactly.
    Both lists are assumed to be sorted by filename (as produced by parse_manifest).
    """
    if len(a) != len(b):
        return False

    return all(entry_a == entry_b for entry_a, entry_b in zip(a, b, strict=True))


__all__ = (
    'MANIFEST_FILENAME',
    'ManifestEntry',
    'manifest_match',
    'parse_manifest',
    'write_manifest',
)
