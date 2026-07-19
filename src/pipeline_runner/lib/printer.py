"""Logging and message formatting for pipeline tasks."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ClassVar, Optional, Protocol, runtime_checkable

from pipeline_runner.lib.printer_helpers import filter_records, serialize_records
from pipeline_runner.lib.types import LogRecord

logging.basicConfig(level=logging.INFO, format="%(message)s")


@runtime_checkable
class HasId(Protocol):
    """Structural protocol: anything with ``.id`` and optionally ``.parent``."""

    @property
    def id(self) -> Any:
        """Return the instance's identifier."""

    @property
    def parent(self) -> Optional["HasId"]:
        """Return the instance's parent, if any."""


class Printer:
    """Manages structured logging with queue, history, and prefix support."""

    _history: ClassVar[list[LogRecord]] = []
    _queue: ClassVar[list[LogRecord]] = []
    _use_queue: bool = False
    _parent: object = None
    _instance: Optional["HasId"] = None

    def __init__(
        self,
        parent: object,
        instance: Optional["HasId"],
    ) -> None:
        """Initialize the printer with parent context and optional instance."""
        self._parent = parent
        self._instance = instance
        self._parent_id = type(parent)
        self._logger = logging.getLogger(f"pipeline.{type(instance).__name__}")

    def _create_record(self, level: int, *args: Any, **kwargs: Any) -> LogRecord:
        """Convert args/kwargs into a structured record."""
        msg_str = " ".join(map(str, args))
        return LogRecord(
            timestamp=datetime.now(UTC),
            level=level,
            message=msg_str,
            instance_id=self.instance.id if self.instance is not None else None,
            args=args,
            kwargs=kwargs,
        )

    def dump(self) -> None:
        """Flush the current queue to the console and clear it."""
        for record in Printer._queue:
            self.logger.log(record.level, record.message, **record.kwargs)
        Printer._queue = []

    def print(self, *args: Any, level: int = logging.INFO, **kwargs: Any) -> None:
        """Record a log entry in history and optionally send to logger."""
        record = self._create_record(level, *args, **kwargs)
        Printer._history.append(record)

        if Printer._use_queue:
            Printer._queue.append(record)
        else:
            self.logger.log(level, record.message, **kwargs)

    def flush(self) -> None:
        """Alias for dump."""
        self.dump()

    def clear_history(self) -> None:
        """Wipe the global history cache."""
        Printer._history = []

    def cherry_pick(
        self,
        level: int | None = None,
        instance_id: Any | None = None,
    ) -> list[LogRecord]:
        """Filter history by level and/or instance id."""
        return filter_records(Printer._history, level=level, instance_id=instance_id)

    def replay_history(self, records: list[LogRecord]) -> None:
        """Output provided records to the logger."""
        for r in records:
            self.logger.log(r.level, r.message, **r.kwargs)

    def save_stdout(self, _file_path: Path | str) -> None:
        """Serialize history to a JSON file."""
        file_path = Path(_file_path).resolve()
        serializable_data = serialize_records(Printer._history)
        with Path(file_path).open("w") as f:
            json.dump(serializable_data, f, indent=4)

    def msg(self, *args: Any, level: int = logging.INFO, **kwargs: Any) -> None:
        """Log a message with a structured prefix."""
        prefix = self.msg_prefix
        first_msg = args[0] if args else ""
        combined_header = f"{prefix}{first_msg}"
        remaining_args = args[1:]
        self.print(combined_header, *remaining_args, level=level, **kwargs)

    def enable_queue(self) -> None:
        """Enable queue mode (buffers messages)."""
        Printer._use_queue = True

    def disable_queue(self) -> None:
        """Disable queue mode and flush."""
        Printer._use_queue = False
        self.dump()

    @property
    def history(self) -> list[LogRecord]:
        """Return the global history list."""
        return self._history

    @property
    def queue(self) -> list[LogRecord]:
        """Return the global queue list."""
        return self._queue

    @property
    def logger(self) -> logging.Logger:
        """Return the logger instance."""
        return self._logger

    @property
    def instance(self) -> Optional["HasId"]:
        """Return the bound instance, if any."""
        return self._instance

    @property
    def id(self) -> Any | None:
        """Return the bound instance's id, or None if unbound."""
        if self._instance is not None:
            return self._instance.id
        return None

    @property
    def msg_prefix(self) -> str:
        """Format prefix: [ID], [ID.Sub], or [unbound]."""
        instance = self._instance
        if instance is None:
            return "\n[unbound] "
        raw_id = instance.id
        if type(raw_id) is tuple:
            parent = instance.parent
            parent_id: int | str = parent.id if parent is not None else "unbound"
            sub_id = f"{raw_id[1]}"
            return f"\n[{parent_id}.{sub_id}] "
        return f"\n[{raw_id}] "
