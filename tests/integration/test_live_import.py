from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from typer.testing import CliRunner

from obelisk.main import app
from obelisk.manifest import parse_manifest
from tests.mocks.git import run_git


if TYPE_CHECKING:
    from pathlib import Path


class GitRepos(TypedDict):
    local: Path
    remote: Path


runner = CliRunner()


def _git_hash_head(repo: Path) -> str:
    return run_git(repo, 'rev-parse', 'HEAD').stdout.strip()


def _git_hash_remote_main(bare_remote: Path) -> str:
    # For a bare repo, resolve the branch ref directly
    return run_git(bare_remote, 'rev-parse', 'refs/heads/main').stdout.strip()


def _git_last_message(repo: Path) -> str:
    return run_git(repo, 'log', '-1', '--pretty=%B').stdout.strip()


def _write_inputs(src_dir: Path) -> tuple[Path, Path]:
    src_dir.mkdir(parents=True, exist_ok=True)
    j = src_dir / 'info.json'
    p = src_dir / 'pic.png'
    j.write_text('{"version":"1","format":"fmt"}', encoding='utf-8')
    p.write_bytes(b'\x89PNG\r\n\x1a\n' + b'bytes')
    return j, p


def test_live_import_happy_path_commits_and_pushes(tmp_path: Path, git_remote_and_local: GitRepos) -> None:
    # Arrange: setup local/remote, destination folder inside local repo, and input files
    local = git_remote_and_local['local']
    remote = git_remote_and_local['remote']

    dest = local / 'data' / 'a'
    dest.mkdir(parents=True, exist_ok=True)

    inputs_dir = tmp_path / 'inputs'
    json_input, png_input = _write_inputs(inputs_dir)

    # Capture remote main before import
    remote_hash_before = _git_hash_remote_main(remote)

    # Act
    res = runner.invoke(
        app,
        [
            'live-import',
            '--repo',
            str(local),
            str(json_input),
            str(png_input),
            'data/a',
        ],
    )

    # Assert CLI success
    assert res.exit_code == 0, res.output
    assert 'Committing changes...' in res.output
    assert 'Pushing to remote...' in res.output

    # Files are copied and manifest written
    manifest_path = dest / '_manifest.json'
    assert (dest / 'info.json').exists()
    assert (dest / 'pic.png').exists()
    assert manifest_path.exists()

    # Manifest has expected entries
    entries = parse_manifest(manifest_path)
    by_name = {e.filename: e for e in entries}
    assert set(by_name) == {'info.json', 'pic.png'}
    assert by_name['info.json'].version == '1'
    assert by_name['info.json'].format == 'fmt'
    assert by_name['pic.png'].hash is not None
    assert by_name['pic.png'].hash.startswith('md5:')

    # Commit created with expected title and includes change list
    msg = _git_last_message(local)
    assert msg.splitlines()[0] == 'Imported 2 changes to data/a'
    assert 'Added:' in msg
    assert 'info.json' in msg
    assert 'pic.png' in msg
    assert 'Removed:' not in msg
    assert 'Updated:' not in msg

    # Remote updated to the same commit as local
    local_head = _git_hash_head(local)
    remote_hash_after = _git_hash_remote_main(remote)
    assert remote_hash_before != remote_hash_after
    assert remote_hash_after == local_head


def test_live_import_skip_pull_implies_skip_push(tmp_path: Path, git_remote_and_local: GitRepos) -> None:
    # Arrange
    local = git_remote_and_local['local']
    remote = git_remote_and_local['remote']
    dest = local / 'data' / 'b'
    dest.mkdir(parents=True, exist_ok=True)
    json_input, png_input = _write_inputs(tmp_path / 'inputs2')

    remote_hash_before = _git_hash_remote_main(remote)

    # Act: --skip-pull only; should also skip push
    res = runner.invoke(
        app,
        [
            'live-import',
            '--repo',
            str(local),
            '--skip-pull',
            str(json_input),
            str(png_input),
            'data/b',
        ],
    )

    # Assert
    assert res.exit_code == 0, res.output
    assert 'Skipping repository synchronization' in res.output
    assert 'Skipping push as requested.' in res.output

    # Local commit exists but remote remains unchanged
    assert _git_last_message(local).startswith('Imported 2 changes to data/b')
    assert _git_hash_remote_main(remote) == remote_hash_before


