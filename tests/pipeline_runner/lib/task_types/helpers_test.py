"""Tests for lib.task_types.helpers_test."""

from typing import Any

from pipeline_runner.lib.task_types.helpers import (
    format_task_result,
    get_task_name,
    get_task_status,
    prepare_task_init,
    validate_task_list,
)
from pipeline_runner.lib.types import TaskStatus


def test_validate_task_list() -> None:
    """Verify validate_task_list."""

    class ValidTask:
        __name__ = "ValidTask"

        def __call__(self) -> None:
            pass

    # Primitives or instances lack a __name__ attribute by default
    invalid_task = 123
    another_invalid = "string_task"

    task_inputs: list[Any] = [ValidTask, invalid_task, another_invalid]
    res = validate_task_list(task_inputs)
    assert len(res) == 1
    assert res[0][0] == "ValidTask"


def test_format_task_result() -> None:
    """Verify format_task_result."""
    assert format_task_result("T1", result=True) == {"T1": True}


def test_get_task_status_missing() -> None:
    """Verify get_task_status_missing."""
    assert get_task_status("Missing", {}, {}, {}) == TaskStatus.MISSING


def test_prepare_task_init_missing() -> None:
    """Verify prepare_task_init_missing."""
    cls, args = prepare_task_init("Missing", {}, None)
    assert cls is None
    assert args is None


def test_get_task_name_string_input() -> None:
    """Verify string inputs return themselves directly."""
    assert get_task_name("ExplicitStringName") == "ExplicitStringName"


def test_get_task_status_completed() -> None:
    """Verify task lifecycle registers as COMPLETED."""

    class FakeTask:
        pass

    assert (
        get_task_status("DoneTask", {"DoneTask": FakeTask}, {}, {"DoneTask": FakeTask})
        == TaskStatus.COMPLETED
    )
