import hashlib
from pathlib import Path

from obelisk.manifest import ManifestEntry


def get_metadata_from_binary(file_path: Path) -> ManifestEntry | None:
    """Extract metadata from a binary file (e.g., image) for manifest entry."""
    # Use MD5 as a fast/simple content change hash, accepting its weakness for cryptographic uses
    hasher = hashlib.md5()  # noqa: S324 - not using for cryptography in any way
    with file_path.open('rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)

    # Also add the file's length to the hash string for extra uniqueness
    file_size = file_path.stat().st_size

    # Construct the manifest entry
    hash_str = f'md5:{hasher.hexdigest()}:{file_size}'
    return ManifestEntry(
        filename=file_path.name,
        hash=hash_str,
    )
