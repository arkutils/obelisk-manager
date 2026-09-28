from __future__ import annotations

import os
from typing import TYPE_CHECKING

from typer.testing import CliRunner

from obelisk.__main__ import app


if TYPE_CHECKING:
    from pathlib import Path


runner = CliRunner()


def _make_folder(tmp_path: Path, name: str) -> Path:
    folder = tmp_path / name
    folder.mkdir()
    return folder


def test_check_passes_on_clean_manifest(tmp_path: Path) -> None:
    folder = _make_folder(tmp_path, 'clean')
    (folder / 'a.json').write_text('{"version":"1"}', encoding='utf-8')
    res_setup = runner.invoke(app, ['update-manifest', str(folder)])
    assert res_setup.exit_code == 0, res_setup.output

    res = runner.invoke(app, ['check', str(folder)])

    assert res.exit_code == 0, res.output
    assert 'No issues found' in res.output


def test_check_defaults_to_current_directory(tmp_path: Path) -> None:
    folder = _make_folder(tmp_path, 'default')
    (folder / 'a.json').write_text('{"version":"1"}', encoding='utf-8')
    res_setup = runner.invoke(app, ['update-manifest', str(folder)])
    assert res_setup.exit_code == 0, res_setup.output

    old_cwd = os.getcwd()  # noqa: PTH109
    try:
        os.chdir(folder)
        res = runner.invoke(app, ['check'])
    finally:
        os.chdir(old_cwd)

    assert res.exit_code == 0, res.output


def test_check_accepts_manifest_file_path(tmp_path: Path) -> None:
    folder = _make_folder(tmp_path, 'file-arg')
    (folder / 'a.json').write_text('{"version":"1"}', encoding='utf-8')
    res_setup = runner.invoke(app, ['update-manifest', str(folder)])
    assert res_setup.exit_code == 0, res_setup.output

    res = runner.invoke(app, ['check', str(folder / '_manifest.json')])

    assert res.exit_code == 0, res.output


def test_check_reports_missing_file(tmp_path: Path) -> None:
    folder = _make_folder(tmp_path, 'missing')
    (folder / 'a.json').write_text('{"version":"1"}', encoding='utf-8')
    res_setup = runner.invoke(app, ['update-manifest', str(folder)])
    assert res_setup.exit_code == 0, res_setup.output

    (folder / 'a.json').unlink()

    res = runner.invoke(app, ['check', str(folder)])

    assert res.exit_code == 1
    assert 'Missing file: a.json' in res.output


def test_check_reports_content_mismatch(tmp_path: Path) -> None:
    folder = _make_folder(tmp_path, 'mismatch')
    (folder / 'a.json').write_text('{"version":"1","metadata":{"foo":"bar"}}', encoding='utf-8')
    res_setup = runner.invoke(app, ['update-manifest', str(folder)])
    assert res_setup.exit_code == 0, res_setup.output

    (folder / 'a.json').write_text('{"version":"1","metadata":{"foo":"baz"}}', encoding='utf-8')

    res = runner.invoke(app, ['check', str(folder)])

    assert res.exit_code == 1
    assert 'Content mismatch: a.json' in res.output


def test_check_ignores_version_only_change_by_default(tmp_path: Path) -> None:
    folder = _make_folder(tmp_path, 'version-only')
    (folder / 'a.json').write_text('{"version":"1","metadata":{"foo":"bar"}}', encoding='utf-8')
    res_setup = runner.invoke(app, ['update-manifest', str(folder)])
    assert res_setup.exit_code == 0, res_setup.output

    (folder / 'a.json').write_text('{"version":"1.1","metadata":{"foo":"bar"}}', encoding='utf-8')

    res = runner.invoke(app, ['check', str(folder)])

    assert res.exit_code == 0, res.output


def test_check_accept_identical_versions_flags_version_only_change(tmp_path: Path) -> None:
    folder = _make_folder(tmp_path, 'version-only-strict')
    (folder / 'a.json').write_text('{"version":"1","metadata":{"foo":"bar"}}', encoding='utf-8')
    res_setup = runner.invoke(app, ['update-manifest', str(folder)])
    assert res_setup.exit_code == 0, res_setup.output

    (folder / 'a.json').write_text('{"version":"1.1","metadata":{"foo":"bar"}}', encoding='utf-8')

    res = runner.invoke(app, ['check', '--accept-identical-versions', str(folder)])

    assert res.exit_code == 1
    assert 'Content mismatch: a.json' in res.output


