from __future__ import annotations

import subprocess
from importlib import import_module, metadata
from shutil import which


def main() -> None:
    """Verify the installed package exposes the CLI and metadata."""
    import_module('obelisk')
    dist_version = metadata.version('obelisk-manager')

    obelisk_exe = which('obelisk-manager')
    if obelisk_exe is None:
        msg = 'Expected the obelisk-manager console script to be on PATH.'
        raise RuntimeError(msg)

    result = subprocess.run(
        [obelisk_exe, '--help'],
        check=True,
        capture_output=True,
        text=True,
    )

    if 'Usage' not in result.stdout:
        msg = "Expected help output to include 'Usage'."
        raise RuntimeError(msg)

    print(f'obelisk-manager {dist_version}')


if __name__ == '__main__':
    main()
