"""Pure helper functions for the printer system."""

import logging
import subprocess
from typing import Any

from pipeline_runner.lib.types import LogRecord


def filter_records(
    history: list[LogRecord],
    level: int | None = None,
    instance_id: Any = None,
) -> list[LogRecord]:
    """Filter LogRecord objects based on criteria."""
    filtered = history
    if level is not None:
        filtered = [r for r in filtered if r.level >= level]
    if instance_id is not None:
        filtered = [r for r in filtered if r.instance_id == instance_id]
    return filtered


def serialize_records(history: list[LogRecord]) -> list[dict[str, Any]]:
    """Convert LogRecord objects into serializable dictionaries."""
    return [
        {
            "timestamp": r.timestamp.isoformat(),
            "level": logging.getLevelName(r.level),
            "instance_id": str(r.instance_id),
            "message": r.message,
        }
        for r in history
    ]


def reconstruct_message(record: LogRecord) -> str:
    """Reconstruct a printable string from a LogRecord."""
    return " ".join(map(str, record.args))


def clear_screen() -> None:
    """Clear the screen on both NT and *nix systems."""
    subprocess.run(["/usr/bin/clear"], check=False)
