import json
import logging
from pathlib import Path
from datetime import datetime

from typing import TYPE_CHECKING, Optional, List, Any

from pipeline_runner.lib.types import LogRecord
from pipeline_runner.lib.printer_helpers import serialize_records, filter_records

if TYPE_CHECKING:
    from pipeline_runner.lib.task_types.suite_task import SuiteTask


logging.basicConfig(level=logging.INFO, format="%(message)s")


class Printer:
    _history: List[LogRecord] = []
    _queue: List[LogRecord] = []
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

        self._logger = logging.getLogger(f"pipeline.{type(instance).__name__}")

    def _create_record(self, level: int, *args, **kwargs) -> LogRecord:
        """Internal helper to convert args/kwargs into a structured record."""
        msg_str = " ".join(map(str, args))
        return LogRecord(
            timestamp=datetime.now(),
            level=level,
            message=msg_str,
            instance_id=self.instance.id,
            args=args,
            kwargs=kwargs,
        )

    def dump(self):
        """Flushes the current queue to the console and clears it."""
        for record in Printer._queue:
            self.logger.log(record.level, record.message, **record.kwargs)
        Printer._queue = []

    def print(self, *args, level: int = logging.INFO, **kwargs):
        record = self._create_record(level, *args, **kwargs)
        Printer._history.append(record)

        if Printer.use_queue:
            Printer._queue.append(record)
        else:
            self.logger.log(level, record.message, **kwargs)

    def flush(self):
        """Alias for dump."""
        self.dump()

    def clear_history(self):
        """Wipes the global history cache."""
        Printer._history = []

    def cherry_pick(
        self, level: Optional[int] = None, instance_id: Any = None
    ) -> List[LogRecord]:
        """Calls the pure filter function using the current history."""
        return filter_records(Printer._history, level=level, instance_id=instance_id)

    def replay_history(self, records: List[LogRecord]):
        """Side-effect: Outputs provided records to the logger."""
        for r in records:
            self.logger.log(r.level, r.message, **r.kwargs)

    def save_stdout(self, _file_path: Path | str):
        """Uses the pure serializer to prepare data, then handles the I/O side effect."""
        file_path = Path(_file_path).resolve()

        # 1. Transform data purely
        serializable_data = serialize_records(Printer._history)

        # 2. Perform the side effect (writing to disk)
        with open(file_path, "w") as f:
            json.dump(serializable_data, f, indent=4)

    def msg(self, *args, level: int = logging.INFO, **kwargs):
        """Standardized message logger with prefix."""
        # 1. Get the prefix (e.g., "\n[1.2] ")
        prefix = self.msg_prefix

        # 2. Extract the first message if it exists, otherwise use an empty string
        # This prevents an IndexError if msg() is called without arguments
        first_msg = args[0] if args else ""

        # 3. Combine the prefix and the first message into one string
        combined_header = f"{prefix}{first_msg}"

        # 4. Capture the remaining messages (if any)
        remaining_args = args[1:]

        # 5. Send the combined header + everything else to the print method
        # We use *remaining_args to "unpack" the rest of the tuple
        self.print(combined_header, *remaining_args, level=level, **kwargs)

    def enable_queue(self):
        Printer._use_queue = True

    def disable_queue(self):
        Printer._use_queue = False
        self.dump()

    @property
    def history(self):
        return self._history

    @property
    def queue(self):
        return self._queue

    @property
    def use_queue(self):
        return self._use_queue

    @property
    def logger(self):
        return self._logger

    @property
    def instance(self):
        return self._instance

    @property
    def id(self):
        if self._instance is not None:
            return self._instance.id

    @property
    def msg_prefix(self):
        # Format: [ID] for main tasks, [ID.Sub] for subtasks
        from pipeline_runner.lib.task_types.suite_sub_task import SuiteSubTask

        if isinstance(self._instance, SuiteSubTask):
            return f"\n[{self.instance.parent.id}.{self.instance.id}] "
        return f"\n[{self.instance.id}] "
