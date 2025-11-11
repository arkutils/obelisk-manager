from __future__ import annotations

import subprocess as _sub
from typing import TYPE_CHECKING, Any

import pytest

from obelisk import git


if TYPE_CHECKING:
    from pathlib import Path


class _RunCalls:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def __call__(
        self,
        args: list[str],
        cwd: str,
        *,
        check: bool,
        capture_output: bool | None = None,
        text: bool | None = None,
    ):  # type: ignore[override]
        self.calls.append(
            {'args': args, 'cwd': cwd, 'check': check, 'capture_output': capture_output, 'text': text},
        )

        # Simulate a CompletedProcess-like with stdout for status calls
        class _Res:
            def __init__(self) -> None:
                self.stdout = ''

        return _Res()


def test_is_git_available_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(git.shutil, 'which', lambda _name: 'C:/Program Files/Git/bin/git.exe')  # type: ignore
    assert git.is_git_available() is True


def test_is_git_available_false(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(git.shutil, 'which', lambda _name: None)  # type: ignore
    assert git.is_git_available() is False


def test_fetch_includes_prune_by_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    runner = _RunCalls()
    monkeypatch.setattr(git.shutil, 'which', lambda _name: 'git')  ## type: ignore
    monkeypatch.setattr(git.subprocess, 'run', runner)

    # Act
    git.fetch(tmp_path, remote='origin')

    # Assert
    assert len(runner.calls) == 1
    call = runner.calls[0]
    assert call['args'] == ['git', 'fetch', '--prune', 'origin']
    assert call['cwd'] == str(tmp_path)
    assert call['check'] is True


def test_fetch_without_prune(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = _RunCalls()
    monkeypatch.setattr(git.shutil, 'which', lambda _name: 'git')  ## type: ignore
    monkeypatch.setattr(git.subprocess, 'run', runner)

    git.fetch(tmp_path, remote='upstream', prune=False)

    assert runner.calls[0]['args'] == ['git', 'fetch', 'upstream']


def test_reset_hard_calls_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = _RunCalls()
    monkeypatch.setattr(git.shutil, 'which', lambda _name: 'git')  ## type: ignore
    monkeypatch.setattr(git.subprocess, 'run', runner)

    git.reset_hard(tmp_path, target_branch='origin/dev')

    assert runner.calls[0]['args'] == ['git', 'reset', '--hard', 'origin/dev']


def test_fast_forward_calls_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = _RunCalls()
    monkeypatch.setattr(git.shutil, 'which', lambda _name: 'git')  ## type: ignore
    monkeypatch.setattr(git.subprocess, 'run', runner)

    git.fast_forward(tmp_path, remote='origin', branch='feature')

    assert runner.calls[0]['args'] == ['git', 'merge', '--ff-only', 'origin/feature']


def test_is_clean_dry_run_true(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # If dry_run is True, should not call subprocess and should return True
    called = {'flag': False}

    def _fail_run(*_args, **_kwargs):  # pyright: ignore[reportMissingParameterType, reportUnknownParameterType]
        called['flag'] = True
        raise AssertionError('subprocess.run should not be called in dry-run')

    monkeypatch.setattr(git.subprocess, 'run', _fail_run)  # pyright: ignore[reportUnknownArgumentType]

    assert git.is_clean(tmp_path, dry_run=True) is True
    assert called['flag'] is False


def test_is_clean_from_porcelain_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class _Res:
        def __init__(self, stdout: str) -> None:
            self.stdout = stdout

    run_was_called = False

    def _fake_run(args: list[str], cwd: str, check: bool, capture_output: bool, text: bool):  # noqa: ARG001, FBT001
        nonlocal run_was_called
        run_was_called = True
        assert capture_output is True
        assert text is True
        return _Res('')

    monkeypatch.setattr(git.shutil, 'which', lambda _name: 'git')  # type: ignore
    monkeypatch.setattr(git.subprocess, 'run', _fake_run)

    assert git.is_clean(tmp_path) is True
    assert run_was_called is True

    run_was_called = False

    def _fake_run_dirty(args: list[str], cwd: str, check: bool, capture_output: bool, text: bool):  # noqa: ARG001, FBT001
        nonlocal run_was_called
        run_was_called = True
        return _Res(' M file.txt\n')

    monkeypatch.setattr(git.subprocess, 'run', _fake_run_dirty)  # pyright: ignore[reportUnknownArgumentType]
    assert git.is_clean(tmp_path) is False
    assert run_was_called is True


def test_commit_all_adds_and_commits(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = _RunCalls()
    monkeypatch.setattr(git.shutil, 'which', lambda _name: 'git')  # type: ignore
    monkeypatch.setattr(git.subprocess, 'run', runner)

    git.commit_all(tmp_path, message='test commit')

    assert [c['args'] for c in runner.calls] == [
        ['git', 'add', '--all'],
        ['git', 'commit', '-m', 'test commit'],
    ]


def test_push_with_and_without_upstream(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = _RunCalls()
    monkeypatch.setattr(git.shutil, 'which', lambda _name: 'git')  ## type: ignore
    monkeypatch.setattr(git.subprocess, 'run', runner)

    git.push(tmp_path, remote='origin', branch='main')
    git.push(tmp_path, remote='origin', branch='main', set_upstream=True)

    assert runner.calls[0]['args'] == ['git', 'push', 'origin', 'main']
    assert runner.calls[1]['args'] == ['git', 'push', 'origin', 'main', '--set-upstream']


def test_dry_run_does_not_call_subprocess(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Ensure all public functions honour dry_run flag
    runner = _RunCalls()
    monkeypatch.setattr(git.shutil, 'which', lambda _name: 'git')  ## type: ignore
    monkeypatch.setattr(git.subprocess, 'run', runner)

    git.fetch(tmp_path, remote='origin', dry_run=True)
    git.reset_hard(tmp_path, target_branch='origin/main', dry_run=True)
    git.fast_forward(tmp_path, dry_run=True)
    git.commit_all(tmp_path, message='m', dry_run=True)
    git.push(tmp_path, dry_run=True)

    assert runner.calls == []


def test_fetch_raises_when_git_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # No git on PATH -> FileNotFoundError
    monkeypatch.setattr(git.shutil, 'which', lambda _name: None)  # type: ignore

    with pytest.raises(FileNotFoundError):
        git.fetch(tmp_path, remote='origin')


def test_subprocess_errors_propagate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*_args: object, **_kwargs: object):  # pyright: ignore[reportUnknownParameterType]
        raise _sub.CalledProcessError(returncode=1, cmd=['git', 'x'])

    # Ensure git path resolves, but run fails
    monkeypatch.setattr(git.shutil, 'which', lambda _name: 'git')  # type: ignore
    monkeypatch.setattr(git.subprocess, 'run', _raise)  # pyright: ignore[reportUnknownArgumentType]

    # Each should propagate CalledProcessError
    with pytest.raises(_sub.CalledProcessError):
        git.fetch(tmp_path)

    with pytest.raises(_sub.CalledProcessError):
        git.reset_hard(tmp_path)

    with pytest.raises(_sub.CalledProcessError):
        git.fast_forward(tmp_path)

    with pytest.raises(_sub.CalledProcessError):
        git.is_clean(tmp_path)

    with pytest.raises(_sub.CalledProcessError):
        git.commit_all(tmp_path, message='m')

    with pytest.raises(_sub.CalledProcessError):
        git.push(tmp_path)
