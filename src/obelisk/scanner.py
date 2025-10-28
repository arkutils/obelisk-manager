from operator import attrgetter
from pathlib import Path

from obelisk.filetypes import registered_types
from obelisk.filtering import file_is_allowed
from obelisk.manifest import ManifestEntry


def create_manifest_from_folder(folder_path: Path) -> list[ManifestEntry]:
    manifest_entries: list[ManifestEntry] = []
    for file_path in folder_path.glob('*.*'):
        extension = file_path.suffix.lstrip('.')

        # Skip filtered files
        if not file_is_allowed(file_path):
            continue

        # Figure out how to handle this file type
        handler = registered_types.get(extension)
        if handler is None:
            continue

        # Gather metadata and create manifest entry
        entry = handler(file_path)
        if entry is not None:
            manifest_entries.append(entry)

    # Ensure deterministic ordering for downstream comparison/writes
    manifest_entries.sort(key=attrgetter('filename'))

    return manifest_entries


__all__ = ('create_manifest_from_folder',)
