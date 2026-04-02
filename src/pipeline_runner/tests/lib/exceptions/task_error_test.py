import pytest
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
