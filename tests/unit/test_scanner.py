from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from obelisk.scanner import create_manifest_from_folder
from tests.mocks.files import patch_path_glob_for_folder


if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def _expected_hash(data: bytes) -> str:
    h = hashlib.md5()  # noqa: S324 - not for cryptography
    h.update(data)
    return f'md5:{h.hexdigest()}:{len(data)}:'


def test_create_manifest_from_folder_basic_and_skips(tmp_path: Path) -> None:
    # Layout:
    #  - visible.json (valid JSON)
    #  - data.jsonc (valid JSON but different extension)
    #  - image.png (binary)
    #  - _hidden.json (should be skipped)
    #  - .dot.json (should be skipped)
    #  - file.gif (unregistered extension -> skipped)
    #  - subdir/nested.json (non-recursive -> skipped)

    root = tmp_path / 'root'
    root.mkdir()

    # Registered JSON with required fields
    (root / 'visible.json').write_text(
        '{\n\t"version": "1.0.0",\n\t"format": "fmt",\n\t"mod": {\n\t\t"id": 123\n\t}\n}',
        encoding='utf-8',
    )

    # Registered JSONC (we provide valid JSON content without comments)
    (root / 'data.jsonc').write_text(
        '{\n\t"version": "2.0",\n\t"format": "x"\n}',
        encoding='utf-8',
    )

    # Registered binary
    png_bytes = b'\x89PNG\r\n\x1a\n' + b'content-bytes'
    (root / 'image.png').write_bytes(png_bytes)

    # Skips
    (root / '_hidden.json').write_text('{"version":"3"}', encoding='utf-8')
    (root / '.dot.json').write_text('{"version":"4"}', encoding='utf-8')
    (root / 'file.gif').write_bytes(b'GIF89a')
    sub = root / 'subdir'
    sub.mkdir()
    (sub / 'nested.json').write_text('{"version":"5"}', encoding='utf-8')

    # Act
    entries = create_manifest_from_folder(root)

    # Assert: only three entries are included
    filenames = [e.filename for e in entries]
    assert filenames == sorted(filenames)
    assert set(filenames) == {'data.jsonc', 'image.png', 'visible.json'}

    by_name = {e.filename: e for e in entries}

    # visible.json details
    vis = by_name['visible.json']
    assert vis.version == '1.0.0'
    assert vis.format == 'fmt'
    assert vis.mod == {'id': 123}
    assert vis.hash is None

    # data.jsonc details
    js = by_name['data.jsonc']
    assert js.version == '2.0'
    assert js.format == 'x'
    assert js.mod is None

    # image.png hash
    img = by_name['image.png']
    assert img.version is None
    assert img.mod is None
    assert img.hash == _expected_hash(png_bytes)


def test_create_manifest_from_folder_ignores_invalid_json(tmp_path: Path) -> None:
    root = tmp_path / 'root'
    root.mkdir()

    # Missing version -> json handler should return None
    (root / 'invalid.json').write_text('{"format":"f"}', encoding='utf-8')

    # Valid entry to ensure we still get results
    (root / 'valid.json').write_text('{"version":"1"}', encoding='utf-8')

    entries = create_manifest_from_folder(root)
    filenames = [e.filename for e in entries]

    assert 'invalid.json' not in filenames
    assert 'valid.json' in filenames
    assert len(entries) == 1


def test_create_manifest_from_folder_no_valid_entries(tmp_path: Path) -> None:
    root = tmp_path / 'root'
    root.mkdir()

    # Unregistered extensions
    (root / 'notes.txt').write_text('hello', encoding='utf-8')
    (root / 'image.gif').write_bytes(b'GIF89a')

    # Hidden/underscored
    (root / '.hidden.json').write_text('{"version":"1"}', encoding='utf-8')
    (root / '_skip.json').write_text('{"version":"1"}', encoding='utf-8')

    # Invalid JSON for our rules (missing version)
    (root / 'invalid.json').write_text('{"format":"f"}', encoding='utf-8')

    # Nested file (non-recursive)
    sub = root / 'nested'
    sub.mkdir()
    (sub / 'inside.json').write_text('{"version":"1"}', encoding='utf-8')

    entries = create_manifest_from_folder(root)
    assert entries == []


def test_create_manifest_from_folder_sorts_entries_correctly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / 'root'
    root.mkdir()

    a = root / 'a.json'
    b = root / 'b.json'
    c = root / 'c.png'

    a.write_text('{"version":"1"}', encoding='utf-8')
    b.write_text('{"version":"2"}', encoding='utf-8')
    c.write_bytes(b'pngbytes')

    scrambled = [c, b, a]

    patch_path_glob_for_folder(monkeypatch, root, '*.*', scrambled)

    entries = create_manifest_from_folder(root)
    filenames = [e.filename for e in entries]

    # Despite scrambled source order, result should be sorted by filename
    assert filenames == ['a.json', 'b.json', 'c.png']
