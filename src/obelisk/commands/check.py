from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

from typer import Argument, Context, Option, Typer

from obelisk.cmd_utils.common_args import (
    ACCEPT_IDENTICAL_VERSIONS_ARG,
    QUIET_ARG,
    VERBOSE_ARG,
    VERSION_ARG,
    initialise_app,
)
from obelisk.filetypes import registered_types
from obelisk.filtering import DEFAULT_IGNORE_PATTERNS, is_under_ignored, resolve_ignored_paths
from obelisk.manifest import MANIFEST_FILENAME, ManifestEntry, entries_match, parse_manifest


if TYPE_CHECKING:
    from collections.abc import Iterable


logger = logging.getLogger('obelisk')

app = Typer()


@app.command(
    name='check',
    no_args_is_help=False,
    short_help='Check a directory against its manifest.',
    help=(
        'Verify that every manifest entry exists and (by default) still matches its file, '
        'and that every non-ignored file in the directory is accounted for in the manifest.'
    ),
)
def check(
    ctx: Context,
    paths: Annotated[
        list[Path] | None,
        Argument(
            help='Directories or manifest files to check. Defaults to the current directory.',
            metavar='PATHS',
        ),
    ] = None,
    ignore: Annotated[
        list[str],
        Option(
            '--ignore',
            help='Glob pattern (relative to each directory) of files/directories to ignore. Repeatable.',
        ),
    ] = list(DEFAULT_IGNORE_PATTERNS),  # noqa: B006 - read-only, never mutated
    fast_check: Annotated[
        bool,
        Option(
            '--fast-check',
            help='Only check file existence and recognised type; skip full metadata comparison.',
        ),
    ] = False,
    accept_identical_versions: ACCEPT_IDENTICAL_VERSIONS_ARG = False,
    show_version: VERSION_ARG = False,
    verbose: VERBOSE_ARG = False,
    quiet: QUIET_ARG = False,
):
    console = initialise_app(ctx)
    print = console.print  # noqa: A001

    any_failed = False
    for raw_path in paths or [Path()]:
        print(f'[bold]Path:[/bold] {raw_path}')

        resolved = _resolve_manifest_and_folder(raw_path)
        if resolved is None:
            print(f'[red]:x: Not a valid path: {raw_path}[/red]')
            any_failed = True
            print()
            continue

        folder_path, manifest_path = resolved
        issues = _check_path(
            folder_path,
            manifest_path,
            ignore_patterns=ignore,
            fast_check=fast_check,
            accept_identical_versions=accept_identical_versions,
        )
        if issues:
            any_failed = True
            for issue in issues:
                print(f'[red]:x: {issue}[/red]')
        else:
            print('[bold green]:thumbs_up: No issues found.[/bold green]')
        print()

    if any_failed:
        ctx.exit(1)


def _resolve_manifest_and_folder(path: Path) -> tuple[Path, Path] | None:
    # Accept either a manifest-containing directory or a direct path to the manifest file
    if path.is_dir():
        return path, path / MANIFEST_FILENAME
    if path.is_file():
        return path.parent, path
    return None


def _check_path(
    folder_path: Path,
    manifest_path: Path,
    *,
    ignore_patterns: Iterable[str],
    fast_check: bool,
    accept_identical_versions: bool,
) -> list[str]:
    issues: list[str] = []

    entries: list[ManifestEntry] = []
    if not manifest_path.is_file():
        issues.append('No _manifest.json found')
    else:
        entries = parse_manifest(manifest_path)

    for entry in entries:
        error = _check_entry(
            folder_path,
            entry,
            fast_check=fast_check,
            accept_identical_versions=accept_identical_versions,
        )
        if error:
            issues.append(error)

    # Stray-file scan is recursive, unlike manifest discovery
    ignored = resolve_ignored_paths(folder_path, ignore_patterns) | {manifest_path}
    known_filenames = {entry.filename for entry in entries}
    for file_path in _walk_files(folder_path, ignored):
        rel = file_path.relative_to(folder_path).as_posix()
        if rel not in known_filenames:
            issues.append(f'Untracked file: {rel}')

    return issues


def _check_entry(
    folder_path: Path,
    entry: ManifestEntry,
    *,
    fast_check: bool,
    accept_identical_versions: bool,
) -> str | None:
    full_path = folder_path / entry.filename
    if not full_path.is_file():
        return f'Missing file: {entry.filename}'

    extension = full_path.suffix.lstrip('.')
    handler = registered_types.get(extension)
    if handler is None:
        return f'Unrecognised file type: {entry.filename}'

    if fast_check:
        return None

    computed = handler(full_path)
    if computed is None:
        return f'Invalid file: {entry.filename}'

    # Handlers only know the file's basename; restore the manifest's (possibly nested) filename
    computed = computed.model_copy(update={'filename': entry.filename})
    if not entries_match(entry, computed, accept_identical_versions=accept_identical_versions):
        return f'Content mismatch: {entry.filename}'

    return None


def _walk_files(root: Path, ignored: set[Path]) -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        dirnames[:] = [name for name in dirnames if not is_under_ignored(current / name, ignored)]
        for filename in filenames:
            file_path = current / filename
            if not is_under_ignored(file_path, ignored):
                files.append(file_path)
    return files


__all__ = ('app',)
