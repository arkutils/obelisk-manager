from collections.abc import Callable
from pathlib import Path

from obelisk.manifest import ManifestEntry


MetadataReader = Callable[[Path], ManifestEntry | None]
