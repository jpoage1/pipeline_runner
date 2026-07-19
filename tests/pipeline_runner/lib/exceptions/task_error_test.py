"""Tests for lib.exceptions.task_error_test."""

from unittest.mock import MagicMock, patch

import pytest

from pipeline_runner.lib.exceptions import TaskError


class MockParent:
    """Mock class."""

    def __init__(self) -> None:
        """Initialize the mock."""
        self.dump_called = False

    def dump_print_queue(self) -> None:
        """Mock method."""
        self.dump_called = True


## TaskError Tests


def test_task_error_inheritance_and_exit() -> None:
    """Verify TaskError correctly calls super() and exits."""
    parent = MockParent()
    with pytest.raises(SystemExit) as e:
        TaskError(parent, "Task Failed")

    assert e.value.code == 1
    assert parent.dump_called is True


@patch("traceback.print_stack")
def test_task_error_prints_traceback(mock_traceback: MagicMock) -> None:
    """Verify that traceback is printed when error is non-critical."""
    parent = MockParent()
    with pytest.raises(SystemExit):
        TaskError(parent, "Traceback Check")

    mock_traceback.assert_called()


@patch("traceback.print_stack")
def test_task_error_non_critical(mock_stack: MagicMock) -> None:
    """Verify non-critical stack trace printing."""
    parent = MagicMock()
    type(parent).__name__ = "MockParent"

    with patch("sys.exit"):
        TaskError(parent, "error message", critical=False)
    mock_stack.assert_called()


def test_task_error_critical() -> None:
    """Verify critical runtime error escalation."""
    parent = MagicMock()
    type(parent).__name__ = "MockParent"

    with pytest.raises(RuntimeError), patch("sys.exit"):
        TaskError(parent, "error message", critical=True)


def test_task_error_critical_branch() -> None:
    """Bypass SuiteError escalation to evaluate TaskError's isolated critical branch."""
    parent = MagicMock()
    with (
        patch("pipeline_runner.lib.exceptions.SuiteError.__init__", return_value=None),
        pytest.raises(RuntimeError, match="isolated critical failure"),
    ):
        TaskError(parent, "isolated critical failure", critical=True)


@patch("traceback.print_stack")
def test_task_error_non_critical_branch(
    mock_stack: MagicMock,
) -> None:
    """Bypass SuiteError escalation to evaluate TaskError's non-critical branch."""
    with patch("pipeline_runner.lib.exceptions.SuiteError.__init__", return_value=None):
        parent = MagicMock()
        TaskError(parent, "isolated non-critical failure", critical=False)
    mock_stack.assert_called_once()
