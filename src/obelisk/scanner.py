from pathlib import Path

from obelisk.filetypes import MetadataReader
from obelisk.filetypes.binary import get_metadata_from_binary
from obelisk.filetypes.json import get_metadata_from_json
from obelisk.manifest import ManifestEntry


def create_manifest_from_folder(folder_path: Path) -> list[ManifestEntry]:
    manifest_entries: list[ManifestEntry] = []
    for file_path in folder_path.glob('*.*'):
        filename = file_path.name
        extension = file_path.suffix.lstrip('.')

        # Skip hidden and special files, and directories
        if filename[:1] in ('.', '_') or file_path.is_dir():
            continue

        # Figure out how to handle this file type
        handler = registered_types.get(extension)
        if handler is None:
            continue

        # Gather metadata and create manifest entry
        entry = handler(file_path)
        if entry is not None:
            manifest_entries.append(entry)

    return manifest_entries


registered_types: dict[str, MetadataReader] = {
    'json': get_metadata_from_json,
    'jsonc': get_metadata_from_json,
    'png': get_metadata_from_binary,
    'jpg': get_metadata_from_binary,
    'jpeg': get_metadata_from_binary,
}
