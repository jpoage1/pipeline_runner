import pytest
from unittest.mock import MagicMock
from pipeline_runner.lib.types import TaskStatus
from pipeline_runner.lib.task_types.helpers import (
    validate_task_list,
    format_task_result,
    get_task_status,
    prepare_task_init,
)


def test_validate_task_list():
    class ValidTask:
        __name__ = "ValidTask"

        def __call__(self):
            pass

    # Primitives or instances lack a __name__ attribute by default
    InvalidTask = 123
    AnotherInvalid = "string_task"

    res = validate_task_list([ValidTask, InvalidTask, AnotherInvalid])
    assert len(res) == 1
    assert res[0][0] == "ValidTask"


def test_format_task_result():
    assert format_task_result("T1", True) == {"T1": True}


def test_get_task_status_missing():
    assert get_task_status("Missing", {}, {}, {}) == TaskStatus.MISSING


def test_prepare_task_init_missing():
    cls, args = prepare_task_init("Missing", {}, None)
    assert cls is None
    assert args is None


def test_get_task_name_string_input():
    """Verify string inputs return themselves directly."""
    from pipeline_runner.lib.task_types.helpers import get_task_name

    assert get_task_name("ExplicitStringName") == "ExplicitStringName"


def test_get_task_status_completed():
    """Verify task lifecycle registers as COMPLETED."""
    from pipeline_runner.lib.task_types.helpers import get_task_status
    from pipeline_runner.lib.types import TaskStatus

    assert (
        get_task_status("DoneTask", {"DoneTask": 1}, {}, {"DoneTask": 1})
        == TaskStatus.COMPLETED
    )
