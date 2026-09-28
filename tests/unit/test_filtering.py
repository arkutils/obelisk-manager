from __future__ import annotations

from typing import TYPE_CHECKING

from obelisk.filtering import DEFAULT_IGNORE_PATTERNS, is_under_ignored, resolve_ignored_paths


if TYPE_CHECKING:
    from pathlib import Path


def test_resolve_ignored_paths_matches_hidden_and_bang_files(tmp_path: Path) -> None:
    (tmp_path / '.hidden').write_text('x', encoding='utf-8')
    (tmp_path / '!excluded.json').write_text('x', encoding='utf-8')
    (tmp_path / 'visible.json').write_text('x', encoding='utf-8')

    sub = tmp_path / 'sub'
    sub.mkdir()
    (sub / '.nested_hidden').write_text('x', encoding='utf-8')

    ignored = resolve_ignored_paths(tmp_path, DEFAULT_IGNORE_PATTERNS)

    assert tmp_path / '.hidden' in ignored
    assert tmp_path / '!excluded.json' in ignored
    assert sub / '.nested_hidden' in ignored
    assert tmp_path / 'visible.json' not in ignored


def test_is_under_ignored_matches_self_and_descendants(tmp_path: Path) -> None:
    git_dir = tmp_path / '.git'
    ignored = {git_dir}

    assert is_under_ignored(git_dir, ignored) is True
    assert is_under_ignored(git_dir / 'config', ignored) is True
    assert is_under_ignored(git_dir / 'objects' / 'pack', ignored) is True
    assert is_under_ignored(tmp_path / 'visible.json', ignored) is False
