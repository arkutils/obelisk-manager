from pathlib import Path

from obelisk.filetypes import allowed_types


def file_is_allowed(file: Path) -> bool:
    """
    Check if a file should be allowed in a manifest.
    Directories are disallowed.
    Files beginning with '.' and '_' are disallowed.
    Files with extensions not in allowed_types are disallowed.
    """
    if file.is_dir():
        return False

    if file.name.startswith(('.', '_')):
        return False

    if file.suffix.lstrip('.') not in allowed_types:  # noqa: SIM103 - better readability
        return False

    return True
