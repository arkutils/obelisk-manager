import json
import hashlib
import logging
from pathlib import Path
from typing import Any, cast

from obelisk.manifest import ManifestEntry


logger = logging.getLogger(__name__)


def _only_string(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    return None


def _only_dict(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return cast('dict[str, Any]', value)
    return None


def _load_json(file_path: Path) -> Any | None:
    with file_path.open('r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            logger.warning('Failed to decode JSON from %s', file_path)
            return None


def _hash_json_content(data: dict[str, Any]) -> str:
    """Hash JSON content excluding version so version-only bumps are ignored.

    Uses a stable, sorted, compact JSON representation to ensure formatting-only
    changes do not alter the hash.
    """

    # Exclude top-level version from the hash to allow version-only tolerance
    filtered = {k: v for k, v in data.items() if k != 'version'}
    normalized = json.dumps(filtered, separators=(',', ':'), ensure_ascii=False)
    digest = hashlib.md5(normalized.encode('utf-8')).hexdigest()  # noqa: S324 - not for security
    return f'md5json:{digest}:{len(normalized)}'


def get_metadata_from_json(file_path: Path) -> ManifestEntry | None:
    # Load the JSON and extract specific fields for the manifest
    data = _load_json(file_path)
    if data is None:
        return None

    # Check it's a dict
    if not isinstance(data, dict):
        logger.warning('Invalid JSON structure in %s', file_path)
        return None

    data_dict = cast('dict[str, Any]', data)

    # Extract the relevant fields from the JSON data
    version = _only_string(data_dict.get('version'))
    format = _only_string(data_dict.get('format'))  # noqa: A001
    metadata = _only_dict(data_dict.get('metadata'))
    mod = _only_dict(data_dict.get('mod'))

    if not version:
        logger.warning('Missing or invalid version in %s', file_path)
        return None

    # Create and return the ManifestEntry
    return ManifestEntry(
        filename=file_path.name,
        version=version,
        hash=_hash_json_content(data_dict),
        format=format,
        metadata=metadata,
        mod=mod,
    )
