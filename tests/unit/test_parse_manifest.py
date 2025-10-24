from __future__ import annotations

from pathlib import Path

from obelisk.manifest import ManifestEntry, parse_manifest


def _data_path(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / 'data' / name


def test_parse_manifest_with_sample_file() -> None:
    path = _data_path('manifest1.json')

    entries = parse_manifest(path)

    # Produce entries for each file for easier checking
    by_name: dict[str, ManifestEntry] = {e.filename: e for e in entries}

    assert '111111111-PrimitivePlus/items.json' in by_name
    assert 'drops.json' in by_name
    assert 'engrams.json' in by_name
    assert 'event_colors.json' in by_name
    assert len(entries) == 4

    items = by_name['111111111-PrimitivePlus/items.json']
    assert items.version == '346.11.8907760'
    assert items.format == '4'  # inherited from top-level when not set on entry
    assert items.mod
    assert items.mod.get('id') == '111111111'
    assert items.hash is None

    drops = by_name['drops.json']
    assert drops.version == '358.3.11382644'
    assert drops.format == '7'  # explicit entry-level overrides top-level

    engrams = by_name['engrams.json']
    assert engrams.version == '358.3.11382644'
    assert engrams.format == '2'  # explicit entry-level overrides top-level

    colors = by_name['event_colors.json']
    assert colors.version == '357.12.10956461'
    assert colors.format == '1'  # explicit entry-level overrides top-level


def test_parse_manifest_top_level_format_propagation(tmp_path: Path) -> None:
    # Construct a minimal manifest json where some entries omit format
    content = {
        'format': '42',
        'files': {
            'a.json': {'version': '1.0'},
            'b.json': {'version': '1.1', 'format': 'x'},
            'c.json': {'version': None},
        },
    }
    p = tmp_path / 'manifest.json'
    p.write_text(__import__('json').dumps(content), encoding='utf-8')

    entries = parse_manifest(p)
    by_name: dict[str, ManifestEntry] = {e.filename: e for e in entries}

    assert by_name['a.json'].format == '42'  # inherited from top-level
    assert by_name['b.json'].format == 'x'  # explicit overrides
    assert by_name['c.json'].format == '42'  # inherited even when version is None


def test_parse_manifest_entries_sorted_by_filename(tmp_path: Path) -> None:
    # Use intentionally unsorted filenames to verify sorting by parse_manifest
    content = {
        'files': {
            'zeta.json': {'version': '1.0'},
            'alpha.json': {'version': '1.0'},
            'mid.json': {'version': '1.0'},
        },
    }
    p = tmp_path / 'manifest.json'
    p.write_text(__import__('json').dumps(content), encoding='utf-8')

    entries = parse_manifest(p)

    filenames = [e.filename for e in entries]
    assert filenames == sorted(filenames)
