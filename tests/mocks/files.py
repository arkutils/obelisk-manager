from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Iterable

    import pytest


def patch_path_glob_for_folder(
    monkeypatch: pytest.MonkeyPatch,
    match_folder: Path,
    match_pattern: str,
    files: Iterable[Path],
) -> None:
    """Monkeypatch Path.glob to return a provided iterable for one folder.

    This limits the override to a single directory and pattern, delegating to
    the original glob implementation for all other calls.
    The `monkeypatch` fixture will automatically restore the original after
    the test, so no explicit teardown is required.
    """

    original_glob = Path.glob

    def fake_glob(self: Path, pattern: str):
        if self == match_folder and pattern == match_pattern:
            return iter(files)
        return original_glob(self, pattern)

    monkeypatch.setattr(Path, 'glob', fake_glob, raising=True)


__all__ = ('patch_path_glob_for_folder',)