def test_check_fast_check_ignores_content_mismatch(tmp_path: Path) -> None:
    folder = _make_folder(tmp_path, 'fast')
    (folder / 'a.json').write_text('{"version":"1","metadata":{"foo":"bar"}}', encoding='utf-8')
    res_setup = runner.invoke(app, ['update-manifest', str(folder)])
    assert res_setup.exit_code == 0, res_setup.output

    (folder / 'a.json').write_text('{"version":"1","metadata":{"foo":"baz"}}', encoding='utf-8')

    res = runner.invoke(app, ['check', '--fast-check', str(folder)])

    assert res.exit_code == 0, res.output


def test_check_reports_untracked_file(tmp_path: Path) -> None:
    folder = _make_folder(tmp_path, 'untracked')
    (folder / 'a.json').write_text('{"version":"1"}', encoding='utf-8')
    res_setup = runner.invoke(app, ['update-manifest', str(folder)])
    assert res_setup.exit_code == 0, res_setup.output

    (folder / 'stray.txt').write_text('junk', encoding='utf-8')

    res = runner.invoke(app, ['check', str(folder)])

    assert res.exit_code == 1
    assert 'Untracked file: stray.txt' in res.output


def test_check_default_ignores_hidden_and_bang_files(tmp_path: Path) -> None:
    folder = _make_folder(tmp_path, 'ignored')
    (folder / 'a.json').write_text('{"version":"1"}', encoding='utf-8')
    res_setup = runner.invoke(app, ['update-manifest', str(folder)])
    assert res_setup.exit_code == 0, res_setup.output

    (folder / '.DS_Store').write_text('junk', encoding='utf-8')
    (folder / '!ignored.json').write_text('{}', encoding='utf-8')

    res = runner.invoke(app, ['check', str(folder)])

    assert res.exit_code == 0, res.output


def test_check_custom_ignore_overrides_default(tmp_path: Path) -> None:
    folder = _make_folder(tmp_path, 'custom-ignore')
    (folder / 'a.json').write_text('{"version":"1"}', encoding='utf-8')
    res_setup = runner.invoke(app, ['update-manifest', str(folder)])
    assert res_setup.exit_code == 0, res_setup.output

    (folder / '.hidden.txt').write_text('junk', encoding='utf-8')

    res = runner.invoke(app, ['check', '--ignore', '*.json', str(folder)])

    # Custom --ignore replaces the defaults entirely, so the hidden-file pattern no
    # longer applies and the hidden file is now reported as untracked
    assert res.exit_code == 1
    assert 'Untracked file: .hidden.txt' in res.output


def test_check_reports_no_manifest_found(tmp_path: Path) -> None:
    folder = _make_folder(tmp_path, 'no-manifest')
    (folder / 'a.json').write_text('{"version":"1"}', encoding='utf-8')

    res = runner.invoke(app, ['check', str(folder)])

    assert res.exit_code == 1
    assert 'No _manifest.json found' in res.output
    assert 'Untracked file: a.json' in res.output


def test_check_multiple_paths_reported_independently(tmp_path: Path) -> None:
    good = _make_folder(tmp_path, 'good')
    (good / 'a.json').write_text('{"version":"1"}', encoding='utf-8')
    res_setup = runner.invoke(app, ['update-manifest', str(good)])
    assert res_setup.exit_code == 0, res_setup.output

    bad = _make_folder(tmp_path, 'bad')

    res = runner.invoke(app, ['check', str(good), str(bad)])

    assert res.exit_code == 1
    assert 'No issues found' in res.output
    assert 'No _manifest.json found' in res.output


def test_check_invalid_path_reported_as_failure(tmp_path: Path) -> None:
    missing = tmp_path / 'does-not-exist'

    res = runner.invoke(app, ['check', str(missing)])

    assert res.exit_code == 1
    assert 'Not a valid path' in res.output
    assert 'does-not-exist' in res.output
