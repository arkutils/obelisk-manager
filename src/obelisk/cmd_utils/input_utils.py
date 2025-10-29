from __future__ import annotations

from typing import TYPE_CHECKING

from obelisk.filtering import file_is_allowed


if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


def _enumerate_input_files(inputs: Iterable[Path]) -> list[Path]:
    """Expand a list of file/dir inputs into a flat list of files.

    - Directories are expanded non-recursively to their immediate children.
    - Only files are returned; directories are ignored.
    """
    files: list[Path] = []
    for p in inputs:
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            files.extend([child for child in p.iterdir() if child.is_file()])
    return files


def collect_allowed_inputs(inputs: Iterable[Path], *, allow_all: bool) -> tuple[list[Path], list[Path]]:
    """Partition inputs into (allowed, filtered) lists.

    Filtering uses ``file_is_allowed`` unless ``allow_all`` is True.
    Returns a tuple of (allowed, filtered).
    """
    input_files = _enumerate_input_files(inputs)
    if allow_all:
        return input_files, []
    allowed: list[Path] = []
    filtered: list[Path] = []
    for p in input_files:
        if file_is_allowed(p):
            allowed.append(p)
        else:
            filtered.append(p)
    return allowed, filtered


__all__ = ('collect_allowed_inputs',)
