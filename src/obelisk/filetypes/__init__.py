from collections.abc import Callable
from pathlib import Path

from obelisk.filetypes.binary import get_metadata_from_binary
from obelisk.filetypes.json import get_metadata_from_json
from obelisk.manifest import ManifestEntry


MetadataReader = Callable[[Path], ManifestEntry | None]


registered_types: dict[str, MetadataReader] = {
    'json': get_metadata_from_json,
    'jsonc': get_metadata_from_json,
    'png': get_metadata_from_binary,
    'jpg': get_metadata_from_binary,
    'jpeg': get_metadata_from_binary,
}

allowed_types = set(registered_types.keys())
version_only_change_insensitive_types = {'json', 'jsonc'}

__all__ = (
    'allowed_types',
    'registered_types',
    'version_only_change_insensitive_types',
)
