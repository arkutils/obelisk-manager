from __future__ import annotations

import logging
from pathlib import Path
from shutil import copy2
from typing import TYPE_CHECKING, Annotated

from typer import Argument, Context, Option, Typer

from obelisk.commits import build_commit_message
from obelisk.common_args import DRY_RUN_ARG, QUIET_ARG, VERBOSE_ARG, VERSION_ARG, initialise_app
from obelisk.filtering import file_is_allowed
from obelisk.git import commit_all, fast_forward, fetch, is_clean, is_git_available, push, reset_hard
from obelisk.manifest import MANIFEST_FILENAME, ManifestEntry, manifest_match, write_manifest
from obelisk.scanner import create_manifest_from_folder


if TYPE_CHECKING:
    from collections.abc import Callable, Iterable


logger = logging.getLogger('obelisk')

app = Typer()


@app.command(
    name='live-import',
    no_args_is_help=True,
    short_help='Import files into a live Obelisk Git repository.',
    help="""Import files into an Obelisk repository, updating the manifest and performing Git actions as needed.

    This command is for managing files in a live Obelisk repository and will perform the following steps:
    1. Fetch and synchronize with the remote repository
    2. Copy the input files or directories into the destination path within the repository
    3. Update or create an Obelisk manifest for that directory
    4. Commit the changes (optionally with a supplied message)
    5. Push the changes to the remote repository
    """,
)
def live_import(
    ctx: Context,
    repo: Annotated[
        Path,
        Option(
            '-r',
            '--repo',
            help='Path to a local Git clone which will be managed.',
            exists=True,
            file_okay=False,
            dir_okay=True,
        ),
    ],
    inputs: Annotated[
        list[Path],
        Argument(
            ...,
            help='Input files or directories to import.',
            exists=True,
            file_okay=True,
            dir_okay=True,
        ),
    ],
    dest: Annotated[
        str,
        Argument(
            ...,
            help='Destination folder, relative to the repo root.',
            metavar='DEST_PATH',
        ),
    ],
    msg_title: Annotated[
        str | None,
        Option(
            '-t',
            '--title',
            help='Title line for the commit message. If not provided, a default summary will be used.',
        ),
    ] = None,
    msg_body: Annotated[
        str | None,
        Option(
            '-b',
            '--body',
            help='Body text for the commit message. By default the file change list is appended.',
        ),
    ] = None,
    exclude_file_list: Annotated[
        bool,
        Option(
            '--exclude-file-list',
            help='Exclude the file change list from the commit message.',
        ),
    ] = False,
    allow_all: Annotated[
        bool,
        Option(
            '-a',
            '--all',
            '--allow-all',
            help='Allow importing files normally filtered out (hidden/underscored or unrecognised types).',
        ),
    ] = False,
    git_reset: Annotated[
        bool,
        Option(
            '--git-reset',
            help='Perform a hard reset to origin/main (destructive) on the repository before importing.',
        ),
    ] = False,
    skip_pull: Annotated[
        bool,
        Option(
            '--skip-pull',
            help='Skip fetch/reset/fast-forward entirely (also implies --skip-push).',
        ),
    ] = False,
    skip_push: Annotated[
        bool,
        Option(
            '--skip-push',
            help='Skip pushing changes to the remote repository.',
        ),
    ] = False,
    show_version: VERSION_ARG = False,
    dry_run: DRY_RUN_ARG = False,
    verbose: VERBOSE_ARG = False,
    quiet: QUIET_ARG = False,
):
    console = initialise_app(ctx)
    print = console.print  # noqa: A001

    if dry_run:
        print('[bold cyan]Dry Run Enabled[/bold cyan]')

    # Check Git availability and repo validity
    _preflight_checks(repo, printer=print, ctx=ctx)

    # Basic DEST_PATH verification (non-absolute, no parent traversal)
    dest_path = _validate_dest_path(repo, dest, printer=print, ctx=ctx)

    # Effective push flag
    do_push = (not skip_pull) and (not skip_push)

    # Ensure repo is clean and up-to-date, unless skipping pull
    _sync_repository(repo, dry_run=dry_run, skip_pull=skip_pull, git_reset=git_reset, printer=print, ctx=ctx)

    # Collect and filter inputs
    print('[bold]Collecting input files...[/bold]')
    allowed = _collect_allowed_inputs(inputs, allow_all, printer=print, ctx=ctx)

    # Ensure destination exists and perform copy + manifest update
    before_entries, after_entries = _apply_import(dest_path, allowed, dry_run=dry_run, printer=print, ctx=ctx)

    # Compute commit message and decide whether to commit
    if manifest_match(before_entries, after_entries):
        print('[green]No manifest changes needed. Skipping commit/push.[/green]')
        return

    commit_msg = build_commit_message(
        before_entries,
        after_entries,
        title=msg_title or 'Imported $total changes to $path',
        add_body=msg_body,
        include_file_list=not exclude_file_list,
        template_fields={'path': dest},
    )
    print('[bold]Commit message:[/bold]')
    print(commit_msg)

    # Commit and optionally push
    print('[bold]Committing changes...[/bold]')
    try:
        commit_all(repo, commit_msg, dry_run=dry_run)
    except Exception as e:
        print(f'[red]Error:[/red] {e}')
        ctx.exit(1)

    _maybe_push(repo, do_push=do_push, dry_run=dry_run, printer=print, ctx=ctx)

    print('[bold green]Live import completed.[/bold green]')


