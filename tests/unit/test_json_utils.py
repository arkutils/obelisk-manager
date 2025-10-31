from __future__ import annotations

import json as _json
from pathlib import Path
from typing import Any

import pytest

from obelisk.json_utils import pretty_json, save_as_json


JsonLike = dict[str, Any] | list[Any] | str | int | float | bool | None


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


@pytest.mark.parametrize(
    'obj',
    [
        {'alpha': 1, 'beta': {'gamma': [1, 2, 3]}, 'delta': True},
        [1, {'x': 'y', 'z': [False, None]}],
        {'outer': {'inner': {'deep': 'value'}}, 'list': [1, 2, 3]},
    ],
)
@pytest.mark.parametrize('indent', [2, 4])
@pytest.mark.parametrize('sorting', ['preserve', 'sorted'])
def test_pretty_json_matches_std_library_when_wrapping_lines(
    obj: JsonLike,
    indent: int,
    sorting: str,
) -> None:
    sort_keys = sorting == 'sorted'
    expected = _json.dumps(obj, indent=indent, sort_keys=sort_keys)
    actual = pretty_json(obj, indent=indent, sort_keys=sort_keys, max_line=0)

    assert actual == expected


def test_pretty_json_inlines_small_structures_when_under_limit() -> None:
    obj = {'a': 1, 'b': 2}

    result = pretty_json(obj, indent=4, max_line=80)

    assert result == '{ "a": 1, "b": 2 }'


def test_pretty_json_inlines_nested_elements_but_wraps_parent() -> None:
    obj = {'outer': {'inner': 1}, 'list': [1, 2]}

    expected = '{\n  "list": [ 1, 2 ],\n  "outer": { "inner": 1 }\n}'
    result = pretty_json(obj, indent=2, sort_keys=True, max_line=30)

    assert result == expected


def test_pretty_json_supports_string_indent_tokens() -> None:
    obj = {'a': [1, 2]}

    expected = '{\n\t"a": [\n\t\t1,\n\t\t2\n\t]\n}'
    result = pretty_json(obj, indent='\t', max_line=0)

    assert result == expected


def test_pretty_json_wraps_arrays_at_exact_limit() -> None:
    obj = [1, 2, 3, 4]

    wrapped = pretty_json(obj, indent=2, max_line=13)
    inline = pretty_json(obj, indent=2, max_line=14)

    assert wrapped == '[\n  1,\n  2,\n  3,\n  4\n]'
    assert inline == '[ 1, 2, 3, 4 ]'


def test_pretty_json_wraps_nested_arrays_at_exact_limit() -> None:
    obj = {'items': [1, 2, 3], 'value': 99}

    wrapped = pretty_json(obj, indent=2, sort_keys=True, max_line=12)
    inline = pretty_json(obj, indent=2, sort_keys=True, max_line=13)

    assert wrapped == '{\n  "items": [\n    1,\n    2,\n    3\n  ],\n  "value": 99\n}'
    assert inline == '{\n  "items": [ 1, 2, 3 ],\n  "value": 99\n}'


def test_pretty_json_wraps_dicts_at_exact_limit() -> None:
    obj = {'a': 1, 'b': 2, 'c': 3}

    wrapped = pretty_json(obj, indent=2, sort_keys=True, max_line=25)
    inline = pretty_json(obj, indent=2, sort_keys=True, max_line=26)

    assert wrapped == '{\n  "a": 1,\n  "b": 2,\n  "c": 3\n}'
    assert inline == '{ "a": 1, "b": 2, "c": 3 }'


def test_pretty_json_wraps_nested_dicts_at_exact_limit() -> None:
    obj = {'outer': {'a': 1, 'b': 2}, 'value': 99}

    wrapped = pretty_json(obj, indent=2, sort_keys=True, max_line=19)
    inline = pretty_json(obj, indent=2, sort_keys=True, max_line=20)

    assert wrapped == '{\n  "outer": {\n    "a": 1,\n    "b": 2\n  },\n  "value": 99\n}'
    assert inline == '{\n  "outer": { "a": 1, "b": 2 },\n  "value": 99\n}'


def test_pretty_json_wraps_top_level_when_collapse_disabled() -> None:
    obj = {'a': 1, 'b': 2}

    result = pretty_json(obj, indent=2, max_line=80, expand_top_level=True)

    assert result == '{\n  "a": 1,\n  "b": 2\n}'


def test_pretty_json_keeps_nested_inline_when_top_level_wrapped() -> None:
    obj = {'outer': {'inner': 1}, 'list': [1, 2]}

    result = pretty_json(obj, indent=2, sort_keys=True, max_line=80, expand_top_level=True)

    assert result == '{\n  "list": [ 1, 2 ],\n  "outer": { "inner": 1 }\n}'