def test_live_import_blocks_unhandled_without_allow_all(tmp_path: Path, git_remote_and_local: GitRepos) -> None:
    # Arrange
    local = git_remote_and_local['local']
    dest = local / 'import'
    dest.mkdir(parents=True, exist_ok=True)
    bad = tmp_path / 'notes.txt'
    bad.write_text('n/a', encoding='utf-8')

    # Act
    res = runner.invoke(
        app,
        [
            'live-import',
            '--repo',
            str(local),
            str(bad),
            'import',
        ],
    )

    # Assert
    assert res.exit_code != 0
    assert 'Some unhandled files are excluded.' in res.output
    # Avoid brittle full-path match because Rich may wrap long paths
    assert 'notes.txt' in res.output


def test_live_import_custom_message_and_no_file_list(tmp_path: Path, git_remote_and_local: GitRepos) -> None:
    # Arrange
    local = git_remote_and_local['local']
    dest = local / 'data' / 'c'
    dest.mkdir(parents=True, exist_ok=True)
    json_input, _ = _write_inputs(tmp_path / 'inputs3')

    # Act
    res = runner.invoke(
        app,
        [
            'live-import',
            '--repo',
            str(local),
            '--title',
            'Imported $total to $path',
            '--body',
            'Processed $added added files',
            '--exclude-file-list',
            str(json_input),
            'data/c',
        ],
    )

    # Assert
    assert res.exit_code == 0, res.output
    msg = _git_last_message(local)
    lines = msg.splitlines()
    assert lines[0] == 'Imported 1 to data/c'
    assert 'Processed 1 added files' in msg
    assert 'Added:' not in msg  # file list excluded
    assert json_input.name not in msg


def test_live_import_second_run_no_changes_skips_commit(tmp_path: Path, git_remote_and_local: GitRepos) -> None:
    # Arrange
    local = git_remote_and_local['local']
    remote = git_remote_and_local['remote']
    dest = local / 'data' / 'stable'
    dest.mkdir(parents=True, exist_ok=True)
    json_input, png_input = _write_inputs(tmp_path / 'inputs4')

    # First run commits and pushes
    res1 = runner.invoke(
        app,
        ['live-import', '--repo', str(local), str(json_input), str(png_input), 'data/stable'],
    )
    assert res1.exit_code == 0, res1.output
    first_remote_hash = _git_hash_remote_main(remote)

    # Second run with same inputs should be a no-op (no commit and no push)
    res2 = runner.invoke(
        app,
        ['live-import', '--repo', str(local), str(json_input), str(png_input), 'data/stable'],
    )
    assert res2.exit_code == 0, res2.output
    assert 'No manifest changes needed. Skipping commit/push.' in res2.output
    assert _git_hash_remote_main(remote) == first_remote_hash


def test_live_import_rejects_parent_traversal_in_dest(tmp_path: Path, git_remote_and_local: GitRepos) -> None:
    # Arrange
    local = git_remote_and_local['local']
    # Valid folder we intend to import to (exists), but pass '../x' in dest
    (local / 'data' / 'ok').mkdir(parents=True, exist_ok=True)
    json_input, _ = _write_inputs(tmp_path / 'inputs5')

    # Act
    res = runner.invoke(
        app,
        ['live-import', '--repo', str(local), str(json_input), 'data/../outside'],
    )

    # Assert
    assert res.exit_code != 0
    assert 'Destination path must not contain parent traversal' in res.output


