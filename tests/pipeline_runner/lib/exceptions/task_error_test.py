import pytest
from unittest.mock import MagicMock
from unittest.mock import patch
from pipeline_runner.lib.exceptions import TaskError


class MockParent:
    def __init__(self):
        self.dump_called = False

    def dump_print_queue(self):
        self.dump_called = True


## TaskError Tests


def test_task_error_inheritance_and_exit():
    """Verify TaskError correctly calls super() and exits."""
    parent = MockParent()
    with pytest.raises(SystemExit) as e:
        TaskError(parent, "Task Failed")

    assert e.value.code == 1
    assert parent.dump_called is True


@patch("traceback.print_stack")
def test_task_error_prints_traceback(mock_traceback):
    """Verify that traceback is printed when error is non-critical."""
    parent = MockParent()
    with pytest.raises(SystemExit):
        TaskError(parent, "Traceback Check")

    mock_traceback.assert_called()


@patch("sys.exit")
@patch("traceback.print_stack")
def test_task_error_non_critical(mock_stack, mock_exit):
    """Verify non-critical stack trace printing."""
    parent = MagicMock()
    type(parent).__name__ = "MockParent"

    TaskError(parent, "error message", critical=False)
    mock_stack.assert_called()


@patch("sys.exit")
def test_task_error_critical(mock_exit):
    """Verify critical runtime error escalation."""
    parent = MagicMock()
    type(parent).__name__ = "MockParent"

    with pytest.raises(
        Exception, match="There was an error while handling an exception: error message"
    ):
        TaskError(parent, "error message", critical=True)


@patch("pipeline_runner.lib.exceptions.SuiteError.__init__", return_value=None)
def test_task_error_critical_branch(mock_super_init):
    """Bypass SuiteError exception escalation to evaluate TaskError's isolated critical branch."""
    parent = MagicMock()
    with pytest.raises(RuntimeError, match="isolated critical failure"):
        TaskError(parent, "isolated critical failure", critical=True)


@patch("pipeline_runner.lib.exceptions.SuiteError.__init__", return_value=None)
@patch("traceback.print_stack")
def test_task_error_non_critical_branch(mock_stack, mock_super_init):
    """Bypass SuiteError exception escalation to evaluate TaskError's non-critical branch."""
    from pipeline_runner.lib.exceptions import TaskError
    from unittest.mock import MagicMock

    parent = MagicMock()
    TaskError(parent, "isolated non-critical failure", critical=False)
    mock_stack.assert_called_once()
