from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(kw_only=True)
class ManifestEntry:
    filename: str
    version: str | None = None
    hash: str | None = None
    format: str | None = None
    mod_data: dict[str, Any] | None = None


def parse_manifest(path: Path) -> list[ManifestEntry]:
    raise NotImplementedError


def write_manifest(path: Path, entries: list[ManifestEntry]) -> None:
    raise NotImplementedError


def manifest_match(a: list[ManifestEntry], b: list[ManifestEntry]) -> bool:
    raise NotImplementedError
