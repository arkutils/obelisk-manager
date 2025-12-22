from __future__ import annotations

from shutil import copy2
from typing import TYPE_CHECKING

from obelisk.filetypes import registered_types, version_only_change_insensitive_types
from obelisk.manifest import MANIFEST_FILENAME, ManifestEntry, entries_match, write_manifest
from obelisk.scanner import create_manifest_from_folder


if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


def apply_import(
    dest_path: Path,
    allowed: list[Path],
    *,
    dry_run: bool,
    printer: Callable[..., None] | None = None,
) -> tuple[list[ManifestEntry], list[ManifestEntry]]:
    """Copy files into dest and write updated manifest.

    Returns a tuple of (before_entries, after_entries).
    """

    def _no_op_printer(_: object = None, __: object = None) -> None:  # pragma: no cover - trivial
        return None

    p: Callable[..., None] = printer or _no_op_printer

    if not dry_run:
        dest_path.mkdir(parents=True, exist_ok=True)

    # Scan current state (before)
    p('[bold]Scanning current manifest (before)...[/bold]')
    before_entries = create_manifest_from_folder(dest_path)
    before_by_name = {entry.filename: entry for entry in before_entries}

    # Copy files
    p('[bold]Copying files...[/bold]')
    for src in allowed:
        dst = dest_path / src.name

        # Skip copying JSON inputs when only the version changed to avoid dirty trees
        ext = src.suffix.lstrip('.').lower()
        existing_entry = before_by_name.get(src.name)
        if ext in version_only_change_insensitive_types and existing_entry is not None:
            handler = registered_types.get(ext)
            prospective_entry = handler(src) if handler else None
            if prospective_entry and entries_match(existing_entry, prospective_entry):
                p(f'  * {src} unchanged (ignoring version); skipping copy')
                continue

        if dry_run:
            p(f'  * {src} -> {dst} [dry-run]')
        else:
            copy2(src, dst)
            p(f'  * {src} -> {dst}')

    # Scan new state (after) and write manifest
    p('[bold]Updating manifest...[/bold]')
    after_entries = create_manifest_from_folder(dest_path)
    manifest_file = dest_path / MANIFEST_FILENAME
    if dry_run:
        p(f'  * Would write manifest: {manifest_file}')
    else:
        write_manifest(manifest_file, after_entries)
        p(f'  * Wrote manifest: {manifest_file}')

    return before_entries, after_entries


__all__ = ('apply_import',)
