from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from obelisk.manifest import ManifestEntry, write_manifest


if TYPE_CHECKING:
    from pathlib import Path


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def test_write_manifest_basic(tmp_path: Path) -> None:
    # Two entries share the same format -> lifted to top-level, omitted per entry
    entries = [
        ManifestEntry(
            filename='a.json',
            version='1',
            format='4',
            mod={'id': 'm1'},
            hash=None,
        ),
        ManifestEntry(
            filename='b.json',
            version='2',
            format='4',
            mod=None,
            hash=None,
        ),
    ]

    path = tmp_path / '_manifest.json'
    write_manifest(path, entries)

    data = _read_json(path)

    # Top-level format chosen from common entry format
    assert data['format'] == '4'

    # Per-entry format omitted as it matches the top-level
    assert data['files']['a.json'] == {'version': '1', 'mod': {'id': 'm1'}}
    assert data['files']['b.json'] == {'version': '2'}


def test_write_manifest_common_format_reduction_mixed(tmp_path: Path) -> None:
    # Most common format should be promoted to top-level; differing formats kept per-entry
    entries = [
        ManifestEntry(filename='a.json', version='1', format='2', mod=None, hash=None),
        ManifestEntry(filename='b.json', version='1', format='2', mod=None, hash=None),
        ManifestEntry(filename='c.json', version='1', format='x', mod=None, hash=None),
        ManifestEntry(filename='d.json', version=None, format=None, mod=None, hash=None),
    ]

    path = tmp_path / '_manifest.json'
    write_manifest(path, entries)

    data = _read_json(path)

    # Top-level picks the most common ('2')
    assert data.get('format') == '2'

    files: dict[str, dict[str, Any]] = data['files']
    # Entries with matching format omit per-entry format
    assert files['a.json'] == {'version': '1'}
    assert files['b.json'] == {'version': '1'}

    # Entry with different format keeps its own
    assert files['c.json'] == {'version': '1', 'format': 'x'}

    # Entry with None format shouldn't include a format key
    assert files['d.json'] == {}


def test_write_manifest_no_formats_present(tmp_path: Path) -> None:
    # When no entry has a format, the top-level format should be omitted
    entries = [
        ManifestEntry(filename='only.json', version='1', format=None, mod=None, hash=None),
        ManifestEntry(filename='second.json', version=None, format=None, mod=None, hash=None),
    ]

    path = tmp_path / '_manifest.json'
    write_manifest(path, entries)

    data = _read_json(path)

    # No top-level format
    assert 'format' not in data

    # No per-entry format fields either
    assert data['files']['only.json'] == {'version': '1'}
    assert data['files']['second.json'] == {}


def test_write_manifest_includes_hash(tmp_path: Path) -> None:
    # Hash should be persisted on the corresponding entry
    entries = [
        ManifestEntry(
            filename='a.json',
            version='1',
            format=None,
            mod=None,
            hash='abc123',
        ),
    ]

    path = tmp_path / '_manifest.json'
    write_manifest(path, entries)

    data = _read_json(path)

    assert 'format' not in data  # no formats provided at all
    assert data['files']['a.json'] == {'version': '1', 'hash': 'abc123'}