def test_live_import_dry_run_new_import_no_changes(tmp_path: Path, git_remote_and_local: GitRepos) -> None:
    # Arrange
    local = git_remote_and_local['local']
    remote = git_remote_and_local['remote']
    dest = local / 'data' / 'dry1'
    dest.mkdir(parents=True, exist_ok=True)
    json_input, png_input = _write_inputs(tmp_path / 'dry_inputs1')

    local_head_before = _git_hash_head(local)
    remote_hash_before = _git_hash_remote_main(remote)

    # Act: dry-run import
    res = runner.invoke(
        app,
        [
            'live-import',
            '--repo',
            str(local),
            '--dry-run',
            str(json_input),
            str(png_input),
            'data/dry1',
        ],
    )

    # Assert: no filesystem changes
    assert res.exit_code == 0, res.output
    assert 'Dry Run Enabled' in res.output
    assert (dest / 'info.json').exists() is False
    assert (dest / 'pic.png').exists() is False
    assert (dest / '_manifest.json').exists() is False

    # Assert: no git changes
    assert _git_hash_head(local) == local_head_before
    assert _git_hash_remote_main(remote) == remote_hash_before


def test_live_import_dry_run_on_existing_content_is_noop(
    tmp_path: Path,
    git_remote_and_local: GitRepos,
) -> None:
    # Arrange: perform a real import first
    local = git_remote_and_local['local']
    remote = git_remote_and_local['remote']
    dest = local / 'data' / 'dry2'
    dest.mkdir(parents=True, exist_ok=True)

    inputs_a = _write_inputs(tmp_path / 'dry_inputs2_a')
    res1 = runner.invoke(
        app,
        ['live-import', '--repo', str(local), str(inputs_a[0]), str(inputs_a[1]), 'data/dry2'],
    )
    assert res1.exit_code == 0, res1.output

    # Capture current on-disk state and git state
    info_path = dest / 'info.json'
    manifest_path = dest / '_manifest.json'
    info_before = info_path.read_text(encoding='utf-8')
    manifest_before = manifest_path.read_text(encoding='utf-8')
    local_head_before = _git_hash_head(local)
    remote_hash_before = _git_hash_remote_main(remote)

    # Prepare different inputs that would change things if not dry-run
    j_new = tmp_path / 'dry_inputs2_b' / 'info.json'
    j_new.parent.mkdir(parents=True, exist_ok=True)
    j_new.write_text('{"version":"2","format":"fmt"}', encoding='utf-8')

    # Act: dry-run live-import with new input only
    res2 = runner.invoke(
        app,
        ['live-import', '--repo', str(local), '--dry-run', str(j_new), 'data/dry2'],
    )

    # Assert: nothing changed on disk and in git
    assert res2.exit_code == 0, res2.output
    assert info_path.read_text(encoding='utf-8') == info_before
    assert manifest_path.read_text(encoding='utf-8') == manifest_before
    assert _git_hash_head(local) == local_head_before
    assert _git_hash_remote_main(remote) == remote_hash_before


def test_live_import_dry_run_with_skip_pull_prints_and_no_changes(
    tmp_path: Path,
    git_remote_and_local: GitRepos,
) -> None:
    # Arrange
    local = git_remote_and_local['local']
    remote = git_remote_and_local['remote']
    dest = local / 'data' / 'dry3'
    dest.mkdir(parents=True, exist_ok=True)
    json_input, _ = _write_inputs(tmp_path / 'dry_inputs3')
    local_head_before = _git_hash_head(local)
    remote_hash_before = _git_hash_remote_main(remote)

    # Act
    res = runner.invoke(
        app,
        ['live-import', '--repo', str(local), '--dry-run', '--skip-pull', str(json_input), 'data/dry3'],
    )

    # Assert: skip-pull messaging and no changes anywhere
    assert res.exit_code == 0, res.output
    assert 'Skipping repository synchronization' in res.output
    assert (dest / 'info.json').exists() is False
    assert (dest / '_manifest.json').exists() is False
    assert _git_hash_head(local) == local_head_before
    assert _git_hash_remote_main(remote) == remote_hash_before


