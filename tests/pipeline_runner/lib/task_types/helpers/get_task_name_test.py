"""Tests for lib.task_types.helpers.get_task_name_test."""

from pipeline_runner.lib.task_types.helpers import get_task_name


class MockTaskClass:
    """Mock class."""


def test_get_task_name_variations() -> None:
    """Verify get_task_name_variations."""
    assert get_task_name("SimpleString") == "SimpleString"
    assert get_task_name(MockTaskClass) == "MockTaskClass"
    assert get_task_name(123) == "123"
