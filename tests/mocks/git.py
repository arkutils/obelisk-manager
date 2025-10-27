from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from pathlib import Path


def run_git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ('git', *args),
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
    )


def create_bare_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    run_git(path, 'init', '--bare')


def init_repo_with_commit(
    path: Path,
    files: dict[str, str | bytes] | None = None,
    branch: str = 'main',
) -> None:
    path.mkdir(parents=True, exist_ok=True)
    run_git(path, 'init')
    if files:
        for name, content in files.items():
            p = path / name
            p.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, bytes):
                p.write_bytes(content)
            else:
                p.write_text(content, encoding='utf-8')
    run_git(path, 'add', '.')
    run_git(path, 'commit', '-m', 'initial commit')
    run_git(path, 'branch', '-M', branch)


def add_remote_and_push(local: Path, remote: Path, remote_name: str = 'origin', branch: str = 'main') -> None:
    run_git(local, 'remote', 'add', remote_name, str(remote))
    run_git(local, 'push', remote_name, branch, '--set-upstream')


def ensure_git_available() -> bool:
    try:
        subprocess.run(
            ['git', '--version'],  # noqa: S607 - we intentionally want to use git from PATH
            capture_output=True,
            check=True,
        )
        return True
    except Exception:
        return False
