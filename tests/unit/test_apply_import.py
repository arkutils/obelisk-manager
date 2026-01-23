from __future__ import annotations

from typing import TYPE_CHECKING

from obelisk.cmd_utils.apply_import import apply_import
from obelisk.manifest import parse_manifest


if TYPE_CHECKING:
    from pathlib import Path


def test_apply_import_respects_accept_identical_versions_flag(tmp_path: Path) -> None:
    # Destination folder with an existing JSON file
    dest = tmp_path / 'dest'
    dest.mkdir()
    (dest / 'a.json').write_text('{"version":"1","metadata":{"foo":"bar"}}', encoding='utf-8')

    # Source file with only a version bump
    srcdir = tmp_path / 'src'
    srcdir.mkdir()
    src = srcdir / 'a.json'
    src.write_text('{"version":"1.1","metadata":{"foo":"bar"}}', encoding='utf-8')

    # When flag is False (default), import should be skipped and manifest unchanged
    _before_entries, _after_entries = apply_import(
        dest,
        [src],
        dry_run=False,
        printer=None,
        accept_identical_versions=False,
    )
    mpath = dest / '_manifest.json'
    assert mpath.exists()
    entries = parse_manifest(mpath)
    by_name = {e.filename: e for e in entries}
    assert by_name['a.json'].version == '1'

    # Now run with the flag enabled - should copy and update manifest
    _before_entries, _after_entries = apply_import(
        dest,
        [src],
        dry_run=False,
        printer=None,
        accept_identical_versions=True,
    )
    entries = parse_manifest(mpath)
    by_name = {e.filename: e for e in entries}
    assert by_name['a.json'].version == '1.1'
