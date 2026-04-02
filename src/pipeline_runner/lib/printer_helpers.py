import os
import logging
from typing import List, Optional, Any

from pipeline_runner.lib.types import LogRecord


def filter_records(
    history: List[LogRecord], level: Optional[int] = None, instance_id: Any = None
) -> List[LogRecord]:
    """Purely filters LogRecord objects based on criteria."""
    filtered = history
    if level is not None:
        filtered = [r for r in filtered if r.level >= level]
    if instance_id is not None:
        filtered = [r for r in filtered if r.instance_id == instance_id]
    return filtered


def serialize_records(history: List[LogRecord]) -> List[dict]:
    """Purely converts LogRecord objects into a list of serializable dictionaries."""
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
    """Purely reconstructs a printable string from a LogRecord."""
    # This handles cases where multiple args were passed to print()
    return " ".join(map(str, record.args))


def clear_screen():
    """Clear the screen on both NT and *nix systems."""
    os.system("cls" if os.name == "nt" else "clear")
