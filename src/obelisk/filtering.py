from collections.abc import Iterable
from pathlib import Path

from obelisk.filetypes import allowed_types


# Common junk plus the project's domain-specific '!'-prefixed convention
DEFAULT_IGNORE_PATTERNS: tuple[str, ...] = (
    '.*',
    '**/.*',
    '!*',
    '**/!*',
    'Thumbs.db',
    '__pycache__',
    '**/__pycache__',
)


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


def resolve_ignored_paths(root: Path, patterns: Iterable[str]) -> set[Path]:
    """Expand glob patterns (relative to root, supporting '**') into a set of matched paths."""
    ignored: set[Path] = set()
    for pattern in patterns:
        ignored.update(root.glob(pattern))
    return ignored


def is_under_ignored(path: Path, ignored: set[Path]) -> bool:
    """Check if path itself, or any of its ancestors, is in the ignored set."""
    return path in ignored or any(parent in ignored for parent in path.parents)
