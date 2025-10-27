from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from .mocks.git import (
    add_remote_and_push,
    create_bare_repo,
    ensure_git_available,
    init_repo_with_commit,
)


if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def git_remote_and_local(tmp_path: Path):
    if not ensure_git_available():
        pytest.skip('git not available on PATH')

    remote = tmp_path / 'remote.git'
    local = tmp_path / 'local_repo'

    create_bare_repo(remote)
    init_repo_with_commit(local, files={'README.md': 'hello'}, branch='main')
    add_remote_and_push(local, remote, branch='main')

    return {'local': local, 'remote': remote}
