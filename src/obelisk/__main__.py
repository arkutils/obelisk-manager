import logging

from typer import Typer

from obelisk.cmd_utils.common_args import VERSION_ARG
from obelisk.commands.add_files import app as add_files_app
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


@app.callback()
def main(show_version: VERSION_ARG = False):  # noqa: FBT002
    pass


app.add_typer(update_manifest_app)
app.add_typer(live_import_app)
app.add_typer(add_files_app)


if __name__ == '__main__':
    app()
