import pytest
import json
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
from pipeline_runner.lib.printer import Printer
from pipeline_runner.lib.types import LogRecord


class MockInstance:
    def __init__(self, id, parent=None):
        self.id = id
        self.parent = parent


@pytest.fixture(autouse=True)
def reset_printer():
    Printer._history = []
    Printer._queue = []
    Printer._use_queue = False


## Orchestration Tests


def test_cherry_pick_calls_helper():
    """Verify cherry_pick delegates to the pure filter_records function."""
    instance = MockInstance(id="1")
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
            Printer._history, level=logging.ERROR, instance_id="1"
        )
        assert result == [record]


def test_replay_history_logs_records():
    """Verify replay_history correctly iterates and logs provided records."""
    printer = Printer(None, MockInstance(id="2"))
    record = MagicMock(spec=LogRecord)
    record.level = logging.INFO
    record.message = "Replayed message"
    record.kwargs = {"extra": "data"}

    with patch.object(printer.logger, "log") as mock_log:
        printer.replay_history([record])
        mock_log.assert_called_once_with(logging.INFO, "Replayed message", extra="data")


def test_save_stdout_writes_json_to_disk(tmp_path):
    """Verify save_stdout serializes history and writes to a file."""
    printer = Printer(None, MockInstance(id="3"))
    printer.print("Log line")

    file_path = tmp_path / "test_log.json"

    # We mock serialize_records to ensure the printer is using it
    with patch("pipeline_runner.lib.printer.serialize_records") as mock_serialize:
        mock_serialize.return_value = [{"msg": "serialized"}]

        printer.save_stdout(file_path)

        mock_serialize.assert_called_once_with(Printer._history)

        # Verify file content
        with open(file_path, "r") as f:
            data = json.load(f)
            assert data == [{"msg": "serialized"}]


## Message Prefix Integration Tests


def test_msg_integrates_prefix_and_args():
    """Verify msg() correctly combines prefix with first arg and passes remaining args."""
    instance = MockInstance(id="10")
    printer = Printer(None, instance)

    # We patch printer.print to see what msg() passes to it
    with patch.object(printer, "print") as mock_print:
        printer.msg("Started", "ContextA", level=logging.CRITICAL)

        # Combined header: prefix + first arg
        expected_header = "\n[10] Started"
        mock_print.assert_called_once_with(
            expected_header, "ContextA", level=logging.CRITICAL
        )


def test_msg_handles_no_args():
    """Verify msg() does not crash when called with no arguments."""
    instance = MockInstance(id="11")
    printer = Printer(None, instance)

    with patch.object(printer, "print") as mock_print:
        printer.msg()

        # Should just be the prefix + empty string
        mock_print.assert_called_once_with("\n[11] ", level=logging.INFO)


## Complex Scenario: SubTask Prefix


@patch("pipeline_runner.lib.task_types.suite_sub_task.SuiteSubTask", spec=True)
def test_msg_subtask_prefix_integration(mock_subtask_class):
    """Verify msg() uses the parent.id.id format for SubTasks."""
    parent = MockInstance(id="P1")
    subtask = MockInstance(id="S1", parent=parent)

    def side_effect(obj, cls):
        if cls.__name__ == "SuiteSubTask":
            return True
        return isinstance(obj, cls)

    with patch("builtins.isinstance", side_effect=side_effect):
        printer = Printer(None, subtask)
        with patch.object(printer, "print") as mock_print:
            printer.msg("SubTask Action")
            mock_print.assert_called_once_with(
                "\n[P1.S1] SubTask Action", level=logging.INFO
            )
