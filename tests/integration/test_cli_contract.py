from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from obelisk import __version__
from obelisk.__main__ import app


if TYPE_CHECKING:
    from pathlib import Path


runner = CliRunner()


@pytest.mark.parametrize(
    'args',
    [
        ['--help'],
        ['update-manifest', '--help'],
        ['add-files', '--help'],
        ['live-import', '--help'],
        ['check', '--help'],
    ],
)
def test_help_is_available_on_root_and_commands(args: list[str]) -> None:
    result = runner.invoke(app, args)

    assert result.exit_code == 0, result.output
    assert 'Usage:' in result.output


def test_root_without_arguments_shows_help() -> None:
    result = runner.invoke(app)

    assert result.exit_code == 2
    assert 'Usage:' in result.output


@pytest.mark.parametrize(
    'args',
    [
        ['--version'],
        ['update-manifest', '--version'],
        ['add-files', '--version'],
        ['live-import', '--version'],
        ['check', '--version'],
    ],
)
def test_version_is_available_on_root_and_commands(args: list[str]) -> None:
    result = runner.invoke(app, args)

    assert result.exit_code == 0, result.output
    assert result.output.strip() == __version__


@pytest.mark.parametrize(
    ('args', 'expected_message'),
    [
        (['add-files', '.'], 'DEST_PATH'),
        (['live-import', '--repo', '.'], 'Missing argument'),
        (['check', '--not-a-real-option'], 'No such option'),
    ],
)
def test_invalid_cli_arguments_return_usage_error(
    args: list[str],
    expected_message: str,
) -> None:
    result = runner.invoke(app, args)

    assert result.exit_code == 2
    assert 'Usage:' in result.output
    assert expected_message in result.output


@pytest.mark.parametrize(
    ('flag', 'expected_level'),
    [('-vv', 'Log Level: 10 (DEBUG)'), ('-qq', 'Log Level: 40 (ERROR)')],
)
def test_verbosity_flags_are_counted(flag: str, expected_level: str, tmp_path: Path) -> None:
    result = runner.invoke(app, ['update-manifest', flag, str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert expected_level in result.output


def test_check_accepts_repeated_ignore_options(tmp_path: Path) -> None:
    (tmp_path / 'tracked.json').write_text('{"version":"1"}', encoding='utf-8')
    setup_result = runner.invoke(app, ['update-manifest', str(tmp_path)])
    assert setup_result.exit_code == 0, setup_result.output

    (tmp_path / 'ignored-one.txt').write_text('one', encoding='utf-8')
    (tmp_path / 'ignored-two.txt').write_text('two', encoding='utf-8')
    result = runner.invoke(
        app,
        [
            'check',
            '--ignore',
            'ignored-one.txt',
            '--ignore',
            'ignored-two.txt',
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert 'No issues found' in result.output


@pytest.mark.parametrize('allow_all_flag', ['-a', '--all', '--allow-all'])
def test_add_files_accepts_allow_all_aliases(
    allow_all_flag: str,
    tmp_path: Path,
) -> None:
    source = tmp_path / 'notes.txt'
    source.write_text('notes', encoding='utf-8')
    dest = tmp_path / 'destination'
    dest.mkdir()

    result = runner.invoke(app, ['add-files', allow_all_flag, str(source), str(dest)])

    assert result.exit_code == 0, result.output
    assert (dest / source.name).read_text(encoding='utf-8') == 'notes'


@pytest.mark.parametrize('allow_all_flag', ['-a', '--all', '--allow-all'])
def test_live_import_accepts_allow_all_aliases(
    allow_all_flag: str,
    tmp_path: Path,
    git_remote_and_local: dict[str, Path],
) -> None:
    source = tmp_path / 'notes.txt'
    source.write_text('notes', encoding='utf-8')
    repo = git_remote_and_local['local']
    dest = repo / 'import'
    dest.mkdir()

    result = runner.invoke(
        app,
        [
            'live-import',
            '--repo',
            str(repo),
            '--skip-pull',
            allow_all_flag,
            str(source),
            'import',
        ],
    )

    assert result.exit_code == 0, result.output
    assert (dest / source.name).read_text(encoding='utf-8') == 'notes'
