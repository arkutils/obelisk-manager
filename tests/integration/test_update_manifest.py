from __future__ import annotations

from typing import TYPE_CHECKING

from typer.testing import CliRunner

from obelisk.main import app
from obelisk.manifest import parse_manifest


if TYPE_CHECKING:
    from pathlib import Path


runner = CliRunner()


def _read_text(p: Path) -> str:
    return p.read_text(encoding='utf-8')


def test_update_manifest_noop_when_matches_existing(tmp_path: Path) -> None:
    # Arrange: create a folder with a json and a png, and generate a manifest once
    folder = tmp_path / 'data'
    folder.mkdir()

    (folder / 'a.json').write_text('{"version":"1"}', encoding='utf-8')
    (folder / 'img.png').write_bytes(b'\x89PNG\r\n\x1a\n' + b'bytes')

    # First run to create manifest
    res1 = runner.invoke(app, ['update-manifest', str(folder)])
    assert res1.exit_code == 0, res1.output

    manifest = folder / '_manifest.json'
    assert manifest.exists()
    before = _read_text(manifest)

    # Act: second run should be a no-op
    res2 = runner.invoke(app, ['update-manifest', str(folder)])

    # Assert
    assert res2.exit_code == 0, res2.output
    assert 'No updates necessary to the manifest.' in res2.output
    after = _read_text(manifest)
    assert after == before


def test_update_manifest_updates_single_file(tmp_path: Path) -> None:
    # Arrange
    folder = tmp_path / 'data'
    folder.mkdir()

    a = folder / 'a.json'
    b = folder / 'b.json'
    a.write_text('{"version":"1"}', encoding='utf-8')
    b.write_text('{"version":"2"}', encoding='utf-8')

    # Initial manifest
    res1 = runner.invoke(app, ['update-manifest', str(folder)])
    assert res1.exit_code == 0, res1.output
    before_entries = parse_manifest(folder / '_manifest.json')
    before_by_name = {e.filename: e for e in before_entries}
    assert before_by_name['a.json'].version == '1'
    assert before_by_name['b.json'].version == '2'

    # Mutate a single file
    a.write_text('{"version":"1.1"}', encoding='utf-8')

    # Act
    res2 = runner.invoke(app, ['update-manifest', str(folder)])

    # Assert
    assert res2.exit_code == 0, res2.output
    assert 'Changes detected in the manifest.' in res2.output

    after_entries = parse_manifest(folder / '_manifest.json')
    after_by_name = {e.filename: e for e in after_entries}
    assert len(after_entries) == 2
    assert after_by_name['a.json'].version == '1.1'
    assert after_by_name['b.json'].version == '2'  # unchanged


def test_update_manifest_creates_json_and_binary(tmp_path: Path) -> None:
    # Arrange
    folder = tmp_path / 'data'
    folder.mkdir()

    (folder / 'info.json').write_text('{"version":"9","format":"fmt"}', encoding='utf-8')
    (folder / 'pic.png').write_bytes(b'\x89PNG\r\n\x1a\n' + b'content')

    # Act
    res = runner.invoke(app, ['update-manifest', str(folder)])

    # Assert
    assert res.exit_code == 0, res.output
    mpath = folder / '_manifest.json'
    assert mpath.exists(), 'Manifest should be created when missing'

    entries = parse_manifest(mpath)
    by_name = {e.filename: e for e in entries}

    assert len(entries) == 2
    assert 'info.json' in by_name
    assert 'pic.png' in by_name
    assert by_name['info.json'].version == '9'
    assert by_name['info.json'].format == 'fmt'
    assert by_name['pic.png'].version is None
    assert by_name['pic.png'].hash is not None
    assert by_name['pic.png'].hash.startswith('md5:')


def test_update_manifest_dry_run_noop_exit_zero(tmp_path: Path) -> None:
    # Arrange: create manifest
    folder = tmp_path / 'data'
    folder.mkdir()
    (folder / 'a.json').write_text('{"version":"1"}', encoding='utf-8')

    res1 = runner.invoke(app, ['update-manifest', str(folder)])
    assert res1.exit_code == 0, res1.output
    manifest = folder / '_manifest.json'
    before = manifest.read_text(encoding='utf-8')

    # Act: dry-run when nothing changed
    res2 = runner.invoke(app, ['update-manifest', '--dry-run', str(folder)])

    # Assert: exit 0 and unchanged
    assert res2.exit_code == 0, res2.output
    assert 'No updates necessary to the manifest.' in res2.output
    after = manifest.read_text(encoding='utf-8')
    assert after == before


def test_update_manifest_dry_run_changes_exit_two(tmp_path: Path) -> None:
    # Arrange: create manifest with two files
    folder = tmp_path / 'data'
    folder.mkdir()
    a = folder / 'a.json'
    b = folder / 'b.json'
    a.write_text('{"version":"1"}', encoding='utf-8')
    b.write_text('{"version":"2"}', encoding='utf-8')

    res1 = runner.invoke(app, ['update-manifest', str(folder)])
    assert res1.exit_code == 0, res1.output
    manifest = folder / '_manifest.json'
    before = manifest.read_text(encoding='utf-8')

    # Mutate one file to trigger change
    a.write_text('{"version":"1.1"}', encoding='utf-8')

    # Act: dry-run; should detect change and exit code 2
    res2 = runner.invoke(app, ['update-manifest', '--dry-run', str(folder)])

    # Assert
    assert res2.exit_code == 2, res2.output
    assert 'Changes detected in the manifest.' in res2.output
    assert 'Dry run mode - no changes will be written.' in res2.output

    # Verify manifest file unchanged on disk
    after = manifest.read_text(encoding='utf-8')
    assert after == before
