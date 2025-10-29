from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

from typer import Argument, Context, Option, Typer

from obelisk.cmd_utils.apply_import import apply_import
from obelisk.cmd_utils.common_args import DRY_RUN_ARG, QUIET_ARG, VERBOSE_ARG, VERSION_ARG, initialise_app
from obelisk.cmd_utils.input_utils import collect_allowed_inputs
from obelisk.manifest import manifest_match


if TYPE_CHECKING:
    from collections.abc import Callable


logger = logging.getLogger('obelisk')

app = Typer()


@app.command(
    name='add-files',
    no_args_is_help=True,
    short_help='Copy files into a folder and update the manifest.',
    help=(
        'Copy the given input files or the files inside directories into the destination folder, '
        'then update or create the Obelisk manifest (_manifest.json) for that folder.'
    ),
)
def add_files(
    ctx: Context,
    inputs: Annotated[
        list[Path],
        Argument(
            ...,
            help='Input files or directories to add.',
            exists=True,
            file_okay=True,
            dir_okay=True,
        ),
    ],
    dest: Annotated[
        Path,
        Argument(
            ...,
            help='Destination folder where files will be copied.',
            metavar='DEST_PATH',
            exists=True,
            file_okay=False,
            dir_okay=True,
        ),
    ],
    allow_all: Annotated[
        bool,
        Option(
            '-a',
            '--all',
            '--allow-all',
            help='Allow importing files normally filtered out (hidden/underscored or unrecognised types).',
        ),
    ] = False,
    show_version: VERSION_ARG = False,
    dry_run: DRY_RUN_ARG = False,
    verbose: VERBOSE_ARG = False,
    quiet: QUIET_ARG = False,
):
    """Copy files into a destination folder and update its _manifest.json."""
    console = initialise_app(ctx)
    print = console.print  # noqa: A001

    if dry_run:
        print('[bold cyan]Dry Run Enabled[/bold cyan]')

    # Resolve and validate destination folder (create later if needed)
    dest_path = _resolve_dest_folder(dest, printer=print, ctx=ctx)

    # Collect and filter inputs
    print('[bold]Collecting input files...[/bold]')
    allowed, filtered = collect_allowed_inputs(inputs, allow_all=allow_all)
    if filtered:
        print(
            '[red]Error:[/red] Some unhandled files are excluded. '
            'Re-run with [yellow]--allow-all/-a[/yellow] if you are sure you wish to include them:',
        )
        for excluded_file in filtered:
            print(f'  - {excluded_file}')
        ctx.exit(1)

    # Perform copy and manifest update
    before_entries, after_entries = apply_import(dest_path, allowed, dry_run=dry_run, printer=print)

    if manifest_match(before_entries, after_entries):
        print('[green]No manifest changes needed.[/green]')
        return

    print('[bold green]Add files completed.[/bold green]')


def _resolve_dest_folder(dest: Path, *, printer: Callable[..., None], ctx: Context) -> Path:
    # Accept absolute or relative; if path exists and is a file, bail.
    dest_path = Path(dest).resolve()
    if dest_path.exists() and not dest_path.is_dir():
        printer('[red]Error:[/red] Destination path exists and is not a directory')
        ctx.exit(1)
    return dest_path


__all__ = ('app',)
