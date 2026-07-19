"""Tests for lib.printer.test_printer_helpers."""

import logging
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from pipeline_runner.lib.printer_helpers import (
    clear_screen,
    filter_records,
    reconstruct_message,
    serialize_records,
)
from pipeline_runner.lib.types import LogRecord


@pytest.fixture
def sample_records() -> Any:
    """Provides a consistent set of LogRecord objects for testing."""
    now = datetime(2026, 4, 1, 12, 0, 0, tzinfo=UTC)
    return [
        LogRecord(
            timestamp=now,
            level=logging.INFO,
            message="Message 1",
            instance_id="1.1",
            args=("Message", 1),
            kwargs={},
        ),
        LogRecord(
            timestamp=now,
            level=logging.ERROR,
            message="Message 2",
            instance_id="1.2",
            args=("Message", 2),
            kwargs={},
        ),
        LogRecord(
            timestamp=now,
            level=logging.DEBUG,
            message="Message 3",
            instance_id="1.1",
            args=("Message", 3),
            kwargs={},
        ),
    ]


## filter_records Tests


def test_filter_records_no_criteria(sample_records: Any) -> None:
    """Verify returning full history when no filters are applied."""
    result = filter_records(sample_records)
    assert len(result) == 3


def test_filter_records_by_level(sample_records: Any) -> None:
    """Verify filtering by minimum log level (inclusive)."""
    # Should find INFO (20) and ERROR (40), excluding DEBUG (10)
    result = filter_records(sample_records, level=logging.INFO)
    assert len(result) == 2
    assert all(r.level >= logging.INFO for r in result)


def test_filter_records_by_instance_id(sample_records: Any) -> None:
    """Verify filtering by specific task instance ID."""
    result = filter_records(sample_records, instance_id="1.1")
    assert len(result) == 2
    assert all(r.instance_id == "1.1" for r in result)


def test_filter_records_combined_criteria(sample_records: Any) -> None:
    """Verify filtering by both level and instance ID."""
    result = filter_records(sample_records, level=logging.INFO, instance_id="1.1")
    assert len(result) == 1
    assert result[0].message == "Message 1"


## serialize_records Tests


def test_serialize_records_structure(sample_records: Any) -> None:
    """Verify LogRecord conversion to serializable dictionary format."""
    result = serialize_records(sample_records)

    assert len(result) == 3
    first = result[0]
    assert first["timestamp"] == "2026-04-01T12:00:00+00:00"
    assert first["level"] == "INFO"
    assert first["instance_id"] == "1.1"
    assert first["message"] == "Message 1"
    # Ensure raw args/kwargs are not in the serialized output
    assert "args" not in first
    assert "kwargs" not in first


## reconstruct_message Tests


def test_reconstruct_message_joins_args() -> None:
    """Verify reconstruction of string from multiple positional arguments."""
    record = LogRecord(
        timestamp=datetime.now(UTC),
        level=logging.INFO,
        message="ignored",
        instance_id="1",
        args=("Task", 101, "started"),
        kwargs={},
    )
    assert reconstruct_message(record) == "Task 101 started"


def test_reconstruct_message_single_arg() -> None:
    """Verify reconstruction with a single argument."""
    record = LogRecord(
        timestamp=datetime.now(UTC),
        level=logging.INFO,
        message="ignored",
        instance_id="1",
        args=("Standalone",),
        kwargs={},
    )
    assert reconstruct_message(record) == "Standalone"


## clear_screen Tests


@patch("pipeline_runner.lib.printer_helpers.subprocess.run")
def test_clear_screen_nt(mock_run: MagicMock) -> None:
    """Verify clear command is executed on all platforms."""
    clear_screen()
    mock_run.assert_called_once_with(["/usr/bin/clear"], check=False)


@patch("pipeline_runner.lib.printer_helpers.subprocess.run")
def test_clear_screen_posix(mock_run: MagicMock) -> None:
    """Verify clear command is executed on all platforms."""
    clear_screen()
    mock_run.assert_called_once_with(["/usr/bin/clear"], check=False)


@patch("pipeline_runner.lib.printer_helpers.subprocess.run")
def test_clear_screen(mock_run: MagicMock) -> None:
    """Verify OS-level screen clear delegation."""
    clear_screen()
    mock_run.assert_called_with(["/usr/bin/clear"], check=False)