def test_live_import_blocks_on_dirty_repo_without_skip_pull(
    tmp_path: Path,
    git_remote_and_local: GitRepos,
) -> None:
    # Arrange: create a dirty working tree by modifying README.md
    local = git_remote_and_local['local']
    remote = git_remote_and_local['remote']
    dest = local / 'data' / 'dirty1'
    dest.mkdir(parents=True, exist_ok=True)
    json_input, png_input = _write_inputs(tmp_path / 'dirty_inputs1')

    # Make repo dirty
    (local / 'README.md').write_text('hello (dirty)', encoding='utf-8')

    # Capture remote before and act
    remote_hash_before = _git_hash_remote_main(remote)
    res = runner.invoke(
        app,
        [
            'live-import',
            '--repo',
            str(local),
            str(json_input),
            str(png_input),
            'data/dirty1',
        ],
    )

    # Assert: command blocked due to dirty repo
    assert res.exit_code != 0
    assert 'Repository has uncommitted changes.' in res.output
    assert 'pass --skip-pull to proceed without sync' in res.output
    # Ensure no commit happened and remote unchanged
    assert _git_hash_remote_main(remote) == remote_hash_before


def test_live_import_dirty_repo_with_skip_pull_commits_and_skips_push(
    tmp_path: Path,
    git_remote_and_local: GitRepos,
) -> None:
    # Arrange
    local = git_remote_and_local['local']
    remote = git_remote_and_local['remote']
    dest = local / 'data' / 'dirty2'
    dest.mkdir(parents=True, exist_ok=True)
    json_input, png_input = _write_inputs(tmp_path / 'dirty_inputs2')

    # Dirty the repo
    (local / 'README.md').write_text('hello (dirty2)', encoding='utf-8')
    remote_hash_before = _git_hash_remote_main(remote)

    # Act: --skip-pull lets us proceed despite dirtiness and implies skip push
    res = runner.invoke(
        app,
        [
            'live-import',
            '--repo',
            str(local),
            '--skip-pull',
            str(json_input),
            str(png_input),
            'data/dirty2',
        ],
    )

    # Assert: success, files and manifest written, commit created, push skipped
    assert res.exit_code == 0, res.output
    assert (dest / 'info.json').exists()
    assert (dest / 'pic.png').exists()
    assert (dest / '_manifest.json').exists()
    msg = _git_last_message(local)
    assert msg.splitlines()[0] == 'Imported 2 changes to data/dirty2'
    assert 'Skipping push as requested.' in res.output
    assert _git_hash_remote_main(remote) == remote_hash_before


def test_live_import_git_reset_does_not_override_dirty_block(
    tmp_path: Path,
    git_remote_and_local: GitRepos,
) -> None:
    # Arrange
    local = git_remote_and_local['local']
    dest = local / 'data' / 'dirty3'
    dest.mkdir(parents=True, exist_ok=True)
    json_input, _ = _write_inputs(tmp_path / 'dirty_inputs3')

    # Dirty the repo
    (local / 'README.md').write_text('hello (dirty3)', encoding='utf-8')

    # Act: even with --git-reset, dirty repos must fail unless --skip-pull
    res = runner.invoke(
        app,
        ['live-import', '--repo', str(local), '--git-reset', str(json_input), 'data/dirty3'],
    )

    # Assert
    assert res.exit_code != 0
    assert 'Repository has uncommitted changes.' in res.output


def test_live_import_dry_run_allows_dirty_repo(
    tmp_path: Path,
    git_remote_and_local: GitRepos,
) -> None:
    # Arrange
    local = git_remote_and_local['local']
    remote = git_remote_and_local['remote']
    dest = local / 'data' / 'dirty4'
    dest.mkdir(parents=True, exist_ok=True)
    json_input, png_input = _write_inputs(tmp_path / 'dirty_inputs4')

    # Dirty the repo
    (local / 'README.md').write_text('hello (dirty4)', encoding='utf-8')
    local_head_before = _git_hash_head(local)
    remote_hash_before = _git_hash_remote_main(remote)

    # Act: dry-run should not block on dirty status and should not change anything
    res = runner.invoke(
        app,
        [
            'live-import',
            '--repo',
            str(local),
            '--dry-run',
            str(json_input),
            str(png_input),
            'data/dirty4',
        ],
    )

    # Assert
    assert res.exit_code == 0, res.output
    assert 'Dry Run Enabled' in res.output
    assert (dest / 'info.json').exists() is False
    assert (dest / 'pic.png').exists() is False
    assert (dest / '_manifest.json').exists() is False
    assert _git_hash_head(local) == local_head_before
    assert _git_hash_remote_main(remote) == remote_hash_before
