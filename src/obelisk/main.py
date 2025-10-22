import logging

from typer import Typer

from obelisk.commands.hello import app as hello_app
from obelisk.commands.live_import import app as live_import_app
from obelisk.commands.update_manifest import app as update_manifest_app


logger = logging.getLogger('obelisk')


app = Typer(
    name='@arkutils/obelisk-import',
    help='A tool for managing data files and their manifests in Obelisk format.',
    no_args_is_help=True,
    add_completion=True,
    rich_markup_mode='rich',
)


app.add_typer(update_manifest_app)
app.add_typer(live_import_app)
app.add_typer(hello_app)


# @app.command(
#     name='add-files',
#     no_args_is_help=True,
#     help="""Add files to a directory and update or create an Obelisk manifest.""",
# )
# def add_files():
#     pass


# @app.command(
#     name='update-manifest',
#     no_args_is_help=True,
#     help="""Update or create an Obelisk manifest in an existing directory.""",
# )
# def update_manifest():
#     pass


# @app.command(
#     name='live-import',
#     no_args_is_help=True,
#     short_help='Import files into a live Obelisk Git repository.',
#     help="""Import files into an Obelisk repository, updating the manifest and performing Git actions as needed.

#     This command is for managing files in a live Obelisk repository and will perform the following:
#     1. Perform `[bold]git fetch[/bold]` on the repository to ensure it is up to date
#     2. Perform `[bold]git rebase --hard origin/main[/bold]` to synchronize with the remote main branch
#     3. Copy the specified input files or directories into the specified destination path within the repository
#     4. Update or create an Obelisk manifest for that directory
#     5. Commit the changes with the specified identity and message
#     6. Push the changes to the remote repository
#     """,
# )
# def live_import(
#     ctx: Context,
#     repo: Annotated[
#         Path,
#         Option(
#             '-r',
#             '--repo',
#             help='Path to a local clone of the Obelisk repository',
#             exists=True,
#             file_okay=False,
#             dir_okay=True,
#         ),
#     ],
#     inputs: list[Path] = Argument(
#         ...,
#         help='Input files or directories to import.',
#         exists=True,
#         file_okay=True,
#         dir_okay=True,
#     ),
#     dest: str = Argument(
#         ...,
#         help='Destination path, relative to the repo root.',
#         metavar='DEST_PATH',
#     ),
#     identity: str | None = Option(
#         None,
#         '-i',
#         '--identity',
#         metavar='EMAIL',
#         help='User email to use for Git.',
#     ),
#     message: str | None = Option(
#         None,
#         '-m',
#         '--message',
#         help='Commit message to use for Git.',
#     ),
#     dry_run: Annotated[
#         bool,
#         Option(
#             '--dry-run',
#             help='Simulate the import without making any changes.',
#         ),
#     ] = False,
#     skip_push: Annotated[
#         bool,
#         Option(
#             '--skip-push',
#             help='Skip pushing changes to the remote repository.',
#         ),
#     ] = False,
#     verbose: Annotated[
#         bool,
#         Option(
#             '--verbose',
#             help='Enable verbose output.',
#         ),
#     ] = False,
#     quiet: Annotated[
#         bool,
#         Option(
#             '--quiet',
#             help='Suppress non-error output.',
#         ),
#     ] = False,
#     show_version: Annotated[
#         bool | None,
#         Option(
#             '--version',
#             help='Show the version and exit',
#             is_eager=True,
#             callback=_handle_version_option,
#         ),
#     ] = False,
# ):
#     console = Console()  # CustomRichConsole()
#     print = console.print

#     if verbose and quiet:
#         print('[red]Error:[/red] Cannot use both --verbose and --quiet options together.')
#         ctx.abort()

#     # Setup logging
#     log_level = logging.INFO if verbose else logging.ERROR if quiet else logging.WARNING
#     logging.basicConfig(
#         level=log_level,
#         format='%(message)s',
#         handlers=[
#             RichHandler(
#                 log_level,
#                 console,
#                 show_time=False,
#             ),
#         ],
#     )

#     # Use Rich to print a title and supplied arguments
#     print('[bold green]Obelisk Import Utility[/bold green]')
#     print(f'[bold]Repository:[/bold] {repo}')
#     print(f'[bold]Destination:[/bold] <repo>/{dest}')
#     print('[bold]Inputs:[/bold]')
#     for input_path in inputs:
#         print(f'    {input_path!s}')
#     if identity:
#         print(f'[bold]Identity:[/bold] {identity}')
#     if message:
#         print(f'[bold]Message:[/bold] {message}')
#     if dry_run:
#         print('[bold yellow]Dry Run Enabled[/bold yellow]')
#     if skip_push:
#         print('[bold yellow]Skip Push Enabled[/bold yellow]')

#     for src in track(
#         inputs,
#         transient=True,
#         description='Importing files...',
#         update_period=0.5,
#         console=console,
#     ):
#         # dest_path = repo / dest / src.name
#         logger.info(f'Import {src} to {(repo / dest / src.name).relative_to(repo)}')
#         logger.warning(f'Import {src} to {(repo / dest / src.name).relative_to(repo)}')

#     logger.error('This is an error message example.')


if __name__ == '__main__':
    app()
