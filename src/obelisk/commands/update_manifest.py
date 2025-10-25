from __future__ import annotations

import logging
from pathlib import Path  # noqa: TC003 - just plain wrong
from typing import Annotated

from typer import Argument, Context, Typer

from obelisk.common_args import DRY_RUN_ARG, QUIET_ARG, VERBOSE_ARG, VERSION_ARG, initialise_app
from obelisk.manifest import manifest_match, parse_manifest, write_manifest
from obelisk.scanner import create_manifest_from_folder


logger = logging.getLogger('obelisk')

app = Typer()


@app.command(
    name='update-manifest',
    no_args_is_help=True,
    short_help='Update the manifest in an existing directory.',
)
def update_manifest(
    ctx: Context,
    folder_or_manifest: Annotated[
        Path,
        Argument(
            help='Path to the manifest or its directory.',
            exists=True,
            file_okay=True,
            dir_okay=True,
            metavar='MANIFEST',
        ),
    ],
    show_version: VERSION_ARG = False,
    dry_run: DRY_RUN_ARG = False,
    verbose: VERBOSE_ARG = False,
    quiet: QUIET_ARG = False,
):
    console = initialise_app(ctx)
    print = console.print  # noqa: A001

    print('[bold green]Obelisk Import Utility[/bold green]')

    # Identify the folder containing the manifest
    if folder_or_manifest.is_dir():
        manifest_path = folder_or_manifest / '_manifest.json'
        folder_path = folder_or_manifest
    else:
        manifest_path = folder_or_manifest
        folder_path = folder_or_manifest.parent

    print(f'[bold]Folder:[/bold] {folder_path}')

    # Parse the existing manifest if it exists
    existing_manifest = None
    if manifest_path.exists():
        existing_manifest = parse_manifest(manifest_path)

    # Scan the folder and create a fresh manifest
    new_manifest = create_manifest_from_folder(folder_path)

    # Compare and update the manifest as needed
    if existing_manifest and manifest_match(existing_manifest, new_manifest):
        print('[bold green]:thumbs_up: No updates necessary to the manifest.[/bold green]')
    else:
        print('[bold green]Changes detected in the manifest.[/bold green]')
        if dry_run:
            print('[bold yellow]:no_entry: Dry run mode - no changes will be written.[/bold yellow]')
        else:
            write_manifest(manifest_path, new_manifest)
            print(f'[bold green]Manifest updated at {manifest_path}[/bold green]')


__all__ = ('app',)
