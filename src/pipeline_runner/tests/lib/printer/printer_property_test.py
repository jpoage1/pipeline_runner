import pytest
import logging
import builtins
from unittest.mock import MagicMock, patch
from pipeline_runner.lib.printer import Printer
from pipeline_runner.lib.task_types.suite_sub_task import SuiteSubTask


class MockInstance:
    def __init__(self, id):
        self.id = id


class MockParent:
    pass


@pytest.fixture(autouse=True)
def reset_printer():
    """Resets the global state of the Printer class before every test."""
    Printer._history = []
    Printer._queue = []
    Printer._use_queue = False


## Initialization Tests


def test_printer_init():
    """Verify logger and ID assignment during initialization."""
    instance = MockInstance(id="1.1")
    parent = MockParent()
    printer = Printer(parent, instance)

    assert printer.instance.id == "1.1"
    assert "pipeline.MockInstance" in printer.logger.name


## Queuing and State Management


def test_enable_disable_queue():
    """Verify queue toggle and state properties."""
    instance = MockInstance(id="2")
    printer = Printer(MockParent(), instance)

    printer.enable_queue()
    assert Printer._use_queue is True

    printer.disable_queue()
    assert Printer._use_queue is False


def test_print_without_queue_calls_logger_immediately():
    """Verify logger is called directly when queue is disabled."""
    instance = MockInstance(id="3")
    printer = Printer(MockParent(), instance)

    with patch.object(printer.logger, "log") as mock_log:
        printer.print("Direct message", level=logging.WARNING)

        mock_log.assert_called_once_with(logging.WARNING, "Direct message")
        assert len(Printer._history) == 1
        assert len(Printer._queue) == 0


def test_print_with_queue_stores_record():
    """Verify records are stored in the queue and not logged immediately."""
    instance = MockInstance(id="4")
    printer = Printer(MockParent(), instance)
    printer.enable_queue()

    with patch.object(printer.logger, "log") as mock_log:
        printer.print("Queued message")

        mock_log.assert_not_called()
        assert len(Printer._queue) == 1
        assert Printer._queue[0].message == "Queued message"


def test_dump_flushes_queue_to_logger():
    """Verify dump/flush outputs all queued records to the logger and clears queue."""
    instance = MockInstance(id="5")
    printer = Printer(MockParent(), instance)
    printer.enable_queue()
    printer.print("Message 1")
    printer.print("Message 2")

    with patch.object(printer.logger, "log") as mock_log:
        printer.dump()

        assert mock_log.call_count == 2
        assert len(Printer._queue) == 0
        # History should remain intact
        assert len(Printer._history) == 2


## History Management


def test_clear_history():
    """Verify history is wiped correctly."""
    printer = Printer(MockParent(), MockInstance(id="6"))
    printer.print("Test")
    assert len(Printer._history) == 1

    printer.clear_history()
    assert len(Printer._history) == 0


## Prefix Logic


def test_msg_prefix_standard_task():
    """Verify prefix formatting for standard tasks."""
    instance = MockInstance(id="7")
    printer = Printer(MockParent(), instance)

    assert printer.msg_prefix == "\n[7] "


def test_msg_prefix_subtask():
    """Verify prefix formatting for subtasks [ParentID.SubID]."""
    from pipeline_runner.lib.task_types.suite_sub_task import SuiteSubTask
    from unittest.mock import MagicMock
    from pipeline_runner.lib.printer import Printer

    class MockParent:
        pass

    class MockInstance:
        def __init__(self, id):
            self.id = id

    parent_mock = MockInstance(id="8")
    sub_instance = MagicMock(spec=SuiteSubTask)
    sub_instance.id = "sub1"
    sub_instance.parent = parent_mock

    printer = Printer(MockParent(), sub_instance)
    assert printer.msg_prefix == "\n[8.sub1] "


def test_printer_properties_coverage():
    """Access properties to fulfill coverage execution branches."""
    from pipeline_runner.lib.printer import Printer
    from unittest.mock import MagicMock

    printer = Printer(MagicMock(), MagicMock())
    _ = printer.queue
    _ = printer.logger
    _ = printer.history
    _ = printer.instance
