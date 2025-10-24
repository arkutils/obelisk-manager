from __future__ import annotations

import json as _json
from pathlib import Path

import pytest

from obelisk.json_utils import save_as_json


def _read(p: Path) -> str:
    return p.read_text(encoding='utf-8')


def test_save_as_json_basic_writes_utf8_lf_and_tabs(tmp_path: Path) -> None:
    # Arrange
    target = tmp_path / 'nested' / 'out.json'
    data = {'x': 1}

    # Act
    save_as_json(target, data)

    # Assert
    assert target.exists(), 'File should be created along with parent directories'
    content = _read(target)

    # Exact pretty JSON with tab indentation and no trailing newline
    assert content == '{\n\t"x": 1\n}'
    # Ensure LF newlines (no CRLF)
    assert '\r\n' not in content
    # Ensure tabs were used for indentation
    assert '\t' in content


@pytest.mark.parametrize(
    ('mod_dict', 'expected_fragment'),
    [
        (
            {'id': 1, 'name': 'Demo', 'ASA': True},
            '"mod": { "id": 1, "name": "Demo", "ASA": true }',
        ),
        (
            {'id': 1, 'name': 'Demo', 'ASA': True, 'author': 'A'},
            '"mod": { "id": 1, "name": "Demo", "ASA": true, "author": "A" }',
        ),
        (
            {
                'id': 1,
                'name': 'Demo',
                'ASA': True,
                'author': 'A',
                'desc': 'd',
            },
            '"mod": { "id": 1, "name": "Demo", "ASA": true, "author": "A", "desc": "d" }',
        ),
    ],
)
def test_save_as_json_shrinks_mod_dicts_to_single_line(
    tmp_path: Path,
    mod_dict: dict[str, object],
    expected_fragment: str,
) -> None:
    # Top-level has exactly three keys, with 'mod' expanding to multi-line before shrinking;
    # this prevents the top-level itself from being shrunk by the regex.
    data = {
        'version': '1.0',
        'format': 'fmt',
        'mod': mod_dict,  # insertion order preserved for deterministic output
    }
    p = tmp_path / 'mod.json'

    save_as_json(p, data)
    content = _read(p)

    # The mod dict should be rendered on a single line exactly as per our regex replacement.
    assert expected_fragment in content
    # And that single line should not contain a newline within the braces
    assert '\n' not in expected_fragment


def test_save_as_json_reproduces_manifest1_formatting(tmp_path: Path) -> None:
    # Arrange: read the golden manifest fixture and re-serialize it
    data_dir = Path(__file__).resolve().parents[1] / 'data'
    src = data_dir / 'manifest1.json'
    original = src.read_text(encoding='utf-8').strip()

    # Sanity: fixture should use tabs and LF newlines
    assert '\t' in original
    assert '\r\n' not in original

    out = tmp_path / 'manifest1.out.json'

    # Act
    loaded = _json.loads(original)
    save_as_json(out, loaded)
    written = _read(out).strip()

    # Assert: exact byte-for-byte textual match
    assert written == original
