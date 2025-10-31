import json
from pathlib import Path
from typing import Any


def save_as_json(path: Path, data: Any) -> None:
    """
    Save the given data as JSON to the specified path.
    This uses a customised formatting to shrink mod dicts to single lines where possible.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('wt', encoding='utf-8', newline='\n') as f:
        content = pretty_json(data, indent='\t', max_line=120, sort_keys=False, expand_top_level=True)
        f.write(content)


JsonType = dict[str, Any] | list[Any] | str | int | float | bool | None


def pretty_json(  # noqa: PLR0913 - acceptable
    obj: JsonType,
    *,
    indent: int | str = 4,
    max_line: int = 100,
    sort_keys: bool = False,
    expand_top_level: bool = False,
    level: int = 0,
) -> str:
    """
    Hybrid JSON pretty-printer:
    - Normal indentation for readability
    - Collapse short dicts/lists onto one line if under max_inline chars
    - Supports sort_keys and indent as int or str
    - Optional top-level control via expand_top_level
    """
    # Normalize indent
    if isinstance(indent, int):
        indent_str = ' ' * indent
    elif isinstance(indent, str):  # type: ignore - runtime safety should not be ignored
        indent_str = indent
    else:
        raise TypeError('indent must be int or str')

    sp = indent_str * level

    if isinstance(obj, dict):
        items: list[str] = []
        keys = sorted(obj.keys()) if sort_keys else list(obj.keys())
        for key in keys:
            value = obj[key]
            content = pretty_json(value, indent=indent, max_line=max_line, sort_keys=sort_keys, level=level + 1)
            items.append(f'{json.dumps(key)}: {content}')
        one_line = '{ ' + ', '.join(items) + ' }'
        if not expand_top_level and len(one_line) + len(sp) <= max_line:
            return one_line
        return '{\n' + ',\n'.join(sp + indent_str + item for item in items) + '\n' + sp + '}'

    if isinstance(obj, list):
        items = [
            pretty_json(value, indent=indent, max_line=max_line, sort_keys=sort_keys, level=level + 1)
            for value in obj
        ]
        one_line = '[ ' + ', '.join(items) + ' ]'
        if not expand_top_level and len(one_line) + len(sp) <= max_line:
            return one_line
        return '[\n' + ',\n'.join(sp + indent_str + item for item in items) + '\n' + sp + ']'

    return json.dumps(obj)


__all__ = (
    'pretty_json',
    'save_as_json',
)
