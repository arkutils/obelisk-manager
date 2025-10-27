from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .manifest import ManifestEntry


logger = logging.getLogger(__name__)

if TYPE_CHECKING:  # type-only imports
    from collections.abc import Iterable


@dataclass(frozen=True)
class _ChangeSets:
    added: list[ManifestEntry]
    removed: list[ManifestEntry]
    updated: list[tuple[ManifestEntry, ManifestEntry]]  # (before, after)


def _diff_entries(
    before: Iterable[ManifestEntry],
    after: Iterable[ManifestEntry],
) -> _ChangeSets:
    """Compute the differences between two manifest entry collections.

    Returns a tuple of added entries, removed entries, and updated pairs.
    Entries are matched by filename.

    Input lists are assumed to already be sorted for deterministic output.
    """
    before_map = {e.filename: e for e in before}
    after_map = {e.filename: e for e in after}

    added: list[ManifestEntry] = []
    removed: list[ManifestEntry] = []
    updated: list[tuple[ManifestEntry, ManifestEntry]] = []

    # Detect additions and updates
    for fname, a_entry in after_map.items():
        b_entry = before_map.get(fname)
        if b_entry is None:
            added.append(a_entry)
        elif b_entry != a_entry:
            updated.append((b_entry, a_entry))

    # Detect removals
    for fname, b_entry in before_map.items():
        if fname not in after_map:
            removed.append(b_entry)

    return _ChangeSets(added=added, removed=removed, updated=updated)


def _fmt_version(v: str | None) -> str:
    return f'v{v}' if v else 'no version'


def build_file_change_list(before: list[ManifestEntry], after: list[ManifestEntry]) -> str:
    """Render a human-friendly list of file changes between two manifests.

    Produces a compact multi-line string containing sections for Added, Updated,
    and Removed files (only sections with entries are included). Version numbers
    are shown when available.

    Input lists are assumed to already be sorted for deterministic output.

    Examples of line formats:
    - Added:  filename.ext (v1.2)
    - Updated: filename.ext (v1.3)
    - Updated: filename.ext
    - Removed: filename.ext
    """
    changes = _diff_entries(before, after)

    sections: list[list[str]] = []

    if changes.added:
        added_block: list[str] = ['Added:']
        added_block.extend(
            [
                f'* {e.filename} ({_fmt_version(e.version)})' if e.version else f'* {e.filename}'
                for e in changes.added
            ],
        )
        sections.append(added_block)

    if changes.updated:
        updated_block: list[str] = ['Updated:']
        for b, a in changes.updated:
            b_ver, a_ver = b.version, a.version
            if b_ver != a_ver:
                updated_block.append(f'* {a.filename} ({_fmt_version(a_ver)})')
            else:
                # Either both None or equal versions; something else changed (hash, mod, format)
                updated_block.append(f'* {a.filename}')
        sections.append(updated_block)

    if changes.removed:
        removed_block: list[str] = ['Removed:']
        removed_block.extend(
            [f'* {e.filename}' for e in changes.removed],
        )
        sections.append(removed_block)

    return '\n\n'.join('\n'.join(block) for block in sections)


def build_commit_message(
    before: list[ManifestEntry],
    after: list[ManifestEntry],
    *,
    include_file_list: bool = True,
    headline: str | None = None,
    message: str | None = None,
) -> str:
    """Create a full commit message.

    Parameters:
    - before/after: Manifest entries before and after the change.
    - headline: Optional first line. If absent a concise summary with counts is used.
    - message: Optional free-form message paragraph appended after the headline.
    - include_file_list: When True, appends a formatted change list.

    Returns the full commit message string suitable for `git commit -m` usage.
    """
    changes = _diff_entries(before, after)

    add_n = len(changes.added)
    upd_n = len(changes.updated)
    rem_n = len(changes.removed)

    if headline is None:
        if add_n == upd_n == rem_n == 0:
            headline_text = 'Obelisk import: no changes'
        else:
            headline_text = f'Obelisk import: +{add_n} ~{upd_n} -{rem_n}'
    else:
        headline_text = headline.strip()

    parts: list[str] = [headline_text]

    if message:
        parts.extend(['', message.strip()])

    if include_file_list:
        change_list = build_file_change_list(before, after)
        if change_list:
            parts.extend(['', change_list])

    return '\n'.join(parts)


__all__ = [
    'build_commit_message',
    'build_file_change_list',
]
