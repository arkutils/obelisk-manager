from __future__ import annotations

import logging
from typing import Annotated

from typer import Argument, Context, Typer

from obelisk.common_args import DRY_RUN_ARG, QUIET_ARG, VERBOSE_ARG, VERSION_ARG, initialise_app


logger = logging.getLogger('obelisk')

app = Typer()


@app.command(
    name='hello',
    short_help='Say hello to the user.',
)
def hello(
    ctx: Context,
    name: Annotated[str | None, Argument(help='Name of the user to greet.')] = None,
    show_version: VERSION_ARG = False,
    dry_run: DRY_RUN_ARG = False,
    verbose: VERBOSE_ARG = False,
    quiet: QUIET_ARG = False,
):
    console = initialise_app(ctx)
    print = console.print  # noqa: A001

    greeting_name = name or 'World'
    logger.info('Preparing to greet %s.', greeting_name)
    logger.debug('Dry run mode is %s.', 'enabled' if dry_run else 'disabled')
    print(f'Hello, [bold blue]{greeting_name}[/bold blue]!')
    logger.warning('This is a warning message.')
    logger.error('This is an error message example.')


__all__ = ('app',)
