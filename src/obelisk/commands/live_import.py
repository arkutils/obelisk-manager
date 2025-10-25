from __future__ import annotations

import logging
from pathlib import Path  # noqa: TC003 - just plain wrong
from typing import Annotated

from rich.progress import track
from typer import Argument, Context, Option, Typer

from obelisk.common_args import DRY_RUN_ARG, QUIET_ARG, VERBOSE_ARG, VERSION_ARG, initialise_app


logger = logging.getLogger('obelisk')

app = Typer()


@app.command(
    name='live-import',
    no_args_is_help=True,
    short_help='Import files into a live Obelisk Git repository.',
    help="""Import files into an Obelisk repository, updating the manifest and performing Git actions as needed.

    This command is for managing files in a live Obelisk repository and will perform the following:
    1. Perform `[bold]git fetch[/bold]` on the repository to ensure it is up to date
    2. Perform `[bold]git rebase --hard origin/main[/bold]` to synchronize with the remote main branch
    3. Copy the specified input files or directories into the specified destination path within the repository
    4. Update or create an Obelisk manifest for that directory
    5. Commit the changes with the specified identity and message
    6. Push the changes to the remote repository
    """,
)
def live_import(
    ctx: Context,
    repo: Annotated[
        Path,
        Option(
            '-r',
            '--repo',
            help='Path to a local clone of the Obelisk repository',
            exists=True,
            file_okay=False,
            dir_okay=True,
        ),
    ],
    inputs: list[Path] = Argument(
        ...,
        help='Input files or directories to import.',
        exists=True,
        file_okay=True,
        dir_okay=True,
    ),
    dest: str = Argument(
        ...,
        help='Destination path, relative to the repo root.',
        metavar='DEST_PATH',
    ),
    identity: str | None = Option(
        None,
        '-i',
        '--identity',
        metavar='EMAIL',
        help='User email to use for Git.',
    ),
    message: str | None = Option(
        None,
        '-m',
        '--message',
        help='Commit message to use for Git.',
    ),
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

    print(f'[bold]Repository:[/bold] {repo}')
    print(f'[bold]Destination:[/bold] <repo>/{dest}')
    print('[bold]Inputs:[/bold]')
    for input_path in inputs:
        print(f'    {input_path!s}')
    if identity:
        print(f'[bold]Identity:[/bold] {identity}')
    if message:
        print(f'[bold]Message:[/bold] {message}')
    if dry_run:
        print('[bold yellow]Dry Run Enabled[/bold yellow]')
    if skip_push:
        print('[bold yellow]Skip Push Enabled[/bold yellow]')

    for src in track(
        inputs,
        transient=True,
        description='Importing files...',
        update_period=0.5,
        console=console,
    ):
        # dest_path = repo / dest / src.name
        logger.info('Import %s to %s', src, (repo / dest / src.name).relative_to(repo))
        logger.warning('Import %s to %s', src, (repo / dest / src.name).relative_to(repo))

    logger.error('This is an error message example.')


__all__ = ('app',)
