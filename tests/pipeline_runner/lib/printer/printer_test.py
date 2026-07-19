"""Tests for lib.printer.printer_test."""

import json
import logging
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from pipeline_runner.lib.printer import Printer
from pipeline_runner.lib.types import LogRecord


class MockInstance:
    """Mock class."""

    def __init__(self, instance_id: str, parent: Any = None) -> None:
        """Initialize the mock."""
        self.id = instance_id
        self.parent = parent


@pytest.fixture(autouse=True)
def reset_printer() -> None:
    """Verify reset_printer."""
    Printer._history = []
    Printer._queue = []
    Printer._use_queue = False


## Orchestration Tests


def test_cherry_pick_calls_helper() -> None:
    """Verify cherry_pick delegates to the pure filter_records function."""
    instance = MockInstance(instance_id="1")
    printer = Printer(None, instance)

    # Populate history manually for the test
    record = MagicMock(spec=LogRecord)
    record.level = logging.ERROR
    record.instance_id = "1"
    Printer._history = [record]

    with patch("pipeline_runner.lib.printer.filter_records") as mock_filter:
        mock_filter.return_value = [record]

        result = printer.cherry_pick(level=logging.ERROR, instance_id="1")

        mock_filter.assert_called_once_with(
            Printer._history,
            level=logging.ERROR,
            instance_id="1",
        )
        assert result == [record]


def test_replay_history_logs_records() -> None:
    """Verify replay_history correctly iterates and logs provided records."""
    printer = Printer(None, MockInstance(instance_id="2"))
    record = MagicMock(spec=LogRecord)
    record.level = logging.INFO
    record.message = "Replayed message"
    record.kwargs = {"extra": "data"}

    with patch.object(printer.logger, "log") as mock_log:
        printer.replay_history([record])
        mock_log.assert_called_once_with(logging.INFO, "Replayed message", extra="data")


def test_save_stdout_writes_json_to_disk(tmp_path: Any) -> None:
    """Verify save_stdout serializes history and writes to a file."""
    printer = Printer(None, MockInstance(instance_id="3"))
    printer.print("Log line")

    file_path = tmp_path / "test_log.json"

    # We mock serialize_records to ensure the printer is using it
    with patch("pipeline_runner.lib.printer.serialize_records") as mock_serialize:
        mock_serialize.return_value = [{"msg": "serialized"}]

        printer.save_stdout(file_path)

        mock_serialize.assert_called_once_with(Printer._history)

        # Verify file content
        with Path(file_path).open() as f:
            data = json.load(f)
            assert data == [{"msg": "serialized"}]


## Message Prefix Integration Tests


def test_msg_integrates_prefix_and_args() -> None:
    """Verify msg() combines prefix with first arg and passes remaining args."""
    instance = MockInstance(instance_id="10")
    printer = Printer(None, instance)

    # We patch printer.print to see what msg() passes to it
    with patch.object(printer, "print") as mock_print:
        printer.msg("Started", "ContextA", level=logging.CRITICAL)

        # Combined header: prefix + first arg
        expected_header = "\n[10] Started"
        mock_print.assert_called_once_with(
            expected_header,
            "ContextA",
            level=logging.CRITICAL,
        )


def test_msg_handles_no_args() -> None:
    """Verify msg() does not crash when called with no arguments."""
    instance = MockInstance(instance_id="11")
    printer = Printer(None, instance)

    with patch.object(printer, "print") as mock_print:
        printer.msg()

        # Should just be the prefix + empty string
        mock_print.assert_called_once_with("\n[11] ", level=logging.INFO)


## Complex Scenario: SubTask Prefix


def test_msg_subtask_prefix_integration() -> None:
    """Verify msg() uses the parent.id.id format for SubTasks."""
    subtask = MagicMock()
    subtask.id = ("P1", "S1")
    subtask.parent.id = "P1"

    printer = Printer(None, subtask)
    with patch.object(printer, "print") as mock_print:
        printer.msg("SubTask Action")
        mock_print.assert_called_once_with(
            "\n[P1.S1] SubTask Action",
            level=logging.INFO,
        )


def test_printer_flush_alias() -> None:
    """Verify flush delegates to dump."""

    class MockInstance:
        def __init__(self, instance_id: str) -> None:
            self.id = instance_id
            self.parent = None

    printer = Printer(MagicMock(), MockInstance(instance_id="alias"))
    with patch.object(printer, "dump") as mock_dump:
        printer.flush()
        mock_dump.assert_called_once()


def test_printer_id_property_no_instance() -> None:
    """Verify ID property returns safely when instance is unbound."""
    printer = Printer(MagicMock(), None)
    assert printer.id is None


def test_printer_id_property_bound_instance() -> None:
    """Verify ID property returns the bound instance ID."""

    class MockBoundInstance:
        id = "BoundID_1"
        parent = None

    printer = Printer(MagicMock(), MockBoundInstance())
    assert printer.id == "BoundID_1"


def test_printer_msg_prefix_standard_task() -> None:
    """Verify base task prefix formatting."""

    class MockBoundInstance:
        id = "BaseID_2"
        parent = None

    printer = Printer(MagicMock(), MockBoundInstance())
    assert printer.msg_prefix == "\n[BaseID_2] "


def test_printer_msg_prefix_import() -> None:
    """Verify the inner import of SuiteSubTask during msg_prefix execution."""

    class MockInstance:
        id = "99"
        parent = None

    printer = Printer(MagicMock(), MockInstance())
    assert printer.msg_prefix == "\n[99] "
