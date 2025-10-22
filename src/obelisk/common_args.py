from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated

from rich.logging import RichHandler
from typer import Exit, Option

from obelisk import __version__
from obelisk.rich_console import CustomRichConsole


if TYPE_CHECKING:
    from rich.console import Console
    from typer import Context


DEFAULT_LOG_LEVEL = logging.INFO


def initialise_app(ctx: Context) -> Console:
    console = CustomRichConsole()
    print = console.print  # noqa: A001

    dry_run = bool(ctx.params.get('dry_run'))
    verbose: int = ctx.params.get('verbose') or 0
    quiet: int = ctx.params.get('quiet') or 0

    log_level = max(10, min(40, DEFAULT_LOG_LEVEL - (10 * verbose) + (10 * quiet)))

    print('[bold green]Obelisk Import Utility[/bold green]')
    print()
    if verbose or quiet:
        print(f'[bold]Log Level:[/bold] {log_level} ({logging.getLevelName(log_level)})')
    if dry_run:
        print('[bold yellow]Dry Run Mode Enabled[/bold yellow]')

    # Setup logging
    logging.basicConfig(
        level=log_level,
        format='%(message)s',
        handlers=[
            RichHandler(
                log_level,
                console,
                show_time=False,
            ),
        ],
    )

    return console


def _handle_version_option(value: str) -> None:
    if not value:
        return
    print(__version__)
    raise Exit(0)


VERBOSE_ARG = Annotated[
    int,
    Option(
        '-v',
        '--verbose',
        help='Increase output verbosity. May be specified multiple times..',
        count=True,
    ),
]

QUIET_ARG = Annotated[
    int,
    Option(
        '-q',
        '--quiet',
        help='Reduce output verbosity. May be specified multiple times.',
        count=True,
    ),
]

VERSION_ARG = Annotated[
    bool,
    Option(
        '--version',
        help='Show the version and exit',
        is_eager=True,
        callback=_handle_version_option,
    ),
]

DRY_RUN_ARG = Annotated[
    bool,
    Option(
        '--dry-run',
        help='Simulate the operation without making any changes.',
    ),
]

__all__ = (
    'DEFAULT_LOG_LEVEL',
    'DRY_RUN_ARG',
    'QUIET_ARG',
    'VERBOSE_ARG',
    'VERSION_ARG',
    'initialise_app',
)
