from __future__ import annotations

from typing import TYPE_CHECKING

from typer.testing import CliRunner

from obelisk.__main__ import app
from obelisk.manifest import parse_manifest


if TYPE_CHECKING:
    from pathlib import Path


runner = CliRunner()


def _write_inputs(src_dir: Path) -> tuple[Path, Path]:
    src_dir.mkdir(parents=True, exist_ok=True)
    j = src_dir / 'info.json'
    p = src_dir / 'pic.png'
    j.write_text('{"version":"1","format":"fmt"}', encoding='utf-8')
    p.write_bytes(b'\x89PNG\r\n\x1a\n' + b'bytes')
    return j, p


def test_add_files_happy_path_copies_and_writes_manifest(tmp_path: Path) -> None:
    # Arrange
    dest = tmp_path / 'data' / 'a'
    dest.mkdir(parents=True, exist_ok=True)
    json_input, png_input = _write_inputs(tmp_path / 'inputs')

    # Act
    res = runner.invoke(app, ['add-files', str(json_input), str(png_input), str(dest)])

    # Assert CLI success and messaging
    assert res.exit_code == 0, res.output
    assert 'Add files completed.' in res.output

    # Files are copied and manifest written
    manifest_path = dest / '_manifest.json'
    assert (dest / 'info.json').exists()
    assert (dest / 'pic.png').exists()
    assert manifest_path.exists()

    # Manifest has expected entries
    entries = parse_manifest(manifest_path)
    by_name = {e.filename: e for e in entries}
    assert set(by_name) == {'info.json', 'pic.png'}
    assert by_name['info.json'].version == '1'
    assert by_name['info.json'].format == 'fmt'
    assert by_name['pic.png'].hash is not None
    assert by_name['pic.png'].hash.startswith('md5:')


def test_add_files_accepts_directory_input_non_recursive(tmp_path: Path) -> None:
    # Arrange: place inputs in a directory, with a nested directory that should be ignored
    dest = tmp_path / 'data' / 'b'
    dest.mkdir(parents=True, exist_ok=True)

    inputs_dir = tmp_path / 'inputs_dir'
    j, p = _write_inputs(inputs_dir)
    # Nested file should not be picked up (non-recursive expansion)
    nested_dir = inputs_dir / 'nested'
    nested_dir.mkdir(parents=True, exist_ok=True)
    (nested_dir / 'extra.json').write_text('{"version":"9","format":"x"}', encoding='utf-8')

    # Act: pass the directory only
    res = runner.invoke(app, ['add-files', str(inputs_dir), str(dest)])

    # Assert
    assert res.exit_code == 0, res.output
    assert (dest / j.name).exists()
    assert (dest / p.name).exists()
    assert (dest / 'extra.json').exists() is False  # not copied from nested dir
    # Manifest should not include the nested file either
    entries = parse_manifest(dest / '_manifest.json')
    names = {e.filename for e in entries}
    assert names == {j.name, p.name}


def test_add_files_blocks_unhandled_without_allow_all(tmp_path: Path) -> None:
    # Arrange
    dest = tmp_path / 'import'
    dest.mkdir(parents=True, exist_ok=True)
    bad = tmp_path / 'notes.txt'
    bad.write_text('n/a', encoding='utf-8')

    # Act
    res = runner.invoke(app, ['add-files', str(bad), str(dest)])

    # Assert
    assert res.exit_code != 0
    assert 'Some unhandled files are excluded.' in res.output
    assert 'notes.txt' in res.output


def test_add_files_dry_run_makes_no_changes(tmp_path: Path) -> None:
    # Arrange
    dest = tmp_path / 'data' / 'dry'
    dest.mkdir(parents=True, exist_ok=True)
    json_input, png_input = _write_inputs(tmp_path / 'dry_inputs')

    # Act
    res = runner.invoke(app, ['add-files', '--dry-run', str(json_input), str(png_input), str(dest)])

    # Assert: message and no filesystem changes
    assert res.exit_code == 0, res.output
    assert 'Dry Run Enabled' in res.output
    assert (dest / 'info.json').exists() is False
    assert (dest / 'pic.png').exists() is False
    assert (dest / '_manifest.json').exists() is False


def test_add_files_second_run_no_changes_skips_work(tmp_path: Path) -> None:
    # Arrange
    dest = tmp_path / 'data' / 'stable'
    dest.mkdir(parents=True, exist_ok=True)
    json_input, png_input = _write_inputs(tmp_path / 'inputs_again')

    # First run
    res1 = runner.invoke(app, ['add-files', str(json_input), str(png_input), str(dest)])
    assert res1.exit_code == 0, res1.output

    # Second run with same inputs should detect no changes
    res2 = runner.invoke(app, ['add-files', str(json_input), str(png_input), str(dest)])
    assert res2.exit_code == 0, res2.output
    assert 'No manifest changes needed.' in res2.output
