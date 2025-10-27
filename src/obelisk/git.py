from __future__ import annotations

import shutil
import logging
import subprocess
from typing import TYPE_CHECKING


logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


def is_git_available() -> bool:
    """Return True if the Git CLI is available on PATH."""
    return shutil.which('git') is not None


def _format_cmd(args: Iterable[str]) -> str:
    return 'git ' + ' '.join(args)


def _git_executable() -> str:
    exe = shutil.which('git')
    if not exe:
        raise FileNotFoundError('git executable not found on PATH')
    return exe


def _run_git(repo_path: Path, args: Iterable[str], *, dry_run: bool = False) -> None:
    """Run a git command in the given repository.

    In dry-run, only logs the command; otherwise executes it.
    Raises CalledProcessError on failure when executing.
    """
    cmd_str = _format_cmd(args)
    logger.debug('git: %s', cmd_str)
    if dry_run:
        return

    subprocess.run(
        [_git_executable(), *list(args)],
        cwd=str(repo_path),
        check=True,
    )


def fetch(
    repo_path: Path,
    remote: str = 'origin',
    *,
    prune: bool = True,
    dry_run: bool = False,
) -> None:
    """Fetch from remote (optionally with --prune)."""
    args: list[str] = ['fetch']
    if prune:
        args.append('--prune')
    args.append(remote)
    _run_git(repo_path, args, dry_run=dry_run)


def reset_hard(
    repo_path: Path,
    target: str = 'origin/main',
    *,
    dry_run: bool = False,
) -> None:
    """Hard reset current branch to the target (e.g., origin/main)."""
    _run_git(repo_path, ['reset', '--hard', target], dry_run=dry_run)


def fast_forward(
    repo_path: Path,
    remote: str = 'origin',
    branch: str = 'main',
    *,
    dry_run: bool = False,
) -> None:
    """Attempt a fast-forward merge from the specified remote branch into the current branch."""
    _run_git(repo_path, ['merge', '--ff-only', f'{remote}/{branch}'], dry_run=dry_run)


def is_clean(repo_path: Path, *, dry_run: bool = False) -> bool:
    """Return True if working tree is clean (no changes staged or unstaged)."""
    if dry_run:
        # Assume clean during dry-run; callers can decide behavior
        logger.info('git: status --porcelain [dry-run: assuming clean]')
        return True

    res = subprocess.run(
        [_git_executable(), 'status', '--porcelain'],
        cwd=str(repo_path),
        check=True,
        capture_output=True,
        text=True,
    )
    return res.stdout.strip() == ''


def commit_all(repo_path: Path, message: str, *, dry_run: bool = False) -> None:
    """Stage all changes and create a commit with the given message."""
    _run_git(repo_path, ['add', '--all'], dry_run=dry_run)
    _run_git(repo_path, ['commit', '-m', message], dry_run=dry_run)


def push(
    repo_path: Path,
    remote: str = 'origin',
    branch: str = 'main',
    *,
    set_upstream: bool = False,
    dry_run: bool = False,
) -> None:
    """Push current branch to remote. Optionally set upstream."""
    args: list[str] = ['push', remote, branch]
    if set_upstream:
        args.append('--set-upstream')
    _run_git(repo_path, args, dry_run=dry_run)


__all__ = (
    'commit_all',
    'fast_forward',
    'fetch',
    'is_clean',
    'is_git_available',
    'push',
    'reset_hard',
)