def _validate_dest_path(repo: Path, dest: str, printer: Callable[..., None], ctx: Context) -> Path:
    """Basic destination validation and normalization.

    - Rejects absolute paths
    - Rejects parent traversal (..)
    - Ensures resulting path is within the repo directory
    - Ensures destination path within the repo already exists and is a directory
    """
    dest = dest or '.'

    dest_p = Path(dest)
    if dest_p.root or dest_p.is_absolute():  # Just checking root is probably enough, but extra safe
        printer('[red]Error:[/red] Destination path must be a relative path')
        ctx.exit(1)

    if any(part == '..' for part in dest_p.parts):
        printer('[red]Error:[/red] Destination path must not contain parent traversal (..)')
        ctx.exit(1)

    # Ensure dest is under repo
    resolved = (repo / dest_p).resolve()
    repo_resolved = repo.resolve()
    try:
        resolved.relative_to(repo_resolved)
    except ValueError:
        printer('[red]Error:[/red] Destination path must be within the repository')
        ctx.exit(1)

    if not resolved.exists() or not resolved.is_dir():
        printer('[red]Error:[/red] Destination path must be an existing directory')
        ctx.exit(1)

    return resolved


def _enumerate_input_files(inputs: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for p in inputs:
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            files.extend([child for child in p.iterdir() if child.is_file()])
    return files


def _preflight_checks(repo: Path, *, printer: Callable[..., None], ctx: Context) -> None:
    # Check we have Git
    if not is_git_available():
        printer('[red]git CLI not found on PATH[/red]')
        ctx.exit(1)

    # Check repo path is a directory
    if not repo.is_dir():
        printer('[red]Repository path must be a directory[/red]')
        ctx.exit(1)

    # Check Git repo
    git_dir = repo / '.git'
    if not git_dir.is_dir():
        printer('[red]Repository path is not a Git repository (missing .git directory)[/red]')
        ctx.exit(1)


def _sync_repository(
    repo: Path,
    *,
    dry_run: bool,
    skip_pull: bool,
    git_reset: bool,
    printer: Callable[..., None],
    ctx: Context,
) -> None:
    if skip_pull:
        printer('[yellow]Skipping repository synchronization [--skip-pull].[/yellow]')
        return

    printer('[bold]Checking repository status...[/bold]')
    if not is_clean(repo, dry_run=dry_run):
        printer('[red]Repository has uncommitted changes.[/red]')
        printer('Commit/stash or pass --skip-pull to proceed without sync.')
        ctx.exit(1)

    printer('[bold]Synchronizing with remote...[/bold]')
    try:
        fetch(repo, dry_run=dry_run)
        if git_reset:
            reset_hard(repo, dry_run=dry_run)
        else:
            fast_forward(repo, dry_run=dry_run)
    except Exception as e:
        printer(f'[red]Error during repository synchronization:[/red] {e}')
        ctx.exit(1)


def _collect_allowed_inputs(
    inputs: Iterable[Path],
    allow_all: bool,
    *,
    printer: Callable[..., None],
    ctx: Context,
) -> list[Path]:
    input_files = _enumerate_input_files(inputs)
    allowed: list[Path] = []
    filtered: list[Path] = []
    for p in input_files:
        if allow_all or file_is_allowed(p):
            allowed.append(p)
        else:
            filtered.append(p)

    if filtered:
        printer(
            '[red]Error:[/red] Some unhandled files are excluded. '
            'Re-run with [yellow]--allow-all/-a[/yellow] if you are sure you wish to include them:',
        )
        for excluded_file in filtered:
            printer(f'  - {excluded_file}')
        ctx.exit(1)
    return allowed


def _apply_import(
    dest_path: Path,
    allowed: list[Path],
    *,
    dry_run: bool,
    printer: Callable[..., None],
    ctx: Context,
) -> tuple[list[ManifestEntry], list[ManifestEntry]]:
    if not dry_run:
        dest_path.mkdir(parents=True, exist_ok=True)

    # Scan current state (before)
    printer('[bold]Scanning current manifest (before)...[/bold]')
    try:
        before_entries = create_manifest_from_folder(dest_path)
    except Exception as e:
        printer(f'[red]Error:[/red] File scan failed: {e}')
        ctx.exit(1)

    # Copy files
    printer('[bold]Copying files...[/bold]')
    for src in allowed:
        dst = dest_path / src.name
        if dry_run:
            printer(f'  * {src} -> {dst} [dry-run]')
        else:
            try:
                copy2(src, dst)
            except Exception as e:
                printer(f'[red]Error:[/red] Failed to copy {src} to {dst}: {e}')
                ctx.exit(1)
            printer(f'  * {src} -> {dst}')

    # Scan new state (after) and write manifest
    printer('[bold]Updating manifest...[/bold]')
    after_entries = create_manifest_from_folder(dest_path)
    manifest_file = dest_path / MANIFEST_FILENAME
    if dry_run:
        printer(f'  * Would write manifest: {manifest_file}')
    else:
        try:
            write_manifest(manifest_file, after_entries)
        except Exception as e:
            printer(f'[red]Error:[/red] Failed to write manifest: {e}')
            ctx.exit(1)
        printer(f'  * Wrote manifest: {manifest_file}')

    return before_entries, after_entries


def _maybe_push(
    repo: Path,
    *,
    do_push: bool,
    dry_run: bool,
    printer: Callable[..., None],
    ctx: Context,
) -> None:
    if do_push:
        printer('[bold]Pushing to remote...[/bold]')
        try:
            push(repo, dry_run=dry_run)
        except Exception as e:
            printer(f'[red]Error:[/red] Failed to push to remote: {e}')
            ctx.exit(1)
    else:
        printer('[yellow]Skipping push as requested.[/yellow]')


__all__ = ('app',)
