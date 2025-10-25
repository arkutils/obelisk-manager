from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

import obelisk.filetypes.binary as bin_ft


if TYPE_CHECKING:
    from pathlib import Path


def _expected_hash(data: bytes) -> str:
    h = hashlib.md5()  # noqa: S324 - not using for cryptography in any way
    h.update(data)
    return f'md5:{h.hexdigest()}:{len(data)}:'


def test_get_metadata_from_binary_empty_file(tmp_path: Path) -> None:
    p = tmp_path / 'empty.bin'
    p.write_bytes(b'')

    entry = bin_ft.get_metadata_from_binary(p)

    assert entry is not None
    assert entry.filename == 'empty.bin'
    assert entry.hash == _expected_hash(b'')
    # other fields should remain None
    assert entry.version is None
    assert entry.format is None
    assert entry.mod is None


def test_get_metadata_from_binary_small_content(tmp_path: Path) -> None:
    data = b'hello world'
    p = tmp_path / 'hello.bin'
    p.write_bytes(data)

    entry = bin_ft.get_metadata_from_binary(p)

    assert entry is not None
    assert entry.filename == 'hello.bin'
    assert entry.hash == _expected_hash(data)


def test_get_metadata_from_binary_chunked_read(tmp_path: Path) -> None:
    # Create content larger than 8192 to exercise the chunked hashing loop
    chunk = b'A' * 8192
    data = chunk + b'TAIL'  # 8196 bytes total
    p = tmp_path / 'large.bin'
    p.write_bytes(data)

    entry = bin_ft.get_metadata_from_binary(p)

    assert entry is not None
    assert entry.filename == 'large.bin'
    assert entry.hash == _expected_hash(data)
