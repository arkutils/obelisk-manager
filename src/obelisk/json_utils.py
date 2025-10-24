import re
import json
from pathlib import Path
from typing import Any


SHRINK_MOD_REGEX3 = r'{\n\s+(.+: .*),\n\s+(.+: .*),\n\s+(.+: .*)\n\s+}'
SHRINK_MOD_REGEX4 = r'{\n\s+(.+: .*),\n\s+(.+: .*),\n\s+(.+: .*),\n\s+(.+: .*)\n\s+}'
SHRINK_MOD_REGEX5 = r'{\n\s+(.+: .*),\n\s+(.+: .*),\n\s+(.+: .*),\n\s+(.+: .*),\n\s+(.+: .*)\n\s+}'


def save_as_json(path: Path, data: Any) -> None:
    """
    Save the given data as JSON to the specified path.
    This uses a customised formatting to shrink mod dicts to single lines where possible.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('wt', encoding='utf-8', newline='\n') as f:
        content = json.dumps(data, indent='\t')
        content = re.sub(SHRINK_MOD_REGEX3, r'{ \1, \2, \3 }', content)
        content = re.sub(SHRINK_MOD_REGEX4, r'{ \1, \2, \3, \4 }', content)
        content = re.sub(SHRINK_MOD_REGEX5, r'{ \1, \2, \3, \4, \5 }', content)
        f.write(content)


__all__ = ('save_as_json',)
