from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ManifestEntry:
    filename: str
    version: str | None
    format: str | None
    mod_data: dict[str, Any] | None


def parse_manifest(path: Path) -> list[ManifestEntry]:
    return []


def write_manifest(path: Path, entries: list[ManifestEntry]) -> None:
    pass


def manifest_match(a: list[ManifestEntry], b: list[ManifestEntry]) -> bool:
    return False
