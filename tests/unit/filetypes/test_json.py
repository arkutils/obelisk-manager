from pathlib import Path
from typing import Any

import pytest

import obelisk.filetypes.json as json_ft


def _data_path(name: str) -> Path:
    # tests/data/<name>
    return Path(__file__).parents[2] / 'data' / name


def test_get_metadata_from_json_valid_with_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange: mock loader to return a simple, valid dict
    def fake_load(_: Path) -> dict[str, Any]:
        return {
            'version': '1.0.0',
            'format': 'custom-format',
            'mod': {'id': 1, 'name': 'Demo'},
            'other': 123,
        }

    monkeypatch.setattr(json_ft, '_load_json', fake_load)
    p = Path('dummy.json')

    # Act
    entry = json_ft.get_metadata_from_json(p)

    # Assert
    assert entry is not None
    assert entry.filename == 'dummy.json'
    assert entry.version == '1.0.0'
    assert entry.format == 'custom-format'
    assert entry.mod == {'id': 1, 'name': 'Demo'}


def test_get_metadata_from_json_non_dict_with_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange: loader returns a non-dict (invalid)
    def fake_load(_: Path) -> list[int]:
        return [1, 2, 3]

    monkeypatch.setattr(json_ft, '_load_json', fake_load)

    # Act / Assert
    assert json_ft.get_metadata_from_json(Path('dummy.json')) is None


def test_get_metadata_from_json_missing_version_with_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange: loader returns dict with no version
    def fake_load(_: Path) -> dict[str, Any]:
        return {'format': 'x'}

    monkeypatch.setattr(json_ft, '_load_json', fake_load)

    # Act / Assert
    assert json_ft.get_metadata_from_json(Path('dummy.json')) is None


def test_get_metadata_from_json_non_string_version_with_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange: loader returns dict with non-string version
    def fake_load(_: Path) -> dict[str, Any]:
        return {'version': 123, 'format': 'x'}

    monkeypatch.setattr(json_ft, '_load_json', fake_load)

    # Act / Assert
    assert json_ft.get_metadata_from_json(Path('dummy.json')) is None


def test_get_metadata_from_json_format_not_string(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange: loader returns dict with non-string format (should coerce to None)
    def fake_load(_: Path) -> dict[str, Any]:
        return {'version': '2.0', 'format': 42, 'mod': {'a': 1}}

    monkeypatch.setattr(json_ft, '_load_json', fake_load)

    entry = json_ft.get_metadata_from_json(Path('dummy.json'))
    assert entry is not None
    assert entry.format is None


def test_get_metadata_from_json_mod_not_dict(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange: loader returns dict with non-dict mod (should coerce to None)
    def fake_load(_: Path) -> dict[str, Any]:
        return {'version': '2.1', 'format': 'fmt', 'mod': [1, 2, 3]}

    monkeypatch.setattr(json_ft, '_load_json', fake_load)

    entry = json_ft.get_metadata_from_json(Path('dummy.json'))
    assert entry is not None
    assert entry.mod is None


def test_get_metadata_from_json_loader_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange: loader fails / returns None
    def fake_load(_: Path) -> None:  # type: ignore[override]
        return None

    monkeypatch.setattr(json_ft, '_load_json', fake_load)

    # Act / Assert
    assert json_ft.get_metadata_from_json(Path('dummy.json')) is None


@pytest.mark.parametrize(
    ('filename', 'expected_version', 'expected_format', 'expected_mod_checks'),
    [
        (
            'input1.json',
            '23456345.11.1',
            '1.16-mod-remap',
            {'id': 123456, 'ASA': True, 'author': 'A Mod Author'},
        ),
        (
            'input2.json',
            '1.1.2',
            '1.16-mod-remap',
            {'id': 654321, 'author': 'A.N. Other'},
        ),
    ],
)
def test_get_metadata_from_json_with_real_files(
    filename: str,
    expected_version: str,
    expected_format: str,
    expected_mod_checks: dict[str, Any],
) -> None:
    # Arrange: use real sample files under tests/data
    path = _data_path(filename)

    # Act
    entry = json_ft.get_metadata_from_json(path)

    # Assert
    assert entry is not None
    assert entry.filename == filename
    assert entry.version == expected_version
    assert entry.format == expected_format
    assert entry.mod is not None
    for k, v in expected_mod_checks.items():
        assert entry.mod.get(k) == v
