import sys
import functools

from rich.console import Console
from rich.segment import Segment


class CustomRichConsole(Console):
    def log(self, *args, **kwargs) -> None:  # type: ignore
        # Backup existing before override
        bak_split_and_crop_lines = Segment.split_and_crop_lines
        bak_width = self.width

        try:
            # Override for custom behavior
            Segment.split_and_crop_lines = functools.partial(
                Segment.split_and_crop_lines,
                pad=False,
            )  # type: ignore
            self.width = sys.maxsize

            result = super().log(*args, **kwargs)  # type: ignore
            return result
        finally:
            # Restore to original
            Segment.split_and_crop_lines = bak_split_and_crop_lines
            self.width = bak_width
