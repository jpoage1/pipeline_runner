"""Tests for lib.printer.printer_property_test."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from pipeline_runner.lib.printer import Printer


class MockInstance:
    """Mock class."""

    def __init__(self, instance_id: str) -> None:
        """Initialize the mock."""
        self.id = instance_id
        self.parent = None


class MockParent:
    """Mock class."""


@pytest.fixture(autouse=True)
def reset_printer() -> None:
    """Resets the global state of the Printer class before every test."""
    Printer._history = []
    Printer._queue = []
    Printer._use_queue = False


## Initialization Tests


def test_printer_init() -> None:
    """Verify logger and ID assignment during initialization."""
    instance = MockInstance(instance_id="1.1")
    parent = MockParent()
    printer = Printer(parent, instance)

    # Captured in a local first: printer.instance is a property call, and
    # a type checker won't narrow a None-check across repeated calls to
    # the same property the way it narrows a plain local variable.
    bound_instance = printer.instance
    assert bound_instance is not None
    assert bound_instance.id == "1.1"
    assert "pipeline.MockInstance" in printer.logger.name


## Queuing and State Management


def test_enable_disable_queue() -> None:
    """Verify queue toggle and state properties."""
    instance = MockInstance(instance_id="2")
    printer = Printer(MockParent(), instance)

    printer.enable_queue()
    assert Printer._use_queue is True

    printer.disable_queue()
    assert Printer._use_queue is False


def test_print_without_queue_calls_logger_immediately() -> None:
    """Verify logger is called directly when queue is disabled."""
    instance = MockInstance(instance_id="3")
    printer = Printer(MockParent(), instance)

    with patch.object(printer.logger, "log") as mock_log:
        printer.print("Direct message", level=logging.WARNING)

        mock_log.assert_called_once_with(logging.WARNING, "Direct message")
        assert len(Printer._history) == 1
        assert len(Printer._queue) == 0


def test_print_with_queue_stores_record() -> None:
    """Verify records are stored in the queue and not logged immediately."""
    instance = MockInstance(instance_id="4")
    printer = Printer(MockParent(), instance)
    printer.enable_queue()

    with patch.object(printer.logger, "log") as mock_log:
        printer.print("Queued message")

        mock_log.assert_not_called()
        assert len(Printer._queue) == 1
        assert Printer._queue[0].message == "Queued message"


def test_dump_flushes_queue_to_logger() -> None:
    """Verify dump/flush outputs all queued records to the logger and clears queue."""
    instance = MockInstance(instance_id="5")
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


def test_clear_history() -> None:
    """Verify history is wiped correctly."""
    printer = Printer(MockParent(), MockInstance(instance_id="6"))
    printer.print("Test")
    assert len(Printer._history) == 1

    printer.clear_history()
    assert len(Printer._history) == 0


## Prefix Logic


def test_msg_prefix_standard_task() -> None:
    """Verify prefix formatting for standard tasks."""
    instance = MockInstance(instance_id="7")
    printer = Printer(MockParent(), instance)

    assert printer.msg_prefix == "\n[7] "


def test_msg_prefix_subtask() -> None:
    """Verify prefix formatting for subtasks [ParentID.SubID]."""

    class MockParent:
        id = "8"

    sub_instance = MagicMock()
    sub_instance.id = ("P1", "S1")
    sub_instance.parent = MockParent()

    printer = Printer(MagicMock(), sub_instance)
    assert printer.msg_prefix == "\n[8.S1] "


def test_printer_properties_coverage() -> None:
    """Access properties to fulfill coverage execution branches."""
    printer = Printer(MagicMock(), MagicMock())
    _ = printer.queue
    _ = printer.logger
    _ = printer.history
    _ = printer.instance
