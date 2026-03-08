import os
import json
from pathlib import Path
from typing import List

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from pipeline_runner.lib.task_types import SuiteTask


def clear_screen():
    """Clear the screen on both NT and *nix systems."""
    os.system("cls" if os.name == "nt" else "clear")


class Printer:
    _queue: List = []
    _cache: List = []
    _use_queue: bool = False
    _parent: Optional["SuiteTask"] = None
    _instance = None

    def __init__(
        self,
        parent,
        instance,
    ):
        self._parent = parent
        self._instance = instance
        self._parent_id = type(parent)
        self._instance_id = instance.get_id()

    def dump(self):
        for args, kwargs in Printer._queue:
            print(*args, **kwargs)
        Printer._queue = []

    def print(self, *args, **kwargs):
        payload = [args, kwargs]
        Printer._cache.append(payload)
        if Printer._use_queue:
            Printer._queue.append(payload)

        else:
            print(*args, flush=True, **kwargs)

    def flush(self):
        for args, kwargs in Printer._queue:
            print(*args, **kwargs)
        Printer._queue = []

    def save_stdout(self, _file_path: Path | str):
        file_path = Path(_file_path).resolve()
        with open(file_path, "w") as f:
            try:
                for line in Printer._cache:
                    try:
                        f.write(line)
                    except:
                        f.write(json.dumps(line))
            except Exception as e:
                print(e.with_traceback)
                raise e

    def _msg_prefix(self):
        # Format: [ID] for main tasks, [ID.Sub] for subtasks
        from pipeline_runner.lib.task_types import SuiteSubTask

        if isinstance(self._instance, SuiteSubTask):
            return f"\n[{self._instance.parent_id}.{self._instance.sub_id}] "
        return f"\n[{self._instance._id}] "

    def msg(self, *args, **kwargs):
        """Standardized message logger."""

        self.print(self._msg_prefix(), *args, **kwargs)

    def enable_queue(self):
        Printer._use_queue = True

    def disable_queue(self):
        Printer._use_queue = False
        self.dump()
