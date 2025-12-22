from __future__ import annotations

from pathlib import Path

from obelisk.manifest import ManifestEntry, manifest_match, parse_manifest


def _data_path(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / 'data' / name


def test_manifest_match_two_copies_same_file() -> None:
    # Same manifest parsed twice should match
    path = _data_path('manifest1.json')
    a = parse_manifest(path)
    b = parse_manifest(path)

    assert manifest_match(a, b) is True
    assert manifest_match(b, a) is True


def test_manifest_match_made_up_equal_data_both_ways() -> None:
    # Build an in-memory list of entries equivalent to a small manifest
    entries_a = [
        ManifestEntry(filename='a.json', version='1', format=None, mod={'id': 'm1'}, hash=None),
        ManifestEntry(filename='b.json', version='2', format='x', mod=None, hash=None),
    ]
    entries_b = [
        ManifestEntry(filename='a.json', version='1', format=None, mod={'id': 'm1'}, hash=None),
        ManifestEntry(filename='b.json', version='2', format='x', mod=None, hash=None),
    ]

    assert manifest_match(entries_a, entries_b) is True
    assert manifest_match(entries_b, entries_a) is True


def test_manifest_match_mismatches_minor_changes() -> None:
    # Base set
    base = [
        ManifestEntry(filename='a.json', version='1', format=None, mod={'id': 'm1'}, hash=None),
        ManifestEntry(filename='b.json', version='2', format='x', mod=None, hash=None),
    ]

    # Version difference
    changed_version = [
        ManifestEntry(filename='a.json', version='1', format=None, mod={'id': 'm1'}, hash=None),
        ManifestEntry(filename='b.json', version='3', format='x', mod=None, hash=None),
    ]
    assert manifest_match(base, changed_version) is True
    assert manifest_match(changed_version, base) is True

    # Missing file
    missing = [
        ManifestEntry(filename='a.json', version='1', format=None, mod={'id': 'm1'}, hash=None),
    ]
    assert manifest_match(base, missing) is False
    assert manifest_match(missing, base) is False

    # Mod change
    mod_changed = [
        ManifestEntry(filename='a.json', version='1', format=None, mod={'id': 'm2'}, hash=None),
        ManifestEntry(filename='b.json', version='2', format='x', mod=None, hash=None),
    ]
    assert manifest_match(base, mod_changed) is False
    assert manifest_match(mod_changed, base) is False

    # Metadata change should still be a mismatch
    metadata_changed = [
        ManifestEntry(
            filename='a.json', version='1', format=None, mod={'id': 'm1'}, metadata={'k': 'v'}, hash=None,
        ),
        ManifestEntry(filename='b.json', version='2', format='x', mod=None, hash=None),
    ]
    assert manifest_match(base, metadata_changed) is False
    assert manifest_match(metadata_changed, base) is False


def test_manifest_match_added_entry_mismatch() -> None:
    # Base set with two entries
    base = [
        ManifestEntry(filename='a.json', version='1', format=None, mod={'id': 'm1'}, hash=None),
        ManifestEntry(filename='b.json', version='2', format='x', mod=None, hash=None),
    ]

    # Added third entry should cause mismatch regardless of order
    added = [
        *base,
        ManifestEntry(filename='c.json', version='3', format=None, mod=None, hash=None),
    ]

    assert manifest_match(base, added) is False
    assert manifest_match(added, base) is False
