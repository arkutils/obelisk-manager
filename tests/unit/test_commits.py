from __future__ import annotations

from obelisk.commits import build_commit_message, build_file_change_list
from obelisk.manifest import ManifestEntry


def make_entry(filename: str, version: str | None = None, hash_: str | None = None) -> ManifestEntry:
    return ManifestEntry(filename=filename, version=version, hash=hash_)


def test_build_file_change_list_all_kinds():
    before = [
        make_entry('a.json', version='1.0'),
        make_entry('b.json', version=None, hash_='abc'),
        make_entry('c.json', version='1.0'),
    ]
    after = [
        make_entry('a.json', version='1.1'),  # updated version
        make_entry('b.json', version=None, hash_='def'),  # updated content no version
        # c.json removed
        make_entry('d.json', version='0.1'),  # added
    ]

    text = build_file_change_list(before, after)

    # Section headings and key lines present in deterministic order
    expected_lines = [
        'Added:',
        '* d.json (v0.1)',
        '',
        'Updated:',
        '* a.json (v1.1)',
        '* b.json',
        '',
        'Removed:',
        '* c.json',
    ]

    assert text.splitlines() == expected_lines


def test_build_commit_message_default_headline_and_list():
    # Arrange
    before = [make_entry('a.json', version='1.0')]
    after = [make_entry('a.json', version='1.1'), make_entry('b.json')]

    # Act
    msg = build_commit_message(before, after)

    # Assert
    lines = msg.splitlines()
    assert lines[0] == 'Obelisk import: +1 ~1 -0'
    assert lines[1] == ''
    added_line = lines.index('Added:')
    assert lines[added_line + 1] == '* b.json'
    updated_line = lines.index('Updated:')
    assert lines[updated_line + 1] == '* a.json (v1.1)'


def test_build_commit_message_custom_parts_and_without_list():
    before: list[ManifestEntry] = []
    after = [make_entry('x.json', version='2.0')]

    msg = build_commit_message(
        before,
        after,
        headline='Add new obelisk configs',
        message='Initial import of configs.',
        include_file_list=False,
    )

    assert msg == 'Add new obelisk configs\n\nInitial import of configs.'


def test_build_commit_message_custom_message_with_list():
    before: list[ManifestEntry] = []
    after = [make_entry('x.json', version='2.0')]

    msg = build_commit_message(
        before,
        after,
        headline='Add new obelisk configs',
        message='Initial import of configs.',
        include_file_list=True,
    )

    expected_lines = [
        'Add new obelisk configs',
        '',
        'Initial import of configs.',
        '',
        'Added:',
        '* x.json (v2.0)',
    ]

    assert msg.splitlines() == expected_lines
